"""Build the neofetch-style profile card (dark_mode.svg, light_mode.svg).

Run: GH_TOKEN=... python3 build_card.py
A GitHub Action reruns it daily to refresh the stats. Standard library only.
"""

import calendar
import datetime
import json
import math
import os
import urllib.request
from xml.sax.saxutils import escape

USER = "fatfreebutter"
BIRTHDAY = datetime.date(2001, 12, 19)
ART_COLS, ART_ROWS = 40, 25
INFO_ROWS = 27
INFO_COLS = 60
THEMES = {
    "dark_mode.svg": ("#161b22", "#c9d1d9", "#ffa657", "#a5d6ff", "#616e7f"),
    "light_mode.svg": ("#f6f8fa", "#24292f", "#953800", "#0a3069", "#8c959f"),
}


def uptime(today: datetime.date, born: datetime.date = BIRTHDAY) -> str:
    months = (today.year - born.year) * 12 + today.month - born.month
    days = today.day - born.day
    if days < 0:
        months -= 1
        last_month = today.replace(day=1) - datetime.timedelta(days=1)
        days += calendar.monthrange(last_month.year, last_month.month)[1]
    return f"{months // 12} years, {months % 12} months, {days} days"


def stats() -> dict[str, int]:
    query = (
        '{user(login:"%s"){followers{totalCount}'
        "repositories(ownerAffiliations:OWNER,privacy:PUBLIC,first:100)"
        "{totalCount nodes{stargazerCount}}"
        "contributionsCollection{totalCommitContributions}}}" % USER
    )
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        user = json.load(response)["data"]["user"]
    repos = user["repositories"]
    return {
        "repos": repos["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos["nodes"]),
        "commits": user["contributionsCollection"]["totalCommitContributions"],
        "followers": user["followers"]["totalCount"],
    }


def art() -> list[str]:
    """A shaded sphere rippling with sound waves."""
    ramp = " .:-=+*#%@"
    lines = []
    for row in range(ART_ROWS):
        line = ""
        for col in range(ART_COLS):
            x = (col - ART_COLS / 2 + 0.5) / (ART_COLS / 2)
            y = (row - ART_ROWS / 2 + 0.5) / (ART_ROWS / 2)
            r = math.hypot(x, y)
            if r >= 0.97:
                line += " "
                continue
            z = math.sqrt(1 - r * r)
            light = max(0.0, -0.45 * x - 0.55 * y + 0.7 * z)
            wave = 0.5 + 0.5 * math.sin(r * 15 + 2 * math.sin(3 * x))
            level = 0.15 + 0.6 * light + 0.3 * wave * z
            line += ramp[min(int(level * len(ramp)), len(ramp) - 1)]
        lines.append(line)
    return lines


def info(s: dict[str, int]) -> list[tuple]:
    def pair(left, right):
        return ("pair", left, right)

    return [
        ("title", "anurag@freiburg"),
        ("kv", "OS", "macOS, Linux"),
        ("kv", "Uptime", uptime(datetime.date.today())),
        ("kv", "Host", "University of Freiburg, Germany"),
        ("kv", "Kernel", "MSc Computer Science, 3rd semester"),
        ("kv", "Role", "Research Assistant, Uniklinikum Freiburg"),
        ("kv", "Origin", "New Delhi -> Germany"),
        ("kv", "Status", "Open to HiWi / research roles"),
        ("blank",),
        ("kv", "Focus", "ML, AI Fundamentals, Cybersecurity"),
        ("kv", "Languages", "Python, TypeScript, Assembly"),
        ("kv", "AI", "LiveKit Agents, Voice AI, Langfuse"),
        ("kv", "Security", "AWS, Azure, IAM, PAM, Network Security"),
        ("kv", "Tools", "Git, Docker, Linux, React, Three.js"),
        ("blank",),
        ("title", "- Experience"),
        ("kv", "Nagarro", "Cloud Security Engineer"),
        ("kv", "HCL Tech", "PAM Security Engineer"),
        ("kv", "IIT Madras", "Cyber Security Analyst Intern"),
        ("blank",),
        ("title", "- Projects"),
        ("kv", "linmap3d", "3D/2D linear algebra visualizer"),
        ("kv", "voice-agent", "Multi-pipeline phone AI (private)"),
        ("blank",),
        ("title", "- GitHub Stats"),
        pair(("Repos", s["repos"]), ("Stars", s["stars"])),
        pair(("Commits this year", s["commits"]), ("Followers", s["followers"])),
    ]


def info_tspans(line: tuple, x: int, y: int) -> str:
    def text(cls: str, value: str) -> str:
        return f'<tspan class="{cls}">{escape(value)}</tspan>'

    def kv(key: str, value: str, width: int) -> str:
        dots = width - len(key) - len(value) - 3
        assert dots >= 2, f"{key}: line too long"
        return (
            text("key", key)
            + ":"
            + text("dots", f" {'.' * dots} ")
            + text("value", value)
        )

    kind = line[0]
    if kind == "blank":
        body = ""
    elif kind == "title":
        body = f"{escape(line[1])} " + text("dots", "-" * (INFO_COLS - len(line[1]) - 1))
    elif kind == "kv":
        body = kv(line[1], line[2], INFO_COLS)
    else:
        left, right = line[1], line[2]
        body = (
            kv(left[0], str(left[1]), 38)
            + text("dots", " | ")
            + kv(right[0], str(right[1]), INFO_COLS - 41)
        )
    return f'<tspan x="{x}" y="{y}">{body}</tspan>'


def svg(theme: tuple, s: dict[str, int]) -> str:
    background, foreground, key, value, dots = theme
    lines = info(s)
    assert len(lines) == INFO_ROWS, f"{len(lines)} info lines, expected {INFO_ROWS}"
    art_text = "\n".join(
        f'<tspan x="15" y="{50 + 20 * i}">{escape(row)}</tspan>'
        for i, row in enumerate(art())
    )
    info_text = "\n".join(
        info_tspans(line, 395, 30 + 20 * i) for i, line in enumerate(lines)
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 570" width="960" height="570" font-family="Consolas,Menlo,'DejaVu Sans Mono',monospace" font-size="15">
<style>
.key {{fill: {key};}}
.value {{fill: {value};}}
.dots {{fill: {dots};}}
text, tspan {{white-space: pre;}}
</style>
<rect width="960" height="570" fill="{background}" rx="15"/>
<text fill="{foreground}">
{art_text}
</text>
<text fill="{foreground}">
{info_text}
</text>
</svg>
"""


def main() -> None:
    s = stats()
    for name, theme in THEMES.items():
        with open(name, "w", encoding="utf-8") as f:
            f.write(svg(theme, s))
    print(s)


if __name__ == "__main__":
    main()
