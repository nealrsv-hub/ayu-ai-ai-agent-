"""AYUSARTHI's chat-first frontend. Run: python -m streamlit run frontend/app.py.

Uses the existing tool server and n8n webhook. Whisper transcribes audio locally;
only a user-confirmed transcript enters the same queue as a typed message.
"""

import base64
import html
import inspect
import json
import logging
import math
import os
import shutil
import tempfile
import threading
import time
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path

import requests
import streamlit as st
from PIL import Image

from backend.voice import Speaker


BASE_DIR = Path(__file__).resolve().parent
SENSOR_URL = os.environ.get("SENSOR_URL", "").strip() or "http://127.0.0.1:8000/tools/sensor-status"
CHAT_URL = os.environ.get("N8N_CHAT_URL", "").strip() or "http://localhost:5678/webhook/ayusarthi-chat"
CHAT_READ_TIMEOUT_SECONDS = 360
LOGGER = logging.getLogger(__name__)
WHISPER_MODEL = "base"

CSS = """
<style>
:root { --ayu-navy: #173a51; --ayu-teal: #087e85; --ayu-muted: #657985;
        --ayu-line: #e0e9ec; --ayu-paper: #fbfcfc; }
.stApp { background: var(--ayu-paper); color: var(--ayu-navy); }
[data-testid="stHeader"] { background: rgba(251,252,252,.96); }
[data-testid="stMainBlockContainer"] {
    max-width: 950px; padding: 4.5rem 2rem 3rem;
}
[data-testid="stSidebar"] { background: #f1f6f6; border-right: 1px solid var(--ayu-line); }
[data-testid="stSidebarUserContent"] { padding-top: 1rem; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: .4rem; }
[data-testid="stSidebar"] [data-testid="stButton"] button > div { justify-content: flex-start; }
[data-testid="stSidebar"] hr { margin: 1.05rem 0; border-color: var(--ayu-line); }
[data-testid="stSidebar"] [data-testid="stButton"] button {
    justify-content: flex-start; border-radius: 9px; min-height: 43px;
    background: transparent; border: 1px solid transparent; color: #425d6b;
    box-shadow: none; transition: background .15s, border-color .15s;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background: #e6eeee; border-color: #d7e5e5;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
    background: #deeeee; color: #086c73; border-color: #cde2e2; font-weight: 600;
}
.st-key-new_chat [data-testid="stButton"] button {
    background: #fff !important; border-color: #cadbdf !important; color: var(--ayu-navy) !important;
}
.ayu-brand { display: flex; align-items: center; gap: 10px; padding: 0 0 1rem; }
.ayu-brand img { width: 70px; border-radius: 10px; }
.ayu-brand strong { display: block; font-size: 14px; letter-spacing: .035em; }
.ayu-brand small { color: var(--ayu-muted); font-size: 11px; }
.ayu-nav-label { color: #73858d; font-size: 10px; font-weight: 700; letter-spacing: .14em;
    margin: 0 0 .55rem .75rem; }
.ayu-topbar { display: flex; justify-content: space-between; gap: 12px; align-items: center;
    flex-wrap: wrap; border-bottom: 1px solid var(--ayu-line); padding: .35rem 0 1rem; }
.ayu-topbar-title { font-size: 14px; font-weight: 650; letter-spacing: .025em; }
.ayu-topbar-subtitle { color: var(--ayu-muted); font-size: 11px; margin-top: 3px; }
.ayu-pills { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.ayu-pill { display: inline-block; padding: 4px 9px; border-radius: 30px; font-size: 11px;
    font-weight: 600; white-space: nowrap; background: #edf2f4; color: #526976; }
.ayu-online { background: #e5f3ee; color: #24755c; }
.ayu-offline { background: #f8eaea; color: #a24c4c; }
.ayu-demo { background: #fff3dd; color: #8a651e; }
.ayu-sidebar-status { padding: .3rem .7rem; }
.ayu-sidebar-status p { color: #73858d; font-size: 11px; margin: 12px 0 0; }
.ayu-home { text-align: center; padding: clamp(24px, 4vh, 54px) 0 22px; }
.ayu-home img { width: 230px; max-width: 65%; border-radius: 20px; mix-blend-mode: multiply; }
.ayu-eyebrow { color: var(--ayu-teal); font-size: 10px; font-weight: 700; letter-spacing: .16em;
    text-transform: uppercase; margin: 18px 0 12px; }
.ayu-home h1 { font-size: clamp(26px, 3.2vw, 36px); letter-spacing: -.035em;
    font-weight: 550; line-height: 1.25; padding: 0; color: var(--ayu-navy); }
.ayu-home p { font-size: 14px; line-height: 1.7; color: var(--ayu-muted); margin: 14px auto 0;
    max-width: 440px; }
.st-key-suggestions [data-testid="stButton"] button {
    background: #fff; color: #345666; border: 1px solid var(--ayu-line);
    border-radius: 13px; min-height: 74px; padding: 16px 12px; box-shadow: 0 3px 9px #173a5103;
    transition: border-color .15s, background .15s, transform .15s;
}
.st-key-suggestions [data-testid="stButton"] button:hover {
    border-color: #90babb; background: #f5faf9; transform: translateY(-2px);
}
.ayu-home-note { text-align: center; color: #7a8b94; font-size: 11px; padding-top: 17px; }
[data-testid="stChatMessage"] { padding: 1.2rem 1rem; border-radius: 14px; background: transparent; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: #edf4f5; margin-left: clamp(0px, 5vw, 60px); border: 1px solid #e2ecee;
}
[data-testid="stChatMessageContent"] { min-width: 0; overflow-wrap: anywhere; line-height: 1.75; }
[data-testid="stChatMessageContent"] pre { max-width: 100%; overflow-x: auto; }
[data-testid="stBottom"] { background: var(--ayu-paper); }
[data-testid="stBottomBlockContainer"] { max-width: 950px; padding: .7rem 2rem 1rem; }
[data-testid="stChatInput"] { border: 1px solid #cbdde1; border-radius: 18px;
    background: #fff; box-shadow: 0 4px 22px #173a5108; }
[data-testid="stChatInput"]:focus-within { border-color: #488f96; }
.ayu-composer-note { color: #758791; text-align: center; font-size: 10px; margin-top: 7px; }
.ayu-page-intro { padding: 28px 0 20px; }
.ayu-page-intro h1 { font-size: 30px; font-weight: 550; letter-spacing: -.03em; padding: 0 0 8px; }
.ayu-page-intro p { color: var(--ayu-muted); font-size: 14px; margin: 0; }
.ayu-grid { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 14px; margin: 18px 0; }
.ayu-card { background: #fff; border: 1px solid var(--ayu-line); padding: 21px;
    border-radius: 14px; min-width: 0; overflow-wrap: anywhere; }
.ayu-card-label { color: var(--ayu-muted); font-size: 12px; margin-bottom: 12px; }
.ayu-card-value { color: var(--ayu-navy); font-size: 26px; font-weight: 550; letter-spacing: -.025em; }
.ayu-card-detail { color: #7a8b94; font-size: 11px; margin-top: 8px; }
.ayu-feature-list { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 12px; margin: 24px 0; }
.ayu-feature-list h3 { font-size: 15px; padding: 0 0 8px; }
.ayu-feature-list p { color: var(--ayu-muted); font-size: 13px; margin: 0; }
.ayu-flow { max-width: 480px; margin: 28px auto; text-align: center; }
.ayu-flow .ayu-card { padding: 17px; font-size: 15px; }
.ayu-arrow { color: #92a9ae; padding: 8px; }
.ayu-fallback { color: var(--ayu-teal); font-weight: 650; letter-spacing: .03em; }
.ayu-splash { min-height: 75vh; display: flex; align-items: center; justify-content: center;
    flex-direction: column; text-align: center; }
.ayu-splash img { width: 320px; max-width: 75vw; border-radius: 24px; mix-blend-mode: multiply; }
.ayu-splash .ayu-logo-wrap { animation: ayu-enter 1.5s ease both; }
.ayu-splash p { font-size: 18px; color: #36576a; margin: 22px 0 8px; }
.ayu-splash small { font-size: 12px; color: #7a8b94; }
@keyframes ayu-enter { from { opacity: 0; transform: scale(.94); } to { opacity: 1; transform: scale(1); } }
@media (prefers-reduced-motion: reduce) {
    .ayu-splash .ayu-logo-wrap { animation: none; }
    .st-key-suggestions button { transition: none !important; transform: none !important; }
}
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] { padding: 4.2rem 1rem 2rem; }
    [data-testid="stBottomBlockContainer"] { padding: .6rem 1rem; }
    .ayu-home { padding-top: 24px; }
    .ayu-home img { width: 185px; }
    .ayu-grid, .ayu-feature-list { grid-template-columns: repeat(2,minmax(0,1fr)); gap: 10px; }
    .ayu-card { padding: 15px; }
    .ayu-card-value { font-size: 22px; }
    .st-key-suggestions [data-testid="stButton"] button { min-height: 48px; }
}
@media (max-width: 380px) { .ayu-feature-list { grid-template-columns: 1fr; } }
</style>
"""


