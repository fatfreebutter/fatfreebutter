"""Claude-powered reasoning loop: takes a spoken request, calls Mac tools, returns a spoken reply."""

import os

import anthropic

from tools import TOOLS, TOOL_DEFINITIONS

MODEL = os.environ.get("JARVIS_MODEL", "claude-opus-5")
EFFORT = os.environ.get("JARVIS_EFFORT", "low")  # low keeps voice replies snappy
MAX_HISTORY = 40

SYSTEM = """You are Jarvis, a voice assistant running on the user's Mac.
Everything you write is read aloud by text-to-speech, so:
- Reply in one to three short, natural spoken sentences.
- No markdown, lists, code blocks, emoji or URLs in replies.
- Be warm, dry and efficient, like a capable butler.
Use the tools to act on the Mac rather than explaining how to do it.
Use web search for current events, weather, or facts you are unsure of.
Prefer the dedicated tools; fall back to AppleScript, then shell, only when needed.
If a tool fails, say briefly what went wrong."""

WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search", "max_uses": 3}


class Brain:
    def __init__(self, confirm):
        """confirm(summary: str) -> bool asks the user to approve a risky action."""
        self.client = anthropic.Anthropic()
        self.confirm = confirm
        self.messages = []

    def reset(self):
        self.messages = []

    def _trim_history(self):
        # Cut only at a plain-text user turn so tool_use/tool_result pairs stay intact.
        if len(self.messages) <= MAX_HISTORY:
            return
        for i in range(len(self.messages) - MAX_HISTORY, len(self.messages)):
            m = self.messages[i]
            if m["role"] == "user" and isinstance(m["content"], str):
                self.messages = self.messages[i:]
                return

    def _execute(self, block):
        _, handler, needs_confirm = TOOLS[block.name]
        if needs_confirm:
            summary = block.input.get("summary") or block.name
            if not self.confirm(summary):
                return "The user declined to run this.", True
        try:
            return str(handler(block.input))[:4000], False
        except Exception as e:  # report failures back to Claude instead of crashing
            return f"Error: {e}", True

    def ask(self, text):
        self._trim_history()
        self.messages.append({"role": "user", "content": text})

        while True:
            response = self.client.beta.messages.create(
                model=MODEL,
                max_tokens=16000,
                system=SYSTEM,
                tools=[*TOOL_DEFINITIONS, WEB_SEARCH],
                messages=self.messages,
                thinking={"type": "adaptive"},
                output_config={"effort": EFFORT},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )

            if response.stop_reason == "refusal":
                self.messages.pop()  # drop the refused turn so the conversation stays usable
                return "Sorry, I can't help with that one."

            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "pause_turn":
                continue  # server-side web search wants to keep going

            if response.stop_reason != "tool_use":
                return " ".join(b.text for b in response.content if b.type == "text").strip() or "Done."

            results = []
            for block in response.content:
                if block.type == "tool_use":
                    output, is_error = self._execute(block)
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": output, "is_error": is_error})
            self.messages.append({"role": "user", "content": results})
