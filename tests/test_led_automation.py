"""Check LED decision transitions, event retention, and local HTTP controls."""

import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from backend.event_detector import LedAutomation
from backend.event_store import EventStore, MAX_RETENTION
from backend.tool_server import ToolState, handler_for


class EventStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store_file = Path(self.temp_dir.name) / "test_events.json"
        self.store = EventStore(storage_path=self.store_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_and_retrieve_event(self):
        event = self.store.add_event(
            event_type="LIGHT_TRIGGERED",
            title="Automatic light turned on",
            description="Darkness detected while standing posture was present.",
            severity="info",
            source="automation",
            is_simulated=True,
        )
        self.assertEqual(event["event_type"], "LIGHT_TRIGGERED")
        self.assertTrue(event["is_simulated"])
        self.assertEqual(event["severity"], "info")
        events = self.store.get_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["id"], event["id"])

    def test_rolling_retention_capped_at_100(self):
        for i in range(125):
            self.store.add_event(event_type="TEST_EVENT", title=f"Event {i}",
                                 description="Retention test", is_simulated=True)
        events = self.store.get_events()
        self.assertEqual(len(events), MAX_RETENTION)
        self.assertEqual(events[0]["title"], "Event 25")
        self.assertEqual(events[-1]["title"], "Event 124")

    def test_clear_events(self):
        self.store.add_event("TYPE", "Title", "Desc")
        self.assertEqual(len(self.store.get_events()), 1)
        self.store.clear()
        self.assertEqual(len(self.store.get_events()), 0)


class LedAutomationUnitTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store_file = Path(self.temp_dir.name) / "events.json"
        self.store = EventStore(storage_path=self.store_file)
        self.automation = LedAutomation(event_store=self.store)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_dark_and_standing_turns_led_on(self):
        state = self.automation.evaluate(light_state="dark", posture_estimate="standing", is_fresh=True)
        self.assertTrue(state)
        self.assertTrue(self.automation.led_on)
        self.assertEqual(self.automation.led_state, "on")

    def test_02_dark_and_sitting_turns_led_off(self):
        state = self.automation.evaluate(light_state="dark", posture_estimate="sitting", is_fresh=True)
        self.assertFalse(state)
        self.assertFalse(self.automation.led_on)
        self.assertEqual(self.automation.led_state, "off")

    def test_03_bright_and_standing_turns_led_off(self):
        state = self.automation.evaluate(light_state="bright", posture_estimate="standing", is_fresh=True)
        self.assertFalse(state)
        self.assertFalse(self.automation.led_on)

    def test_04_bright_and_sitting_turns_led_off(self):
        state = self.automation.evaluate(light_state="bright", posture_estimate="sitting", is_fresh=True)
        self.assertFalse(state)
        self.assertFalse(self.automation.led_on)

    def test_05_off_to_on_logs_light_triggered_once(self):
        self.assertFalse(self.automation.led_on)
        self.automation.evaluate(light_state="dark", posture_estimate="standing", is_fresh=True, is_simulated=True)
        events = self.store.get_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "LIGHT_TRIGGERED")
        self.assertEqual(events[0]["title"], "Automatic light turned on")
        self.assertEqual(events[0]["severity"], "info")
        self.assertEqual(events[0]["source"], "automation")
        self.assertTrue(events[0]["is_simulated"])

    def test_06_staying_on_does_not_duplicate_event(self):
        self.automation.evaluate("dark", "standing", True)
        self.assertEqual(len(self.store.get_events()), 1)
        for _ in range(9):
            self.automation.evaluate("dark", "standing", True)
        self.assertEqual(len(self.store.get_events()), 1)

    def test_07_on_to_off_logs_recovery_once(self):
        self.automation.evaluate("dark", "standing", True)
        self.assertEqual(len(self.store.get_events()), 1)
        self.automation.evaluate("dark", "sitting", True)
        events = self.store.get_events()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[1]["event_type"], "RECOVERY")
        self.assertEqual(events[1]["title"], "Automatic light turned off")
        self.assertEqual(events[1]["description"], "Automatic light condition cleared")
        self.assertEqual(events[1]["severity"], "info")
        for _ in range(5):
            self.automation.evaluate("dark", "sitting", True)
        self.assertEqual(len(self.store.get_events()), 2)

    def test_08_stale_sensor_turns_led_off_and_logs_recovery(self):
        self.automation.evaluate("dark", "standing", True)
        self.assertTrue(self.automation.led_on)
        self.automation.evaluate("dark", "standing", is_fresh=False)
        self.assertFalse(self.automation.led_on)
        events = self.store.get_events()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[1]["event_type"], "RECOVERY")

    def test_09_unknown_posture_turns_led_off(self):
        self.automation.evaluate("dark", "standing", True)
        self.assertTrue(self.automation.led_on)
        self.automation.evaluate("dark", "unknown", True)
        self.assertFalse(self.automation.led_on)

    def test_10_invalid_light_state_handled_safely(self):
        for invalid_light in [None, "", "dim", 123, False, "DARKNESS"]:
            state = self.automation.evaluate(light_state=invalid_light, posture_estimate="standing", is_fresh=True)
            self.assertFalse(state)
        self.assertEqual(len(self.store.get_events()), 0)

    def test_11_fail_safe_method(self):
        self.automation.evaluate("dark", "standing", True)
        self.assertTrue(self.automation.led_on)
        self.automation.fail_safe()
        self.assertFalse(self.automation.led_on)
        events = self.store.get_events()
        self.assertEqual(events[-1]["event_type"], "RECOVERY")
        self.automation.fail_safe()
        self.assertEqual(len(self.store.get_events()), 2)

    def test_12_demo_vs_live_mode_events(self):
        self.automation.evaluate("dark", "standing", True, is_simulated=True)
        self.assertTrue(self.store.get_events()[-1]["is_simulated"])
        self.automation.evaluate("bright", "standing", True, is_simulated=True)
        self.assertTrue(self.store.get_events()[-1]["is_simulated"])
        self.automation.evaluate("dark", "standing", True, is_simulated=False)
        self.assertFalse(self.store.get_events()[-1]["is_simulated"])
        self.automation.evaluate("bright", "standing", True, is_simulated=False)
        self.assertFalse(self.store.get_events()[-1]["is_simulated"])


class ToolServerLedIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        temp_path = Path(cls.temp.name)
        cls.state = ToolState(demo=True,
                              state_path=temp_path / "greeting_state.json",
                              events_path=temp_path / "event_history.json")
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(cls.state))
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.demo_thread = threading.Thread(target=cls.state.demo_loop, daemon=True)
        cls.demo_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.state.stop.set()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=2)
        cls.demo_thread.join(timeout=2)
        cls.temp.cleanup()

    def get_json(self, path):
        with urlopen(self.base + path, timeout=3) as response:
            self.assertIn("application/json", response.headers["Content-Type"])
            return json.load(response)

    def post_json(self, path, payload):
        req = Request(self.base + path,
                      data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=10) as response:
            return json.load(response)

    def test_initial_status_exposes_light_and_led_state(self):
        data = self.get_json("/tools/sensor-status")
        self.assertIn("light_state", data)
        self.assertIn("led_on", data)
        self.assertIn("led_state", data)
        self.assertFalse(data["led_on"])
        self.assertEqual(data["led_state"], "off")

    def test_set_light_rejects_invalid_json_values(self):
        for value in ([], {}, None, True, 42, "dim"):
            with self.subTest(value=value):
                with self.assertRaises(HTTPError) as error:
                    self.post_json("/control", {"action": "set-light", "light": value})
                self.assertEqual(error.exception.code, 400)

    def test_set_light_and_wakeup_triggers_led_automation(self):
        self.post_json("/control", {"action": "reset-demo"})
        status = self.get_json("/tools/sensor-status")
        self.assertFalse(status["led_on"])
        res = self.post_json("/control", {"action": "set-light", "light": "dark"})
        self.assertEqual(res["light_state"], "dark")
        wakeup_res = self.post_json("/control", {"action": "wakeup"})
        self.assertTrue(wakeup_res.get("simulation"))
        status = self.get_json("/tools/sensor-status")
        self.assertEqual(status["posture_estimate"], "standing")
        self.assertEqual(status["light_state"], "dark")
        self.assertTrue(status["led_on"])
        self.assertEqual(status["led_state"], "on")
        events = self.get_json("/tools/event-history").get("events", [])
        self.assertTrue(any(e["event_type"] == "LIGHT_TRIGGERED" for e in events))
        self.post_json("/control", {"action": "set-light", "light": "bright"})
        self.state.monitor.consume({"distance_cm": 80, "light_state": "bright"}, simulated_pose="standing")
        status = self.get_json("/tools/sensor-status")
        self.assertFalse(status["led_on"])
        self.assertEqual(status["led_state"], "off")
        events = self.get_json("/tools/event-history").get("events", [])
        self.assertTrue(any(e["event_type"] == "RECOVERY" for e in events))


if __name__ == "__main__":
    unittest.main()

