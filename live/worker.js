// Live status strip for the GitHub profile: Freiburg time and latest public push.
// Rendered on every request. Only public events are read, and only the repo name
// is shown, never a commit message.
const USER = "fatfreebutter";
const THEMES = {
  dark: { bg: "#161b22", fg: "#c9d1d9", key: "#ffa657", value: "#a5d6ff", live: "#3fb950" },
  light: { bg: "#f6f8fa", fg: "#24292f", key: "#953800", value: "#0a3069", live: "#1a7f37" },
};

const escapeXml = (text) =>
  text.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);

function ago(iso, now) {
  const minutes = Math.max(0, Math.floor((now - new Date(iso)) / 60000));
  if (minutes < 60) return `${minutes}m ago`;
  if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`;
  return `${Math.floor(minutes / 1440)}d ago`;
}

async function latestPush(now) {
  try {
    const response = await fetch(
      `https://api.github.com/users/${USER}/events/public?per_page=30`,
      {
        headers: { "User-Agent": USER, Accept: "application/vnd.github+json" },
        // Cached by Cloudflare: GitHub allows 60 anonymous requests an hour.
        cf: { cacheTtl: 300, cacheEverything: true },
      },
    );
    if (!response.ok) return null;
    const push = (await response.json()).find((e) => e.type === "PushEvent");
    return push && `${push.repo.name.split("/")[1]}, ${ago(push.created_at, now)}`;
  } catch {
    return null;
  }
}

export function render(theme, now, push) {
  const t = THEMES[theme] ?? THEMES.dark;
  const time = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Berlin",
    hour: "2-digit",
    minute: "2-digit",
  }).format(now);
  const hour = Number(time.slice(0, 2));
  const state = hour >= 8 && hour < 24 ? "awake" : "asleep";
  const field = (key, value) =>
    `<tspan class="key">${key}</tspan>: <tspan class="value">${escapeXml(value)}</tspan>`;
  const parts = [
    field("Freiburg", `${time} (${state})`),
    field("Last push", push ?? "no recent public push"),
  ].join('<tspan class="dim">  |  </tspan>');
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 44" width="960" height="44" font-family="Consolas,Menlo,'DejaVu Sans Mono',monospace" font-size="15" role="img" aria-label="Live status: Freiburg ${time}">
<style>
.key {fill: ${t.key};} .value {fill: ${t.value};} .dim {fill: ${t.fg}; opacity: .5;} text, tspan {white-space: pre;}
.dot {animation: pulse 1.6s ease-in-out infinite;}
@keyframes pulse {50% {opacity: .25;}}
@media (prefers-reduced-motion: reduce) {.dot {animation: none;}}
</style>
<rect width="960" height="44" fill="${t.bg}" rx="10"/>
<circle class="dot" cx="24" cy="22" r="5" fill="${t.live}"/>
<text x="38" y="27" fill="${t.live}">LIVE</text>
<text x="92" y="27" fill="${t.fg}">${parts}</text>
</svg>`;
}

export default {
  async fetch(request) {
    const now = new Date();
    const theme = new URL(request.url).searchParams.get("theme");
    return new Response(render(theme, now, await latestPush(now)), {
      headers: {
        "Content-Type": "image/svg+xml; charset=utf-8",
        // Asks GitHub's image proxy to fetch a fresh copy on each page load.
        "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
      },
    });
  },
};
