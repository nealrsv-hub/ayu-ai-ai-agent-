# AYUSARTHI architecture

The prototype separates deterministic monitoring from model-generated conversation.

## Components and requests

- The ESP32 sends newline-delimited JSON at 115200 baud. Demo mode supplies labelled simulated samples instead.
- `Monitor` validates numbers, estimates posture from configured distance bands, and tracks freshness and greeting state.
- `LedAutomation` calculates a software LED decision. It records transitions through `EventStore`, which retains the latest 100 events.
- Streamlit requests sensor snapshots from the Python HTTP server and sends chat messages to n8n.
- A separately configured n8n workflow calls the model and may use the backend's read-only tools.

`backend/data/calibration.json` starts with no posture bands. Real distance data therefore produces an unknown posture until measured ranges are configured.

## Interfaces

| Method and path | Purpose |
|---|---|
| `GET /health` | Backend availability and demo-mode flag |
| `GET /tools/sensor-status` | Current values, freshness, posture estimate, and software LED decision |
| `GET /tools/event-history` | Local event history |
| `GET /tools/profile` | Synthetic demonstration profile |
| `GET /tools/health-notes?query=walking` | English keyword retrieval over supplied notes |
| `POST /control` | Manual arming and demo controls |

The chat contract is `{"chatInput":"...","sessionId":"..."}` with a nonempty `{"answer":"..."}` response. Session IDs allow a workflow to associate requests, but memory must be configured in n8n.

## LED and refresh limits

The API's top-level `led_on` and `led_state` describe the Python rule result. Serial telemetry may also contain a firmware-reported `values.led_on`. These are separate states: Python does not send commands to the ESP32 or confirm physical actuation.

Monitoring refreshes when Streamlit reruns, including manual refresh and page navigation. It is not a continuous browser stream.

## State and security

Event history and greeting state are local JSON files ignored by Git. Writes replace a temporary file, but storage failures are logged rather than reported to API callers. The store uses an in-process lock and is not designed for multiple backend processes.

The backend binds to `127.0.0.1`. It has no application authentication. Keep `/control` out of model tools and do not expose this service to an untrusted network.

The supplied profile is synthetic. Room readings are not body vital signs. Posture is an estimate, not wakefulness or fall confirmation. Model credentials belong in n8n. Frontend logs contain response status and content type, not answer bodies.
