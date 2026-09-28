"""Build a HyperFrames composition in the house style."""

from __future__ import annotations

import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

HOOK = 3.0
SCENE = 4.0
OUTRO = 2.5
ACCENTS = ["#F5B942", "#8FB8FF", "#FF7A7A", "#5BE49B", "#D2A8FF", "#FFB086"]
_WORDS = [
    "Zero",
    "One",
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
    "Ten",
    "Eleven",
    "Twelve",
]
TEMPLATE = Path(__file__).resolve().parent.parent / "template"


def count_word(n: int) -> str:
    if 0 <= n < len(_WORDS):
        return _WORDS[n]
    return str(n)


def name_px(name: str, vertical: bool) -> int:
    length = len(name)
    if vertical:
        if length <= 7:
            return 200
        if length <= 11:
            return 168
        if length <= 16:
            return 120
        return 84
    if length <= 7:
        return 120
    if length <= 11:
        return 96
    if length <= 16:
        return 72
    return 52


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


def _css(vertical: bool) -> str:
    if vertical:
        return """
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #080A19; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #080A19; color: #F4F6FF; font-family: "Plus Jakarta Sans", sans-serif; }
      .clip { position: absolute; inset: 0; }
      #bg { overflow: hidden; }
      .glow { position: absolute; width: 1100px; height: 1100px; border-radius: 50%; filter: blur(120px); opacity: 0.35; }
      #glowA { left: -300px; top: -200px; background: #2B3A8C; }
      #glowB { left: 300px; top: 1100px; background: #3A1F6B; }
      .grid { position: absolute; inset: 0; background-image: linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px); background-size: 90px 90px; }
      .inner { position: absolute; left: 90px; right: 90px; top: 220px; display: flex; flex-direction: column; gap: 36px; }
      .eyebrow { font-family: "JetBrains Mono", monospace; font-size: 34px; letter-spacing: 0.12em; color: #C9CFEA; }
      .acc { color: var(--accent); }
      .name { font-family: "Instrument Serif", serif; font-weight: 400; line-height: 0.92; letter-spacing: -0.01em; color: var(--accent); }
      .sub { font-size: 42px; line-height: 1.28; color: #E6E9FA; max-width: 900px; }
      .card { border: 2px solid rgba(255,255,255,0.14); background: rgba(255,255,255,0.06); border-radius: 36px; padding: 36px 40px 40px; display: flex; flex-direction: column; gap: 22px; }
      .cardlabel { font-family: "JetBrains Mono", monospace; font-size: 26px; letter-spacing: 0.14em; color: #B8BFDD; }
      .tabs { display: flex; flex-wrap: wrap; gap: 16px; }
      .tab { display: block; font-family: "JetBrains Mono", monospace; font-size: 30px; font-weight: 600; padding: 12px 20px; border-radius: 16px; border: 2px solid var(--accent); color: #F4F6FF; background: rgba(8,10,25,0.6); }
      .list { display: flex; flex-direction: column; gap: 18px; }
      .li { display: flex; align-items: flex-start; gap: 18px; font-size: 34px; line-height: 1.25; color: #F4F6FF; }
      .li span:last-child { flex: 1; min-width: 0; }
      .dot { display: block; width: 16px; height: 16px; margin-top: 12px; border-radius: 50%; background: var(--accent); flex: none; }
      .extra { font-family: "JetBrains Mono", monospace; font-size: 28px; color: #D5DAF0; }
      .quote { font-family: "Instrument Serif", serif; font-style: italic; font-size: 64px; line-height: 1.12; color: #FFFFFF; max-width: 900px; }
      .chips { display: flex; gap: 16px; flex-wrap: wrap; }
      .chip { display: block; font-family: "JetBrains Mono", monospace; font-size: 28px; padding: 12px 20px; border-radius: 999px; background: rgba(255,255,255,0.1); color: #F4F6FF; }
      #hook-in, #outro-in { position: absolute; left: 90px; right: 90px; top: 0; bottom: 0; display: flex; flex-direction: column; justify-content: center; gap: 36px; }
      .big { font-family: "Instrument Serif", serif; font-size: 180px; line-height: 0.95; color: #FFFFFF; }
      .big2 { font-family: "Instrument Serif", serif; font-style: italic; font-size: 120px; line-height: 1.02; color: #F5B942; }
      .leagues { display: flex; gap: 18px; flex-wrap: wrap; }
      .lg { display: block; font-family: "JetBrains Mono", monospace; font-size: 34px; font-weight: 600; padding: 12px 24px; border-radius: 14px; background: rgba(255,255,255,0.08); }
      .fine { font-family: "JetBrains Mono", monospace; font-size: 26px; color: #B8BFDD; letter-spacing: 0.04em; }
      .outline { font-family: "Instrument Serif", serif; font-size: 140px; line-height: 1.0; color: #FFFFFF; }
      .outline2 { font-family: "Instrument Serif", serif; font-style: italic; font-size: 100px; line-height: 1.05; color: #5BE49B; }
      .disc { font-size: 36px; line-height: 1.3; color: #E6E9FA; max-width: 900px; }
      .credit { font-family: "JetBrains Mono", monospace; font-size: 28px; color: #C9CFEA; }
"""
    return """
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1920px; height: 1080px; overflow: hidden; background: #080A19; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #080A19; color: #F4F6FF; font-family: "Plus Jakarta Sans", sans-serif; }
      .clip { position: absolute; inset: 0; }
      #bg { overflow: hidden; }
      .glow { position: absolute; width: 900px; height: 900px; border-radius: 50%; filter: blur(100px); opacity: 0.35; }
      #glowA { left: -200px; top: -240px; background: #2B3A8C; }
      #glowB { left: 1100px; top: 400px; background: #3A1F6B; }
      .grid { position: absolute; inset: 0; background-image: linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px); background-size: 80px 80px; }
      .inner { position: absolute; left: 96px; right: 96px; top: 72px; display: flex; flex-direction: column; gap: 18px; }
      .eyebrow { font-family: "JetBrains Mono", monospace; font-size: 22px; letter-spacing: 0.12em; color: #C9CFEA; }
      .acc { color: var(--accent); }
      .name { font-family: "Instrument Serif", serif; font-weight: 400; line-height: 0.92; letter-spacing: -0.01em; color: var(--accent); }
      .sub { font-size: 28px; line-height: 1.25; color: #E6E9FA; max-width: 1500px; }
      .card { border: 2px solid rgba(255,255,255,0.14); background: rgba(255,255,255,0.06); border-radius: 24px; padding: 22px 28px 24px; display: flex; flex-direction: column; gap: 14px; }
      .cardlabel { font-family: "JetBrains Mono", monospace; font-size: 18px; letter-spacing: 0.14em; color: #B8BFDD; }
      .tabs { display: flex; flex-wrap: wrap; gap: 12px; }
      .tab { display: block; font-family: "JetBrains Mono", monospace; font-size: 22px; font-weight: 600; padding: 8px 14px; border-radius: 12px; border: 2px solid var(--accent); color: #F4F6FF; background: rgba(8,10,25,0.6); }
      .list { display: flex; flex-direction: column; gap: 10px; }
      .li { display: flex; align-items: flex-start; gap: 14px; font-size: 26px; line-height: 1.25; color: #F4F6FF; }
      .li span:last-child { flex: 1; min-width: 0; }
      .dot { display: block; width: 12px; height: 12px; margin-top: 10px; border-radius: 50%; background: var(--accent); flex: none; }
      .extra { font-family: "JetBrains Mono", monospace; font-size: 20px; color: #D5DAF0; }
      .quote { font-family: "Instrument Serif", serif; font-style: italic; font-size: 42px; line-height: 1.12; color: #FFFFFF; max-width: 1500px; }
      .chips { display: flex; gap: 12px; flex-wrap: wrap; }
      .chip { display: block; font-family: "JetBrains Mono", monospace; font-size: 20px; padding: 8px 14px; border-radius: 999px; background: rgba(255,255,255,0.1); color: #F4F6FF; }
      #hook-in, #outro-in { position: absolute; left: 96px; right: 96px; top: 0; bottom: 0; display: flex; flex-direction: column; justify-content: center; gap: 22px; }
      .big { font-family: "Instrument Serif", serif; font-size: 120px; line-height: 0.95; color: #FFFFFF; }
      .big2 { font-family: "Instrument Serif", serif; font-style: italic; font-size: 84px; line-height: 1.02; color: #F5B942; }
      .leagues { display: flex; gap: 14px; flex-wrap: wrap; }
      .lg { display: block; font-family: "JetBrains Mono", monospace; font-size: 24px; font-weight: 600; padding: 8px 16px; border-radius: 12px; background: rgba(255,255,255,0.08); }
      .fine { font-family: "JetBrains Mono", monospace; font-size: 20px; color: #B8BFDD; letter-spacing: 0.04em; }
      .outline { font-family: "Instrument Serif", serif; font-size: 96px; line-height: 1.0; color: #FFFFFF; }
      .outline2 { font-family: "Instrument Serif", serif; font-style: italic; font-size: 72px; line-height: 1.05; color: #5BE49B; }
      .disc { font-size: 28px; line-height: 1.3; color: #E6E9FA; max-width: 1400px; }
      .credit { font-family: "JetBrains Mono", monospace; font-size: 22px; color: #C9CFEA; }
"""


