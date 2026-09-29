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
_FROM = re.compile(r"^- FROM: `### Requirement: (.*)`$", re.M)
_TO = re.compile(r"^- TO: `### Requirement: (.*)`$", re.M)
_MARKERS = ("spec", "spec_exempt")

Marker = tuple[str, str | None]
Test = tuple[str, str, list[Marker]]


def _split(heading: re.Pattern[str], text: str) -> dict[str, str]:
    """Return each heading's captured title, stripped, mapped to its body."""
    parts = heading.split(text)
    return {
        title.strip(): body
        for title, body in zip(parts[1::2], parts[2::2], strict=True)
    }


def _requirements(text: str) -> dict[str, set[str]]:
    """Return each requirement's title, mapped to the keys of its scenarios."""
    return {
        title: set(_KEY.findall(body))
        for title, body in _split(_REQUIREMENT, text).items()
    }


def spec_keys(root: Path) -> set[str]:
    """Return the living spec's keys, as the active changes' deltas leave them.

    Each delta applies in OpenSpec's order: a RENAMED requirement carries its keys
    to its new title, a REMOVED one drops them, a MODIFIED one replaces them, an
    ADDED one brings its own.
    """
    living = {
        path.parent.name: _requirements(path.read_text())
        for path in sorted((root / "openspec" / "specs").glob("*/spec.md"))
    }
    changes = root / "openspec" / "changes"
    # The glob's depth leaves out `archive/<id>/`: an archived delta is folded in.
    for delta in sorted(changes.glob("*/specs/*/spec.md")):
        reqs = living.setdefault(delta.parent.name, {})
        sections = _split(_SECTION, delta.read_text())
        renamed = sections.get("RENAMED Requirements", "")
        for old, new in zip(_FROM.findall(renamed), _TO.findall(renamed), strict=True):
            reqs[new.strip()] = reqs.pop(old.strip(), set())
        for title in _REQUIREMENT.findall(sections.get("REMOVED Requirements", "")):
            reqs.pop(title.strip(), None)
        for heading in ("MODIFIED Requirements", "ADDED Requirements"):
            reqs |= _requirements(sections.get(heading, ""))
    return {key for reqs in living.values() for held in reqs.values() for key in held}


def _names_marker(node: ast.Attribute) -> bool:
    """Return whether `node` is `<x>.mark.spec` or `<x>.mark.spec_exempt`."""
    return (
        node.attr in _MARKERS
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "mark"
    )


def _target(decorator: ast.expr) -> ast.expr:
    """Return a decorator's callee if it is a call, else the decorator itself."""
    return decorator.func if isinstance(decorator, ast.Call) else decorator


def _marker(decorator: ast.expr) -> Marker | None:
    """Return a `spec` or `spec_exempt` decorator as (name, argument), else None.

    An argument that is not one string literal reads as None, so `unmarked` fails it.
    """
    call = decorator if isinstance(decorator, ast.Call) else None
    target = _target(decorator)
    if not (isinstance(target, ast.Attribute) and _names_marker(target)):
        return None
    if call and len(call.args) == 1 and not call.keywords:
        (arg,) = call.args
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return target.attr, arg.value
    return target.attr, None


Function = ast.FunctionDef | ast.AsyncFunctionDef


def _collected(body: list[ast.stmt], prefix: str = "") -> list[tuple[str, Function]]:
    """Return each `test_` function pytest collects from `body`, by its test id.

    That is a top-level one, and a method of a `Test*` class, nested or not.
    """
    found: list[tuple[str, Function]] = []
    for node in body:
        if isinstance(node, Function) and node.name.startswith("test_"):
            found.append((prefix + node.name, node))
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            found += _collected(node.body, f"{prefix}{node.name}::")
    return found


def _modules(root: Path) -> list[tuple[str, ast.Module]]:
    """Return each test module under `tests/`, parsed, by its repo-relative path."""
    return [
        (path.relative_to(root).as_posix(), ast.parse(path.read_text()))
        for path in sorted((root / "tests").rglob("test_*.py"))
    ]


def marked_tests(root: Path) -> list[Test]:
    """Return each test pytest collects under `tests/` with its `spec*` markers.

    e.g. `@pytest.mark.spec("a:b:c") def test_x` in `tests/test_y.py`
    -> ("tests/test_y.py", "test_x", [("spec", "a:b:c")]).
    A method of a `Test*` class reads `TestZ::test_x`.
    """
    return [
        (file, name, [m for d in node.decorator_list if (m := _marker(d))])
        for file, module in _modules(root)
        for name, node in _collected(module.body)
    ]


def stray(root: Path) -> list[str]:
    """Return every `spec*` marker not on a collected test's decorators, as `file:line`.

    A module's `pytestmark`, a `pytest.param(marks=...)`, a class's decorator: each
    would bind a test this checker never reads.
    """
    found: list[str] = []
    for file, module in _modules(root):
        read = {
            id(_target(d))
            for _, node in _collected(module.body)
            for d in node.decorator_list
        }
        found += [
            f"{file}:{node.lineno}"
            for node in ast.walk(module)
            if isinstance(node, ast.Attribute)
            and _names_marker(node)
            and id(node) not in read
        ]
    return sorted(found)


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


