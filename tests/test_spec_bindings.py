"""Every spec↔test binding, held by the gate.

Each scenario key has a test, each `spec` marker names a key, and each test carries
exactly one of `spec` and `spec_exempt`. Keys are read with a regex, markers with
`ast`: no marker is built at runtime. Why: `0045` design D1, D2.
"""

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

_KEY = re.compile(r"^- \*\*Key:\*\* `([^`]+)`", re.M)
_SECTION = re.compile(r"^## (.*)$", re.M)
_REQUIREMENT = re.compile(r"^### Requirement: (.*)$", re.M)
_MARKERS = ("spec", "spec_exempt")

Marker = tuple[str, str | None]
Test = tuple[str, str, list[Marker]]


def _sections(text: str) -> dict[str, str]:
    """Return each `## ` heading of a spec file, mapped to its body."""
    parts = _SECTION.split(text)
    return dict(zip(parts[1::2], parts[2::2], strict=True))


def _requirements(text: str) -> dict[str, set[str]]:
    """Return each requirement's title, mapped to the keys of its scenarios."""
    parts = _REQUIREMENT.split(text)
    return {
        title.strip(): set(_KEY.findall(body))
        for title, body in zip(parts[1::2], parts[2::2], strict=True)
    }


def spec_keys(root: Path) -> set[str]:
    """Return the living spec's keys, as the active changes' deltas leave them.

    A delta's ADDED and MODIFIED keys join; a REMOVED requirement's living keys leave.
    """
    living = {
        path.parent.name: _requirements(path.read_text())
        for path in sorted((root / "openspec" / "specs").glob("*/spec.md"))
    }
    keys = {key for reqs in living.values() for held in reqs.values() for key in held}
    added: set[str] = set()
    changes = root / "openspec" / "changes"
    for delta in sorted(changes.glob("*/specs/*/spec.md")):
        if delta.parts[len(changes.parts)] == "archive":
            continue
        capability = delta.parent.name
        for heading, body in _sections(delta.read_text()).items():
            if heading.strip() in ("ADDED Requirements", "MODIFIED Requirements"):
                added |= set(_KEY.findall(body))
            elif heading.strip() == "REMOVED Requirements":
                for title in _REQUIREMENT.findall(body):
                    keys -= living.get(capability, {}).get(title.strip(), set())
    return keys | added


def _marker(decorator: ast.expr) -> Marker | None:
    """Return a `spec` or `spec_exempt` decorator as (name, argument), else None.

    An argument that is not one string literal reads as None, so `unmarked` fails it.
    """
    call = decorator if isinstance(decorator, ast.Call) else None
    target = call.func if call else decorator
    if not (
        isinstance(target, ast.Attribute)
        and target.attr in _MARKERS
        and isinstance(target.value, ast.Attribute)
        and target.value.attr == "mark"
    ):
        return None
    if call and len(call.args) == 1 and not call.keywords:
        (arg,) = call.args
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return target.attr, arg.value
    return target.attr, None


def marked_tests(root: Path) -> list[Test]:
    """Return each `test_` function under `tests/` with its `spec*` markers.

    e.g. `@pytest.mark.spec("a:b:c") def test_x` in `tests/test_y.py`
    -> ("tests/test_y.py", "test_x", [("spec", "a:b:c")])
    """
    found: list[Test] = []
    for path in sorted((root / "tests").rglob("test_*.py")):
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and (
                node.name.startswith("test_")
            ):
                markers = [m for d in node.decorator_list if (m := _marker(d))]
                found.append((path.relative_to(root).as_posix(), node.name, markers))
    return found


def unbound(keys: set[str], tests: list[Test]) -> list[str]:
    """Return every key no `spec` marker names, sorted."""
    named = {arg for _, _, markers in tests for kind, arg in markers if kind == "spec"}
    return sorted(keys - named)


def unknown(keys: set[str], tests: list[Test]) -> list[str]:
    """Return every `spec` marker naming no key, as `file::test -> key`, sorted."""
    return sorted(
        f"{file}::{name} -> {arg}"
        for file, name, markers in tests
        for kind, arg in markers
        if kind == "spec" and arg is not None and arg not in keys
    )


def unmarked(tests: list[Test]) -> list[str]:
    """Return every test without exactly one readable marker, as `file::test`."""
    return sorted(
        f"{file}::{name}"
        for file, name, markers in tests
        if len(markers) != 1 or markers[0][1] is None
    )


