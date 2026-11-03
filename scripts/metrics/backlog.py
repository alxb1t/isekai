# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print how many open cards the primary checkout's backlog holds.

Run from any checkout of the repository: `backlog.py`.
"""

import re
import subprocess
import sys
from pathlib import Path

CARD = re.compile(r"^- \*\*\S+·", re.MULTILINE)


def cards(text: str) -> int:
    """Return the number of cards in a backlog.

    e.g. a line "- **0060·R5 — a**" and a line "- **op·x — b**" -> 2
    """
    return len(CARD.findall(text))


def backlog_path() -> Path:
    """Return the backlog file in the primary checkout's `.minions/`."""
    common = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return Path(common).parent / ".minions" / "backlog.md"


def main() -> int:
    """Print the card count, or the reason it cannot be read."""
    try:
        path = backlog_path()
        text = path.read_text(encoding="utf-8")
    except (subprocess.CalledProcessError, OSError) as refusal:
        print(f"backlog unreadable: {refusal}", file=sys.stderr)
        return 1
    print(cards(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