def get_logo_path():
    """Accept the standard logo filename and older asset names."""
    for name in ("ayusarthi_logo.jpeg", "ayusarthi_logo.jpeg.jpeg",
                 "ayusarthi_logo.jpg", "ayusarthi_logo.png"):
        candidate = BASE_DIR / name
        if candidate.is_file():
            return candidate
    return None


@st.cache_data(show_spinner=False)
def load_logo_base64(path, modified_ns):
    """Validate bytes before embedding. The mtime invalidates replaced assets."""
    del modified_ns
    raw = Path(path).read_bytes()
    with Image.open(BytesIO(raw)) as picture:
        mime = Image.MIME.get(picture.format)
        picture.verify()
    if mime not in ("image/jpeg", "image/png", "image/webp"):
        raise ValueError("Use a JPEG, PNG, or WebP logo.")
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"


def prepare_logo():
    try:
        path = get_logo_path()
        if path is None:
            raise FileNotFoundError(f"No ayusarthi_logo.jpeg or supported fallback in {BASE_DIR}")
        return load_logo_base64(str(path), path.stat().st_mtime_ns), None
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        warning = f"Logo could not be loaded: {exc}. Check the filename and image permissions."
        if st.session_state.get("logo_warning") != warning:
            LOGGER.warning(warning)
            st.session_state.logo_warning = warning
        return None, warning


