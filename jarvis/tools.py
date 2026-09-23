"""macOS actions Jarvis can take, exposed to Claude as tools."""

import datetime
import shutil
import subprocess
import webbrowser


def _run(cmd, timeout=20):
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    out = (proc.stdout + proc.stderr).strip()
    if proc.returncode != 0:
        raise RuntimeError(out or f"exit code {proc.returncode}")
    return out or "done"


def _osascript(script):
    if not shutil.which("osascript"):
        raise RuntimeError("osascript not found - this action only works on macOS")
    return _run(["osascript", "-e", script])


def open_app(name):
    return _run(["open", "-a", name])


def open_url(url):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"opened {url}"


def set_volume(level):
    level = max(0, min(100, int(level)))
    _osascript(f"set volume output volume {level}")
    return f"volume set to {level}"


def media_control(action):
    # Targets whichever of Spotify / Music is running.
    verbs = {"play": "play", "pause": "pause", "toggle": "playpause",
             "next": "next track", "previous": "previous track"}
    verb = verbs[action]
    script = f'''
    if application "Spotify" is running then
        tell application "Spotify" to {verb}
        return "Spotify"
    else
        tell application "Music" to {verb}
        return "Music"
    end if'''
    return f"{action} sent to " + _osascript(script)


def system_status():
    parts = [datetime.datetime.now().strftime("Local time: %A %d %B %Y, %H:%M")]
    if shutil.which("pmset"):
        parts.append(_run(["pmset", "-g", "batt"]))
    return "\n".join(parts)


def run_applescript(script):
    return _osascript(script)


def run_shell(command):
    return _run(["/bin/zsh" if shutil.which("zsh") else "/bin/sh", "-c", command], timeout=60)


def _schema(props, required=None):
    return {"type": "object", "properties": props,
            "required": required if required is not None else list(props),
            "additionalProperties": False}


# (definition, handler, needs_confirmation)
TOOLS = {
    "open_app": (
        {"description": "Open or focus a macOS application by name, e.g. 'Safari', 'Spotify', 'Visual Studio Code'.",
         "input_schema": _schema({"name": {"type": "string"}})},
        lambda i: open_app(i["name"]), False),
    "open_url": (
        {"description": "Open a website or URL in the default browser.",
         "input_schema": _schema({"url": {"type": "string"}})},
        lambda i: open_url(i["url"]), False),
    "set_volume": (
        {"description": "Set system output volume, 0-100.",
         "input_schema": _schema({"level": {"type": "integer"}})},
        lambda i: set_volume(i["level"]), False),
    "media_control": (
        {"description": "Control music playback in Spotify or Apple Music.",
         "input_schema": _schema({"action": {"type": "string",
                                             "enum": ["play", "pause", "toggle", "next", "previous"]}})},
        lambda i: media_control(i["action"]), False),
    "system_status": (
        {"description": "Get the current local date/time and battery status.",
         "input_schema": _schema({})},
        lambda i: system_status(), False),
    "run_applescript": (
        {"description": "Run an AppleScript snippet via osascript. Use for Mac automation not covered by other "
                        "tools (reminders, calendar, Finder, dark mode, system settings, app control). "
                        "The user must confirm aloud before it runs.",
         "input_schema": _schema({"script": {"type": "string"},
                                  "summary": {"type": "string", "description": "One short spoken sentence describing what this does."}})},
        lambda i: run_applescript(i["script"]), True),
    "run_shell": (
        {"description": "Run a zsh command on the Mac and return its output. The user must confirm aloud before it runs.",
         "input_schema": _schema({"command": {"type": "string"},
                                  "summary": {"type": "string", "description": "One short spoken sentence describing what this does."}})},
        lambda i: run_shell(i["command"]), True),
}

TOOL_DEFINITIONS = [{"name": name, "strict": True, **definition}
                    for name, (definition, _, _) in TOOLS.items()]
