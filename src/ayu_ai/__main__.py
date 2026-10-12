"""Run with python -m ayu_ai after installing the package."""
import argparse
from pathlib import Path
from ayu_ai.assistant import reply
from ayu_ai.config import load_settings
from ayu_ai.sensors import DisconnectedSensors
from ayu_ai.voice import Speaker


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ayu AI typed-command starter")
    parser.add_argument("--config", type=Path, help="Optional TOML configuration file")
    parser.add_argument("--message", help="Handle one typed message and exit")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--speak", dest="speak", action="store_true")
    mode.add_argument("--no-speak", dest="speak", action="store_false")
    parser.set_defaults(speak=None)
    args = parser.parse_args(argv)
    try:
        settings = load_settings(args.config)
    except (OSError, ValueError) as error:
        parser.error(f"Could not load configuration: {error}")
    enabled = settings.voice_enabled if args.speak is None else args.speak
    speaker = Speaker(enabled)
    sensors = DisconnectedSensors()
    try:
        if args.message is not None:
            response = reply(args.message, sensors)
            print(response)
            speaker.say(response)
            return 0
        print("Ayu AI starter: typed input; no live hardware or medical advice. Type help.")
        while True:
            text = input("You: ")
            response = reply(text, sensors)
            print("Ayu:", response)
            speaker.say(response)
            if text.strip().casefold() in {"exit", "quit"}:
                break
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye!")
    finally:
        speaker.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