def logo_html(logo):
    if logo:
        return f'<img src="{logo}" alt="AYUSARTHI AI logo">'
    return '<span class="ayu-fallback">AYUSARTHI AI</span>'


def initialize_session():
    defaults = {"session_id": str(uuid.uuid4()), "messages": [], "page": "Chat",
                "splash_done": False, "pending_prompt": None, "mic_notice": None,
                "mic_recording": None, "voice_status": "idle", "voice_error": None,
                "voice_transcript": "", "voice_pending": False,
                "spoken_replies_enabled": True, "last_spoken_reply": None}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def new_chat():
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.pending_prompt = None
    st.session_state.last_spoken_reply = None
    clear_voice()
    st.session_state.page = "Chat"


def set_page(page):
    st.session_state.page = page


def queue_prompt(prompt):
    if isinstance(prompt, str) and prompt.strip():
        prompt = prompt.strip()
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.pending_prompt = prompt
        st.session_state.mic_notice = None


def accept_composer():
    submission = st.session_state.get("composer")
    if isinstance(submission, str):
        queue_prompt(submission)
    elif submission is not None:
        if submission.get("audio") is not None:
            capture_mic_recording(submission["audio"])
            if submission.get("text", ""):
                st.session_state.composer = submission["text"]
        else:
            queue_prompt(submission.get("text", ""))


class TranscriptionError(RuntimeError):
    """An actionable voice-input error suitable for display without a traceback."""


@st.cache_resource(show_spinner=False)
def load_whisper_model():
    """Lazy-load once per app process. Whisper keeps model weights in its own cache."""
    import whisper
    return whisper.load_model(WHISPER_MODEL, device="cpu"), threading.Lock()