@pytest.fixture(scope="module")
def keys() -> set[str]:
    """Read the repository's keys once for the module."""
    return spec_keys(REPO_ROOT)


@pytest.fixture(scope="module")
def tests() -> list[Test]:
    """Parse the repository's tests once for the module."""
    return marked_tests(REPO_ROOT)


@pytest.mark.spec_exempt("structural: every scenario key has a test")
def test_every_key_has_a_test(keys: set[str], tests: list[Test]) -> None:
    missing = unbound(keys, tests)
    assert not missing, f"keys no test names: {missing[:5]}"


@pytest.mark.spec_exempt("structural: every spec marker names a scenario key")
def test_every_marker_names_a_key(keys: set[str], tests: list[Test]) -> None:
    stray = unknown(keys, tests)
    assert not stray, f"markers naming no key: {stray[:5]}"


@pytest.mark.spec_exempt("structural: every test carries one marker")
def test_every_test_carries_one_marker(tests: list[Test]) -> None:
    loose = unmarked(tests)
    assert not loose, f"tests without exactly one marker: {loose[:5]}"


@pytest.mark.spec_exempt("structural: no spec marker sits where none is read")
def test_no_marker_sits_where_none_is_read() -> None:
    loose = stray(REPO_ROOT)
    assert not loose, f"spec markers off a test's decorators: {loose[:5]}"


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
    tests = """\
import pytest

KEY = "cap:kept:kept"


def test_kept():
    pass


@pytest.mark.spec("cap:gone:gone")
def test_gone():
    pass


@pytest.mark.spec("cap:kept:kept")
@pytest.mark.spec_exempt("structural")
def test_both():
    pass


@pytest.mark.spec(KEY)
def test_built():
    pass
"""
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


@pytest.mark.spec_exempt("structural: twin of test_every_test_carries_one_marker")
def test_a_test_inside_a_test_class_is_checked(tmp_path: Path) -> None:
    tests = """\
import pytest


class TestCap:
    def test_loose(self):
        pass

    @pytest.mark.spec("cap:kept:kept")
    def test_kept(self):
        pass

    class TestInner:
        def test_deep(self):
            pass


class Helper:
    def test_not_collected(self):
        pass
"""
    root = _tree(tmp_path, tests)
    assert unmarked(marked_tests(root)) == [
        "tests/test_cap.py::TestCap::TestInner::test_deep",
        "tests/test_cap.py::TestCap::test_loose",
    ]


@pytest.mark.spec_exempt("structural: twin of test_no_marker_sits_where_none_is_read")
def test_a_module_pytestmark_naming_a_spec_marker_is_caught(tmp_path: Path) -> None:
    tests = 'import pytest\n\npytestmark = pytest.mark.spec("cap:kept:kept")\n'
    assert stray(_tree(tmp_path, tests)) == ["tests/test_cap.py:3"]


@pytest.mark.spec_exempt("structural: twin of test_no_marker_sits_where_none_is_read")
def test_a_param_marks_naming_a_spec_marker_is_caught(tmp_path: Path) -> None:
    tests = """\
import pytest


@pytest.mark.parametrize(
    "x", [pytest.param(1, marks=pytest.mark.spec_exempt("structural"))]
)
@pytest.mark.spec("cap:kept:kept")
def test_kept(x):
    pass
"""
    assert stray(_tree(tmp_path, tests)) == ["tests/test_cap.py:5"]


@pytest.mark.spec_exempt("structural: twin of the active deltas' keys, per 0045 D2")
def test_a_modified_requirement_that_re_keys_a_scenario_drops_the_old_key(
    tmp_path: Path,
) -> None:
    delta = """\
## MODIFIED Requirements

### Requirement: Gone
#### Scenario: moved
- **Key:** `cap:gone:moved`
"""
    root = _tree(tmp_path, _TESTS.replace("cap:gone:gone", "cap:gone:moved"), delta)
    assert spec_keys(root) == {"cap:kept:kept", "cap:gone:moved"}
    assert unbound(spec_keys(root), marked_tests(root)) == []


@pytest.mark.spec_exempt("structural: twin of the active deltas' keys, per 0045 D2")
def test_a_renamed_requirement_keeps_its_keys_until_a_modified_one_re_keys_them(
    tmp_path: Path,
) -> None:
    renamed = """\
## RENAMED Requirements

- FROM: `### Requirement: Gone`
- TO: `### Requirement: Went`
"""
    assert spec_keys(_tree(tmp_path / "a", delta=renamed)) == {
        "cap:kept:kept",
        "cap:gone:gone",
    }
    re_keyed = f"""\
{renamed}
## MODIFIED Requirements

### Requirement: Went
#### Scenario: gone
- **Key:** `cap:went:gone`
"""
    assert spec_keys(_tree(tmp_path / "b", delta=re_keyed)) == {
        "cap:kept:kept",
        "cap:went:gone",
    }
