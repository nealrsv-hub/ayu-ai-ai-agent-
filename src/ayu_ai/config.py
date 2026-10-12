"""Small validated configuration; no secrets are required."""
from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class Settings:
    voice_enabled: bool = False


def load_settings(path: Path | None = None) -> Settings:
    if path is None:
        return Settings()
    with path.open("rb") as stream:
        data = tomllib.load(stream)
    if set(data) - {"voice"}:
        raise ValueError("Only the [voice] configuration section is supported.")
    voice = data.get("voice", {})
    if not isinstance(voice, dict) or set(voice) - {"enabled"}:
        raise ValueError("[voice] supports only enabled = true or false.")
    enabled = voice.get("enabled", False)
    if not isinstance(enabled, bool):
        raise ValueError("voice.enabled must be true or false.")
    return Settings(voice_enabled=enabled)
