# AYU AI / AYUSARTHI

AI-assisted elderly monitoring, voice assistance, local sensor automation, and a hackathon caregiver-oriented interface.

> **Prototype scope:** This is a hackathon demonstration, not a medical device. Sensor readings are room/environment and distance measurements, not body vital signs or medical diagnoses.

## Architecture

```text
ESP32-S3 sensors
      |
      | USB serial JSON
      v
Python backend/tool server
      |
      +----> local event rules / event history
      |
      +----> n8n AI Agent ----> Gemini model credential in n8n
      |
      v
Streamlit AYU AI frontend
```

## Repository structure

```text
frontend/              Streamlit chat/monitoring UI and logo
backend/               Python tool server, sensor monitor, events, voice helpers
backend/data/          fictional demo profile, reviewed notes, calibration
hardware/esp32-s3/     ESP32-S3 integration notes and telemetry helper
automation/n8n/        n8n setup notes and local start script
prompts/               AI Agent system prompt
tests/                 local integration and regression tests
docs/                  event design and setup notes
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

The Streamlit frontend is being moved into `frontend/` on the organization branch. It connects only to the local Python tool server and local n8n webhook in the current prototype.

## Hardware

The confirmed ESP32-S3 project used HC-SR04, DHT11, a digital LDR module, OLED and LED. See `hardware/esp32-s3/README.md` for the pin map and serial telemetry contract.

## Current limitations

- `calibration.json` intentionally has no real posture bands until the physical installation is measured.
- The repository contains a serial telemetry helper, not a claim that the complete final ESP32 firmware has been independently revalidated here.
- A credential-reviewed n8n workflow export was not included in the uploaded source package.
- This prototype must not be used to diagnose, prescribe, or make medical decisions.
