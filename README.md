# Ayu AI

A beginner-friendly Python foundation for a health-assistance project with optional spoken replies and a future sensor connection.

**Status: starter prototype.** The assistant uses a few explicit commands, not an LLM or trained ML model. It is not a medical or emergency-response system.

## What works today

- Typed commands: `hello`, `help`, `time`, `sensors`, `exit` (or `quit`).
- Terminal replies, with optional local text-to-speech.
- A sensor interface whose default implementation returns **not connected**, never invented readings.
- Configuration validation and automated tests requiring no hardware.

Not implemented: microphone recognition, open-ended AI conversation, sensor transport or firmware, fall detection, notifications, emergency calls, or control of a fan, door, LCD, or OLED. This repository does not contain or replace any earlier hackathon implementation.

## First run (no hardware, API key, or paid service)

Use Python 3.11 or newer; the starter was checked with Python 3.12. Run commands from the repository folder.

### Windows Command Prompt

```bat
git clone https://github.com/nealrsv-hub/ayu-ai-ai-agent-.git
cd ayu-ai-ai-agent-
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install -e .
python -m ayu_ai
```

For this private repository, Git must be signed in to an account with access. If Python 3.12 is not installed, use an installed Python 3.11+ interpreter to create the environment.

### macOS / Linux

```sh
git clone https://github.com/nealrsv-hub/ayu-ai-ai-agent-.git
cd ayu-ai-ai-agent-
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m ayu_ai
```

Try `hello`, then `sensors`. The latter must report that hardware integration is not implemented. Type `exit` to stop; Ctrl+C and end-of-input also stop cleanly.

A one-command check:
```sh
python -m ayu_ai --message sensors
```

## Optional spoken output

```sh
python -m pip install -e ".[voice]"
python -m ayu_ai --speak --message hello
```

You still **type** your input. This does not enable a microphone. Speech uses the computer's local speech engine through [pyttsx3](https://pypi.org/project/pyttsx3/); OS audio setup may be required. See [the upstream installation notes](https://github.com/nateshmbhat/pyttsx3#installation) if initialization fails. Linux may need eSpeak NG. No speech engine or speaker was available for an audible end-to-end test in the development environment.

If speech fails, a warning appears and printed replies continue. Use `--no-speak` to force text mode. The base app has no third-party runtime dependencies; the optional voice dependency is declared in `pyproject.toml`. Install commands may require internet access; normal operation makes no application network requests.

## Configuration

Defaults work without a configuration file. To change them, copy `config.example.toml` to `config.toml` and run:
```sh
python -m ayu_ai --config config.toml
```

Only `[voice].enabled` (boolean) is supported. `--speak` / `--no-speak` override it. Invalid or unknown settings produce an error instead of being silently ignored.

There are no API keys, model IDs, serial ports, or GPIO settings yet. Do not add credentials to source code. Local configuration, environment files, virtual environments, and logs are ignored by Git. The application does not store conversations or record audio.

## Small application layout

| Path | Purpose |
| --- | --- |
| `src/ayu_ai/__main__.py` | Terminal input and application wiring |
| `src/ayu_ai/assistant.py` | Small, deterministic command handler |
| `src/ayu_ai/voice.py` | Optional spoken output; text remains available |
| `src/ayu_ai/config.py` | TOML configuration validation |
| `src/ayu_ai/sensors.py` | Interface for a future sensor reader; disconnected by default |
| `tests/` | Hardware-free behavior and failure-path checks |
| `docs/MILESTONES.md` | Three short next milestones and completion checks |

The flow is typed input → command handler → printed response → optional speech. A `sensors` command asks the sensor source for its status. There is no web server, database, agent framework, or background monitoring process.

## Future hardware boundary

The project context includes an ESP32-S3, ultrasonic sensor, DHT11, LDR, OLED, LCD, and motor/propeller. None is driven or read by this code. No wiring, pin assignments, motor driver, or board protocol is assumed here.

Start later with **one confirmed DHT11 reading from the ESP32-S3**, after agreeing the transport and message format. Implement a source matching `SensorSource` and explicitly wire it into the entry point. Display errors and missing/stale readings honestly; never interpret missing data as a safe room. Keep physical actuator control out of the first integration.

## Check your changes

After installing the base package:
```sh
python -m unittest discover -s tests -v
```

Tests use a fake speech engine where needed; passing them does not certify microphone, audio hardware, sensor behavior, medical accuracy, or emergency response. See [the initial milestone plan](docs/MILESTONES.md).
