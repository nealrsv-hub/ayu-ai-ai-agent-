# AYUSARTHI judge package

This folder is a review copy of the AYU AI hackathon prototype: a Streamlit frontend, local Python sensor API, synthetic fixtures, and an n8n agent prompt.

**Scope:** room/environment measurements and distance estimates. This is not a medical device. Caregiver accounts and alert delivery are placeholder pages.

## Run the sensor demo

Open a terminal in this folder, create an environment, and install dependencies:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m backend.tool_server --demo
```

On macOS/Linux use `python3 -m venv .venv` and `source .venv/bin/activate`.

In a second activated terminal, still in this folder:

```bat
python -m streamlit run frontend/app.py --server.address 127.0.0.1
```

Monitoring works with the backend alone and refreshes when the page reruns. The calculated LED state is software-only; there is no implemented physical LED command path.

## AI chat

AI chat also requires a local n8n workflow and a provider credential stored in n8n. A workflow export is not included.

Use `POST http://localhost:5678/webhook/ayusarthi-chat` with `{"chatInput":"...","sessionId":"..."}`, returning `{"answer":"..."}`. Configure the agent using `prompts/agent_system_prompt.txt`. Its tools can read sensor status, the synthetic profile, and keyword-matched educational notes. Keep `/control` out of model tools.

The frontend reads `N8N_CHAT_URL` and `SENSOR_URL` from the process environment. `.env.example` documents their defaults; `.env` is not loaded automatically. The parent repository's `automation/n8n/README.md` contains the longer setup contract.

## Included code

| Path | Purpose |
|---|---|
| `frontend/` | Chat/monitoring UI, logo, and dependencies |
| `backend/tool_server.py` | Local API, serial input, and simulator |
| `backend/monitor.py`, `event_detector.py`, `event_store.py` | Sensor checks, software LED rules, and event storage |
| `backend/voice.py` | Optional local speech output |
| `backend/data/` | Synthetic profile, source-linked note fixtures, and empty calibration |
| `prompts/`, `docs/` | Agent instructions and architecture notes |

The parent repository is the development source and contains tests, hardware notes, and auxiliary tools. This copy is retained for review; shared files must stay in sync.

## Voice, privacy, and limitations

Whisper input needs an FFmpeg executable on `PATH` and an initial model download. Review the transcript before sending. Backend speech uses `--speak`; the frontend has a separate **Spoken replies** toggle.

The backend has no authentication and must stay on loopback. Use synthetic data and keep credentials in n8n. Real posture needs installation-specific calibration. Full firmware, a workflow export, and measured end-to-end results are not included.
