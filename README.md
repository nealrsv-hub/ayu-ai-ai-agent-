# AyuSaarthi AI

AI-assisted elderly monitoring, voice assistance, local sensor automation, caregiver-oriented software, and a dual-axis solar-tracking demonstration for renewable-energy awareness.

> **Prototype scope:** This is a hackathon demonstration, not a medical device. Sensor readings are room/environment and distance measurements, not body vital signs or medical diagnoses. The solar subsystem demonstrates light tracking; it is not currently claimed to power or charge the complete AyuSaarthi system.

## Architecture

```text
Room sensors                       Dual-axis solar tracker
HC-SR04 / DHT11 / digital LDR      2 light sensors + 2 servos + small PV panel
        \                                      /
         \                                    /
                  ESP32-S3
                     |
            local deterministic rules
                     |
              USB serial JSON
                     v
          Python backend/tool server
             |                 |
             |                 +----> local event rules / event history
             |
             +----------------------> n8n AI Agent ----> Gemini credential in n8n
                                      |
                                      v
                           Streamlit AyuSaarthi AI frontend
```

Time-critical sensing and actuator rules remain local. The AI layer receives system context but is not the only safety layer and is not trusted to directly drive motors.

## Repository structure

```text
frontend/              Streamlit chat/monitoring UI and logo
backend/               Python tool server, sensor monitor, events, voice helpers
backend/data/          fictional demo profile, reviewed notes, calibration
hardware/esp32-s3/     ESP32-S3 integration notes and telemetry helper
automation/n8n/        n8n setup notes and local start script
prompts/               AI Agent system prompt
tests/                 local integration and regression tests
docs/                  architecture, event design, setup and solar-tracker design notes
```

## Privacy and secrets

No model API key is required in the Python source. The hackathon design stores the Gemini key in the n8n credential store. Never commit `.env`, API keys, passwords, Wi-Fi credentials, n8n credentials, or real patient data.

## Run locally

### Backend

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r backend\requirements.txt
python -m backend.tool_server --demo --speak
```

The backend binds to loopback and exposes endpoints such as:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/tools/sensor-status`
- `http://127.0.0.1:8000/tools/profile`
- `http://127.0.0.1:8000/tools/health-notes?query=walking`

### n8n

```bat
automation\n8n\start_n8n.bat
```

### Frontend

The Streamlit frontend connects only to the local Python tool server and local n8n webhook in the current prototype.

## Hardware

### Room monitoring

The confirmed ESP32-S3 room-monitoring stack uses HC-SR04, DHT11, a digital LDR module, OLED and LED.

### Dual-axis solar tracker

The updated integrated prototype adds:

- a small photovoltaic solar panel;
- 2 LDR/light sensors positioned to compare incident light;
- 2 servo motors for horizontal and vertical panel movement;
- mechanical mounting for two-axis motion;
- regulated servo power with a common ground shared with the controller.

The tracker compares the two light-sensor readings and adjusts the servos toward the stronger light direction. Exact solar-tracker GPIO assignments, servo limits and sensor thresholds are deliberately left unclaimed until they are fixed and validated on the physical build.

See `hardware/esp32-s3/README.md` for the confirmed room-monitoring pin map and `docs/SOLAR_TRACKER.md` for the solar subsystem integration plan.

## Current limitations

- `calibration.json` intentionally has no real posture bands until the physical installation is measured.
- The repository contains a serial telemetry helper, not a claim that the complete final ESP32 firmware has been independently revalidated here.
- The solar tracker is currently a light-following demonstration. Solar charging, MPPT, battery management and measured energy-gain claims are outside the current validated scope.
- Solar-tracker GPIO assignments, LDR interface details, servo travel limits and power sizing must be validated on the final hardware before they are treated as fixed specifications.
- A credential-reviewed n8n workflow export was not included in the uploaded source package.
- This prototype must not be used to diagnose, prescribe, or make medical decisions.
