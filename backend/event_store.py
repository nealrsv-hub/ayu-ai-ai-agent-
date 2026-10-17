"""Keep the latest 100 events in a local JSON file."""

import json
import logging
import os
import tempfile
import threading
import uuid
from datetime import datetime
from pathlib import Path

LOGGER = logging.getLogger(__name__)
MAX_RETENTION = 100


class EventStoreError(RuntimeError):
    """History could not be read or committed; existing data is preserved."""


def _reject_nonfinite(value):
    raise ValueError("Event history contains a non-finite JSON number")


class EventStore:
    def __init__(self, storage_path=None):
        base_dir = Path(__file__).resolve().parent / "data"
        self.storage_path = Path(storage_path) if storage_path is not None else base_dir / "event_history.json"
        self.lock = threading.Lock()
        self._error = None
        with self.lock:
            try:
                if not self.storage_path.exists():
                    self.storage_path.parent.mkdir(parents=True, exist_ok=True)
                    self._write_file([])
                else:
                    self._read_file()
            except OSError as exc:
                self._error = "write_failed"
                LOGGER.error("Event history initialization failed (%s)", type(exc).__name__)
            except EventStoreError:
                # Monitoring stays available while /health reports degraded storage.
                pass

    def _read_file(self):
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"),
                              parse_constant=_reject_nonfinite)
            if not isinstance(data, list) or not all(isinstance(event, dict) for event in data):
                raise ValueError("Expected a list of event objects")
        except (OSError, ValueError, UnicodeError) as exc:
            self._error = "read_failed"
            LOGGER.error("Event history read failed (%s); file preserved", type(exc).__name__)
            raise EventStoreError("Event history is unavailable; inspect the storage file.") from exc
        if self._error == "read_failed":
            self._error = None
        return data

    def _write_file(self, events):
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.storage_path.parent,
                prefix=f".{self.storage_path.stem}-", suffix=".tmp", delete=False,
            ) as stream:
                temporary = Path(stream.name)
                json.dump(events, stream, indent=2, ensure_ascii=False, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.storage_path)
        except (OSError, TypeError, ValueError) as exc:
            self._error = "write_failed"
            LOGGER.error("Event history write failed (%s); previous file preserved", type(exc).__name__)
            raise EventStoreError("Event history could not be saved.") from exc
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    LOGGER.warning("Event history temporary file could not be removed")
        self._error = None

    def status(self):
        """Check readability without clearing a previous write failure."""
        with self.lock:
            try:
                self._read_file()
            except EventStoreError:
                pass
            return {"available": self._error is None, "error": self._error}

    def add_event(self, event_type, title, description, severity="info",
                  source="automation", is_simulated=True, confidence=None,
                  timestamp=None, extra=None):
        """Return an event only after it has been saved successfully."""
        iso_time = timestamp or datetime.now().astimezone().isoformat(timespec="seconds")
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": iso_time,
            "event_type": str(event_type),
            "severity": str(severity),
            "source": str(source),
            "title": str(title),
            "description": str(description),
            "confidence": confidence if isinstance(confidence, (int, float)) else None,
            "is_simulated": bool(is_simulated),
        }
        if extra and isinstance(extra, dict):
            event["extra"] = extra

        with self.lock:
            events = self._read_file()
            events.append(event)
            self._write_file(events[-MAX_RETENTION:])
        return event

    def get_events(self, limit=MAX_RETENTION):
        """Read recent events, raising on unreadable or malformed history."""
        with self.lock:
            events = self._read_file()
            return events[-limit:] if limit and limit > 0 else events

    def clear(self):
        """Explicitly replace history with an empty list."""
        with self.lock:
            self._write_file([])
