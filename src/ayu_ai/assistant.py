"""Predictable commands, deliberately not an LLM."""
from datetime import datetime
from ayu_ai.sensors import SensorSource


def reply(text: str, sensors: SensorSource) -> str:
    command = text.strip().casefold()
    if command in {"hello", "hi"}:
        return "Hello! I am Ayu AI's starter assistant. Type help for commands."
    if command == "help":
        return "Commands: hello, help, time, sensors, exit (or quit). Input is typed."
    if command == "time":
        return "Local computer time: " + datetime.now().strftime("%H:%M")
    if command == "sensors":
        return sensors.status()
    if command in {"exit", "quit"}:
        return "Goodbye!"
    if not command:
        return "Please type a command. Try help."
    return "This starter handles only explicit commands. Type help to see them."
