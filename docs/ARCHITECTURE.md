# AYUSARTHI architecture

## Data and control path

```text
ROOM MONITORING                          SOLAR TRACKING
HC-SR04 / DHT11 / digital LDR           light sensors / 2 servos / PV panel
             \                                  /
              \                                /
                        ESP32-S3
                 local deterministic rules
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

The dual-axis solar tracker follows the same safety principle: light sensing and servo positioning should remain a local ESP32-S3 control loop. AI/cloud availability must not be required for panel movement, and the AI Agent should not directly command servo angles in the current prototype.

## Solar-tracker boundary

The updated hardware concept contains a small photovoltaic panel, two light sensors and two servos for horizontal/vertical positioning. This is presently treated as a renewable-energy/light-tracking demonstration.

Not yet claimed as validated:

- solar charging or battery management;
- MPPT or energy-yield optimization;
- final tracker GPIO assignments;
- calibrated servo travel limits;
- a measured gain in harvested energy;
- solar status as a required Python/API field.

See `SOLAR_TRACKER.md` for the hardware-integration plan and acceptance tests.

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
- Servo movement should be bounded by tested mechanical limits and powered from a suitable regulated supply rather than the ESP32-S3 3.3 V rail.
- The solar panel is not presented as a complete system power source unless a validated power path is added.
- API credentials stay in n8n's credential store.
