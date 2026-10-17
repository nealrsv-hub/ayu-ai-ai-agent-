"""Check response parsing, connection status, and chat-log privacy."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from frontend import app


class FrontendContractTest(unittest.TestCase):
    def test_unreadable_sensor_response_is_not_connected(self):
        response = Mock()
        response.json.return_value = {"values": []}
        with patch.object(app.requests, "get", return_value=response):
            result = app.get_sensor_status()
        self.assertFalse(result["connected"])
        self.assertIsNone(result["data"])
        self.assertIsNotNone(result["error"])

    def test_valid_sensor_response_is_connected(self):
        response = Mock()
        response.json.return_value = {"values": {}, "fresh": False}
        with patch.object(app.requests, "get", return_value=response):
            result = app.get_sensor_status()
        self.assertTrue(result["connected"])
        self.assertFalse(result["data"]["fresh"])

    def test_chat_logs_metadata_without_response_content(self):
        private_text = "PRIVATE_RESPONSE_SENTINEL"
        response = Mock(status_code=200, headers={"content-type": "application/json"})
        response.text = private_text
        response.json.return_value = {"answer": private_text}
        with patch.object(app.requests, "post", return_value=response), \
                patch.object(app.st, "session_state", SimpleNamespace(session_id="test")), \
                self.assertLogs(app.LOGGER, level="INFO") as logs:
            answer = app.ask_ayusarthi("Test question")
        self.assertEqual(answer, private_text)
        self.assertNotIn(private_text, "\n".join(logs.output))
        self.assertIn("status=200", "\n".join(logs.output))

    def test_nested_answer_is_read_and_empty_answer_is_rejected(self):
        self.assertEqual(app.extract_ayusarthi_answer([{"body": {"answer": "Hello"}}]), "Hello")
        for payload in ({"answer": ""}, [], {"unexpected": "value"}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                app.extract_ayusarthi_answer(payload)


if __name__ == "__main__":
    unittest.main()
