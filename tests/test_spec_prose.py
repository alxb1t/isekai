"""Every spec reads without history, and no line in it passes 120 characters.

The rule is `CLAUDE.md`'s *How a spec reads*; this holds the parts a test can check,
over the effective spec — the living `spec.md` with each active delta's blocks in
place, which is what a release will fold. Why: `0046` design D5.
"""

import re
from pathlib import Path

import pytest

from tests.specs import effective, write_tree

REPO_ROOT = Path(__file__).resolve().parent.parent
WIDTH = 120

_HISTORY = re.compile(
    r"\bv0\.\d+"  # an isekai version
    r"|\b00\d\d(?:-[a-z]|`?\s+design)"  # a change id, followed by its slug or `design`
    r"|`[0-9a-f]{7,12}`"  # a commit hash, backticked
)
# `ui` keeps its history until the work that reshapes it rewrites it.
_HISTORY_EXEMPT = frozenset({"ui"})
# A title is kept whatever its length: a delta names its requirement by it.
_TITLES = ("### Requirement: ", "#### Scenario: ")


def texts(root: Path) -> dict[str, str]:
    """Return each capability's effective spec as one text."""
    return {
        cap: preamble
        + "".join(f"### Requirement: {title}{body}" for title, body in reqs.items())
        for cap, (preamble, reqs) in effective(root).items()
    }


def history(specs: dict[str, str]) -> list[str]:
    """Return every line naming a version, a change id or a commit, as `cap: line`."""
    return [
        f"{cap}: {line.strip()}"
        for cap, text in specs.items()
        if cap not in _HISTORY_EXEMPT
        for line in text.splitlines()
        if _HISTORY.search(line)
    ]


def long_lines(specs: dict[str, str]) -> list[str]:
    """Return every line past `WIDTH` characters but a title, as `cap: line`."""
    return [
        f"{cap}: {line[:60]}…"
        for cap, text in specs.items()
        for line in text.splitlines()
        if len(line) > WIDTH and not line.startswith(_TITLES)
    ]


@pytest.fixture(scope="module")
def specs() -> dict[str, str]:
    """Read the repository's effective spec once for the module."""
    return texts(REPO_ROOT)


@pytest.mark.spec_exempt("structural: no spec names a version, a change id or a commit")
def test_no_spec_names_a_version_change_or_commit(specs: dict[str, str]) -> None:
    found = history(specs)
    assert not found, f"history in a spec: {found[:5]}"


@pytest.mark.spec_exempt("structural: no spec line passes 120 characters")
def test_no_spec_line_passes_120_characters(specs: dict[str, str]) -> None:
    found = long_lines(specs)
    assert not found, f"spec lines past {WIDTH} characters: {found[:5]}"


_LIVING = """\
# Capability: `{cap}`

## Purpose

What it is for.

## Requirements

### Requirement: Kept

The system SHALL keep.

### Requirement: Told

{told}
"""


def _tree(root: Path, told: str, delta: str | None = None, cap: str = "cap") -> Path:
    """Write one capability whose `Told` requirement reads `told`."""
    return write_tree(root, _LIVING.format(cap=cap, told=told), delta, cap)


@pytest.mark.spec_exempt(
    "structural: twin of test_no_spec_names_a_version_change_or_commit"
)
@pytest.mark.parametrize(
    "line",
    [
        "The rule changed in v0.21.",
        "It came with 0044-the-session.",
        "See `0045` design D2.",
        "It was deleted in `8baf2b3`.",
    ],
)
def test_a_version_a_change_or_a_commit_is_caught(tmp_path: Path, line: str) -> None:
    assert history(texts(_tree(tmp_path, line))) == [f"cap: {line}"]


@pytest.mark.spec_exempt(
    "structural: twin of test_no_spec_names_a_version_change_or_commit"
)
def test_history_reads_the_effective_spec(tmp_path: Path) -> None:
    delta = """\
## MODIFIED Requirements

### Requirement: Told

The system SHALL tell, as it did in v0.20.

## ADDED Requirements

### Requirement: New

The system SHALL be new since v0.30.
"""
    root = _tree(tmp_path, "The rule changed in v0.21.", delta)
    assert history(texts(root)) == [
        "cap: The system SHALL tell, as it did in v0.20.",
        "cap: The system SHALL be new since v0.30.",
    ]
    exempt = _tree(tmp_path / "ui", "The rule changed in v0.21.", cap="ui")
    assert history(texts(exempt)) == []


@pytest.mark.spec_exempt("structural: twin of test_no_spec_line_passes_120_characters")
def test_a_line_past_120_characters_is_caught(tmp_path: Path) -> None:
    long = "x" * (WIDTH + 1)
    delta = (
        f"## ADDED Requirements\n\n### Requirement: {long}\n\n#### Scenario: {long}\n"
    )
    root = _tree(tmp_path, f"{'y' * WIDTH}\n{long}", delta)
    assert long_lines(texts(root)) == [f"cap: {long[:60]}…"]
