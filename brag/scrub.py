"""Remove secret-looking spans from text that may be drawn on screen."""

from __future__ import annotations

import re

# Order matters only for overlap; each pattern is applied to the whole string.
_PATTERNS = [
    re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
    re.compile(
        r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|rediss|amqp|ssh)://\S+",
        re.I,
    ),
    re.compile(r"\bhttps?://\S+", re.I),
    re.compile(r"\b[A-Z][A-Z0-9_]{2,}\s*=\s*\S+"),
    re.compile(
        r"\b(?:ghp|gho|ghu|ghs|ghr|github_pat|sk|xox[baprs]|AKIA|AIza)[A-Za-z0-9_\-]{8,}\b"
    ),
    re.compile(r"\bBearer\s+\S+", re.I),
    re.compile(r"\b[\w.-]+\.(?:neon\.tech|amazonaws\.com|railway\.app)\b", re.I),
    re.compile(r"\b[a-z]{3,}-[a-z]{3,}-\d{5,}\b"),
    re.compile(r"\b[a-f0-9]{32,}\b", re.I),
]


def contains_secret(text: str) -> bool:
    return any(p.search(text or "") for p in _PATTERNS)


def scrub(text: str) -> str:
    """Delete secret spans and collapse the whitespace they leave behind."""
    out = text or ""
    for pattern in _PATTERNS:
        out = pattern.sub("", out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r" +([,.;:)])", r"\1", out)
    out = re.sub(r"\(\s*\)", "", out)
    return out.strip()
