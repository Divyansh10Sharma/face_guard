"""
AlertSystem — voice alerts for each detection type.
Uses pyttsx3 for offline text-to-speech (no internet required).
"""

from helpers.tts_helper import speak


VOICE_MESSAGES = {
    "calibrated":  "You are all set",
    "face_touch":  "Stop touching your face",   # Tweak: change message text here
    "frustrated":  "Fix your expression",       # Tweak: e.g. "Relax your face"
    "squint"    :  "Relax your eyes",           # Tweak: e.g. "Look away from the screen"
    "low_blink" :  "Blink more",                # Tweak: e.g. "Remember to blink"
}


class AlertSystem:
    def beep(self, alert_type):
        if alert_type in VOICE_MESSAGES:
            speak(VOICE_MESSAGES[alert_type])
