# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print how many references in the top-level docs point at nothing.

Run from the repository root: `references.py`. A reference is a relative
link to a missing file or anchor, or a `D<n>` with no decision heading.
"""

import re
import sys
import unicodedata
from pathlib import Path

DOCS = (
    "AGENTS.md",
    "README.md",
    "ARCHITECTURE.md",
    "CODING_STANDARDS.md",
    "CONTRIBUTING.md",
    "THREAT_MODEL.md",
)
DECISIONS = "docs/decisions.md"
FENCE = re.compile(r"^(`{3,}|~{3,}).*?^\1[ \t]*$", re.MULTILINE | re.DOTALL)
CODE_SPAN = re.compile(r"`[^`\n]*`")
LINK = re.compile(r"\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
HTML_ANCHOR = re.compile(r"""<a\s+[^>]*?(?:id|name)=["']([^"']+)["']""")
DECISION_HEADING = re.compile(r"^### D(\d+) ·", re.MULTILINE)
DECISION_REF = re.compile(r"\bD(\d+)\b")


def prose(text: str) -> str:
    """Return `text` without its fenced code blocks."""
    return FENCE.sub("", text)


def slug(heading: str) -> str:
    """Return the anchor GitHub gives a heading.

    e.g. "D10 · The face" -> "d10--the-face"
    """
    kept = "".join(
        char
        for char in heading.strip().lower()
        if char in "_- " or unicodedata.category(char)[0] in "LM" or char.isdecimal()
    )
    return kept.replace(" ", "-")


def anchors(text: str) -> set[str]:
    """Return every anchor a markdown text offers, repeated headings suffixed."""
    body = prose(text)
    found = set(HTML_ANCHOR.findall(body))
    seen: dict[str, int] = {}
    for heading in HEADING.findall(body):
        base = slug(heading)
        count = seen.get(base, 0)
        found.add(base if count == 0 else f"{base}-{count}")
        seen[base] = count + 1
    return {anchor.lower() for anchor in found}


def broken_links(root: Path, name: str) -> int:
    """Return the relative links in `name` to a missing file or anchor."""
    file = root / name
    broken = 0
    for target in LINK.findall(CODE_SPAN.sub("", prose(file.read_text("utf-8")))):
        if SCHEME.match(target):
            continue
        path, _, anchor = target.partition("#")
        linked = (file.parent / path) if path else file
        if not linked.exists():
            broken += 1
        elif anchor and linked.suffix == ".md" and linked.is_file():
            if anchor.lower() not in anchors(linked.read_text("utf-8")):
                broken += 1
    return broken


def decisions(root: Path) -> set[str]:
    """Return the numbers of the decisions `docs/decisions.md` has a heading for."""
    return set(DECISION_HEADING.findall((root / DECISIONS).read_text("utf-8")))


def dangling_decisions(root: Path, name: str, known: set[str]) -> int:
    """Return the `D<n>` mentions in `name` that name no decision."""
    text = (root / name).read_text("utf-8")
    return sum(number not in known for number in DECISION_REF.findall(text))


def scanned(root: Path) -> list[str]:
    """Return the docs to read, as paths relative to `root`."""
    found = [name for name in DOCS if (root / name).is_file()]
    return found + sorted(
        path.relative_to(root).as_posix() for path in (root / "docs").glob("*.md")
    )


def count(root: Path) -> int:
    """Return every broken link and dangling decision across the scanned docs."""
    known = decisions(root)
    return sum(
        broken_links(root, name) + dangling_decisions(root, name, known)
        for name in scanned(root)
    )


def main() -> int:
    """Print the count, or the reason it cannot be read."""
    try:
        print(count(Path.cwd()))
    except OSError as refusal:
        print(f"unreadable: {refusal}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
