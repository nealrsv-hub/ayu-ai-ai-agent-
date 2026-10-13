"""Typed questions -> n8n webhook -> optional offline spoken answer."""
import argparse
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from uuid import uuid4

from backend.http_client import post_json
from backend.voice import Speaker, hear_once


def get_answer(url, question, session_id):
    result = post_json(url, {"chatInput": question, "sessionId": session_id})
    if not isinstance(result, dict) or not isinstance(result.get("answer"), str):
        raise ValueError("n8n must return a JSON object with an answer string. Check Respond to Webhook.")
    if not result["answer"].strip():
        raise ValueError("n8n returned an empty answer. Inspect the AI Agent execution.")
    return result["answer"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=os.environ.get("N8N_CHAT_URL"))
    parser.add_argument("--speak", action="store_true")
    parser.add_argument("--voice-model", help="Optional directory for an English Vosk speech model")
    args = parser.parse_args()
    if not args.url:
        parser.error("Pass --url with the Production URL copied from your n8n Webhook node.")
    parts = urlsplit(args.url)
    if parts.scheme != "http" or parts.hostname not in {"localhost", "127.0.0.1", "::1"}:
        parser.error("This starter expects a local HTTP n8n URL on your laptop.")
    speaker = Speaker(enabled=args.speak)
    session_id = str(uuid4())
    print("Fictional demonstration only. Ask about the demo, or public health notes.")
    print("Commands: /new (new conversation), /hear (optional microphone), /quit")
    while True:
        try:
            question = input("You: ").strip()
            if question == "/quit":
                break
            if question == "/new":
                session_id = str(uuid4())
                print("New session started.")
                continue
            if question == "/hear":
                if not args.voice_model:
                    print("Pass --voice-model first, or use typed input.")
                    continue
                speaker.wait_idle()
                with speaker.audio_lock:
                    question = hear_once(args.voice_model)
                print("Heard:", question)
            if not question:
                continue
            answer = get_answer(args.url, question[:2000], session_id)
            print("AYUSARTHI:", answer)
            speaker.say(answer)
        except HTTPError as exc:
            print(f"n8n HTTP {exc.code}. Check the webhook URL and workflow execution; no AI answer is available.")
        except (URLError, TimeoutError):
            print("n8n is unavailable or timed out. Keep its terminal open and check the URL.")
        except (ValueError, RuntimeError) as exc:
            print(str(exc))
        except ImportError:
            print("Microphone dependencies are missing. Use typed input or install requirements-voice.txt.")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    main()