@pytest.mark.spec_exempt("structural: every scenario key has a test")
def test_every_key_has_a_test() -> None:
    missing = unbound(spec_keys(REPO_ROOT), marked_tests(REPO_ROOT))
    assert not missing, f"keys no test names: {missing[:5]}"


@pytest.mark.spec_exempt("structural: every spec marker names a scenario key")
def test_every_marker_names_a_key() -> None:
    stray = unknown(spec_keys(REPO_ROOT), marked_tests(REPO_ROOT))
    assert not stray, f"markers naming no key: {stray[:5]}"


@pytest.mark.spec_exempt("structural: every test carries one marker")
def test_every_test_carries_one_marker() -> None:
    loose = unmarked(marked_tests(REPO_ROOT))
    assert not loose, f"tests without exactly one marker: {loose[:5]}"


_LIVING = """\
## Requirements

### Requirement: Kept
#### Scenario: kept
- **Key:** `cap:kept:kept`

### Requirement: Gone
#### Scenario: gone
- **Key:** `cap:gone:gone`
"""

_TESTS = """\
import pytest


@pytest.mark.spec("cap:kept:kept")
def test_kept():
    pass


@pytest.mark.spec("cap:gone:gone")
def test_gone():
    pass
"""


def _tree(root: Path, tests: str = _TESTS, delta: str | None = None) -> Path:
    """Write a spec, a test file and, if given, an active delta under `root`."""
    (root / "openspec" / "specs" / "cap").mkdir(parents=True)
    (root / "openspec" / "specs" / "cap" / "spec.md").write_text(_LIVING)
    (root / "tests").mkdir()
    (root / "tests" / "test_cap.py").write_text(tests)
    if delta is not None:
        spec = root / "openspec" / "changes" / "0001-x" / "specs" / "cap" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text(delta)
    return root


@pytest.mark.spec_exempt("structural: twin of test_every_key_has_a_test")
def test_a_key_with_no_test_is_caught(tmp_path: Path) -> None:
    root = _tree(tmp_path, _TESTS.replace('"cap:gone:gone"', '"cap:kept:kept"'))
    assert unbound(spec_keys(root), marked_tests(root)) == ["cap:gone:gone"]


@pytest.mark.spec_exempt("structural: twin of test_every_marker_names_a_key")
def test_a_marker_naming_no_key_is_caught(tmp_path: Path) -> None:
    root = _tree(tmp_path, _TESTS.replace("cap:gone:gone", "cap:gone:typo"))
    assert unknown(spec_keys(root), marked_tests(root)) == [
        "tests/test_cap.py::test_gone -> cap:gone:typo"
    ]


@pytest.mark.spec_exempt("structural: twin of test_every_test_carries_one_marker")
def test_a_test_with_no_marker_or_two_is_caught(tmp_path: Path) -> None:
    tests = (
        _TESTS.replace('@pytest.mark.spec("cap:kept:kept")\n', "")
        + '\n\n@pytest.mark.spec("cap:kept:kept")\n'
        + '@pytest.mark.spec_exempt("structural")\ndef test_both():\n    pass\n'
        + '\n\nKEY = "cap:kept:kept"\n\n\n@pytest.mark.spec(KEY)\n'
        + "def test_built():\n    pass\n"
    )
    root = _tree(tmp_path, tests)
    assert unmarked(marked_tests(root)) == [
        "tests/test_cap.py::test_both",
        "tests/test_cap.py::test_built",
        "tests/test_cap.py::test_kept",
    ]


@pytest.mark.spec_exempt("structural: twin of the active deltas' keys, per 0045 D2")
def test_an_added_key_is_demanded_and_a_removed_one_is_not(tmp_path: Path) -> None:
    delta = """\
## ADDED Requirements

### Requirement: New
#### Scenario: new
- **Key:** `cap:new:new`

## REMOVED Requirements

### Requirement: Gone
**Reason**: replaced.
"""
    root = _tree(
        tmp_path, _TESTS.replace('@pytest.mark.spec("cap:gone:gone")\n', ""), delta
    )
    assert spec_keys(root) == {"cap:kept:kept", "cap:new:new"}
    assert unbound(spec_keys(root), marked_tests(root)) == ["cap:new:new"]
    archived = root / "openspec" / "changes" / "archive" / "0000-y" / "specs" / "cap"
    archived.mkdir(parents=True)
    (archived / "spec.md").write_text(delta.replace("cap:new:new", "cap:old:old"))
    assert "cap:old:old" not in spec_keys(root)
