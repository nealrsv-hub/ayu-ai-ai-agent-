"""Local Python tools for an n8n agent. Bind to loopback; use fictional demo data.

Run: python tool_server.py --demo
Real serial: python tool_server.py --serial COM5
No cloud model API is called by this process.
"""
import argparse
import json
import re
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from backend.event_detector import LedAutomation
from backend.event_store import EventStore
from backend.monitor import Monitor
from backend.voice import Speaker

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
DEMO_VALUES = {"distance_cm": 80.0, "temperature_c": 26.0, "humidity_pct": 55.0}


class ToolState:
    def __init__(self, demo=False, speak=False, state_path=None, events_path=None):
        self.demo = demo
        self.speaker = Speaker(enabled=speak)
        self.stop = threading.Event()
        self.demo_lock = threading.Lock()
        self.wake_lock = threading.Lock()
        self.demo_pose = "sitting"
        self.demo_light_state = "bright"
        self.notes = json.loads((DATA_DIR / "health_notes.json").read_text(encoding="utf-8"))
        self.profile = json.loads((DATA_DIR / "profile_demo.json").read_text(encoding="utf-8"))
        if self.profile.get("is_synthetic") is not True:
            raise ValueError("This free-API demonstration requires a fictional profile.")
        bands = json.loads((DATA_DIR / "calibration.json").read_text(encoding="utf-8"))["bands_cm"]
        if state_path is None:
            state_path = DATA_DIR / ("demo_greeting_state.json" if demo else "greeting_state.json")
        self.monitor = Monitor(bands=bands, state_path=state_path, emit=self.emit)
        if events_path is None:
            events_path = DATA_DIR / "event_history.json"
        self.event_store = EventStore(storage_path=events_path)
        self.led_automation = LedAutomation(event_store=self.event_store)

    def emit(self, message):
        print(("[SIMULATION] " if self.demo else "") + message, flush=True)
        self.speaker.say(message)

    def status(self):
        stale = self.monitor.check_stale()
        if stale:
            self.led_automation.fail_safe(is_simulated=self.demo)
        snapshot = self.monitor.snapshot()
        led_on = self.led_automation.evaluate(
            light_state=snapshot.get("light_state", "unknown"),
            posture_estimate=snapshot.get("posture_estimate", "unknown"),
            is_fresh=snapshot.get("fresh", False),
            is_simulated=self.demo,
        )
        snapshot.update({
            "is_simulated": self.demo,
            "local_time": datetime.now().astimezone().isoformat(timespec="seconds"),
            "data_source": "fictional demonstration" if self.demo else "ESP serial telemetry",
            "measurement_scope": "Distance estimate and room temperature/humidity; no body vital signs.",
            "demo_greeting_clock": "07:00 local time, simulated" if self.demo else None,
            "led_on": led_on,
            "led_state": "on" if led_on else "off",
        })
        return snapshot

    def health_notes(self, query):
        words = set(re.findall(r"[a-z]+", query.lower()))
        matches = []
        for note in self.notes:
            score = len(words.intersection(note.get("keywords", [])))
            if score:
                matches.append((score, note))
        matches.sort(key=lambda item: item[0], reverse=True)
        return {
            "query": query,
            "retrieval": "Small English keyword search, not a trained model or vector database.",
            "scope": "Public educational summaries; no individual medical advice.",
            "matches": [note for _, note in matches[:2]],
            "instruction_if_empty": "Say there is no supporting note. Do not invent evidence.",
        }

    def demo_loop(self):
        while not self.stop.is_set():
            with self.demo_lock:
                pose = self.demo_pose
                light = self.demo_light_state
            now = datetime.now().astimezone().replace(hour=7, minute=0, second=0, microsecond=0)
            data = dict(DEMO_VALUES)
            data["light_state"] = light
            self.monitor.consume(data, now=now, simulated_pose=pose)
            snap = self.monitor.snapshot()
            self.led_automation.evaluate(
                light_state=snap.get("light_state", "unknown"),
                posture_estimate=snap.get("posture_estimate", "unknown"),
                is_fresh=snap.get("fresh", False),
                is_simulated=self.demo,
            )
            self.stop.wait(0.25)

    def wakeup(self):
        if not self.demo:
            return 409, {"error": "wakeup is available only with --demo"}
        if not self.wake_lock.acquire(blocking=False):
            return 409, {"error": "A wakeup simulation is already running"}
        try:
            with self.demo_lock:
                self.demo_pose = "lying"
            self.monitor.arm()
            time.sleep(0.65)
            with self.demo_lock:
                self.demo_pose = "standing"
            time.sleep(3.6)
            return 200, {"simulation": True, "status": self.status(),
                         "note": "Greeting is once per simulated local date. Use reset-demo to repeat."}
        finally:
            self.wake_lock.release()


