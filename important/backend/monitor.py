"""Distance-based demo monitoring. These rules are not medical validation."""
import json
import math
import threading
import time
from datetime import datetime
from pathlib import Path


def finite_number(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def validate_bands(bands):
    result = {}
    for pose, band in bands.items():
        if pose not in {"standing", "sitting", "lying"}:
            raise ValueError("Use standing, sitting, or lying as band names.")
        if (not isinstance(band, list) or len(band) != 2
                or not all(finite_number(x) for x in band)
                or not 0 < band[0] < band[1]):
            raise ValueError("Each band must be [positive_min_cm, positive_max_cm].")
        result[pose] = band
    ordered = sorted(result.values())
    if any(left[1] >= right[0] for left, right in zip(ordered, ordered[1:])):
        raise ValueError("Leave a gap between posture bands; overlaps are ambiguous.")
    return result


class Monitor:
    def __init__(self, bands=None, state_path=None, emit=print,
                 stable_seconds=3.0, stale_seconds=3.0):
        self.bands = validate_bands(bands or {})
        self.state_path = Path(state_path) if state_path else None
        self.emit = emit
        self.stable_seconds = stable_seconds
        self.stale_seconds = stale_seconds
        self.lock = threading.RLock()
        self.last_greeted = None
        self.armed = False
        self.baseline_seen = False
        self.stand_since = None
        self.last_received = None
        self.pose = "unknown"
        self.latest = {}
        self.stale_reported = False
        if self.state_path and self.state_path.exists():
            try:
                self.last_greeted = json.loads(self.state_path.read_text()).get("last_greeted")
            except (OSError, ValueError, AttributeError):
                self.emit("Greeting state could not be read; arm the monitor again.")

    def arm(self):
        with self.lock:
            self.armed = True
            self.baseline_seen = False
            self.stand_since = None
        self.emit("Morning greeting armed. Observe sitting/lying, then stable standing.")

    def classify(self, distance):
        if not finite_number(distance) or distance <= 0:
            return "unknown"
        for pose, (low, high) in self.bands.items():
            if low <= distance <= high:
                return pose
        return "unknown"

    def _break_continuity(self):
        self.pose = "unknown"
        self.baseline_seen = False
        self.stand_since = None

    def consume(self, data, now=None, tick=None, simulated_pose=None):
        """simulated_pose is used only by the explicitly labelled simulator."""
        if not isinstance(data, dict):
            return False
        now = now or datetime.now().astimezone()
        tick = time.monotonic() if tick is None else tick
        greeting = False
        with self.lock:
            if self.last_received is not None and tick - self.last_received > self.stale_seconds:
                self._break_continuity()
            self.last_received = tick
            self.stale_reported = False
            self.latest = {
                key: data[key] if finite_number(data.get(key)) else None
                for key in ("distance_cm", "temperature_c", "humidity_pct")
            }
            if self.latest["humidity_pct"] is not None and not 0 <= self.latest["humidity_pct"] <= 100:
                self.latest["humidity_pct"] = None
            raw_light = data.get("light_state")
            if isinstance(raw_light, str) and raw_light.strip().lower() in {"dark", "bright"}:
                self.latest["light_state"] = raw_light.strip().lower()
            else:
                self.latest["light_state"] = "unknown"
            raw_led = data.get("led_on")
            if raw_led is None:
                raw_led = (data.get("led_state") == "on")
            self.latest["led_on"] = bool(raw_led) if isinstance(raw_led, bool) else False
            pose = simulated_pose or self.classify(self.latest["distance_cm"])
            self.pose = pose if pose in {"standing", "sitting", "lying"} else "unknown"
            if self.pose == "unknown":
                self._break_continuity()
            elif self.pose in {"sitting", "lying"}:
                self.baseline_seen = True
                self.stand_since = None
            elif self.stand_since is None:
                self.stand_since = tick
            today = now.date().isoformat()
            if (self.armed and self.baseline_seen and self.pose == "standing"
                    and self.stand_since is not None
                    and tick - self.stand_since >= self.stable_seconds
                    and 5 <= now.hour < 11 and self.last_greeted != today):
                self.last_greeted = today
                self.armed = False
                if self.state_path:
                    try:
                        self.state_path.parent.mkdir(parents=True, exist_ok=True)
                        temp = self.state_path.with_suffix(".tmp")
                        temp.write_text(json.dumps({"last_greeted": today}))
                        temp.replace(self.state_path)
                    except OSError:
                        self.emit("State could not be saved; greeting survives only this session.")
                greeting = True
        if greeting:
            self.emit("Good morning! How are you feeling today?")
        return greeting

    def check_stale(self, tick=None):
        tick = time.monotonic() if tick is None else tick
        with self.lock:
            stale = self.last_received is not None and tick - self.last_received > self.stale_seconds
            if stale:
                self._break_continuity()
                if not self.stale_reported:
                    self.stale_reported = True
                    self.emit("Sensor data is stale. Monitoring is unavailable.")
            return stale

    def snapshot(self, tick=None):
        tick = time.monotonic() if tick is None else tick
        with self.lock:
            age = None if self.last_received is None else max(0, tick - self.last_received)
            fresh = age is not None and age <= self.stale_seconds
            light = self.latest.get("light_state", "unknown") if fresh else "unknown"
            led_on = self.latest.get("led_on", False) if fresh else False
            return {"fresh": fresh, "age_seconds": age,
                    "posture_estimate": self.pose if fresh else "unknown",
                    "armed": self.armed,
                    "values": dict(self.latest) if fresh else {},
                    "light_state": light,
                    "led_on": led_on,
                    "led_state": "on" if led_on else "off",
                    "last_greeted": self.last_greeted}
