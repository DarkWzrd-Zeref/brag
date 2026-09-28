# brag

One command turns one or more GitHub repos into a short MP4. This repository is `DarkWzrd-Zeref/brag`.

It reads real repo facts, writes a HyperFrames composition in the house style, and renders by calling the local engine's `render.sh`. It does not invoke `npx`, `hyperframes cloud`, or any credit path itself.

## Install

- Node.js 22 or newer
- FFmpeg (`ffmpeg` and `ffprobe` on your PATH)
- Python 3
- The local engine, [DarkWzrd-Zeref/hyperframes](https://github.com/DarkWzrd-Zeref/hyperframes), cloned next to this repo so the wrapper is `../hyperframes/render.sh`:

```text
brag/
../hyperframes/render.sh
```

If the engine lives somewhere else, set `HYPERFRAMES_HOME` to that directory. No other path edits.

Private repos need `gh auth login`, or `GH_TOKEN` / `GITHUB_TOKEN` with access to those repos. No HeyGen account.

## Run

```bash
./brag.sh DarkWzrd-Zeref/mlb-predictions \
  DarkWzrd-Zeref/athena-bets \
  DarkWzrd-Zeref/ufc-bets \
  DarkWzrd-Zeref/atlas-apex
```

That writes `brag-output/brag.mp4` and `brag-output/brag.jpg`.

```bash
./brag.sh --format horizontal --title "Ship log" --output ./out/one.mp4 owner/repo
./brag.sh --audio ./licensed-track.mp3 owner/repo@some-branch
```

A repo can be `owner/repo`, `owner/repo@branch`, or a `github.com` URL. `--format` is `vertical` (1080×1920, the default) or `horizontal` (1920×1080).

## Rails

- Render goes through `../hyperframes/render.sh` only (or `HYPERFRAMES_HOME` when the engine is not a sibling). That wrapper refuses cloud render, HeyGen hosted rendering, Lambda, and `hyperframes publish`.
- Counts on screen are the GitHub pull-request total and the commit count on the branch that was read. If a fact is missing, it is left off. Nothing is filled in.
- README lines are scrubbed before they are drawn: emails, connection strings, tokens, env assignments, database hosts, project ids, and URLs.
- Silence is the default. `--audio` is for a file you have rights to use (music or voiceover).
- Do not commit rendered MP4s or secrets. `brag-output/` and `*.mp4` are gitignored.

## Licenses

- This pipeline: MIT (`LICENSE`)
- Instrument Serif, Plus Jakarta Sans, and JetBrains Mono: SIL Open Font License (`licenses/fonts-OFL.txt`)
- GSAP 3.14.2 is vendored under `template/assets/` so render does not depend on a CDN. It is free to use, including commercially.
