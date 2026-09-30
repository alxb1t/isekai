"""Every spec and every comment reads without history, and no spec line passes 120.

The spec guard holds `CLAUDE.md`'s *How a spec reads* where a test can, over the
effective spec — the living `spec.md` with each active delta's blocks in place,
which is what a release will fold. The comment guard holds its *A comment says what
and why*, over the comments, docstrings and `spec_exempt` reasons of the code.
Both read history through one pattern.
"""

import ast
import io
import re
import subprocess
import tokenize
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.specs import effective, write_tree

REPO_ROOT = Path(__file__).resolve().parent.parent
WIDTH = 120

_HISTORY = re.compile(
    r"\bv0\.\d{1,2}(?:\.\d{1,2})?(?!\.?\d)"  # an isekai version, not v0.2.2.4
    r"|\b00\d\d(?:-[a-z]|`?\s+(?:design|proposal|tasks|D\d))"  # a change id cited
    r"|design\.md`?,?\s*D\d+"  # a design citation
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


# Each form `_HISTORY` reads, fed to both guards' twins.
_CITED = [
    "since v0.21",
    "see 0044-the-session",
    "`0045` design D2",
    "design.md D4",
    "deleted in `8baf2b3`",
]


@pytest.mark.spec_exempt(
    "structural: twin of test_no_spec_names_a_version_change_or_commit"
)
@pytest.mark.parametrize("cited", _CITED)
def test_a_version_a_change_or_a_commit_is_caught(tmp_path: Path, cited: str) -> None:
    line = f"The rule is kept, {cited}."
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


# The trees whose comments carry no history. `ui/` and `evaluation/` keep theirs
# until the work that reshapes each rewrites it.
_COMMENT_TREES = ("isekai", "tools", "infra", "tests", "start.sh", "Dockerfile")
_DEFINITIONS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _python_prose(text: str) -> Iterator[tuple[int, str]]:
    """Yield each comment, docstring line and `spec_exempt` reason, with its line."""
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == tokenize.COMMENT:
            yield token.start[0], token.string
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, _DEFINITIONS) and (doc := ast.get_docstring(node, False)):
            for offset, line in enumerate(doc.splitlines()):
                yield node.body[0].lineno + offset, line
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "spec_exempt"
        ):
            for reason in node.args:
                if isinstance(reason, ast.Constant) and isinstance(reason.value, str):
                    yield reason.lineno, reason.value


def _shell_prose(text: str) -> Iterator[tuple[int, str]]:
    """Yield each `#` line of a shell script or a `Dockerfile`, with its line."""
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("#"):
            yield number, line


def comment_history(root: Path, paths: list[str]) -> list[str]:
    """Return every comment or docstring line naming history, as `file:line`.

    e.g. a comment citing a version at line 7 of `isekai/run.py` → `isekai/run.py:7`
    """
    found = []
    for name in paths:
        if name.endswith(".py"):
            reader = _python_prose
        elif name.endswith(".sh") or Path(name).name == "Dockerfile":
            reader = _shell_prose
        else:
            continue
        prose = reader((root / name).read_text())
        found += [f"{name}:{line}" for line, text in prose if _HISTORY.search(text)]
    return found


@pytest.mark.spec_exempt("structural: no comment names a version, a change or a design")
def test_no_comment_names_a_version_change_or_design() -> None:
    tracked = subprocess.run(
        ["git", "ls-files", *_COMMENT_TREES],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    assert tracked, "git ls-files listed no source"
    found = comment_history(REPO_ROOT, tracked)
    assert not found, f"history in a comment: {found[:5]}"


@pytest.mark.spec_exempt(
    "structural: twin of test_no_comment_names_a_version_change_or_design"
)
@pytest.mark.parametrize("cited", _CITED)
def test_history_in_a_comment_or_a_docstring_is_caught(
    tmp_path: Path, cited: str
) -> None:
    (tmp_path / "comment.py").write_text(f"x = 1  # kept, {cited}\n")
    (tmp_path / "docstring.py").write_text(f'def f():\n    """Kept, {cited}."""\n')
    (tmp_path / "reason.py").write_text(
        f'@pytest.mark.spec_exempt("{cited}")\ndef test() -> None: ...\n'
    )
    (tmp_path / "start.sh").write_text(f"#!/bin/sh\n# kept, {cited}\n")
    names = ["comment.py", "docstring.py", "reason.py", "start.sh"]

    assert comment_history(tmp_path, names) == [
        "comment.py:1",
        "docstring.py:2",
        "reason.py:1",
        "start.sh:2",
    ]


@pytest.mark.spec_exempt(
    "structural: twin of test_no_comment_names_a_version_change_or_design"
)
def test_a_third_partys_version_and_code_are_not_history(tmp_path: Path) -> None:
    (tmp_path / "data.py").write_text(
        '"""The pack at v0.2.2.4."""\nRUNS = ".data/v0.20"  # the pack, v0.2.2.4\n'
    )
    (tmp_path / "Dockerfile").write_text("FROM base:v0.21\n# the pack at v0.2.2.4\n")

    assert comment_history(tmp_path, ["data.py", "Dockerfile"]) == []
