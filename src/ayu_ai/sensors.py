"""Extension point only: no device transport, readings, or firmware."""
from typing import Protocol


class SensorSource(Protocol):
    def status(self) -> str:
        """Return an honest human-readable status without triggering actuators."""
        ...


class DisconnectedSensors:
    def status(self) -> str:
        return "Sensors are not connected. Hardware integration is not implemented."
