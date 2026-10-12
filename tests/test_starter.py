import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from ayu_ai.assistant import reply
from ayu_ai.config import load_settings
from ayu_ai.sensors import DisconnectedSensors
from ayu_ai.voice import Speaker


class StarterTests(unittest.TestCase):
    def test_disconnected_is_honest(self):
        self.assertIn("not connected", reply(" SENSORS ", DisconnectedSensors()))

    def test_sensor_boundary_can_be_injected(self):
        source = Mock()
        source.status.return_value = "SIMULATED fixture"
        self.assertEqual(reply("sensors", source), "SIMULATED fixture")

    def test_unknown_input_does_not_invent_advice(self):
        self.assertIn("explicit commands", reply("diagnose me", DisconnectedSensors()))

    def test_config_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_text("[voice]\nenabled = true\n", encoding="utf-8")
            self.assertTrue(load_settings(path).voice_enabled)
            for invalid in ('[voice]\nenabled = "false"', '[voice]\nextra = 1',
                            'sensor = "live"', '[voice'):
                with self.subTest(invalid=invalid):
                    path.write_text(invalid, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_settings(path)

    def test_missing_voice_library_keeps_text_usable(self):
        with patch.dict(sys.modules, {"pyttsx3": None}), contextlib.redirect_stderr(io.StringIO()) as errors:
            speaker = Speaker(True)
            speaker.say("Hello")
            speaker.close()
        self.assertIn("continuing with text", errors.getvalue())

    def test_failed_speech_is_disabled_and_cleaned_up(self):
        engine = Mock()
        engine.runAndWait.side_effect = RuntimeError("audio unavailable")
        module = Mock()
        module.init.return_value = engine
        with patch.dict(sys.modules, {"pyttsx3": module}), contextlib.redirect_stderr(io.StringIO()):
            speaker = Speaker(True)
            speaker.say("first")
            speaker.say("second")
        engine.say.assert_called_once_with("first")
        engine.stop.assert_called_once()

    def test_cli_and_clean_exit(self):
        result = subprocess.run([sys.executable, "-m", "ayu_ai"],
                                input="hello\nsensors\nexit\n", text=True,
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("not connected", result.stdout)
        self.assertIn("Goodbye", result.stdout)

    def test_bad_config_fails_with_actionable_error(self):
        result = subprocess.run([sys.executable, "-m", "ayu_ai", "--config",
                                 "nonexistent-config.toml"], text=True,
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Could not load configuration", result.stderr)


if __name__ == "__main__":
    unittest.main()
