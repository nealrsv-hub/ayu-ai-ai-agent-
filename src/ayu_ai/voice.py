"""Optional local speech. Audio errors must not stop terminal use."""
import sys


class Speaker:
    def __init__(self, enabled: bool = False):
        self._engine = None
        if enabled:
            try:
                import pyttsx3
                self._engine = pyttsx3.init()
            except Exception:
                # Optional engines can fail with platform-specific exceptions.
                print("Speech unavailable. Install the voice extra and check OS audio; "
                      "continuing with text.", file=sys.stderr)

    def say(self, text: str) -> None:
        if self._engine is None:
            return
        try:
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception:
            print("Speech failed; continuing with text.", file=sys.stderr)
            self.close()

    def close(self) -> None:
        engine, self._engine = self._engine, None
        if engine is not None:
            try:
                engine.stop()
            except Exception:
                pass  # Cleanup must not hide a usable text response.
