"""Meaningful local contract checks. No n8n, cloud key, audio, or hardware required."""
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from backend.chat_client import get_answer
from backend.http_client import post_json
from backend.tool_server import ToolState, handler_for


class ToolsIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.state = ToolState(demo=False, state_path=Path(cls.temp.name) / "state.json")
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(cls.state))
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        cls.temp.cleanup()

    def read(self, path):
        with urlopen(self.base + path, timeout=3) as response:
            self.assertIn("application/json", response.headers["Content-Type"])
            return json.load(response)

    def test_disconnected_sensor_has_no_invented_values(self):
        with self.state.monitor.lock:
            self.state.monitor.last_received = None
        data = self.read("/tools/sensor-status")
        self.assertFalse(data["fresh"])
        self.assertFalse(data["is_simulated"])
        self.assertEqual(data["values"], {})
        self.assertEqual(data["posture_estimate"], "unknown")

    def test_stale_sample_is_withheld_and_serial_label_cannot_override(self):
        self.state.monitor.consume({"distance_cm": 50, "posture": "standing"}, tick=0)
        data = self.read("/tools/sensor-status")
        self.assertFalse(data["fresh"])
        self.assertEqual(data["values"], {})
        self.assertEqual(data["posture_estimate"], "unknown")

    def test_evidence_keeps_source_and_unsupported_question_returns_empty(self):
        result = self.read("/tools/health-notes?query=walking")
        self.assertEqual(result["matches"][0]["id"], "WHO_ACTIVITY")
        self.assertTrue(result["matches"][0]["source_url"].startswith("https://www.who.int/"))
        self.assertEqual(self.read("/tools/health-notes?query=medicine-dose")["matches"], [])

    def test_empty_health_query_rejected(self):
        with self.assertRaises(HTTPError) as context:
            self.read("/tools/health-notes")
        self.assertEqual(context.exception.code, 400)

    def test_demo_controls_do_not_change_real_monitor(self):
        before = self.state.monitor.last_received
        with self.assertRaises(HTTPError) as context:
            post_json(self.base + "/control", {"action": "wakeup"}, timeout=3)
        self.assertEqual(context.exception.code, 409)
        self.assertEqual(self.state.monitor.last_received, before)

    def test_profile_is_explicitly_fictional_and_bad_json_shape_rejected(self):
        self.assertTrue(self.read("/tools/profile")["is_synthetic"])
        with self.assertRaises(HTTPError) as context:
            post_json(self.base + "/control", ["arm"], timeout=3)
        self.assertEqual(context.exception.code, 400)


class ChatContractTest(unittest.TestCase):
    def test_unicode_and_multiline_answer_and_session_roundtrip(self):
        captured = []
        answer = 'Namaste!\nA quoted "demo" answer. नमस्ते'

        class FakeWebhook(BaseHTTPRequestHandler):
            def do_POST(self):
                captured.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                raw = json.dumps({"answer": answer}, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), FakeWebhook)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            result = get_answer(f"http://127.0.0.1:{server.server_port}/webhook/test", "What is this?", "session-123")
            self.assertEqual(result, answer)
            self.assertEqual(captured, [{"chatInput": "What is this?", "sessionId": "session-123"}])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
