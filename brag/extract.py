"""Turn a README plus repo metadata into on-screen copy. No invented counts."""

from __future__ import annotations

import re

from brag.scrub import contains_secret, scrub

_LEAGUES = {"MLB", "NFL", "NBA", "NHL", "UFC", "MMA", "ETH", "BTC", "SOL", "XRP"}
_DROP_WORDS = {"bets", "app", "bot", "project", "the", "a", "an"}
_FENCE = re.compile(r"```.*?```", re.S)
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_H1 = re.compile(r"^#\s+(.+)$", re.M)
_H2 = re.compile(r"^##\s+(.+)$", re.M)


def _prose(readme: str) -> str:
    text = _FENCE.sub(" ", readme or "")
    text = _MD_LINK.sub(r"\1", text)
    text = text.replace("`", "")
    return text


def _clean_inline(text: str) -> str:
    text = text.replace("**", "").replace("*", "")
    text = re.sub(r"[\U0001F300-\U0001FAFF]", "", text)
    text = re.sub(r"\s+", " ", text).strip(" \t-—–|:")
    return scrub(text)


def display_name(repo: str, readme: str, description: str) -> str:
    h1_match = _H1.search(readme or "")
    h1 = h1_match.group(1) if h1_match else ""
    caps = re.findall(r"\b[A-Z][A-Z0-9]{2,}(?:\s+[A-Z][A-Z0-9]{2,}){0,2}\b", h1)
    for token in caps:
        if token not in _LEAGUES:
            return token
    words = re.findall(r"[A-Za-z][A-Za-z0-9+]*", h1)
    if len(words) >= 2 and words[-1].lower() in _DROP_WORDS:
        words = words[:-1]
    if not words:
        words = re.findall(r"[A-Za-z0-9]+", repo) or [repo]
    return " ".join(words[:3]).upper()


def category(h1: str, description: str, readme: str) -> str:
    blobs = [f"{h1}\n{description or ''}", (readme or "")[:600], readme or ""]
    for blob in blobs:
        low = blob.lower()
        if re.search(r"\bmlb\b|\bbaseball\b", low):
            return "MLB"
        if re.search(r"\bnfl\b", low):
            return "NFL"
        if re.search(r"\bufc\b|\bmma\b", low):
            return "UFC"
        if re.search(r"crypto|bitcoin|ethereum|\beth\b|\bbtc\b|coingecko|solana", low):
            return "CRYPTO"
    return ""


def _sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    out = []
    for chunk in chunks:
        if contains_secret(chunk):
            continue
        piece = _clean_inline(chunk)
        if len(piece) < 8:
            continue
        for clause in re.split(r"\s*;\s*", piece):
            clause = clause.strip(" .")
            if len(clause) >= 8 and not contains_secret(clause):
                out.append(clause)
    return out


def _usable(text: str, limit: int) -> str:
    text = _clean_inline(text)
    if not text or contains_secret(text):
        return ""
    if len(text) <= limit:
        return text
    cut = text[: limit + 1].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return cut if len(cut) >= 12 else ""


def subtitle(readme: str, description: str) -> str:
    prose = _prose(readme)
    h1 = _H1.search(prose)
    body = prose[h1.end() :] if h1 else prose
    body = re.split(r"\n##\s+", body, maxsplit=1)[0]
    picked: list[str] = []
    for sentence in _sentences(body):
        if sentence.lower().strip(".") == "private":
            continue
        if contains_secret(sentence):
            continue
        if re.search(r"21\+|entertainment only|bet responsibly|1-800", sentence, re.I):
            continue
        if _uppercase_ratio(sentence) > 0.65:
            continue
        candidate = sentence.strip(".")
        if picked and len(". ".join(picked + [candidate])) > 140:
            break
        picked.append(candidate)
        if len(picked) == 2:
            break
    text = ". ".join(picked)
    if text and not text.endswith("."):
        text += "."
    text = _usable(text, 150)
    if text:
        return text if text.endswith(".") else text + "."
    fallback = _usable(description or "", 150)
    if fallback and not fallback.endswith("."):
        fallback += "."
    return fallback


_QUOTE_STRONG = re.compile(
    r"never invented|no invented|every number|immutable|no trade|does not place|do not place",
    re.I,
)
_QUOTE_HINT = re.compile(
    r"paper only|disabled on purpose|not a guarantee|entertainment only",
    re.I,
)


def quote(readme: str) -> str:
    best = ""
    best_score = 0
    for sentence in _sentences(_prose(readme)):
        if contains_secret(sentence):
            continue
        if len(sentence) > 90 or len(sentence) < 12:
            continue
        score = 0
        if re.search(r"never invented|every number|immutable|no trade", sentence, re.I):
            score += 7
        elif _QUOTE_STRONG.search(sentence):
            score += 6
        elif _QUOTE_HINT.search(sentence):
            score += 5
        if 18 <= len(sentence) <= 78:
            score += 2
        if sentence[:1].isupper():
            score += 1
        if score > best_score:
            best = sentence.rstrip(".")
            best_score = score
    if best_score < 5:
        return ""
    if not best.endswith("."):
        best += "."
    return best


def _uppercase_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if c.isupper()) / len(letters)


