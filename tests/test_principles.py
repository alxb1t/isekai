"""The *Held by* lines of `docs/principles.md`, resolved against the suite.

A renamed or deleted test would otherwise orphan the principle naming it while the
page still reads as held. Only `tests/<file>.py::<name>` names are checked; prose
such as *review* is not. Why: `0027` design D4.
"""

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PRINCIPLES = REPO_ROOT / "docs" / "principles.md"

_HELD_BY = "- **Held by:**"
_NAMED = re.compile(r"`(tests/[\w/]+\.py)::(\w+)`")


def _principles(text: str) -> dict[str, list[str]]:
    """Return each `### ` principle's title, mapped to its *Held by* bullets' text.

    A bullet runs to the next top-level `- **` bullet or heading, sub-bullets in.
    """
    found: dict[str, list[str]] = {}
    title: str | None = None
    held = False
    for line in text.splitlines():
        if line.startswith(("#", "- **")):
            held = False
        if line.startswith("### "):
            title = line.removeprefix("### ")
            found[title] = []
        elif line.startswith("#"):
            title = None
        if title is not None and line.startswith(_HELD_BY):
            held = True
            found[title].append("")
        if held and title is not None:
            found[title][-1] += line + "\n"
    return found


def _defined(path: Path) -> set[str]:
    return {
        node.name
        for node in ast.parse(path.read_text()).body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }


def missing_tests(text: str, root: Path) -> list[str]:
    """Return every `tests/<file>.py::<name>` a *Held by* names that is not defined."""
    missing: list[str] = []
    for bullets in _principles(text).values():
        for file, name in _NAMED.findall("".join(bullets)):
            path = root / file
            if not path.is_file() or name not in _defined(path):
                missing.append(f"{file}::{name}")
    return missing


def without_one_held_by(text: str) -> list[str]:
    """Return every principle that has no *Held by* bullet, or more than one."""
    return [title for title, bullets in _principles(text).items() if len(bullets) != 1]


@pytest.mark.spec_exempt("structural: every test a principle names exists")
def test_every_test_a_principle_names_exists() -> None:
    assert missing_tests(PRINCIPLES.read_text(), REPO_ROOT) == []


@pytest.mark.spec_exempt("structural: every principle says once what holds it")
def test_every_principle_has_one_held_by_line() -> None:
    assert without_one_held_by(PRINCIPLES.read_text()) == []


@pytest.mark.spec_exempt("structural: twin of test_every_test_a_principle_names_exists")
def test_the_check_catches_a_named_test_that_does_not_exist(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_here():\n    pass\n")
    text = (
        "### A rule\n\n"
        "- **Held by:** `tests/test_x.py::test_here`,\n"
        "  - `tests/test_x.py::test_gone`\n"
        "- **Known breaks:** `tests/test_x.py::test_not_a_holder`\n"
    )

    assert missing_tests(text, tmp_path) == ["tests/test_x.py::test_gone"]


@pytest.mark.spec_exempt(
    "structural: twin of test_every_principle_has_one_held_by_line"
)
def test_the_check_catches_a_principle_without_a_held_by_line() -> None:
    text = (
        "### Held\n\n- **Held by:** review.\n\n"
        "### Unheld\n\n- **Why:** a reason.\n\n"
        "## A group\n\n- **Held by:** outside any principle.\n"
    )

    assert without_one_held_by(text) == ["Unheld"]
