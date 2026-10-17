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
      +----> n8n AI Agent ----> model credential stored in n8n
      |
      v
Streamlit AYUSARTHI frontend
```

## Repository structure

```text
streamlit_app.py        canonical branded Streamlit entrypoint
frontend/               Streamlit UI implementation and AYUSARTHI logo
backend/                tool server, sensor monitor, events and voice helpers
backend/data/           fictional demo profile, reviewed notes and calibration
hardware/esp32-s3/      ESP32-S3 integration notes and telemetry helper
automation/n8n/         n8n setup notes and local start script
prompts/                AI Agent system prompt
tests/                  integration, automation and repository smoke tests
docs/                   architecture documentation
```

## Setup

From the repository root on Windows:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

The root requirements file installs both backend and frontend Python dependencies. Local Whisper microphone transcription also requires the **FFmpeg executable** on PATH.

### Optional environment configuration

The current defaults are local-only and work without a `.env` loader. To override them in your shell, set:

```text
N8N_CHAT_URL=http://localhost:5678/webhook/ayusarthi-chat
SENSOR_URL=http://127.0.0.1:8000/tools/sensor-status
```

`.env.example` documents these names, but `.env` files are intentionally ignored and are not automatically loaded by the Python code.

## Run locally

### 1. Backend

```bat
python -m backend.tool_server --demo --speak
```

Useful endpoints include:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/tools/sensor-status`
- `http://127.0.0.1:8000/tools/event-history`
- `http://127.0.0.1:8000/tools/profile`
- `http://127.0.0.1:8000/tools/health-notes?query=walking`

### 2. n8n

```bat
automation\n8n\start_n8n.bat
```

Configure the local workflow using `automation/n8n/README.md`. Model credentials belong in n8n's credential store and must not be committed.

### 3. Frontend

Run the canonical entrypoint from the repository root:

```bat
python -m streamlit run streamlit_app.py
```

This entrypoint uses `frontend/ayusarthi_logo.jpeg` as the browser/page icon when available, then loads the existing UI from `frontend/app.py`.

## Tests

The repository contains hardware-independent backend and repository smoke tests:

```bat
python -m unittest discover -s tests -v
```

The smoke tests verify that critical files such as the frontend logo, tool server and project entrypoint remain present and readable.

## Hardware

The confirmed ESP32-S3 prototype used HC-SR04, DHT11, a digital LDR module, OLED and LED. See `hardware/esp32-s3/README.md` for the documented pin map and serial telemetry contract.

The repository currently contains a validated telemetry helper, **not** a complete final firmware sketch. Full firmware should only be added from the actual tested Arduino/Codex source after credential review.

## Privacy and secrets

Never commit `.env`, API keys, passwords, Wi-Fi credentials, n8n credentials, private patient data, or ESP32 secret files. The included profile is explicitly synthetic demonstration data.

## Current limitations

- `backend/data/calibration.json` intentionally has no real posture bands until the physical installation is measured.
- A credential-reviewed n8n workflow export is not currently included.
- Caregiver/alert pages are prototype UI modules rather than active emergency services.
- This prototype must not be used to diagnose, prescribe, or make medical decisions.