def _chips(scene: dict) -> list[str]:
    chips = []
    prs = scene["pr_count"]
    commits = scene["commit_count"]
    if isinstance(prs, int):
        chips.append(f"{prs} PR" if prs == 1 else f"{prs} PRs")
    if isinstance(commits, int):
        chips.append(f"{commits} commit" if commits == 1 else f"{commits} commits")
    if scene.get("language"):
        chips.append(scene["language"])
    chips.append(scene["repo"])
    return chips


def _rows_html(scene: dict, sid: str) -> str:
    rows = scene.get("rows") or []
    if not rows:
        return ""
    if scene.get("row_style") == "tabs":
        inner = "".join(f'<span class="tab">{_esc(row)}</span>' for row in rows)
        body = f'<div class="tabs">{inner}</div>'
    else:
        inner = "".join(
            f'<div class="li"><span class="dot"></span><span>{_esc(row)}</span></div>' for row in rows
        )
        body = f'<div class="list">{inner}</div>'
    extra = ""
    if scene.get("extra"):
        extra = f'<p class="extra">{_esc(scene["extra"])}</p>'
    return (
        f'<div id="{sid}-card" class="card">'
        f'<p class="cardlabel">{_esc(scene.get("card_label") or "README")}</p>'
        f"{body}{extra}</div>"
    )