def handler_for(state):
    class Handler(BaseHTTPRequestHandler):
        def reply(self, code, value):
            raw = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            try:
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            url = urlsplit(self.path)
            if url.path == "/health":
                self.reply(200, {"ok": True, "is_simulated": state.demo})
            elif url.path == "/tools/sensor-status":
                self.reply(200, state.status())
            elif url.path == "/tools/event-history":
                self.reply(200, {"events": state.event_store.get_events()})
            elif url.path == "/tools/profile":
                self.reply(200, state.profile)
            elif url.path == "/tools/health-notes":
                query = parse_qs(url.query).get("query", [""])[0]
                if not query.strip() or len(query) > 500:
                    self.reply(400, {"error": "Supply a nonempty query of at most 500 characters"})
                else:
                    self.reply(200, state.health_notes(query))
            else:
                self.reply(404, {"error": "Unknown endpoint"})

        def do_POST(self):
            if urlsplit(self.path).path != "/control":
                self.reply(404, {"error": "Unknown endpoint"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 2048:
                    raise ValueError("Invalid content length")
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("Expected a JSON object")
            except (ValueError, UnicodeError):
                self.reply(400, {"error": "Expected a small JSON object"})
                return
            action = body.get("action")
            if action == "arm":
                state.monitor.arm()
                self.reply(200, {"armed": True})
            elif action == "wakeup":
                self.reply(*state.wakeup())
            elif action == "set-light":
                if not state.demo:
                    self.reply(409, {"error": "set-light is available only with --demo"})
                    return
                light = body.get("light", "bright")
                if light not in {"dark", "bright"}:
                    self.reply(400, {"error": "light must be 'dark' or 'bright'"})
                    return
                with state.demo_lock:
                    state.demo_light_state = light
                self.reply(200, {"light_state": light})
            elif action == "reset-demo" and state.demo:
                if not state.wake_lock.acquire(blocking=False):
                    self.reply(409, {"error": "Wait for the wakeup simulation to finish"})
                    return
                try:
                    with state.monitor.lock:
                        state.monitor.last_greeted = None
                        state.monitor.armed = False
                        state.monitor._break_continuity()
                        state.monitor.state_path.unlink(missing_ok=True)
                    with state.demo_lock:
                        state.demo_pose = "sitting"
                        state.demo_light_state = "bright"
                    state.led_automation.reset()
                    self.reply(200, {"demo_reset": True})
                finally:
                    state.wake_lock.release()
            else:
                self.reply(400, {"error": "Allowed actions: arm, wakeup (demo), reset-demo (demo), set-light (demo)"})

        def log_message(self, format, *args):
            pass
    return Handler


def serial_loop(state, port):
    import serial
    try:
        with serial.Serial(port, 115200, timeout=0.5) as device:
            while not state.stop.is_set():
                raw = device.readline()
                if raw:
                    try:
                        data = json.loads(raw)
                    except (ValueError, UnicodeError):
                        continue
                    state.monitor.consume(data)
                    snap = state.monitor.snapshot()
                    state.led_automation.evaluate(
                        light_state=snap.get("light_state", "unknown"),
                        posture_estimate=snap.get("posture_estimate", "unknown"),
                        is_fresh=snap.get("fresh", False),
                        is_simulated=False,
                    )
                if state.monitor.check_stale():
                    state.led_automation.fail_safe(is_simulated=False)
    except serial.SerialException:
        print("Serial connection failed. Check the port and close Arduino Serial Monitor.", flush=True)


def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--demo", action="store_true")
    source.add_argument("--serial", help="COM5 on Windows, /dev/ttyUSB0 on Linux, etc.")
    parser.add_argument("--speak", action="store_true")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.serial:
        try:
            import serial  # noqa: F401
        except ImportError:
            parser.error("Install pyserial first: python -m pip install -r requirements.txt")
    state = ToolState(demo=args.demo, speak=args.speak)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(state))
    if args.demo:
        threading.Thread(target=state.demo_loop, daemon=True).start()
    elif args.serial:
        threading.Thread(target=serial_loop, args=(state, args.serial), daemon=True).start()
        if not state.monitor.bands:
            print("No calibration bands: real posture remains unknown until you calibrate.")
    else:
        print("No telemetry source. Use --demo or --serial COM5.")
    print(f"Python tools ready: http://127.0.0.1:{args.port}/health", flush=True)
    print("Keep this terminal open. Ctrl+C stops it.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        state.stop.set()
        server.server_close()


if __name__ == "__main__":
    main()
