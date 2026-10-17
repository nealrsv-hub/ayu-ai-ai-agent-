# Development and demo checks

Run commands from the repository root in a Python 3.12 environment. The default installation supports typed chat and sensor monitoring:

```bash
python -m pip install -r requirements.txt -c constraints-demo.txt
python -m unittest discover -s tests -v
```

The constraints capture the tested Linux text/sensor dependencies. CI also installs and checks Windows, including any additional platform dependencies, and records each resolved environment. Voice dependencies remain optional and outside these checks. Review dependency changes together with test results and advisory reports; a clean advisory scan is not a security guarantee.

## Repeat the backend demonstration

```bash
python -m scripts.check_demo --output dist/demo-check.json
```

This command starts a temporary backend on a loopback port, uses synthetic values, and checks the public HTTP endpoints. It exercises profile retrieval, keyword notes, software LED transitions, event persistence, and invalid control input. State is kept in a temporary directory and removed afterward. No model, microphone, speaker, or physical hardware is involved.

For the interactive application, follow the main README. A complete AI/hardware demonstration still requires the actual n8n workflow, provider setup, firmware, and sensor calibration. Label simulated observations explicitly in any recording.

## Build the judge archive

```bash
python -m scripts.build_judge_bundle --sync
python -m scripts.build_judge_bundle --check
python -m scripts.build_judge_bundle
```

The output is `dist/AYUSARTHI-judge.zip`. Only explicitly listed canonical files are included. Runtime data, private configuration, virtual environments, and unrelated files are excluded. A `SHA256SUMS.txt` manifest records the included file hashes. Stable archive metadata makes repeated builds of the same source byte-identical.

`--sync` refreshes shared files in `judge_submission/` and preserves its separate README. Edit shared source in the root application, then sync; do not maintain two independent implementations. CI rejects drift and uploads the generated archive and verification reports as workflow artifacts.

## Storage failures

The backend preserves corrupt event files and rejects further appends until the file is repaired. It does not silently replace unreadable history with an empty list. Failed writes preserve the previous file and report a degraded status.

- `/health` returns 503 when the event store reports a problem.
- `/tools/event-history` returns 503 if history cannot be read.
- `/tools/sensor-status` remains available and includes `event_history.available` and a generic error code.
- The software LED OFF decision remains available even when logging fails. A missed transition is not automatically replayed as a saved event.

If storage fails, stop the backend, preserve the affected file for diagnosis, and check disk space, permissions, and JSON structure. Restore valid history from a backup before restarting. An observed write failure clears after a subsequent successful save. Use one backend process per state directory.

## Before submitting changes

Run the tests, sync/check the judge copy, and run the simulated backend check. Inspect the diff for changed behavior, inaccurate claims, and credentials. CI runs the same checks on Linux and Windows and audits the resolved text/sensor dependencies. Keep medical claims, measured hardware results, and model performance separate from simulated or mocked tests.
