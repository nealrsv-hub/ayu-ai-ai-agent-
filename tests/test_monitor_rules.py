"""Check calibration and greeting timing with a deterministic clock."""
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from backend.monitor import Monitor, validate_bands


class MonitorRulesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = datetime(2026, 1, 2, 7, tzinfo=timezone.utc)
        self.messages = []
        self.path = Path(self.temp.name) / "greeting.json"
        self.monitor = Monitor(
            bands={"standing": [40, 60], "sitting": [80, 100]},
            state_path=self.path, emit=self.messages.append,
        )

    def sample(self, distance, tick):
        return self.monitor.consume({"distance_cm": distance}, now=self.now, tick=tick)

    def test_overlapping_or_nonfinite_calibration_is_rejected(self):
        for bands in ({"standing": [1, 4], "sitting": [4, 8]},
                      {"standing": [1, float("inf")]}, {"standing": [True, 4]}):
            with self.subTest(bands=bands), self.assertRaises(ValueError):
                validate_bands(bands)

    def test_uncalibrated_real_reading_cannot_claim_posture(self):
        monitor = Monitor(emit=self.messages.append)
        monitor.consume({"distance_cm": 50, "posture": "standing"}, tick=0)
        self.assertEqual(monitor.snapshot(tick=0)["posture_estimate"], "unknown")

    def test_greeting_needs_baseline_and_three_seconds_standing(self):
        self.monitor.arm()
        self.assertFalse(self.sample(50, 0))
        self.assertFalse(self.sample(50, 3))
        self.assertFalse(self.sample(90, 4))
        self.assertFalse(self.sample(50, 5))
        self.assertFalse(self.sample(50, 7.9))
        self.assertTrue(self.sample(50, 8))
        self.assertFalse(self.monitor.armed)

    def test_stale_gap_breaks_the_greeting_sequence(self):
        self.monitor.arm()
        self.sample(90, 0)
        self.sample(50, 1)
        self.assertFalse(self.sample(50, 5))
        self.assertFalse(self.monitor.baseline_seen)
        self.assertEqual(self.monitor.snapshot(tick=9)["values"], {})

    def test_saved_greeting_prevents_repetition_after_restart(self):
        self.monitor.arm()
        self.sample(90, 0)
        self.sample(50, 1)
        self.assertTrue(self.sample(50, 4))
        self.monitor = Monitor(bands=self.monitor.bands, state_path=self.path,
                               emit=self.messages.append)
        self.monitor.arm()
        self.sample(90, 5)
        self.sample(50, 6)
        self.assertFalse(self.sample(50, 9))

    def test_greeting_is_suppressed_outside_morning(self):
        self.now = self.now.replace(hour=14)
        self.monitor.arm()
        self.sample(90, 0)
        self.sample(50, 1)
        self.assertFalse(self.sample(50, 4))


if __name__ == "__main__":
    unittest.main()