def duration(n: int) -> float:
    return HOOK + n * SCENE + OUTRO


def render_html(scenes: list[dict], *, vertical: bool, title: str, disclaimer_line: str, when: datetime) -> str:
    n = len(scenes)
    width, height = (1080, 1920) if vertical else (1920, 1080)
    total = duration(n)
    hook_a = title or (f"{n} desk." if n == 1 else f"{n} desks.")
    total_prs = sum(int(scene["pr_count"]) for scene in scenes)
    hook_b = f"{total_prs} pull request." if total_prs == 1 else f"{total_prs} pull requests."
    stamp = f"{when.strftime('%b')} {when.day}, {when.year}"
    fine = f"GitHub PR counts as of {stamp}"
    categories = []
    for scene in scenes:
        cat = scene.get("category") or ""
        if cat and cat not in categories:
            categories.append(cat)
    league_html = "".join(
        f'<span class="lg" style="color:{ACCENTS[i % len(ACCENTS)]}">{_esc(cat)}</span>'
        for i, cat in enumerate(categories)
    )
    sections = []
    tweens = []
    for index, scene in enumerate(scenes):
        sid = f"s{index}"
        start = HOOK + index * SCENE
        accent = ACCENTS[index % len(ACCENTS)]
        px = name_px(scene["name"], vertical)
        quote_html = ""
        if scene.get("quote"):
            quote_html = f'<p id="{sid}-quote" class="quote">“{_esc(scene["quote"])}”</p>'
        sections.append(
            f'''
      <section id="{sid}" class="clip scene" data-start="{start:.1f}" data-duration="{SCENE:.1f}" data-track-index="1" style="--accent:{accent}">
        <div id="{sid}-in" class="inner">
          <p id="{sid}-eyebrow" class="eyebrow"><span class="acc">{index + 1:02d} / {n:02d}</span> · {_esc(scene.get("category") or "")}</p>
          <h2 id="{sid}-name" class="name" style="font-size:{px}px">{_esc(scene["name"])}</h2>
          <p id="{sid}-sub" class="sub">{_esc(scene.get("subtitle") or "")}</p>
          {_rows_html(scene, sid)}
          {quote_html}
          <div id="{sid}-chips" class="chips">{"".join(f'<span class="chip">{_esc(chip)}</span>' for chip in _chips(scene))}</div>
        </div>
      </section>'''
        )
        card_tween = ""
        if scene.get("rows"):
            card_tween = f'''
      tl.fromTo("#{sid}-card", {{opacity:0, y:50, scale:0.96}}, {{opacity:1, y:0, scale:1, duration:0.5, ease:"power3.out"}}, {start + 0.60:.2f});
      tl.fromTo("#{sid}-card .tab, #{sid}-card .li", {{opacity:0, y:16}}, {{opacity:1, y:0, duration:0.3, stagger:0.06, ease:"power2.out"}}, {start + 0.80:.2f});'''
        quote_tween = ""
        if scene.get("quote"):
            quote_tween = f'''
      tl.fromTo("#{sid}-quote", {{opacity:0, y:24}}, {{opacity:1, y:0, duration:0.45, ease:"power2.out"}}, {start + 1.30:.2f});'''
        tweens.append(
            f'''
      tl.fromTo("#{sid}-eyebrow", {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.4, ease:"power3.out"}}, {start + 0.05:.2f});
      tl.fromTo("#{sid}-name", {{opacity:0, y:60}}, {{opacity:1, y:0, duration:0.55, ease:"power3.out"}}, {start + 0.12:.2f});
      tl.fromTo("#{sid}-sub", {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.45, ease:"power2.out"}}, {start + 0.35:.2f});{card_tween}{quote_tween}
      tl.fromTo("#{sid}-chips", {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.35, ease:"power2.out"}}, {start + 1.60:.2f});
      tl.to("#{sid}-in", {{opacity:0, y:-40, duration:0.3, ease:"power2.in"}}, {start + SCENE - 0.32:.2f});'''
        )
    outro_at = HOOK + n * SCENE
    desk_word = count_word(n)
    outro_a = f"{desk_word} desk." if n == 1 else f"{desk_word} desks."
    disc_html = ""
    disc_tween = ""
    if disclaimer_line:
        disc_html = f'<p id="out-c" class="disc">{_esc(disclaimer_line)}</p>'
        disc_tween = f'tl.fromTo("#out-c", {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.35}}, {outro_at + 0.75:.2f});'
    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={width}, height={height}" />
    <title>{_esc(hook_a)}</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: "Instrument Serif"; src: url("assets/fonts/InstrumentSerif-Regular.ttf"); font-style: normal; }}
      @font-face {{ font-family: "Instrument Serif"; src: url("assets/fonts/InstrumentSerif-Italic.ttf"); font-style: italic; }}
      @font-face {{ font-family: "Plus Jakarta Sans"; src: url("assets/fonts/PlusJakartaSans-VariableFont_wght.ttf"); font-weight: 200 800; }}
      @font-face {{ font-family: "JetBrains Mono"; src: url("assets/fonts/JetBrainsMono-VariableFont_wght.ttf"); font-weight: 100 800; }}
      {_css(vertical)}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="{width}" data-height="{height}" data-fps="30">
      <div id="bg" class="clip" data-start="0" data-duration="{total}" data-track-index="0">
        <div class="grid"></div>
        <div id="glowA" class="glow" data-layout-allow-overflow></div>
        <div id="glowB" class="glow" data-layout-allow-overflow></div>
      </div>

      <section id="hook" class="clip scene" data-start="0" data-duration="{HOOK}" data-track-index="1">
        <div id="hook-in">
          <p id="hook-a" class="big">{_esc(hook_a)}</p>
          <p id="hook-b" class="big2">{_esc(hook_b)}</p>
          <div id="hook-l" class="leagues">{league_html}</div>
          <p id="hook-f" class="fine">{_esc(fine)}</p>
        </div>
      </section>
{"".join(sections)}
      <section id="outro" class="clip scene" data-start="{outro_at}" data-duration="{OUTRO}" data-track-index="1">
        <div id="outro-in">
          <p id="out-a" class="outline">{_esc(outro_a)}</p>
          <p id="out-b" class="outline2">No invented numbers.</p>
          {disc_html}
          <p id="out-d" class="credit">made with brag + HyperFrames · rendered locally</p>
        </div>
      </section>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#glowA", {{x:0, y:0}}, {{x:260, y:380, duration:{total}, ease:"none"}}, 0);
      tl.fromTo("#glowB", {{x:0, y:0}}, {{x:-240, y:-420, duration:{total}, ease:"none"}}, 0);
      tl.fromTo("#hook-a", {{opacity:0, y:60}}, {{opacity:1, y:0, duration:0.5, ease:"power3.out"}}, 0.1);
      tl.fromTo("#hook-b", {{opacity:0, y:60}}, {{opacity:1, y:0, duration:0.5, ease:"power3.out"}}, 0.55);
      tl.fromTo("#hook-l .lg", {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.3, stagger:0.08, ease:"power2.out"}}, 1.0);
      tl.fromTo("#hook-f", {{opacity:0}}, {{opacity:1, duration:0.3}}, 1.4);
      tl.to("#hook-in", {{opacity:0, y:-40, duration:0.3, ease:"power2.in"}}, {HOOK - 0.32:.2f});
{"".join(tweens)}
      tl.fromTo("#out-a", {{opacity:0, y:50}}, {{opacity:1, y:0, duration:0.45, ease:"power3.out"}}, {outro_at + 0.10:.2f});
      tl.fromTo("#out-b", {{opacity:0, y:50}}, {{opacity:1, y:0, duration:0.45, ease:"power3.out"}}, {outro_at + 0.40:.2f});
      {disc_tween}
      tl.fromTo("#out-d", {{opacity:0}}, {{opacity:1, duration:0.35}}, {outro_at + 0.95:.2f});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''