def _polish_token(raw: str) -> str | None:
    raw = re.sub(r"\s*·\s*N\b", "", raw)
    raw = re.sub(r"\{[^}]+\}", "", raw)
    bits = re.split(r"[—–]", raw)
    shorts = []
    for bit in bits:
        bit = _clean_inline(bit).strip(" .")
        if 2 <= len(bit) <= 24 and not contains_secret(bit):
            shorts.append(bit)
    if not shorts:
        return None
    return max(shorts, key=lambda item: (_uppercase_ratio(item), -len(item)))


def _tab_run(line: str) -> list[str]:
    if line.count(",") < 3:
        return []
    tokens = []
    for part in line.split(","):
        token = _polish_token(part)
        if token is None:
            if tokens:
                break
            continue
        tokens.append(token)
    if len(tokens) < 4:
        return []
    if sum(_uppercase_ratio(t) for t in tokens) / len(tokens) < 0.55:
        return []
    return tokens[:6]


def _backtick_labels(readme_no_fence: str) -> list[str]:
    labels = []
    for span in re.findall(r"`([^`]{2,48})`", readme_no_fence):
        span = re.sub(r"\{[^}]+\}", "", span)
        span = _clean_inline(span)
        if 2 <= len(span) <= 28 and not contains_secret(span) and " " in span or span[:1].isupper():
            if not re.search(r"https?://|/[a-z]", span) and " " in span:
                labels.append(span)
    # Keep a contiguous series of short UI phrases, not scattered code identifiers.
    if len(labels) < 3:
        return []
    return labels[:6]


def _timeframes(text: str) -> list[str]:
    order = ["1W", "1D", "12H", "4H", "2H", "1H", "30M", "15M", "5M", "1M"]
    found = [token for token in order if re.search(rf"\b{token}\b", text)]
    return found if len(found) >= 3 else []


def _section_bullets(readme: str) -> tuple[str, list[str]]:
    prose = _FENCE.sub("\n", readme or "")
    parts = re.split(r"\n(?=##\s+)", prose)
    preferred = []
    fallback = []
    for part in parts:
        heading_match = _H2.search(part) or re.match(r"##\s+(.+)", part)
        heading = _clean_inline(heading_match.group(1)) if heading_match else ""
        if re.search(r"environment|railway|account|deploy|install|license", heading, re.I):
            continue
        items = []
        for line in part.splitlines():
            bullet = re.match(r"^\s*[-*]\s+(.+)$", line)
            if not bullet:
                continue
            if contains_secret(bullet.group(1)):
                continue
            item = _usable(bullet.group(1), 48)
            if item and not item.lower().startswith(("python", "pip ", "npm ")):
                items.append(item.rstrip("."))
        if len(items) < 2:
            continue
        pair = (heading.upper()[:32] if heading else "README", items[:3])
        if re.search(r"data|method|feature|card|market|highlight|overview", heading, re.I):
            preferred.append(pair)
        else:
            fallback.append(pair)
    if preferred:
        return preferred[0]
    if fallback:
        return fallback[0]
    return "", []


def card(readme: str) -> tuple[str, list[str], str, str]:
    """Return card label, rows, style (tabs|list), and an optional extra line."""
    no_fence = _FENCE.sub("\n", readme or "")
    frames = _timeframes(no_fence)
    if frames:
        return "TIMEFRAMES", frames, "tabs", ""
    for line in no_fence.splitlines():
        if "`" not in line:
            continue
        labels = _backtick_labels(line)
        if len(labels) >= 3:
            label = "MARKETS" if re.search(r"market", line, re.I) else "LABELS"
            return label, labels, "tabs", ""
    for line in no_fence.splitlines():
        run = _tab_run(line)
        if run:
            label = "TABS" if re.search(r"\btabs?\b", line, re.I) else "LABELS"
            return label, run, "tabs", ""
    heading, items = _section_bullets(readme or "")
    if items:
        style = "tabs" if all(len(item) <= 18 for item in items) else "list"
        return heading or "README", items, style, ""
    return "", [], "list", ""


def disclaimer(readmes: list[str]) -> str:
    best = ""
    for readme in readmes:
        for sentence in _sentences(_prose(readme)):
            if contains_secret(sentence):
                continue
            if not re.search(r"\b21\+|entertainment only|for research and entertainment", sentence, re.I):
                continue
            sentence = sentence.rstrip(".")
            if not best or len(sentence) < len(best):
                best = sentence
    if not best:
        return ""
    return best if best.endswith(".") else best + "."


def present(fact: dict) -> dict:
    """Add on-screen fields. Counts pass through unchanged from the API."""
    readme = fact.get("readme") or ""
    h1_match = _H1.search(readme)
    h1 = h1_match.group(1) if h1_match else ""
    label, rows, style, extra = card(readme)
    scene = {
        "owner": fact["owner"],
        "repo": fact["repo"],
        "branch": fact.get("branch") or "",
        "name": display_name(fact["repo"], readme, fact.get("description") or ""),
        "category": category(h1, fact.get("description") or "", readme),
        "language": fact.get("language") or "",
        "pr_count": fact["pr_count"],
        "commit_count": fact["commit_count"],
        "subtitle": subtitle(readme, fact.get("description") or ""),
        "quote": quote(readme),
        "card_label": label,
        "rows": rows,
        "row_style": style,
        "extra": extra,
    }
    if not scene["category"]:
        scene["category"] = (scene["language"] or "REPO").upper()
    quote_text = (scene.get("quote") or "").rstrip(".").lower()
    if quote_text and quote_text in (scene.get("subtitle") or "").lower():
        scene["quote"] = ""
    return scene
