"""Call the local HyperFrames engine only through its render.sh wrapper."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

LOCAL_COMMANDS = frozenset({"doctor", "check", "render", "poster"})


class EngineError(RuntimeError):
    pass


def engine_home() -> Path:
    """Sibling clone named hyperframes, or HYPERFRAMES_HOME when it lives elsewhere."""
    override = os.environ.get("HYPERFRAMES_HOME", "").strip()
    if override:
        home = Path(override).expanduser().resolve()
        if not (home / "render.sh").is_file():
            raise EngineError(f"HYPERFRAMES_HOME has no render.sh: {home}")
        return home
    sibling = Path(__file__).resolve().parents[1].parent / "hyperframes"
    if (sibling / "render.sh").is_file():
        return sibling
    raise EngineError(
        "local HyperFrames engine not found. Clone DarkWzrd-Zeref/hyperframes "
        "next to this repo as hyperframes, or set HYPERFRAMES_HOME to that clone."
    )


def _run(argv: list[str]) -> None:
    if Path(argv[0]).name != "render.sh":
        raise EngineError("refusing to render through anything but render.sh")
    if len(argv) < 2 or argv[1] not in LOCAL_COMMANDS:
        raise EngineError("refusing engine command that is not doctor, check, render, or poster")
    print("+", " ".join(argv), flush=True)
    subprocess.run(argv, check=True)


def render_invocation(composition: Path, mp4: Path, *, fps: int = 30) -> list[list[str]]:
    script = str(engine_home() / "render.sh")
    return [
        [script, "check", str(composition)],
        [script, "render", str(composition), "--output", str(mp4), "--fps", str(fps)],
    ]


def poster_invocation(mp4: Path, jpg: Path, at: float = 2.0) -> list[str]:
    script = str(engine_home() / "render.sh")
    return [script, "poster", str(mp4), "--output", str(jpg), "--at", f"{at:.3f}"]


def check_and_render(composition: Path, mp4: Path, *, fps: int = 30) -> None:
    mp4.parent.mkdir(parents=True, exist_ok=True)
    for argv in render_invocation(composition, mp4, fps=fps):
        _run(argv)


def poster(mp4: Path, jpg: Path, at: float = 2.0) -> None:
    jpg.parent.mkdir(parents=True, exist_ok=True)
    _run(poster_invocation(mp4, jpg, at))
