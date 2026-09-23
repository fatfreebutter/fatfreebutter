#!/usr/bin/env python3
"""Jarvis: a voice-activated assistant for macOS powered by Claude.

    python jarvis.py          # voice mode: say "Jarvis, ..." to wake it
    python jarvis.py --text   # type instead of talk (handy for testing)
"""

import argparse
import os
import re

from brain import Brain
from voice import Listener, speak

WAKE_WORDS = [w.strip().lower() for w in os.environ.get("JARVIS_WAKE", "jarvis,hey jarvis").split(",")]
STOP_PHRASES = {"goodbye", "good bye", "shut down", "exit", "quit"}
RESET_PHRASES = {"forget that", "new conversation", "start over"}
YES = re.compile(r"\b(yes|yeah|yep|sure|confirm|do it|go ahead|affirmative)\b", re.I)


def strip_wake_word(phrase):
    """Return the command after the wake word, '' if only the wake word, or None if absent."""
    lower = phrase.lower()
    for wake in sorted(WAKE_WORDS, key=len, reverse=True):
        idx = lower.find(wake)
        if idx != -1:
            return phrase[idx + len(wake):].strip(" ,.!?")
    return None


def handle(brain, command):
    """Process one command. Returns False when Jarvis should exit."""
    lower = command.lower().strip(" .!?")
    if lower in STOP_PHRASES:
        speak("Goodbye.")
        return False
    if lower in RESET_PHRASES:
        brain.reset()
        speak("Consider it forgotten.")
        return True
    try:
        speak(brain.ask(command))
    except Exception as e:
        print(f"Error: {e!r}")
        speak("Sorry, I ran into a problem reaching my brain.")
    return True


def run_text():
    brain = Brain(confirm=lambda s: bool(re.match(r"y", input(f"Jarvis wants to: {s}. Allow? [y/N] "), re.I)))
    speak("Jarvis online. Type your request.")
    while True:
        try:
            command = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if command and not handle(brain, command):
            break


def run_voice():
    listener = Listener()

    def confirm(summary):
        speak(f"I'm about to {summary}. Shall I go ahead?")
        answer = listener.listen(timeout=6, phrase_limit=4) or ""
        print(f"You: {answer}")
        return YES.search(answer) is not None

    brain = Brain(confirm=confirm)
    speak("Jarvis online.")
    print(f"Listening for wake word: {', '.join(WAKE_WORDS)}  (Ctrl+C to quit)")

    while True:
        phrase = listener.listen(phrase_limit=10)
        if not phrase:
            continue
        command = strip_wake_word(phrase)
        if command is None:
            continue
        print(f"You: {phrase}")
        if not command:
            speak("Yes?")
            command = listener.listen(timeout=6) or ""
            print(f"You: {command}")
            if not command:
                continue
        if not handle(brain, command):
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--text", action="store_true", help="type commands instead of speaking")
    args = parser.parse_args()
    try:
        run_text() if args.text else run_voice()
    except KeyboardInterrupt:
        print()
