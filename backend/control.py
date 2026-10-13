"""Manually arm the greeting or trigger a labelled wakeup simulation.

Do not attach /control as an AI Agent tool.
"""
import argparse
import json
from urllib.error import HTTPError, URLError

from backend.http_client import post_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["arm", "wakeup", "reset-demo"])
    args = parser.parse_args()
    try:
        result = post_json("http://127.0.0.1:8000/control", {"action": args.action}, timeout=10)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"Control request failed: {type(exc).__name__}. Start tool_server.py first.")


if __name__ == "__main__":
    main()
