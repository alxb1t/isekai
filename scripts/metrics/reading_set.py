# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print the words in the files every agent reads before work.

Run from the repository root: `reading_set.py`.
"""

import sys
from pathlib import Path

READING_SET = (
    "AGENTS.md",
    "CODING_STANDARDS.md",
    "CONTRIBUTING.md",
    "ARCHITECTURE.md",
    "THREAT_MODEL.md",
    "docs/principles.md",
    "docs/decisions.md",
)


def words(root: Path) -> int:
    """Return the whitespace-separated words across the reading set."""
    return sum(len((root / name).read_text("utf-8").split()) for name in READING_SET)


def main() -> int:
    """Print the word count, or the reason it cannot be read."""
    try:
        print(words(Path.cwd()))
    except OSError as refusal:
        print(f"reading set unreadable: {refusal}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
