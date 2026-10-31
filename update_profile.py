"""Regenerate dark_mode.svg and light_mode.svg for the GitHub profile card.

Runs daily via GitHub Actions. Stdlib only. Without a token it reuses the
last numbers saved in stats.json.
"""
import html
import json
import os
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

USER = "Bkapk"
CAREER_START = date(2021, 8, 1)  # first full-time web job
HERE = Path(__file__).parent
W = 52                           # info column width in characters

# portraits made with tools/make_ascii.py; dense glyphs = bright skin on dark, dark hair on light
ART = {t: (HERE / f"art_{t}.txt").read_text().rstrip().splitlines() for t in ("dark", "light")}

THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", art="#8b949e", key="#ffa657",
                 value="#a5d6ff", dots="#484f58", text="#c9d1d9", accent="#7ee787"),
    "light": dict(bg="#f6f8fa", border="#d0d7de", art="#57606a", key="#953800",
                  value="#0a3069", dots="#c2cfde", text="#24292f", accent="#116329"),
}


def gql(query, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)["data"]


def fetch_stats(token):
    """Contributions in the last year (public + private counts, when private ones are shown on the profile)."""
    data = gql(f'{{ user(login: "{USER}") {{ contributionsCollection {{ contributionCalendar {{ totalContributions }} }} }} }}', token)
    return {"year": data["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]}


def uptime(start, today):
    months = (today.year - start.year) * 12 + today.month - start.month - (today.day < start.day)
    y, m = divmod(months, 12)
    return f"{y} years, {m} months shipping" if m else f"{y} years shipping"


def build_lines(stats):
    """Each line is a list of (text, role) chunks; role picks the color."""
    def row(key, value, role="value"):
        dots = "." * max(1, W - len(key) - len(value) - 3)
        return [(key + ":", "key"), (f" {dots} ", "dots"), (value, role)]

    def heading(title):
        return [(f"─ {title} " + "─" * (W - len(title) - 3), "text")]

    return [
        [(f"{USER.lower()}@github ", "text"), ("─" * (W - len(USER) - 8), "text")],
        row("Host", "Weble Studio, Prishtina"),
        row("Role", "Founder · Design + engineering"),
        row("Uptime", uptime(CAREER_START, date.today())),
        row("Shipped", "200+ projects"),
        row("IDE", "Claude Code, VS Code"),
        row("Languages.Code", "PHP, TypeScript, Rust"),
        row("Languages.Real", "Albanian, English, German"),
        [],
        heading("Building"),
        row("Weble Master MCP", "WordPress as an MCP server", "accent"),
        row("Claude Code plugins", "security audit + agents", "accent"),
        row("Still Player", "video player in Rust", "accent"),
        [],
        heading("Contact"),
        row("Web", "weble.studio"),
        row("LinkedIn", "in/bleart-kepuska"),
        [],
        heading("GitHub"),
        row("Contributions", f"{stats['year']:,} in the last year"),
    ]


def render(theme, lines):
    c = THEMES[theme]
    art = ART[theme]
    line_h, art_x, info_x, top = 9, 22, 410, 40
    height = max(len(art) * line_h + top + 15, len(lines) * 20 + top + 5)
    art_top = top + (height - top - 25 - len(art) * line_h) // 2
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="850" height="{height}" viewBox="0 0 850 {height}" '
        'font-family="ui-monospace, SFMono-Regular, Consolas, Menlo, monospace" font-size="13px">',
        f'<rect x="0.5" y="0.5" width="849" height="{height - 1}" rx="10" fill="{c["bg"]}" stroke="{c["border"]}"/>',
    ]
    for i, art_line in enumerate(art):
        out.append(f'<text x="{art_x}" y="{art_top + i * line_h}" fill="{c["art"]}" font-size="8px" xml:space="preserve">{html.escape(art_line)}</text>')
    for i, chunks in enumerate(lines):
        if not chunks:
            continue
        spans = "".join(f'<tspan fill="{c[role]}">{html.escape(text)}</tspan>' for text, role in chunks)
        out.append(f'<text x="{info_x}" y="{top + i * 20}" xml:space="preserve">{spans}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    cache = HERE / "stats.json"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    stats = json.loads(cache.read_text()) if cache.exists() else {"year": 0}
    if token:
        stats = fetch_stats(token)
        cache.write_text(json.dumps(stats, indent=2) + "\n")
    lines = build_lines(stats)
    for theme in THEMES:
        (HERE / f"{theme}_mode.svg").write_text(render(theme, lines), encoding="utf-8")
    print(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC  {stats}")


if __name__ == "__main__":
    main()
