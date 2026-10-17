"""Optional offline speech output and push-to-talk recognition."""
import json
import queue
import threading
import time


class Speaker:
    def __init__(self, enabled=False):
        self.enabled = enabled
        self.pending = queue.Queue()
        self.busy = threading.Event()
        self.ready = threading.Event()
        self.audio_lock = threading.RLock()
        if enabled:
            threading.Thread(target=self._worker, daemon=True).start()
        else:
            self.ready.set()

    def say(self, text):
        if self.enabled:
            self.pending.put(text)

    def _worker(self):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 155)
        except Exception as exc:
            self.enabled = False
            self.ready.set()
            print(f"Speech output unavailable ({type(exc).__name__}); text remains available.")
            return
        self.ready.set()
        while True:
            text = self.pending.get()
            self.busy.set()
            try:
                with self.audio_lock:
                    engine.say(text)
                    engine.runAndWait()
            except Exception as exc:
                print(f"Speech output failed ({type(exc).__name__}).")
            finally:
                self.busy.clear()
                self.pending.task_done()

    def wait_idle(self, timeout=20):
        deadline = time.monotonic() + timeout
        while not self.ready.is_set() or self.busy.is_set() or not self.pending.empty():
            if time.monotonic() > deadline:
                raise RuntimeError("Speech is still busy. Try typed input.")
            time.sleep(0.1)


def hear_once(model_path, seconds=8):
    """Recognize one recorded English question using a separately downloaded model."""
    import sounddevice as sd
    from vosk import KaldiRecognizer, Model
    model = Model(str(model_path))
    device = sd.query_devices(kind="input")
    rate = int(device["default_samplerate"])
    print(f"Listening for {seconds} seconds. Ask one question.")
    audio = sd.rec(int(seconds * rate), samplerate=rate, channels=1, dtype="int16")
    sd.wait()
    recognizer = KaldiRecognizer(model, rate)
    result_words = []
    block_frames = max(1, rate // 4)
    for offset in range(0, len(audio), block_frames):
        if recognizer.AcceptWaveform(audio[offset:offset + block_frames].tobytes()):
            result_words.append(json.loads(recognizer.Result()).get("text", ""))
    result_words.append(json.loads(recognizer.FinalResult()).get("text", ""))
    return " ".join(part for part in result_words if part).strip()
