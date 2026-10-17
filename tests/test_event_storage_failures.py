"""Exercise corrupt history and failed writes without losing existing data."""
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

from backend.event_detector import LedAutomation
from backend.event_store import EventStore, EventStoreError
from backend.tool_server import ToolState, handler_for


class EventStorageFailureTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "events.json"
        self.store = EventStore(self.path)

    def test_corrupt_history_is_preserved_and_append_fails(self):
        for contents in ("{broken", "", "{}", "[42]", "\ufffd", '[{"confidence":NaN}]'):
            with self.subTest(contents=contents):
                self.path.write_text(contents, encoding="utf-8")
                with self.assertRaises(EventStoreError):
                    self.store.add_event("TEST", "Title", "Description")
                self.assertEqual(self.path.read_text(encoding="utf-8"), contents)
                self.assertFalse(self.store.status()["available"])

    def test_failed_replace_preserves_history_and_cleans_temporary_file(self):
        original = self.store.add_event("FIRST", "Title", "Description")
        with patch("backend.event_store.os.replace", side_effect=PermissionError):
            with self.assertRaises(EventStoreError):
                self.store.add_event("SECOND", "Title", "Description")
        self.assertEqual(self.store.get_events(), [original])
        self.assertEqual(self.store.status()["error"], "write_failed")
        self.assertEqual(list(self.path.parent.glob(".*.tmp")), [])
        self.store.add_event("RECOVERED", "Title", "Description")
        self.assertTrue(self.store.status()["available"])

    def test_unserializable_event_does_not_damage_previous_history(self):
        previous = self.path.read_bytes()
        with self.assertRaises(EventStoreError):
            self.store.add_event("TEST", "Title", "Description", extra={"bad": object()})
        self.assertEqual(self.path.read_bytes(), previous)

    def test_corrupt_startup_keeps_service_constructible(self):
        self.path.write_text("not-json")
        store = EventStore(self.path)
        self.assertFalse(store.status()["available"])
        self.assertEqual(self.path.read_text(), "not-json")

    def test_storage_failure_does_not_block_led_off_decision(self):
        automation = LedAutomation(self.store)
        self.assertTrue(automation.evaluate("dark", "standing", True))
        self.path.write_text("not-json")
        self.assertFalse(automation.fail_safe())
        self.assertFalse(self.store.status()["available"])

    def test_api_reports_degraded_storage_but_keeps_sensor_endpoint(self):
        state = ToolState(demo=True, state_path=Path(self.temp.name) / "greeting.json",
                          events_path=self.path)
        self.path.write_text("not-json")
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(state))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            for endpoint in ("/health", "/tools/event-history"):
                with self.subTest(endpoint=endpoint):
                    with self.assertRaises(HTTPError) as error:
                        urlopen(base + endpoint, timeout=3)
                    self.assertEqual(error.exception.code, 503)
                    self.assertIsInstance(json.load(error.exception), dict)
            with urlopen(base + "/tools/sensor-status", timeout=3) as response:
                self.assertFalse(json.load(response)["event_history"]["available"])
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
