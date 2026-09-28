"""Rails: real copy only, secrets never reach the composition."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path

from brag.compose import render_html
from brag.extract import card, disclaimer, display_name, present, quote, subtitle
from brag.github_api import link_last_page, parse_repo
from brag.scrub import contains_secret, scrub

MLB = """
# MLB Predictions — ULTRON v3 / SERAPH v4

Daily bot that pulls the slate, runs the SERAPH v4 engine, writes structured JSON, and emits the ULTRON card.

**FOR ENTERTAINMENT ONLY · MUST BE 21+ · BET RESPONSIBLY**

The SERAPH slate still sits in the same tabs — GAMES, ENGINE v4, PROPS, TOP PLAYS · N, LOG, RECORD — with game cards.

## Data rules

- Every number has a source. If a lookup fails, leave it blank.
- Email ops@example.com or export DATABASE_URL=postgresql://user:pw@ep-test.neon.tech/db
- Project id sample-mist-00000000 stays off the card.
"""

ATHENA = """
# Athena Bets

Live NFL research and a prospective, automatically graded paper ledger.

## Data and methods

- ESPN's NFL scoreboard supplies scheduled games, live score, and news.
- nflverse history trains team strength from completed games.
- No-vig odds, push-aware EV, and capped Kelly.

An entry is immutable; later changes cannot rewrite its line, price, or stake.

For research and entertainment, 21+. No profitability claim.
"""

AEGIS = """
# Aegis Bets

UFC / MMA sports intelligence desk. The Place control is disabled on purpose.

Odds, fighter records, and outcomes are **never invented**.

**Markets** use MMA language when a price exists: `{fighter} to win`, `{fighter} by KO/TKO`, `{fighter} by Submission`, `{fighter} by Decision`, `Over/Under {n} Rounds`.
"""

ATLAS = """
# ATLAS APEX

