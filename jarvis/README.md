# Jarvis — voice assistant for macOS

Say **"Jarvis, …"** and it listens, thinks with Claude, acts on your Mac, and answers out loud.

```
mic ──► wake word ("jarvis") ──► speech-to-text ──► Claude (tools + web search) ──► macOS `say`
```

## What it can do

| Ask | Tool |
|---|---|
| "Jarvis, open Spotify" | `open_app` |
| "Jarvis, open GitHub" | `open_url` |
| "Jarvis, volume to 30" | `set_volume` |
| "Jarvis, next song" / "pause" | `media_control` (Spotify or Music) |
| "Jarvis, how's my battery?" | `system_status` |
| "Jarvis, what's the weather in Freiburg?" | web search |
| "Jarvis, turn on dark mode" / "remind me at 5 to study" | `run_applescript` — **asks you to confirm aloud** |
| "Jarvis, how much disk space is free?" | `run_shell` — **asks you to confirm aloud** |

Other commands: **"forget that"** clears the conversation, **"goodbye"** quits.

## Setup

```bash
brew install portaudio                  # needed by PyAudio
cd jarvis
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...     # from console.anthropic.com
python jarvis.py                        # or: python jarvis.py --text
```

The first run asks for **microphone** permission for your terminal. AppleScript actions may also prompt for
**Automation** / **Accessibility** access (System Settings → Privacy & Security).

## Configuration (env vars)

| Var | Default | Notes |
|---|---|---|
| `JARVIS_MODEL` | `claude-opus-5` | Any Claude model ID |
| `JARVIS_EFFORT` | `low` | `low`…`max`; higher = smarter but slower replies |
| `JARVIS_VOICE` | `Daniel` | Any voice from `say -v '?'` |
| `JARVIS_RATE` | `190` | Speaking rate (words/min) |
| `JARVIS_WAKE` | `jarvis,hey jarvis` | Comma-separated wake phrases |

## Notes

- Speech-to-text uses Google's free web recognizer via `SpeechRecognition` (needs internet, no key).
- Requests use server-side refusal fallbacks (`fallbacks="default"`), so a declined request is retried
  on Anthropic's recommended fallback model instead of failing.
- Shell and AppleScript actions never run without a spoken "yes".
- Run at login: add `python /path/to/jarvis/jarvis.py` as a Login Item, or wrap it in a `launchd` agent.
