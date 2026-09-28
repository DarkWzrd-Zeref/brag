#!/usr/bin/env bash
# One command: GitHub repos -> composition -> local HyperFrames MP4.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
exec python3 -m brag "$@"
