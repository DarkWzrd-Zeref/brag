"""brag: one command from GitHub repos to a local HyperFrames MP4."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from brag.compose import write_composition
from brag.extract import disclaimer, present
from brag.github_api import GitHubError, gather
from brag.engine import check_and_render, poster
from brag.scrub import contains_secret, scrub

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="brag",
        description="Gather real GitHub facts and render a short MP4 locally with HyperFrames.",
    )
    parser.add_argument(
        "repos",
        nargs="+",
        help="owner/repo, owner/repo@branch, or a github.com URL",
    )
    parser.add_argument(
        "--format",
        choices=("vertical", "horizontal"),
        default="vertical",
        help="vertical is 1080x1920, horizontal is 1920x1080 (default: vertical)",
    )
    parser.add_argument(
        "--output",
        default="brag-output/brag.mp4",
        help="MP4 path (poster JPG is written beside it). Default: brag-output/brag.mp4",
    )
    parser.add_argument("--title", default="", help="optional hook line instead of the desk count")
    parser.add_argument(
        "--audio",
        default="",
        help="optional licensed music or voiceover file. Default is silence",
    )
    parser.add_argument("--fps", type=int, default=30, help="frames per second (default: 30)")
    return parser


def _output_path(raw: str) -> Path:
    path = Path(raw)
    if path.suffix.lower() != ".mp4":
        path = path / "brag.mp4"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _public_facts(scene: dict) -> dict:
    keep = (
        "owner",
        "repo",
        "branch",
        "name",
        "category",
        "language",
        "pr_count",
        "commit_count",
        "subtitle",
        "quote",
        "card_label",
        "rows",
        "row_style",
    )
    return {key: scene.get(key) for key in keep}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.fps < 1 or args.fps > 60:
        print("fps must be between 1 and 60", file=sys.stderr)
        return 2
    title = scrub(args.title).strip()
    if args.title and (not title or contains_secret(args.title)):
        print("refusing title that looks secret or scrubs to empty", file=sys.stderr)
        return 2
    audio = None
    if args.audio:
        audio = Path(args.audio)
        if not audio.is_file():
            print(f"audio file not found: {audio}", file=sys.stderr)
            return 2
        if audio.suffix.lower() not in AUDIO_EXTS:
            print(f"unsupported audio type {audio.suffix}", file=sys.stderr)
            return 2

    scenes = []
    readmes = []
    for spec in args.repos:
        print(f"fetching {spec}", flush=True)
        try:
            fact = gather(spec)
        except GitHubError as err:
            print(str(err), file=sys.stderr)
            return 1
        readmes.append(fact.get("readme") or "")
        scene = present(fact)
        print(
            f"  {scene['owner']}/{scene['repo']}@{scene['branch']}: "
            f"{scene['pr_count']} PRs, {scene['commit_count']} commits, "
            f"{scene['language'] or 'no language'}",
            flush=True,
        )
        scenes.append(scene)

    when = datetime.now(timezone.utc)
    mp4 = _output_path(args.output)
    jpg = mp4.with_suffix(".jpg")
    composition = mp4.parent / f"{mp4.stem}-composition"
    line = disclaimer(readmes)
    print(f"writing {composition}", flush=True)
    write_composition(
        composition,
        scenes,
        vertical=args.format == "vertical",
        title=title,
        disclaimer_line=line,
        audio=audio,
        when=when,
    )
    (mp4.parent / f"{mp4.stem}-facts.json").write_text(
        json.dumps(
            {
                "generatedAt": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "format": args.format,
                "disclaimer": line,
                "scenes": [_public_facts(scene) for scene in scenes],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("hyperframes check, then local render", flush=True)
    check_and_render(composition, mp4, fps=args.fps)
    poster(mp4, jpg, at=2.0)
    print(f"mp4    {mp4.resolve()}")
    print(f"poster {jpg.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
