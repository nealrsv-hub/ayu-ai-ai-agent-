# AYUSARTHI architecture

## Data path

```text
HC-SR04 / DHT11 / digital LDR
             |
          ESP32-S3
             |
      USB serial JSON
             |
             v
      Python tool server
      |      |       |
      |      |       +--> local event history
      |      +----------> posture/environment state
      +-----------------> read-only HTTP tools
                             |
                             v
                         n8n AI Agent
                             |
                             v
                      Streamlit frontend
```

The Python layer keeps deterministic sensor and automation logic separate from the language model. Current sensor values are exposed as evidence to the agent; the model is not trusted to fabricate or directly control hardware.

## Current prototype endpoints

- `/health`
- `/tools/sensor-status`
- `/tools/event-history`
- `/tools/profile`
- `/tools/health-notes?query=...`

The `/control` endpoint is a local/manual demonstration interface and should not be attached to the AI Agent as an autonomous tool.

## Safety boundaries

- Room temperature/humidity are environmental readings, not body vital signs.
- Posture is an estimate from calibrated distance bands.
- Simulated values are explicitly labelled.
- Stale sensor readings are withheld rather than reused as current data.
- API credentials stay in n8n's credential store.
