"""Deterministic LED automation and event detection for AYUSARTHI.

Rules:
- LED ON condition:
    light_state == "dark"
    AND posture_estimate == "standing"
    AND sensor data is fresh/valid
- LED OFF condition:
    light_state != "dark"
    OR posture_estimate != "standing"
    OR sensor data is stale/invalid

Transitions:
- OFF -> ON: logs LIGHT_TRIGGERED once.
- ON -> OFF: logs RECOVERY once ("Automatic light condition cleared").
- Stable states (ON -> ON or OFF -> OFF) do not duplicate events.
- Fails safe to OFF on stale or invalid data.
"""

import logging
import threading
from backend.event_store import EventStore

LOGGER = logging.getLogger(__name__)


class LedAutomation:
    def __init__(self, event_store=None):
        self.event_store = event_store or EventStore()
        self.lock = threading.Lock()
        self._led_on = False

    @property
    def led_on(self) -> bool:
        with self.lock:
            return self._led_on

    @property
    def led_state(self) -> str:
        with self.lock:
            return "on" if self._led_on else "off"

    def evaluate(self, light_state: str, posture_estimate: str,
                 is_fresh: bool, is_simulated: bool = True,
                 timestamp: str = None) -> bool:
        """Evaluate automation inputs and update LED state with transition event logging."""
        valid_light = isinstance(light_state, str) and light_state.strip().lower() == "dark"
        valid_posture = isinstance(posture_estimate, str) and posture_estimate.strip().lower() == "standing"
        fresh = bool(is_fresh)
        should_turn_on = valid_light and valid_posture and fresh

        with self.lock:
            previous_state = self._led_on
            if should_turn_on and not previous_state:
                self._led_on = True
                self.event_store.add_event(
                    event_type="LIGHT_TRIGGERED",
                    title="Automatic light turned on",
                    description="Darkness detected while standing posture was present.",
                    severity="info",
                    source="automation",
                    is_simulated=is_simulated,
                    timestamp=timestamp,
                )
                LOGGER.info("LED turned ON (LIGHT_TRIGGERED logged)")
            elif not should_turn_on and previous_state:
                self._led_on = False
                self.event_store.add_event(
                    event_type="RECOVERY",
                    title="Automatic light turned off",
                    description="Automatic light condition cleared",
                    severity="info",
                    source="automation",
                    is_simulated=is_simulated,
                    timestamp=timestamp,
                )
                LOGGER.info("LED turned OFF (RECOVERY logged)")
            return self._led_on

    def fail_safe(self, is_simulated: bool = True, timestamp: str = None) -> bool:
        """Immediately transition to safe OFF state if currently ON."""
        with self.lock:
            if self._led_on:
                self._led_on = False
                self.event_store.add_event(
                    event_type="RECOVERY",
                    title="Automatic light turned off",
                    description="Automatic light condition cleared",
                    severity="info",
                    source="automation",
                    is_simulated=is_simulated,
                    timestamp=timestamp,
                )
                LOGGER.info("LED failed safe to OFF (RECOVERY logged)")
            return self._led_on

    def reset(self):
        """Reset state to initial OFF without logging events."""
        with self.lock:
            self._led_on = False
