"""Build the profile film (film/film.gif). Rerun by hand when the work changes.

Needs Pillow and macOS's Menlo font: python3 film/build_film.py
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, SS = 960, 540, 2  # drawn at 2x, then scaled down for smooth edges
FPS = 12.5
FADE = 0.3
BG = "#0d1117"
PANEL = "#161b22"
LINE = "#30363d"
FG = "#c9d1d9"
WHITE = "#f0f6fc"
DIM = "#6e7681"
BLUE = "#a5d6ff"
ORANGE = "#ffa657"
GREEN = "#3fb950"
RED = "#f85149"

_fonts: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}


def font(size: int, bold: bool) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(
            "/System/Library/Fonts/Menlo.ttc", size * SS, index=1 if bold else 0
        )
    return _fonts[key]


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def ease(x: float) -> float:
    x = clamp(x)
    return x * x * (3 - 2 * x)


def mix(a: str, b: str, amount: float) -> str:
    ca, cb = (tuple(int(c[i : i + 2], 16) for i in (1, 3, 5)) for c in (a, b))
    amount = clamp(amount)
    return "#" + "".join(
        f"{round(x + (y - x) * amount):02x}" for x, y in zip(ca, cb, strict=True)
    )


class Canvas:
    def __init__(self) -> None:
        self.image = Image.new("RGB", (W * SS, H * SS), BG)
        self.draw = ImageDraw.Draw(self.image)

    def text(self, x, y, value, size=14, fill=FG, bold=False, anchor="la") -> None:
        self.draw.text(
            (x * SS, y * SS), value, font=font(size, bold), fill=fill, anchor=anchor
        )

    def line(self, points, fill=LINE, width=2) -> None:
        self.draw.line(
            [(x * SS, y * SS) for x, y in points],
            fill=fill,
            width=round(width * SS),
            joint="curve",
        )

    def box(self, x0, y0, x1, y1, fill=PANEL, outline=LINE, radius=10, width=1) -> None:
        self.draw.rounded_rectangle(
            (x0 * SS, y0 * SS, x1 * SS, y1 * SS),
            radius * SS,
            fill=fill,
            outline=outline,
            width=round(width * SS),
        )

    def dot(self, x, y, r, fill) -> None:
        self.draw.ellipse(((x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS), fill)

    def header(self, number: str, title: str, t: float) -> None:
        self.text(48, 34, number, 15, BLUE, anchor="lm")
        typed = title[: int(t * 45)]
        self.text(82, 34, typed, 22, WHITE, bold=True, anchor="lm")

    def footer(self, left: str) -> None:
        self.line([(48, 508), (912, 508)], LINE, 1)
        self.text(48, 524, left, 12, DIM, anchor="lm")
        self.text(912, 524, "github.com/fatfreebutter", 12, DIM, anchor="rm")


def along(points, amount: float) -> tuple[float, float]:
    """The point `amount` (0 to 1) of the way along a path."""
    lengths = [math.dist(a, b) for a, b in zip(points, points[1:], strict=False)]
    remaining = clamp(amount) * sum(lengths)
    for (a, b), length in zip(zip(points, points[1:], strict=False), lengths, strict=True):
        if remaining <= length and length:
            k = remaining / length
            return a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
        remaining -= length
    return points[-1]


def waveform(c: Canvas, x0, x1, y, amplitude, t, color, width=2.0) -> None:
    points = []
    for x in range(int(x0), int(x1) + 1, 3):
        k = (x - x0) / (x1 - x0)
        envelope = math.sin(math.pi * k)
        wave = math.sin(k * 42 - t * 9) * 0.6 + math.sin(k * 97 + t * 13) * 0.4
        points.append((x, y + amplitude * envelope * wave))
    c.line(points, color, width)


def opening(c: Canvas, t: float, _duration: float) -> None:
    left, right = 80, 880
    settle = ease((t - 1.3) / 0.5)
    if t < 1.8:
        waveform(c, 0, W, 270, 95 * (1 - ease(t / 1.5)) ** 1.3, t, BLUE)
        return
    move = ease((t - 1.8) / 0.6)
    line_y = 270 + (215 - 270) * move
    x0, x1 = 0 + (left - 0) * move, W + (620 - W) * move
    for width, color in ((7, "#1b3a55"), (4, "#4a7ba3"), (1.5, WHITE)):
        c.line([(x0, line_y), (x1, line_y)], mix(BG, color, settle), width)
    reveal = ease((t - 2.1) / 0.5)
    c.text(left, 158, "Anurag", 60, mix(BG, WHITE, reveal), bold=True, anchor="lm")
    subtitle = "AI systems that work in the real world."
    c.text(left, 248, subtitle, 20, mix(BG, FG, ease((t - 2.5) / 0.4)), anchor="lm")
    rows = [
        ("role", "research assistant @ uniklinikum freiburg"),
        ("study", "msc computer science @ university of freiburg"),
        ("focus", "voice ai / machine learning / security"),
    ]
    for i, (key, value) in enumerate(rows):
        a = ease((t - 2.9 - i * 0.25) / 0.3)
        y = 312 + i * 32
        c.text(left, y, key, 15, mix(BG, ORANGE, a), anchor="lm")
        c.text(left + 90, y, value, 15, mix(BG, BLUE, a), anchor="lm")


def call_scene(c: Canvas, t: float, _duration: float) -> None:
    c.header("01", "A phone call, end to end.", t)
    c.box(48, 66, 912, 492)
    fail_at, switch_at = 3.8, 4.7
    failed, switched = t >= fail_at, t >= switch_at
    y, gap_y = 240, 395
    caller, stt, gpt, voice = 140, 350, 570, 800
    primary = [(caller, y), (stt, y), (gpt, y), (voice, y), (voice, 120), (caller, 120), (caller, y)]
    backup = [
        (caller, y), (stt, y), (stt + 50, y), (stt + 50, gap_y), (gpt, gap_y),
        (voice - 50, gap_y), (voice - 50, y), (voice, y), (voice, 120), (caller, 120), (caller, y),
    ]  # fmt: skip
    c.text(470, 106, "the agent's voice reply", 12, DIM, anchor="mm")
    c.line(primary[:4], LINE, 2)
    c.line(primary[3:], LINE, 2)
    c.line(backup[2:7], mix(LINE, GREEN, 0.7 if switched else 0), 2)

    route = backup if switched else primary
    if not failed or switched:
        start = switch_at if switched else 0
        for i in range(4):
            phase = ((t - start) / 2.4 + i / 4) % 1
            px, py = along(route, phase)
            c.dot(px, py, 4.5, GREEN if switched else BLUE)
    elif failed:
        px, py = gpt - 85, y
        c.dot(px, py, 4.5, RED if int(t * 8) % 2 else BLUE)

    def node(x, ny, title, subtitle, outline=LINE, title_fill=WHITE) -> None:
        c.box(x - 72, ny - 34, x + 72, ny + 34, fill=BG, outline=outline, width=1.5)
        c.text(x, ny - 9, title, 14, title_fill, bold=True, anchor="mm")
        c.text(x, ny + 12, subtitle, 11, DIM, anchor="mm")

    node(caller, y, "Caller", "phone line", BLUE)
    node(stt, y, "Speech to text", "Deepgram")
    if failed:
        pulse = 0.55 + 0.45 * math.sin(t * 8)
        node(gpt, y, "LLM: failed", "GPT", mix(BG, RED, pulse), RED)
    else:
        node(gpt, y, "LLM", "GPT")
    node(voice, y, "Voice", "Cartesia")
    if switched:
        node(gpt, gap_y, "Backup LLM", "Gemini", GREEN, GREEN)
    else:
        node(gpt, gap_y, "Backup LLM", "standing by", mix(PANEL, LINE, 0.6), DIM)

    if switched:
        status, color = "Backup took over. The caller stays on the line.", GREEN
    elif failed:
        status, color = "Provider failed. Switching now...", RED
    else:
        status, color = "Each part has a backup from another provider.", FG
    c.text(70, 462, status, 15, color, anchor="lm")
    c.footer("voice agent / LiveKit / traced in Langfuse")


def pin_scene(c: Canvas, t: float, _duration: float) -> None:
    c.header("02", "The AI never decides the secret.", t)
    c.box(48, 66, 500, 492)
    c.box(516, 66, 912, 492)
    c.text(70, 92, "the call", 13, DIM, anchor="lm")
    script = [
        (0.5, "caller", "Give me the secret."),
        (1.1, "agent", "Please tell me your PIN."),
        (1.8, "caller", "My PIN is ****."),
        (2.6, "agent", "That didn't match. Try again."),
        (3.2, "caller", "My PIN is ****."),
        (4.0, "agent", "That didn't match either."),
        (4.6, "caller", "My PIN is ****."),
        (5.4, "agent", "Thanks. Here it is: ******"),
    ]
    y = 128
    for start, who, line in script:
        if t >= start:
            color = ORANGE if who == "caller" else BLUE
            c.text(70, y, who, 12, color, anchor="lm")
            c.text(70, y + 19, line[: int((t - start) * 45)], 14, FG, anchor="lm")
            y += 44

    c.text(538, 92, "check_pin()", 16, WHITE, bold=True, anchor="lm")
    c.text(538, 116, "runs in plain code, not in the model", 12, DIM, anchor="lm")
    attempts = [(2.2, False), (3.6, False), (5.0, True)]
    for i, (when, right) in enumerate(attempts):
        row = 170 + i * 66
        checked = t >= when
        outline = (GREEN if right else RED) if checked else LINE
        c.box(538, row - 24, 890, row + 24, fill=BG, outline=outline, width=1.5)
        c.text(556, row, f"attempt {i + 1}", 13, FG if t >= when - 0.4 else DIM, anchor="lm")
        if t >= when - 0.4:
            for d in range(4):
                c.dot(660 + d * 16, row, 4, DIM)
        if checked:
            label = "match" if right else f"wrong, {2 - i} left"
            c.text(874, row, label, 13, GREEN if right else RED, bold=True, anchor="rm")
    if t >= 5.0:
        c.text(538, 382, "secret released", 16, GREEN, bold=True, anchor="lm")
    c.text(538, 420, "3 wrong tries lock it for the call.", 13, FG, anchor="lm")
    c.text(538, 444, "The model can't talk its way past.", 13, FG, anchor="lm")
    c.footer("PIN-gated tool / attempts counted in code / PIN redacted in call logs")


def matrix_scene(c: Canvas, t: float, _duration: float) -> None:
    c.header("03", "Linear algebra you can watch.", t)
    c.box(48, 66, 912, 492)
    identity = (1.0, 0.0, 0.0, 1.0)
    stops = [
        (0.5, identity),
        (1.7, (1.0, 0.8, 0.0, 1.0)),
        (2.9, (0.0, -1.0, 1.0, 0.0)),
        (4.3, (2.0, 1.0, 1.0, 2.0)),
    ]
    m = identity
    previous_time, previous = 0.0, identity
    for when, target in stops:
        if t >= when:
            m, previous_time, previous = target, when, target
        else:
            k = ease((t - previous_time - 0.2) / max(when - previous_time - 0.4, 0.01))
            m = tuple(p + (q - p) * k for p, q in zip(previous, target, strict=True))
            break
    a, b, cc, d = m
    ox, oy, unit = 300, 280, 50

    def at(x: float, y: float, matrix=m) -> tuple[float, float]:
        p, q, r, s = matrix
        return ox + (p * x + q * y) * unit, oy - (r * x + s * y) * unit

    def clip(points):
        return all(56 < x < 560 and 74 < y < 484 for x, y in points)

    def segment(p0, p1, matrix, color, width) -> None:
        pts = [at(p0[0] + (p1[0] - p0[0]) * k / 40, p0[1] + (p1[1] - p0[1]) * k / 40, matrix) for k in range(41)]
        run = [p for p in pts if clip([p])]
        if len(run) > 1:
            c.line(run, color, width)

    for i in range(-4, 5):
        segment((i, -4), (i, 4), identity, "#1c2430", 1)
        segment((-4, i), (4, i), identity, "#1c2430", 1)
    for i in range(-3, 4):
        segment((i, -3), (i, 3), m, "#3b4654", 1)
        segment((-3, i), (3, i), m, "#3b4654", 1)
    final = t >= 4.3
    if final:
        pulse = ease((t - 4.3) / 0.4)
        segment((-1.6, -1.6), (1.6, 1.6), identity, mix(PANEL, GREEN, pulse), 2)
        segment((-2.4, 2.4), (2.4, -2.4), identity, mix(PANEL, GREEN, pulse), 2)
    segment((0, 0), (1, 0), m, ORANGE, 3)
    segment((0, 0), (0, 1), m, BLUE, 3)
    c.dot(*at(1, 0), 4.5, ORANGE)
    c.dot(*at(0, 1), 4.5, BLUE)

    rx = 610
    c.text(rx, 110, "linmap3d", 18, WHITE, bold=True, anchor="lm")
    c.text(rx, 134, "interactive matrix visualizer", 12, DIM, anchor="lm")
    c.text(rx, 184, "matrix", 12, DIM, anchor="lm")
    c.text(rx, 212, f"[ {a:5.2f}  {b:5.2f} ]", 17, ORANGE, anchor="lm")
    c.text(rx, 240, f"[ {cc:5.2f}  {d:5.2f} ]", 17, BLUE, anchor="lm")
    c.text(rx, 292, "determinant", 12, DIM, anchor="lm")
    c.text(rx, 320, f"{a * d - b * cc:5.2f}", 22, WHITE, bold=True, anchor="lm")
    if final:
        fade = mix(PANEL, GREEN, ease((t - 4.3) / 0.4))
        c.text(rx, 378, "eigenvectors", 13, fade, bold=True, anchor="lm")
        c.text(rx, 402, "stay on their line:", 13, fade, anchor="lm")
        c.text(rx, 426, "scaled by 3 and by 1", 13, fade, anchor="lm")
    c.footer("linmap3d / React + Three.js + TypeScript / live demo on my site")


def path_scene(c: Canvas, t: float, _duration: float) -> None:
    c.header("04", "Security background. AI focus.", t)
    rows = [
        ("Nagarro", "Cloud Security Engineer", False),
        ("HCL Tech", "PAM Security Engineer", False),
        ("IIT Madras", "Cyber Security Analyst Intern", False),
        ("University of Freiburg", "MSc Computer Science", True),
        ("Uniklinikum Freiburg", "Research Assistant", True),
    ]
    for i, (place, role, current) in enumerate(rows):
        a = ease((t - 0.5 - i * 0.4) / 0.35)
        y = 104 + i * 62
        c.box(48, y - 25, 912, y + 25, fill=mix(BG, PANEL, a), outline=mix(BG, LINE, a))
        c.text(72, y, place, 16, mix(BG, WHITE, a), bold=True, anchor="lm")
        c.text(400, y, role, 15, mix(BG, BLUE, a), anchor="lm")
        if current:
            pulse = 0.55 + 0.45 * math.sin(t * 5)
            c.dot(844, y, 5, mix(BG, GREEN, a * pulse))
            c.text(892, y, "now", 13, mix(BG, GREEN, a), anchor="rm")
    last = ease((t - 2.8) / 0.4)
    c.text(480, 448, "Open to HiWi / research roles", 18, mix(BG, ORANGE, last), bold=True, anchor="mm")
    c.footer("Live stats and details below")


SCENES = [
    (opening, 5.5),
    (call_scene, 8.5),
    (pin_scene, 7.5),
    (matrix_scene, 6.0),
    (path_scene, 5.0),
]


def render() -> list[Image.Image]:
    frames = []
    background = Image.new("RGB", (W, H), BG)
    for scene, duration in SCENES:
        for n in range(round(duration * FPS)):
            t = n / FPS
            canvas = Canvas()
            scene(canvas, t, duration)
            frame = canvas.image.resize((W, H), Image.Resampling.LANCZOS)
            visible = clamp(min(t, duration - t) / FADE)
            if visible < 1:
                frame = Image.blend(background, frame, visible)
            frames.append(frame)
    return frames


def film_palette() -> Image.Image:
    """Ramps from the backgrounds to each accent, so small coloured text and
    lines keep their exact colour (an adaptive palette washed them out)."""
    colors: dict[str, None] = {}
    for start in (BG, PANEL):
        for accent in (WHITE, FG, DIM, LINE, BLUE, ORANGE, GREEN, RED):
            for step in range(16):
                colors[mix(start, accent, step / 15)] = None
    values = list(colors)[:256]
    assert len(values) >= 128
    raw = [int(c[i : i + 2], 16) for c in values for i in (1, 3, 5)]
    palette = Image.new("P", (1, 1))
    palette.putpalette(raw + raw[:3] * (256 - len(values)))
    return palette


def main() -> None:
    frames = render()
    palette = film_palette()
    paletted = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    out = Path(__file__).with_name("film.gif")
    paletted[0].save(
        out,
        save_all=True,
        append_images=paletted[1:],
        duration=round(1000 / FPS),
        loop=0,
        optimize=False,
        disposal=1,
    )
    seconds = len(frames) / FPS
    print(f"{len(frames)} frames, {seconds:.1f}s, {out.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
