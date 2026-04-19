import threading
import pyttsx3


def speak(text, rate=150, volume=1.0):
    """Speaks text in a background thread so it never blocks the caller."""
    def run():
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)      # Words per minute — tweak 120–180
        engine.setProperty("volume", volume)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    threading.Thread(target=run, daemon=True).start()