Private. Live signals (CoinGecko + Neon + Railway). No trade execution.
"""


class ScrubTests(unittest.TestCase):
    def test_strips_secret_shapes(self):
        raw = (
            "ping ops@example.com host ep-leaf.neon.tech "
            "DATABASE_URL=postgresql://user:pw@db.example/app "
            "token ghp_abcdefghijklmnopqrstuvwxyz sample-mist-00000000 "
            "https://app.example.railway.app/secret"
        )
        cleaned = scrub(raw)
        self.assertFalse(contains_secret(cleaned))
        for needle in ("ops@example.com", "neon.tech", "postgresql://", "ghp_", "00000000", "railway.app"):
            self.assertNotIn(needle, cleaned)

    def test_keeps_plain_sentence(self):
        self.assertEqual(scrub("Every number has a source."), "Every number has a source.")


class ExtractTests(unittest.TestCase):
    def test_names_and_categories(self):
        self.assertEqual(display_name("mlb-predictions", MLB, ""), "ULTRON")
        self.assertEqual(display_name("athena-bets", ATHENA, ""), "ATHENA")
        self.assertEqual(display_name("ufc-bets", AEGIS, ""), "AEGIS")
        self.assertEqual(display_name("atlas-apex", ATLAS, ""), "ATLAS APEX")

    def test_quotes_are_verbatim_fragments(self):
        self.assertEqual(quote(MLB), "Every number has a source.")
        self.assertEqual(quote(ATHENA), "An entry is immutable.")
        self.assertIn("never invented", quote(AEGIS))
        self.assertEqual(quote(ATLAS), "No trade execution.")

    def test_ultron_tabs(self):
        label, rows, style, _extra = card(MLB)
        self.assertEqual(style, "tabs")
        self.assertEqual(rows, ["GAMES", "ENGINE v4", "PROPS", "TOP PLAYS", "LOG", "RECORD"])
        self.assertEqual(label, "TABS")

    def test_aegis_markets(self):
        _label, rows, style, _extra = card(AEGIS)
        self.assertEqual(style, "tabs")
        self.assertIn("to win", rows)
        self.assertIn("by KO/TKO", rows)
        self.assertIn("Over/Under Rounds", rows)

    def test_secrets_do_not_become_copy(self):
        fact = {
            "owner": "o",
            "repo": "mlb-predictions",
            "branch": "main",
            "description": "Automated MLB predictions",
            "language": "Python",
            "pr_count": 65,
            "commit_count": 162,
            "readme": MLB,
        }
        scene = present(fact)
        blob = " ".join(
            [
                scene["subtitle"],
                scene["quote"],
                scene["card_label"],
                " ".join(scene["rows"]),
            ]
        )
        self.assertNotIn("example.com", blob)
        self.assertNotIn("postgresql", blob)
        self.assertNotIn("00000000", blob)
        self.assertEqual(scene["pr_count"], 65)
        self.assertEqual(scene["commit_count"], 162)
        self.assertIn("Daily bot", scene["subtitle"])

    def test_disclaimer_is_short_and_real(self):
        line = disclaimer([MLB, ATHENA, AEGIS])
        self.assertIn("21+", line)
        self.assertLessEqual(len(line), 80)


class ComposeTests(unittest.TestCase):
    def test_html_has_counts_and_no_secrets(self):
        scenes = [
            present(
                {
                    "owner": "DarkWzrd-Zeref",
                    "repo": "mlb-predictions",
                    "branch": "main",
                    "description": "",
                    "language": "Python",
                    "pr_count": 65,
                    "commit_count": 162,
                    "readme": MLB,
                }
            ),
            present(
                {
                    "owner": "DarkWzrd-Zeref",
                    "repo": "atlas-apex",
                    "branch": "main",
                    "description": "ATLAS APEX — live signals (CoinGecko + Neon + Railway). No trade execution.",
                    "language": "",
                    "pr_count": 18,
                    "commit_count": 1,
                    "readme": ATLAS,
                }
            ),
        ]
        doc = render_html(
            scenes,
            vertical=True,
            title="",
            disclaimer_line=disclaimer([MLB, ATLAS]),
            when=datetime(2026, 9, 28, tzinfo=timezone.utc),
        )
        self.assertIn("2 desks.", doc)
        self.assertIn("83 pull requests.", doc)
        self.assertIn("65 PRs", doc)
        self.assertIn("1 commit", doc)
        self.assertIn("No invented numbers.", doc)
        self.assertIn("data-width=\"1080\"", doc)
        self.assertIn("data-height=\"1920\"", doc)
        self.assertNotIn("example.com", doc)
        self.assertNotIn("postgresql", doc)
        self.assertNotIn("hyperframes cloud", doc)
        self.assertNotIn("JavaScript", doc)
        self.assertIn('src="assets/gsap.min.js"', doc)

    def test_audio_file_is_optional_copy(self):
        from brag.compose import write_composition

        dest = Path("/tmp/brag-compose-test")
        write_composition(
            dest,
            [
                {
                    "name": "ULTRON",
                    "category": "MLB",
                    "repo": "mlb-predictions",
                    "language": "Python",
                    "pr_count": 1,
                    "commit_count": 2,
                    "subtitle": "Daily bot.",
                    "quote": "Every number has a source.",
                    "card_label": "TABS",
                    "rows": ["GAMES"],
                    "row_style": "tabs",
                    "extra": "",
                }
            ],
            vertical=True,
            title="",
            disclaimer_line="",
            audio=None,
            when=datetime(2026, 9, 28, tzinfo=timezone.utc),
        )
        text = (dest / "index.html").read_text()
        self.assertNotIn("<audio", text)
        self.assertIn("1 desk.", text)
        self.assertIn("1 pull request.", text)


class EngineTests(unittest.TestCase):
    def test_render_goes_through_the_sibling_wrapper(self):
        import os

        from brag.engine import poster_invocation, render_invocation

        old = os.environ.pop("HYPERFRAMES_HOME", None)
        try:
            commands = render_invocation(Path("composition"), Path("out/clip.mp4"), fps=30)
            frame = poster_invocation(Path("out/clip.mp4"), Path("out/clip.jpg"), 2.0)
        finally:
            if old is not None:
                os.environ["HYPERFRAMES_HOME"] = old
        self.assertEqual([cmd[1] for cmd in commands], ["check", "render"])
        for cmd in commands:
            self.assertTrue(cmd[0].endswith("/hyperframes/render.sh"))
            self.assertNotIn("npx", cmd)
            self.assertNotIn("cloud", " ".join(cmd))
        self.assertEqual(frame[1], "poster")
        self.assertTrue(frame[0].endswith("/hyperframes/render.sh"))

    def test_pipeline_does_not_call_npx(self):
        package = Path(__file__).resolve().parents[1] / "brag"
        for path in package.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("npx", text)
            self.assertNotIn("hyperframes@", text)
            self.assertNotIn("hyperframes cloud", text)


class ParseTests(unittest.TestCase):
    def test_specs(self):
        self.assertEqual(parse_repo("DarkWzrd-Zeref/atlas-apex"), ("DarkWzrd-Zeref", "atlas-apex", None))
        self.assertEqual(
            parse_repo("DarkWzrd-Zeref/atlas-apex@cursor/atlas-apex-railway-75ff"),
            ("DarkWzrd-Zeref", "atlas-apex", "cursor/atlas-apex-railway-75ff"),
        )
        self.assertEqual(
            parse_repo("https://github.com/DarkWzrd-Zeref/ufc-bets/tree/main"),
            ("DarkWzrd-Zeref", "ufc-bets", "main"),
        )

    def test_link_header(self):
        header = (
            '<https://api.github.com/repos/o/r/pulls?state=all&per_page=1&page=2>; rel="next", '
            '<https://api.github.com/repos/o/r/pulls?state=all&per_page=1&page=65>; rel="last"'
        )
        self.assertEqual(link_last_page(header), 65)
        self.assertIsNone(link_last_page(""))


if __name__ == "__main__":
    unittest.main()
