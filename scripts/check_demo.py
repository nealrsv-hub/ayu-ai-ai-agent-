"""Run the simulated backend through its HTTP interface using temporary state."""
import argparse
import json
import platform
import tempfile
import threading
from contextlib import redirect_stdout
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import sys

from backend.tool_server import ToolState, handler_for


def check_demo():
    checks = []

    def require(condition, name):
        if not condition:
            raise RuntimeError(f"Check failed: {name}")
        checks.append(name)

    with tempfile.TemporaryDirectory(prefix="ayusarthi-check-") as directory:
        root = Path(directory)
        state = ToolState(demo=True, state_path=root / "greeting.json",
                          events_path=root / "events.json")
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(state))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        simulator = threading.Thread(target=state.demo_loop, daemon=True)
        worker.start()
        simulator.start()
        base = f"http://127.0.0.1:{server.server_port}"

        def request(path, body=None):
            data = json.dumps(body).encode() if body is not None else None
            req = Request(base + path, data=data, headers={"Content-Type": "application/json"})
            with urlopen(req, timeout=10) as response:
                return json.load(response)

        try:
            health = request("/health")
            require(health["ok"] and health["is_simulated"], "healthy simulated backend")
            require(request("/tools/profile")["is_synthetic"] is True, "synthetic profile")
            notes = request("/tools/health-notes?query=walking")["matches"]
            require(bool(notes) and bool(notes[0]["source_url"]), "source-linked keyword retrieval")
            require(request("/tools/health-notes?query=unsupported-topic")["matches"] == [],
                    "unsupported topic has no invented source")
            request("/control", {"action": "set-light", "light": "dark"})
            request("/control", {"action": "wakeup"})
            status = request("/tools/sensor-status")
            require(status["fresh"] and status["is_simulated"], "fresh samples labelled simulated")
            require(status["posture_estimate"] == "standing" and status["led_on"],
                    "software LED rule responds to dark and standing")
            events = request("/tools/event-history")["events"]
            require(any(event["event_type"] == "LIGHT_TRIGGERED" and event["is_simulated"]
                        for event in events), "simulated transition persisted")
            try:
                request("/control", {"action": "set-light", "light": []})
            except HTTPError as error:
                require(error.code == 400, "invalid control rejected")
                error.close()
            else:
                require(False, "invalid control rejected")
        finally:
            state.stop.set()
            simulator.join(timeout=2)
            server.shutdown()
            server.server_close()
            worker.join(timeout=2)
    return {
        "passed": True,
        "scope": "Simulated local backend only; no model, microphone, speaker, or physical hardware tested.",
        "python": platform.python_version(),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Also save the JSON result, for example dist/demo-check.json")
    args = parser.parse_args()
    with redirect_stdout(sys.stderr):
        result = check_demo()
    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
