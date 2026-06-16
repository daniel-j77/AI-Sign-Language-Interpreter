import pyttsx3
import threading

_engine = pyttsx3.init()
_lock = threading.Lock()

_engine.setProperty("rate", 170)

# 🔥 ADDED: volume + voice selection
_engine.setProperty("volume", 1.0)

voices = _engine.getProperty('voices')
print("Available voices:", voices)  # 🔥 shows all voices

# 🔥 Use female voice if available
if len(voices) > 1:
    _engine.setProperty('voice', voices[1].id)
else:
    _engine.setProperty('voice', voices[0].id)


def text_to_speech(text):

    if not text:
        return

    def speak():
        with _lock:
            _engine.stop()
            _engine.say(text)
            _engine.runAndWait()

    threading.Thread(target=speak, daemon=True).start()