def write_composition(
    dest: Path,
    scenes: list[dict],
    *,
    vertical: bool,
    title: str,
    disclaimer_line: str,
    audio: Path | None,
    when: datetime | None = None,
) -> float:
    dest.mkdir(parents=True, exist_ok=True)
    assets = dest / "assets"
    if assets.exists():
        shutil.rmtree(assets)
    shutil.copytree(TEMPLATE / "assets", assets)
    shutil.copy(TEMPLATE / "hyperframes.json", dest / "hyperframes.json")
    shutil.copy(TEMPLATE / "package.json", dest / "package.json")
    moment = when or datetime.now(timezone.utc)
    html_doc = render_html(
        scenes,
        vertical=vertical,
        title=title,
        disclaimer_line=disclaimer_line,
        when=moment,
    )
    if audio is not None:
        ext = audio.suffix.lower() or ".mp3"
        target = assets / "audio" / f"bed{ext}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(audio, target)
        total = duration(len(scenes))
        tag = (
            f'<audio id="bed" src="assets/audio/bed{ext}" data-start="0" '
            f'data-duration="{total}" data-volume="0.9" data-track-index="2"></audio>'
        )
        html_doc = html_doc.replace("</body>", f"    {tag}\n  </body>", 1)
    (dest / "index.html").write_text(html_doc, encoding="utf-8")
    meta = {
        "id": "brag",
        "name": title or "brag",
        "createdAt": moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (dest / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return duration(len(scenes))
