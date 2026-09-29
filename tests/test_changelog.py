"""The changelog keeps its format, and nothing cites it.

`CHANGELOG.md` is a release record: Keep a Changelog sections, one short bullet
per change, and each heading naming its change. It is not a source, so no code,
doc or README points into it (`0038` design D8).
"""

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = REPO_ROOT / "CHANGELOG.md"

SECTIONS = frozenset({"Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"})
VERSION = re.compile(
    r"## \[(?P<version>\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}"
    r"(?P<change> · \d{4}-[a-z0-9-]+)?"
)
# The first version cut from a change; every heading below it predates the changes.
FIRST_CHANGE = (0, 7, 0)
BULLET_LIMIT = 300

# Files that name the changelog because they write, read or check it.
MAY_CITE = frozenset(
    {
        "CHANGELOG.md",
        "CLAUDE.md",
        "docs/pins.md",
        "tests/test_flow.py",
        "tests/test_docs.py",
        "tests/test_changelog.py",
    }
)
FROZEN = "openspec/changes/"


def bullets(lines: list[str]) -> list[str]:
    """Return each top-level bullet with its continuation lines joined.

    e.g. ["- a b", "  c", "", "- d"] -> ["- a b c", "- d"]
    """
    joined: list[str] = []
    for line in lines:
        if line.startswith("- "):
            joined.append(line)
        elif joined and line.startswith(" ") and line.strip():
            joined[-1] += " " + line.strip()
    return joined


def format_problems(text: str) -> list[str]:
    """Return every way `text` breaks the changelog's format, in file order."""
    lines = text.splitlines()
    problems: list[str] = []

    headings = [line for line in lines if line.startswith("## ")]
    if not headings or headings[0] != "## [Unreleased]":
        problems.append("the first ## heading is not ## [Unreleased]")
    for heading in headings[1:]:
        match = VERSION.fullmatch(heading)
        if match is None:
            problems.append(f"malformed heading: {heading}")
            continue
        version = tuple(int(part) for part in match["version"].split("."))
        if (version >= FIRST_CHANGE) != (match["change"] is not None):
            problems.append(f"change id wrong for its version: {heading}")

    sectioned = True
    for line in lines:
        if line.startswith("## "):
            sectioned = VERSION.fullmatch(line) is None
        elif line.startswith("### "):
            sectioned = True
            if line[4:] not in SECTIONS:
                problems.append(f"not a Keep a Changelog section: {line}")
        elif line.startswith("- ") and not sectioned:
            problems.append(f"bullet outside a section: {line}")
        if re.match(r"\s+[-*] ", line):
            problems.append(f"nested bullet: {line.strip()}")

    for bullet in bullets(lines):
        if len(bullet) > BULLET_LIMIT:
            problems.append(f"bullet past {BULLET_LIMIT} characters: {bullet[:60]}…")
    return problems


def citations(root: Path, paths: list[str]) -> list[str]:
    """Return the paths under `root` whose text names `CHANGELOG.md` and may not."""
    hits: list[str] = []
    for path in paths:
        if path in MAY_CITE or path.startswith(FROZEN):
            continue
        file = root / path
        if not file.is_file():
            continue
        try:
            text = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "CHANGELOG.md" in text:
            hits.append(path)
    return hits


@pytest.mark.spec_exempt("structural: the changelog keeps its format")
def test_the_changelog_keeps_its_format() -> None:
    text = CHANGELOG.read_text()

    assert VERSION.search(text), "the changelog holds no version heading at all"
    assert format_problems(text) == []


@pytest.mark.spec_exempt("structural: twin of test_the_changelog_keeps_its_format")
@pytest.mark.parametrize(
    ("text", "problem"),
    [
        ("## [0.1.0] - 2026-07-28\n", "the first ## heading"),
        ("## [Unreleased]\n\n## [0.25.0] - 2026-09-27\n", "change id wrong"),
        (
            "## [Unreleased]\n\n## [0.6.0] - 2026-08-15 · 0001-mf-standard\n",
            "change id wrong",
        ),
        ("## [Unreleased]\n\n## [0.5.0]\n", "malformed heading"),
        ("## [Unreleased]\n\n### Notes\n", "not a Keep a Changelog section"),
        ("## [Unreleased]\n\n### Added\n\n- a\n  - b\n", "nested bullet"),
        (
            "## [Unreleased]\n\n## [0.30.0] - 2026-09-29 · 0043-the-session\n\n- a\n",
            "bullet outside a section",
        ),
        (
            "## [Unreleased]\n\n### Added\n\n- "
            + "word " * 40
            + "\n  "
            + "word " * 30
            + "\n",
            "bullet past",
        ),
    ],
)
def test_the_format_check_reports_each_break(text: str, problem: str) -> None:
    problems = format_problems(text)

    assert any(found.startswith(problem) for found in problems), problems


@pytest.mark.spec_exempt("structural: nothing cites the changelog")
def test_nothing_cites_the_changelog() -> None:
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout.splitlines()

    assert "CHANGELOG.md" in tracked, "git ls-files did not list the changelog"
    assert citations(REPO_ROOT, tracked) == []


@pytest.mark.spec_exempt("structural: twin of test_nothing_cites_the_changelog")
def test_the_citation_check_reports_a_file_naming_the_changelog(tmp_path: Path) -> None:
    (tmp_path / "evaluation").mkdir()
    (tmp_path / "evaluation" / "README.md").write_text("a gap `CHANGELOG.md` names")
    (tmp_path / "CLAUDE.md").write_text("`CHANGELOG.md` follows Keep a Changelog")
    (tmp_path / "openspec" / "changes" / "0001-x").mkdir(parents=True)
    (tmp_path / "openspec" / "changes" / "0001-x" / "design.md").write_text(
        "CHANGELOG.md:12"
    )
    (tmp_path / "photo.png").write_bytes(b"\xff\xd8CHANGELOG.md\xff")

    paths = [
        "evaluation/README.md",
        "CLAUDE.md",
        "openspec/changes/0001-x/design.md",
        "photo.png",
    ]

    assert citations(tmp_path, paths) == ["evaluation/README.md"]
