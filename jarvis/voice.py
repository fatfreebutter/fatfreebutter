"""Microphone input (speech-to-text) and spoken output (macOS `say`)."""

import os
import shutil
import subprocess

VOICE = os.environ.get("JARVIS_VOICE", "Daniel")  # British English voice bundled with macOS
RATE = os.environ.get("JARVIS_RATE", "190")


def speak(text):
    print(f"Jarvis: {text}")
    if shutil.which("say"):
        subprocess.run(["say", "-v", VOICE, "-r", RATE, text])


class Listener:
    def __init__(self):
        import speech_recognition as sr  # imported lazily so --text mode needs no audio deps

        self.sr = sr
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.mic = sr.Microphone()
        with self.mic as source:
            print("Calibrating for background noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def listen(self, timeout=None, phrase_limit=12):
        """Return the transcribed phrase, or None on silence / unintelligible audio."""
        with self.mic as source:
            try:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
            except self.sr.WaitTimeoutError:
                return None
        try:
            return self.recognizer.recognize_google(audio)
        except self.sr.UnknownValueError:
            return None
        except self.sr.RequestError as e:
            print(f"Speech service error: {e}")
            return None