def transcribe_audio(audio_data):
    """Transcribe a native Streamlit WAV or captured bytes and remove its temp file."""
    recording = audio_data.getvalue() if hasattr(audio_data, "getvalue") else audio_data
    if not isinstance(recording, (bytes, bytearray)) or not recording:
        raise TranscriptionError("No microphone recording was received. Please record again.")
    if shutil.which("ffmpeg") is None:
        raise TranscriptionError(
            "FFmpeg executable is missing from PATH. Install FFmpeg, then restart "
            "your terminal and Streamlit. The ffmpeg-python package alone is not enough."
        )
    try:
        model, inference_lock = load_whisper_model()
    except Exception as exc:
        LOGGER.warning("Whisper model load failed (%s)", type(exc).__name__)
        if "Application Control" in str(exc):
            raise TranscriptionError(
                "Windows Application Control blocked a Whisper dependency. "
                "Whisper cannot load until that installation issue is resolved. Text chat still works."
            ) from exc
        raise TranscriptionError(
            "The local Whisper base model could not load. Check the Whisper installation, "
            "free disk space, and internet access for the first model download. Text chat still works."
        ) from exc
    try:
        with tempfile.TemporaryDirectory(prefix="ayusarthi-voice-") as directory:
            path = Path(directory) / "recording.wav"
            path.write_bytes(recording)
            try:
                with inference_lock:
                    result = model.transcribe(str(path), fp16=False, task="transcribe",
                                              verbose=None, condition_on_previous_text=False)
            except Exception as exc:
                LOGGER.warning("Whisper transcription failed (%s)", type(exc).__name__)
                raise TranscriptionError(
                    "This recording could not be transcribed. Try again or record a short, clear message. "
                    "Nothing was sent to AYUSARTHI."
                ) from exc
    except OSError as exc:
        raise TranscriptionError(
            "The temporary audio file could not be created or cleaned up. "
            "Check available disk space and temporary-folder permissions, then try again."
        ) from exc
    text = result.get("text") if isinstance(result, dict) else None
    if not isinstance(text, str) or not text.strip():
        raise TranscriptionError("No speech was recognized. Please record again or type your message.")
    return text.strip()


def clear_voice():
    st.session_state.mic_recording = None
    st.session_state.mic_notice = None
    st.session_state.voice_status = "idle"
    st.session_state.voice_error = None
    st.session_state.voice_pending = False
    st.session_state.voice_transcript = ""
    st.session_state.voice_draft = ""


def capture_mic_recording(audio):
    """Queue local transcription only; never queue an AI message from a recording."""
    clear_voice()
    recording = audio.getvalue() if audio is not None else b""
    st.session_state.mic_recording = recording or None
    st.session_state.voice_status = "received" if recording else "error"
    st.session_state.voice_pending = bool(recording)
    st.session_state.mic_notice = (
        f"Recording received · {len(recording):,} bytes."
        if recording else "No audio data was received. Please record again."
    )


def accept_audio_input(key):
    """Compatibility callback for native st.audio_input on older Streamlit versions."""
    audio = st.session_state.get(key)
    if audio is not None:
        capture_mic_recording(audio)
    else:
        clear_voice()


def retry_transcription():
    if st.session_state.mic_recording:
        st.session_state.voice_pending = True
        st.session_state.voice_status = "received"
        st.session_state.voice_error = None


def preserve_voice_draft():
    st.session_state.voice_transcript = st.session_state.voice_draft


def send_voice_transcript():
    text = st.session_state.get("voice_draft", st.session_state.voice_transcript).strip()
    if st.session_state.voice_status == "ready" and text:
        queue_prompt(text)
        clear_voice()


def get_sensor_status():
    """One bounded snapshot per rerun; never substitute invented readings."""
    result = {"connected": False, "data": None, "error": None,
              "checked_at": datetime.now().astimezone().strftime("%H:%M:%S %Z")}
    try:
        response = requests.get(SENSOR_URL, timeout=(2, 3))
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or not isinstance(data.get("values"), dict):
            raise ValueError("Expected a sensor object containing a values object.")
        result["data"] = data
        result["connected"] = True
    except requests.RequestException:
        result["error"] = "The sensor endpoint could not be reached or returned an error."
    except ValueError:
        result["error"] = "The sensor endpoint returned an unreadable response."
    return result


