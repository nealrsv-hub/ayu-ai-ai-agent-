"""Keep the latest 100 events in a local JSON file."""

import json
import logging
import threading
import uuid
from datetime import datetime
from pathlib import Path

LOGGER = logging.getLogger(__name__)
MAX_RETENTION = 100


class EventStore:
    def __init__(self, storage_path=None):
        if storage_path is None:
            base_dir = Path(__file__).resolve().parent / "data"
            self.storage_path = base_dir / "event_history.json"
        else:
            self.storage_path = Path(storage_path)
        self.lock = threading.Lock()
        self._ensure_storage()

    def _ensure_storage(self):
        with self.lock:
            if not self.storage_path.exists():
                try:
                    self.storage_path.parent.mkdir(parents=True, exist_ok=True)
                    self._write_file([])
                except OSError as exc:
                    LOGGER.warning("Could not initialize event storage file: %s", exc)

    def _read_file(self):
        try:
            if not self.storage_path.exists():
                return []
            content = self.storage_path.read_text(encoding="utf-8").strip()
            if not content:
                return []
            data = json.loads(content)
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError) as exc:
            LOGGER.warning("Error reading event history (%s), resetting to empty list", exc)
            return []

    def _write_file(self, events):
        tmp_path = self.storage_path.with_suffix(".tmp")
        try:
            tmp_path.write_text(json.dumps(events, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp_path.replace(self.storage_path)
        except OSError as exc:
            LOGGER.warning("Error writing event history: %s", exc)
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except OSError:
                pass

    def add_event(self, event_type, title, description, severity="info",
                  source="automation", is_simulated=True, confidence=None,
                  timestamp=None, extra=None):
        """Append an event and keep the latest 100 events."""
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
            if len(events) > MAX_RETENTION:
                events = events[-MAX_RETENTION:]
            self._write_file(events)
        return event

    def get_events(self, limit=MAX_RETENTION):
        """Retrieve recent events in chronological order, capped at limit."""
        with self.lock:
            events = self._read_file()
            if limit and limit > 0:
                return events[-limit:]
            return events

    def clear(self):
        """Clear all stored events."""
        with self.lock:
            self._write_file([])

