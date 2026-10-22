# AYU AI — Judge Submission

This folder is the focused, self-contained frontend and backend package for the AYU AI / AYUSARTHI hackathon prototype.

AYU AI demonstrates:

- a Streamlit caregiver-oriented interface;
- a local Python API for sensor status, demo profile, reviewed health notes, and event history;
- deterministic sensor/event automation with safe stale-data handling;
- optional offline speech output and local Whisper transcription;
- a constrained AI-agent prompt that avoids diagnosis and clearly labels simulated data.

> Prototype only: this is not a medical device. It does not measure body temperature, heart rate, oxygen saturation, sleep quality, or a confirmed fall.

## Architecture

```text
ESP32-S3 telemetry or demo simulator
                 |
                 v
Python backend/tool server (localhost:8000)
        |                    |
        v                    v
sensor + event logic     n8n AI tools
                              |
                              v
                    Gemini credential in n8n
                              |
                              v
                 Streamlit frontend
```

## Included files

| Area | Files | Why included |
|---|---|---|
| Frontend | `frontend/app.py`, logo, requirements | Complete user interface and its required asset/dependencies |
| Backend API | `backend/tool_server.py` | Local HTTP endpoints, demo simulator, and serial telemetry entry point |
| Core logic | `monitor.py`, `event_detector.py`, `event_store.py` | Sensor validation, posture estimation, LED rules, and event history |
| Voice | `backend/voice.py` | Optional offline text-to-speech support |
| Demo data | `backend/data/*.json` | Explicitly fictional profile, reviewed educational notes, and calibration placeholder |
| AI behavior | `prompts/agent_system_prompt.txt` | Safety and evidence rules for the n8n AI Agent |
| Setup | `requirements.txt`, `.env.example`, `docs/ARCHITECTURE.md` | Reproducible install and concise technical overview |

The full development repository retains hardware notes, automation helpers, auxiliary command-line clients, and extended tests. They are intentionally omitted here so judges can review the essential application quickly.

## Run the core demo

Open a terminal in this `judge_submission` folder.

### 1. Create the environment

Windows:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 2. Start the backend

```bash
python -m backend.tool_server --demo --speak
```

The local API will be available at `http://127.0.0.1:8000`.

Useful endpoints:

- `/health`
- `/tools/sensor-status`
- `/tools/event-history`
- `/tools/profile`
- `/tools/health-notes?query=walking`

### 3. Start the frontend

In a second activated terminal, still inside `judge_submission`:

```bash
python -m streamlit run frontend/app.py
```

Open the local URL printed by Streamlit.

Sensor monitoring and the simulation work through the Python backend. AI chat additionally expects the local n8n webhook shown in `.env.example`; the Gemini key belongs in n8n's credential store and is never committed.

## Voice note

Text chat does not require FFmpeg. Local Whisper transcription does require an FFmpeg executable on `PATH`. Speech output is optional; omit `--speak` if audio is unavailable.

## Privacy and security

- No API keys, passwords, Wi-Fi credentials, or real patient records are included.
- The profile is explicitly marked synthetic.
- Runtime event and greeting-state files are generated locally and should not be committed.
- The backend binds to loopback only.