def extract_ayusarthi_answer(payload, depth=0):
    """Read n8n's answer from its configured or pass-through response shapes."""
    if depth > 5:
        raise ValueError("The webhook response is nested too deeply.")
    if isinstance(payload, str):
        text = payload.strip()
        if not text:
            raise ValueError("The webhook response contains empty text.")
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            return text
        return extract_ayusarthi_answer(decoded, depth + 1)
    if isinstance(payload, list):
        if len(payload) != 1:
            raise ValueError("The webhook response array must contain one result.")
        return extract_ayusarthi_answer(payload[0], depth + 1)
    if isinstance(payload, dict):
        for key in ("answer", "output"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for key in ("body", "data", "json"):
            if key in payload:
                try:
                    return extract_ayusarthi_answer(payload[key], depth + 1)
                except ValueError:
                    pass
    raise ValueError("The webhook response needs non-empty answer or output text.")


def ask_ayusarthi(prompt):
    response = requests.post(CHAT_URL, json={
        "chatInput": prompt, "sessionId": st.session_state.session_id,
    }, timeout=(3, CHAT_READ_TIMEOUT_SECONDS))
    LOGGER.info(
        "n8n webhook response status=%s content_type=%s",
        response.status_code,
        response.headers.get("content-type"),
    )
    response.raise_for_status()
    return extract_ayusarthi_answer(response.json())


@st.cache_resource(show_spinner=False)
def get_speaker():
    """Reuse the project's local, asynchronous text-to-speech worker."""
    return Speaker(enabled=True)


def speak_assistant_reply(answer, message_index):
    """Queue one successful reply for speech at most once per chat message."""
    if not st.session_state.spoken_replies_enabled:
        return
    reply_id = f"{st.session_state.session_id}:{message_index}"
    if st.session_state.last_spoken_reply == reply_id:
        return
    st.session_state.last_spoken_reply = reply_id
    try:
        get_speaker().say(answer)
    except Exception as exc:
        LOGGER.warning("Speech output failed; text reply remains available: %s", exc)


def status_html(sensor):
    online = sensor["connected"]
    css, label = ("ayu-online", "System online") if online else ("ayu-offline", "System offline")
    content = f'<span class="ayu-pill {css}" title="Sensor tool server connectivity">● {label}</span>'
    data = sensor.get("data") or {}
    if data.get("is_simulated") is True:
        content += '<span class="ayu-pill ayu-demo">Demo Mode</span>'
    elif data.get("is_simulated") is False:
        content += '<span class="ayu-pill">Sensor mode</span>'
    else:
        content += '<span class="ayu-pill">Data mode unknown</span>'
    return f'<div class="ayu-pills">{content}</div>'


def render_splash(logo):
    if st.session_state.splash_done:
        return
    st.markdown(f'<div class="ayu-splash"><div class="ayu-logo-wrap">{logo_html(logo)}</div>'
                '<p>Your health is our priority.</p><small>Powered by Neel · CODEX 404</small></div>',
                unsafe_allow_html=True)
    st.session_state.splash_done = True
    time.sleep(1.8)
    st.rerun()


def render_sidebar(logo, sensor, logo_warning):
    with st.sidebar:
        st.markdown(f'<div class="ayu-brand">{logo_html(logo)}<div><strong>AYUSARTHI AI</strong>'
                    '<small>A little support, every day.</small></div></div>', unsafe_allow_html=True)
        with st.container(key="new_chat"):
            st.button("New Chat", icon=":material/add:", on_click=new_chat, use_container_width=True)
        st.toggle(
            "Spoken replies",
            key="spoken_replies_enabled",
            help="Speak each new successful reply using this computer's local voice.",
        )
        st.divider()
        st.markdown('<div class="ayu-nav-label">YOUR ASSISTANT</div>', unsafe_allow_html=True)
        nav_item("Chat", ":material/chat_bubble_outline:")
        st.divider()
        st.markdown('<div class="ayu-nav-label">MONITORING</div>', unsafe_allow_html=True)
        for page, icon in (("Monitoring", ":material/home_health:"),
                           ("Caregiver", ":material/group:"), ("Alerts", ":material/notifications_none:")):
            nav_item(page, icon)
        st.divider()
        nav_item("About", ":material/info:")
        st.divider()
        st.markdown(f'<div class="ayu-sidebar-status">{status_html(sensor)}'
                    '<p>AYUSARTHI Prototype<br>Powered by Neel · CODEX 404</p></div>', unsafe_allow_html=True)
        if logo_warning:
            with st.expander("Developer: logo warning"):
                st.warning(logo_warning)


def nav_item(page, icon):
    st.button(page, icon=icon, key=f"nav_{page}", use_container_width=True,
              type="primary" if st.session_state.page == page else "secondary",
              on_click=set_page, args=(page,))


def render_topbar(sensor):
    st.markdown('<div class="ayu-topbar"><div><div class="ayu-topbar-title">AYUSARTHI AI</div>'
                '<div class="ayu-topbar-subtitle">Your everyday companion</div></div>'
                f'{status_html(sensor)}</div>', unsafe_allow_html=True)


def render_home(logo):
    st.markdown(f'<div class="ayu-home">{logo_html(logo)}'
                '<div class="ayu-eyebrow">Here to help. Here to care.</div>'
                '<h1>How can I help you today?</h1>'
                '<p>Your AI companion for monitoring,<br>assistance and health education.</p></div>',
                unsafe_allow_html=True)
    with st.container(key="suggestions"):
        suggestions = (
            ("Check room status", ":material/home:", "What do the current room sensor readings show? State whether they are simulated and fresh."),
            ("Check activity status", ":material/directions_walk:", "What posture does the monitoring system currently estimate? Explain its limitations and whether the data is simulated."),
            ("Health education", ":material/spa:", "Share a short general health education tip from the supplied health notes, with its source."),
        )
        for column, (label, icon, prompt) in zip(st.columns(3), suggestions):
            with column:
                st.button(label, icon=icon, use_container_width=True, on_click=queue_prompt, args=(prompt,))
    st.markdown('<div class="ayu-home-note">Thoughtful assistance, grounded in the information available.</div>',
                unsafe_allow_html=True)


def render_composer():
    native_audio = "accept_audio" in inspect.signature(st.chat_input).parameters
    kwargs = {"accept_audio": True} if native_audio else {}
    st.chat_input("Ask AYUSARTHI anything…", key="composer", on_submit=accept_composer,
                  max_chars=12000, **kwargs)
    if hasattr(st, "bottom"):
        with st.bottom:
            render_voice_input(native_audio)
    else:
        render_voice_input(native_audio)


def render_voice_input(native_audio):
    """Local transcription and explicit review beside the existing composer."""
    note = "Mic beta · Local Whisper · Review the transcript before sending."
    if not native_audio:
        if hasattr(st, "audio_input"):
            with st.expander("Microphone · beta"):
                st.caption("Transcribed locally. Only the text you confirm is sent to AYUSARTHI.")
                key = f"audio_{st.session_state.session_id}"
                st.audio_input("Record a question (beta)", key=key,
                               on_change=accept_audio_input, args=(key,))
        else:
            note = "Microphone unavailable in this Streamlit version. Text chat is ready."
    if st.session_state.voice_pending:
        st.session_state.voice_pending = False
        st.session_state.voice_status = "processing"
        progress = st.empty()
        progress.caption(st.session_state.mic_notice or "Recording received.")
        try:
            with st.spinner("Transcribing locally… First use may download the base model."):
                transcript = transcribe_audio(st.session_state.mic_recording)
            st.session_state.voice_transcript = transcript
            st.session_state.voice_draft = transcript
            st.session_state.voice_status = "ready"
            st.session_state.mic_notice = "Transcript ready · Review and edit before sending."
        except TranscriptionError as exc:
            st.session_state.voice_status = "error"
            st.session_state.voice_error = str(exc)
        finally:
            progress.empty()
    recording = st.session_state.get("mic_recording")
    if st.session_state.mic_notice:
        st.caption(st.session_state.mic_notice)
    if recording:
        with st.container(border=True, key="voice_review"):
            if st.session_state.voice_status == "ready":
                st.session_state.voice_draft = st.session_state.voice_transcript
                st.text_area("You said:", key="voice_draft", height=80,
                             on_change=preserve_voice_draft)
                send, discard = st.columns([2, 1])
                send.button("Send to AYUSARTHI", key="send_voice", type="primary",
                            on_click=send_voice_transcript,
                            disabled=not st.session_state.voice_draft.strip(), use_container_width=True)
                discard.button("Discard", key="discard_voice", on_click=clear_voice,
                               use_container_width=True)
            else:
                if st.session_state.voice_error:
                    st.warning(st.session_state.voice_error)
                elif st.session_state.voice_status == "processing":
                    st.caption("Transcription was interrupted. Retry when ready.")
                retry, discard = st.columns([2, 1])
                retry.button("Retry transcription", on_click=retry_transcription,
                             use_container_width=True)
                discard.button("Discard", key="discard_voice", on_click=clear_voice,
                               use_container_width=True)
            with st.expander("Play recording"):
                st.audio(recording, format="audio/wav")
    note_html = f'<div class="ayu-composer-note">{note}</div>'
    st.markdown(note_html, unsafe_allow_html=True)


def render_chat_page(logo):
    if not st.session_state.messages:
        render_home(logo)
    for message in st.session_state.messages:
        avatar = None if message["role"] == "user" else ":material/spa:"
        with st.chat_message(message["role"], avatar=avatar):
            if message.get("error"):
                st.error(message["content"])
            else:
                st.markdown(message["content"])
    pending = st.session_state.pending_prompt
    if pending:
        st.session_state.pending_prompt = None
        with st.chat_message("assistant", avatar=":material/spa:"):
            try:
                with st.spinner("AYUSARTHI is thinking…"):
                    answer = ask_ayusarthi(pending)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                speak_assistant_reply(answer, len(st.session_state.messages) - 1)
            except requests.Timeout:
                record_chat_error("AYUSARTHI took too long to respond. Please try again. The previous request may still finish in n8n.")
            except requests.RequestException:
                record_chat_error("The AI connection is unavailable. Check that n8n is running and the AYUSARTHI chat workflow is published, then try again.")
            except ValueError:
                record_chat_error("The AI returned an unreadable response. Check that the n8n webhook returns an answer field containing text.")
    render_composer()


def record_chat_error(message):
    st.error(message)
    st.session_state.messages.append({"role": "assistant", "content": message, "error": True})


def page_intro(title, description):
    st.markdown(f'<div class="ayu-page-intro"><h1>{html.escape(title)}</h1>'
                f'<p>{html.escape(description)}</p></div>', unsafe_allow_html=True)


def number(value, suffix=""):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return f"{value:g}{suffix}"
    return "Unavailable"


def card(label, value, detail):
    return (f'<div class="ayu-card"><div class="ayu-card-label">{html.escape(label)}</div>'
            f'<div class="ayu-card-value">{html.escape(str(value))}</div>'
            f'<div class="ayu-card-detail">{html.escape(detail)}</div></div>')


def render_monitoring_page(sensor):
    page_intro("A view of the room", "Current sensor readings, with their source and freshness in view.")
    st.button("Refresh readings", icon=":material/refresh:")
    data = sensor.get("data")
    if data is None:
        st.error("Monitoring unavailable")
        st.caption(sensor["error"] or "No sensor data is available.")
        st.caption(f"Last checked: {sensor['checked_at']}")
        return
    if data.get("is_simulated") is True:
        st.info("Demo / Simulated Data — these readings are fictional demonstration values.", icon=":material/science:")
    elif data.get("is_simulated") is not False:
        st.warning("Data source mode is unknown; these readings are not confirmed as hardware data.")
    fresh = data.get("fresh") is True
    if not fresh:
        st.warning("Sensor data is stale or freshness is unknown. Readings may not reflect the current room.")
    values = data["values"]
    posture = data.get("posture_estimate")
    posture = posture.replace("_", " ").capitalize() if isinstance(posture, str) and posture else "Unknown"
    age = number(data.get("age_seconds"), " s")
    cards = [
        card("Current status", "Receiving data" if fresh else "Check readings", "Sensor snapshot; not a health assessment"),
        card("Posture estimate", posture, "Estimated from distance readings"),
        card("Distance", number(values.get("distance_cm"), " cm"), "Distance from the sensor"),
        card("Room temperature", number(values.get("temperature_c"), " °C"), "Ambient room temperature"),
        card("Humidity", number(values.get("humidity_pct"), " %"), "Relative room humidity"),
        card("Freshness", "Fresh" if fresh else "Stale / unknown", f"Reading age: {age}"),
    ]
    st.markdown('<div class="ayu-grid">' + "".join(cards) + '</div>', unsafe_allow_html=True)
    st.caption("Room temperature is ambient temperature, not body temperature.")
    source = data.get("data_source")
    st.caption(f"Last checked: {sensor['checked_at']} · Snapshot updates when you refresh or navigate.")
    if isinstance(source, str):
        st.text(f"Source: {source}")


def render_caregiver_page():
    page_intro("Care, with more context", "A future space for caregivers to understand changes over time.")
    st.markdown('<span class="ayu-pill ayu-demo">Coming next · Prototype module</span>', unsafe_allow_html=True)
    features = (
        ("Activity timeline", "A planned view of activity estimates over time."),
        ("Event history", "A planned record of detected events for review."),
        ("Daily summaries", "A planned summary of the day's available observations."),
        ("Caregiver alerts", "Planned notifications when supported events need attention."),
        ("Environment overview", "A planned view of room conditions over time."),
    )
    markup = "".join(f'<div class="ayu-card"><h3>{title}</h3><p>{description}</p></div>'
                     for title, description in features)
    st.markdown(f'<div class="ayu-feature-list">{markup}</div>', unsafe_allow_html=True)
    st.caption("This module is not active. Caregiver accounts, event history, and notifications are not connected.")


def render_alerts_page():
    page_intro("A clearer path to support", "The planned alert flow, from observation to caregiver awareness.")
    st.markdown('<span class="ayu-pill ayu-demo">Coming next · Prototype module</span>', unsafe_allow_html=True)
    steps = ["Sensors", "Event detection", "AYUSARTHI", "Caregiver alert"]
    flow = '<div class="ayu-arrow" aria-hidden="true">↓</div>'.join(
        f'<div class="ayu-card">{step}</div>' for step in steps)
    st.markdown(f'<div class="ayu-flow" aria-label="Planned alert pipeline">{flow}</div>', unsafe_allow_html=True)
    st.info("Alert delivery is not enabled. No caregiver messages or emergency calls are sent from this page.")


def render_about_page():
    page_intro("Thoughtfully built for everyday support", "AYUSARTHI AI · Hackathon prototype")
    st.markdown("AYUSARTHI combines room sensor status, a fictional demo profile, source-linked educational notes, and chat through a separately configured n8n workflow.")
    st.markdown("General health education is available through chat. Posture is an estimate; the system does not provide medical diagnoses or measure body temperature, heart rate, or blood pressure.")
    st.caption("Microphone input uses local Whisper base transcription. Review and confirm the text before it enters chat. Laptop speech output is a separate system.")
    st.caption("System online describes the sensor tool server. The AI connection is checked when you send a message. Chat requests go through your existing n8n workflow.")
    st.caption("Powered by Neel · CODEX 404")


def main(configure_page=True):
    if configure_page:
        st.set_page_config(page_title="AYUSARTHI AI", page_icon="🌿", layout="wide", initial_sidebar_state="expanded")
    st.markdown(CSS, unsafe_allow_html=True)
    initialize_session()
    logo, logo_warning = prepare_logo()
    render_splash(logo)
    sensor = get_sensor_status()
    render_sidebar(logo, sensor, logo_warning)
    render_topbar(sensor)
    page = st.session_state.page
    if page == "Chat":
        render_chat_page(logo)
    elif page == "Monitoring":
        render_monitoring_page(sensor)
    elif page == "Caregiver":
        render_caregiver_page()
    elif page == "Alerts":
        render_alerts_page()
    else:
        render_about_page()


if __name__ == "__main__":
    main()

