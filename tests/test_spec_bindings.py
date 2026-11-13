"""Every spec↔test binding, held by the gate.

Each living key has a test, each `spec` marker names a key the living spec or an
open delta holds, and each test carries one or more `spec` markers or one
`spec_exempt`. Keys are read with a regex, markers with `ast`: no marker is built
at runtime. A vitest test under `ui/src/` binds through `spec("<key>", …)` or
`spec(["<key>", …], …)`, read with a regex.
"""

import ast
import re
from pathlib import Path

import pytest

from tests.specs import effective, write_tree

REPO_ROOT = Path(__file__).resolve().parent.parent

_KEY = re.compile(r"^- \*\*Key:\*\* `([^`]+)`", re.M)
_SCENARIO = re.compile(r"^#### Scenario: (.*)$", re.M)
_LAYERS_LINE = re.compile(r"^- \*\*Layers:\*\* (.*)$", re.M)
LAYERS = ("unit", "e2e")
E2E_DIR = "tests/e2e/"
_MARKERS = ("spec", "spec_exempt")
_SKIPS = ("skip", "skipif")
_STRUCTURAL = "structural: "
_TWIN_OF = "twin of "
_LITERAL = r"(['\"])([^'\"\n]+)\1"
_VITEST_SPEC = re.compile(rf"\bspec\(\s*(?:{_LITERAL}\s*,|\[([^\]]*)\]\s*,)?")
_VITEST_ITEM = re.compile(_LITERAL)
# A test declared past `spec` binds nothing: vitest's own `test`, `it` and their
# modifiers, at the start of a line.
_VITEST_BARE = re.compile(r"^\s*(?:test|it)(?:\.\w+)*\(", re.M)

Marker = tuple[str, str | None]
Test = tuple[str, str, list[Marker]]
Scenario = tuple[str, str, str | None, str | None]


def spec_keys(root: Path) -> set[str]:
    """Return the living spec's keys, as the active changes' deltas leave them."""
    return {
        key
        for _, reqs in effective(root).values()
        for body in reqs.values()
        for key in _KEY.findall(body)
    }


def living_keys(root: Path) -> set[str]:
    """Return the keys in `openspec/specs/` alone, before any delta applies."""
    return {
        key
        for path in sorted((root / "openspec" / "specs").glob("*/spec.md"))
        for key in _KEY.findall(path.read_text())
    }


def demanded(root: Path) -> set[str]:
    """Return the keys a test must name: the living ones no active delta removes.

    A key only an open delta adds may be named but is not demanded, so a cut
    that adds a scenario stays green until its build writes the test.
    """
    return spec_keys(root) & living_keys(root)


def nameable(root: Path) -> set[str]:
    """Return the keys a marker may name: the living ones, and the active deltas'."""
    return spec_keys(root) | living_keys(root)


def _names_marker(node: ast.AST, names: tuple[str, ...] = _MARKERS) -> bool:
    """Return whether `node` is `<x>.mark.<name>` for one of `names`.

    e.g. `pytest.mark.spec` -> True for the default names `spec` and `spec_exempt`.
    """
    return (
        isinstance(node, ast.Attribute)
        and node.attr in names
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


def _vitest_markers(match: re.Match[str]) -> list[Marker]:
    """Return a `spec(` call's keys as markers, one None for any not a string literal.

    e.g. `spec(['a:b:c', "d:e:f"], …)` -> [("spec", "a:b:c"), ("spec", "d:e:f")].
    """
    if match.group(2):
        return [("spec", match.group(2))]
    items = [item.strip() for item in (match.group(3) or "").split(",")]
    literals = [_VITEST_ITEM.fullmatch(item) for item in items if item]
    if not literals or not all(literals):
        return [("spec", None)]
    return [("spec", m.group(2)) for m in literals if m]


def vitest_tests(root: Path) -> list[Test]:
    """Return each vitest test under `ui/src/` with its binding, as `marked_tests` does.

    e.g. `spec("a:b:c", …)` on line 7 of `ui/src/x.test.ts`
    -> ("ui/src/x.test.ts", "line 7", [("spec", "a:b:c")]).
    A key that is not a string literal reads as None, and so does a bare `test(`.
    """
    found: list[Test] = []
    for path in sorted((root / "ui" / "src").rglob("*.test.ts")):
        file, text = path.relative_to(root).as_posix(), path.read_text()

        def line(at: int, text: str = text) -> str:
            return f"line {text.count(chr(10), 0, at) + 1}"

        found += [
            (file, line(m.start()), _vitest_markers(m))
            for m in _VITEST_SPEC.finditer(text)
        ]
        found += [(file, line(m.end()), []) for m in _VITEST_BARE.finditer(text)]
    return found


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
    """Return every test without its `spec` keys or one `spec_exempt`, as `file::test`.

    That is a test with no marker, a marker not read, `spec_exempt` beside another,
    or a `spec_exempt` whose reason is blank.
    """
    return sorted(
        f"{file}::{name}"
        for file, name, markers in tests
        if not markers
        or any(arg is None for _, arg in markers)
        or (len(markers) > 1 and any(kind == "spec_exempt" for kind, _ in markers))
        or any(
            kind == "spec_exempt" and not (arg or "").strip() for kind, arg in markers
        )
    )


def scenarios(root: Path) -> list[Scenario]:
    """Return each scenario of the effective spec as (capability, title, key, layers).

    e.g. a block holding `- **Key:** `a:b:c`` and `- **Layers:** unit`
    -> ("a", "the title", "a:b:c", "unit"). A line the block lacks reads as None.
    """
    found: list[Scenario] = []
    for capability, (_, reqs) in effective(root).items():
        for body in reqs.values():
            parts = _SCENARIO.split(body)
            for title, block in zip(parts[1::2], parts[2::2], strict=True):
                key, layers = _KEY.search(block), _LAYERS_LINE.search(block)
                found.append(
                    (
                        capability,
                        title.strip(),
                        key.group(1) if key else None,
                        layers.group(1).strip() if layers else None,
                    )
                )
    return found


def scenario_faults(root: Path) -> list[str]:
    """Return each scenario with no key, no layers, or a layers value off the list.

    e.g. `- **Layers:** both` -> "cap: the title: Layers `both` is not unit or e2e".
    """
    faults: list[str] = []
    for capability, title, key, layers in scenarios(root):
        at = f"{capability}: {title}"
        if key is None:
            faults.append(f"{at}: no Key")
        if layers is None:
            faults.append(f"{at}: no Layers")
        elif layers not in LAYERS:
            faults.append(f"{at}: Layers `{layers}` is not unit or e2e")
    return sorted(faults)


def layer_faults(root: Path, tests: list[Test]) -> list[str]:
    """Return each demanded key with no binder on its layer, as `key (layer)`.

    An `e2e` key needs a binder under `tests/e2e/`, a `unit` key one outside it.
    A vitest binder is outside. A caller passes the tests that run, via `running`.
    """
    layers = {
        key: layer for _, _, key, layer in scenarios(root) if key and layer in LAYERS
    }
    bound = {
        (arg, file.startswith(E2E_DIR))
        for file, _, markers in tests
        for kind, arg in markers
        if kind == "spec" and arg
    }
    return sorted(
        f"{key} ({layer})"
        for key in demanded(root)
        if (layer := layers.get(key)) and (key, layer == "e2e") not in bound
    )


def _pytestmark_skips(body: list[ast.stmt]) -> bool:
    """Return whether `body` assigns a `pytestmark` holding a `skip` or `skipif` mark.

    e.g. `pytestmark = [pytest.mark.slow, pytest.mark.skip(reason="x")]` -> True.
    """
    return any(
        isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in node.targets)
        and any(_names_marker(n, _SKIPS) for n in ast.walk(node.value))
        for node in body
    )


def _skipped_in(
    body: list[ast.stmt], prefix: str = "", inherited: bool = False
) -> set[str]:
    """Return each test id in `body` a skip marks, its own or one it inherits.

    A skip on a `Test*` class or in a `pytestmark` of the class or the module
    disables every test beneath it, as pytest does.
    """
    skips = inherited or _pytestmark_skips(body)
    found: set[str] = set()
    for node in body:
        if not isinstance(node, Function | ast.ClassDef):
            continue
        skips_here = skips or any(
            _names_marker(_target(d), _SKIPS) for d in node.decorator_list
        )
        if isinstance(node, Function) and node.name.startswith("test_"):
            if skips_here:
                found.add(prefix + node.name)
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            found |= _skipped_in(node.body, f"{prefix}{node.name}::", skips_here)
    return found


def skipped(root: Path) -> set[tuple[str, str]]:
    """Return each collected test a skip disables, as (file, test).

    A `skip` or `skipif` on the test, on a `Test*` class around it, or in a
    `pytestmark` of its class or module. e.g. `@pytest.mark.skipif(cond, reason="x")
    def test_y` in `tests/test_z.py` -> ("tests/test_z.py", "test_y").
    """
    return {
        (file, name)
        for file, module in _modules(root)
        for name in _skipped_in(module.body)
    }


def running(tests: list[Test], skipped: set[tuple[str, str]]) -> list[Test]:
    """Return `tests` less each one in `skipped`, the tests that run."""
    return [t for t in tests if (t[0], t[1]) not in skipped]


def rests_on_skips(
    keys: set[str], tests: list[Test], skipped: set[tuple[str, str]]
) -> list[str]:
    """Return every key whose binders are all in `skipped`, sorted.

    A key no test names is `unbound`'s, not this one's.
    """
    binders: dict[str, list[bool]] = {}
    for file, name, markers in tests:
        for kind, arg in markers:
            if kind == "spec" and arg is not None and arg in keys:
                binders.setdefault(arg, []).append((file, name) in skipped)
    return sorted(key for key, each in binders.items() if all(each))


def _reason_fault(reason: str, known: set[str]) -> str | None:
    """Return why `reason` is off both forms, or None when it is one of them."""
    if not reason.startswith(_STRUCTURAL):
        return f"`{reason}` does not begin `{_STRUCTURAL}`"
    rule = reason.removeprefix(_STRUCTURAL).strip()
    if not rule:
        return "no rule after `structural:`"
    if not rule.startswith(("twin", "the twin")):
        return None
    if not rule.startswith(_TWIN_OF):
        return f"`{reason}` is a twin that does not read `twin of <test>`"
    absent = [t for t in rule.removeprefix(_TWIN_OF).split(" and ") if t not in known]
    return f"names no collected test: {absent}" if absent else None


def reason_faults(tests: list[Test]) -> list[str]:
    """Return each `spec_exempt` reason off both forms, as `file::test: why`, sorted.

    A reason opens `structural: `, then a rule that does not open with `twin`, or
    `twin of` and each test it names, joined by `and`, each collected under `tests/`.
    """
    known = {name.rsplit("::", 1)[-1] for _, name, _ in tests}
    faults = (
        (file, name, _reason_fault(reason, known))
        for file, name, markers in tests
        for kind, reason in markers
        if kind == "spec_exempt" and reason is not None
    )
    return sorted(f"{file}::{name}: {why}" for file, name, why in faults if why)


# Behaviour tests exempt as structural, each with the scenario it waits for. A row
# goes when its test is bound or gone; the table never grows past its ceiling.
_EDIT_REQUEST = "edit · An edit request is made from a render and its composite"
_EDIT_REFUSED = "edit · A request the composite cannot support is refused"
_EDIT_SESSION = "edit · A render session runs every pending edit"
_RENDER_RECORD = (
    "cli · A render session writes its record into the collection, "
    "from its start to its end"
)
_NONE_FITS = "no requirement fits"
BEHAVIOUR_EXEMPT = {
    "tests/test_edit.py::"
    "test_edit_derive_the_ink_is_the_composite_divided_by_the_render": _EDIT_REQUEST,
    "tests/test_edit.py::"
    "test_edit_derive_darkness_follows_the_darkest_channel": _EDIT_REQUEST,
    "tests/test_edit.py::"
    "test_edit_derive_the_mask_covers_the_ink_and_reaches_past_its_edge": _EDIT_REQUEST,
    "tests/test_edit.py::"
    "test_edit_derive_a_feather_of_nothing_leaves_a_hard_edge": _EDIT_REQUEST,
    "tests/test_edit.py::"
    "test_edit_derive_the_control_is_darkness_times_the_gain_clipped": _EDIT_REQUEST,
    "tests/test_edit.py::test_edit_derive_a_png_decodes_to_the_pixels_it_holds": (
        _NONE_FITS
    ),
    "tests/test_edit.py::"
    "test_edit_refuse_a_composite_that_does_not_decode_names_the_export": (
        _EDIT_REFUSED
    ),
    "tests/test_edit.py::"
    "test_edit_crop_the_sampling_size_is_a_multiple_of_eight_on_its_long_side": (
        "edit · The crop is the tattoo's own, widened and grown by two guards"
    ),
    "tests/test_edit.py::"
    "test_edit_request_a_composite_that_is_missing_is_refused_and_writes_nothing": (
        _EDIT_REFUSED
    ),
    "tests/test_edit.py::"
    "test_edit_request_a_source_that_is_no_render_is_refused": _EDIT_REQUEST,
    "tests/test_edit.py::"
    "test_edit_verb_an_untracked_edit_is_refused_naming_the_tracked_ones": (
        "edit · An edit is one flat directory, pinned by its digest"
    ),
    "tests/test_edit.py::"
    "test_edit_sample_pending_lists_the_requests_with_no_image_in_chain_order": (
        _EDIT_SESSION
    ),
    "tests/test_edit.py::"
    "test_edit_stitch_an_answer_that_is_no_image_is_refused": _EDIT_SESSION,
    "tests/test_edit.py::"
    "test_edit_pending_progress_json_prints_a_line_per_sampled_edit": _NONE_FITS,
    "tests/test_edit_placement.py::"
    "test_placement_request_writes_in_the_order_a_request_is_read": (
        "tattoo · A bake writes the edit request and its placement record"
    ),
    "tests/test_edit_session.py::"
    "test_edit_group_a_group_holding_an_edits_file_is_no_group_of_failure_records": (
        "edit · A discard takes edits"
    ),
    "tests/test_render.py::test_a_dependent_before_its_source_is_refused_naming_both": (
        "cli · A render session's limit is estimated from its work"
    ),
    "tests/test_render.py::"
    "test_a_request_of_another_shape_is_refused_into_the_log": _NONE_FITS,
    "tests/test_render.py::"
    "test_a_lost_create_exits_3_and_a_failed_teardown_names_gpunit_down": (
        _RENDER_RECORD
    ),
    "tests/test_render.py::"
    "test_a_failed_body_is_named_beside_a_failed_teardown": _RENDER_RECORD,
    "tests/test_render.py::"
    "test_bake_quote_every_root_asked_has_its_edits_and_the_bakes_add_up": (
        "edit · An edit's time is estimated from its work"
    ),
}
BEHAVIOUR_CEILING = 21


def behaviour_faults(
    tests: list[Test], table: dict[str, str], ceiling: int
) -> list[str]:
    """Return each stale row of `table`, and the table itself when past `ceiling`.

    A row is stale when its test is gone or carries a `spec` marker.

    e.g. a row `tests/a.py::test_b` whose test carries a `spec` marker
    -> "tests/a.py::test_b: bound to a key".
    """
    marked = {f"{file}::{name}": markers for file, name, markers in tests}
    faults = [
        f"{row}: no such test" if row not in marked else f"{row}: bound to a key"
        for row in table
        if row not in marked or any(kind == "spec" for kind, _ in marked[row])
    ]
    if len(table) > ceiling:
        faults.append(f"the table holds {len(table)} rows, past its ceiling {ceiling}")
    return sorted(faults)


@pytest.fixture(scope="module")
def keys() -> set[str]:
    """Read the repository's nameable keys once for the module."""
    return nameable(REPO_ROOT)


@pytest.fixture(scope="module")
def required() -> set[str]:
    """Read the repository's demanded keys once for the module."""
    return demanded(REPO_ROOT)


@pytest.fixture(scope="module")
def tests() -> list[Test]:
    """Parse the repository's tests, pytest's and vitest's, once for the module."""
    return marked_tests(REPO_ROOT) + vitest_tests(REPO_ROOT)


@pytest.mark.spec_exempt("structural: every living key has a test")
def test_every_key_has_a_test(required: set[str], tests: list[Test]) -> None:
    missing = unbound(required, tests)
    assert not missing, f"keys no test names: {missing[:5]}"


@pytest.mark.spec_exempt("structural: every spec marker names a scenario key")
def test_every_marker_names_a_key(keys: set[str], tests: list[Test]) -> None:
    stray = unknown(keys, tests)
    assert not stray, f"markers naming no key: {stray[:5]}"


@pytest.mark.spec_exempt("structural: every test carries its keys or its exemption")
def test_every_test_carries_its_keys_or_its_exemption(tests: list[Test]) -> None:
    loose = unmarked(tests)
    assert not loose, f"tests without their keys or one exemption: {loose[:5]}"


@pytest.mark.spec_exempt("structural: no spec marker sits where none is read")
def test_no_marker_sits_where_none_is_read() -> None:
    loose = stray(REPO_ROOT)
    assert not loose, f"spec markers off a test's decorators: {loose[:5]}"


@pytest.mark.spec_exempt("structural: every scenario names its key and its layer")
def test_every_scenario_names_its_key_and_its_layer() -> None:
    faults = scenario_faults(REPO_ROOT)
    assert not faults, f"scenarios without their key or layer: {faults[:5]}"


@pytest.mark.spec_exempt("structural: every key has a test on its own layer")
def test_every_key_has_a_test_on_its_layer(tests: list[Test]) -> None:
    faults = layer_faults(REPO_ROOT, running(tests, skipped(REPO_ROOT)))
    assert not faults, f"keys with no running test on their layer: {faults[:5]}"


@pytest.mark.spec_exempt("structural: no key rests on skipped tests alone")
def test_no_key_rests_only_on_skipped_tests(
    required: set[str], tests: list[Test]
) -> None:
    loose = rests_on_skips(required, tests, skipped(REPO_ROOT))
    assert not loose, f"keys whose every test a decorator skips: {loose[:5]}"


@pytest.mark.spec_exempt("structural: every exemption reason is a rule or a twin")
def test_every_exemption_reason_is_a_rule_or_a_twin_of_a_test(
    tests: list[Test],
) -> None:
    faults = reason_faults(tests)
    assert not faults, f"exemption reasons off both forms: {faults[:5]}"


@pytest.mark.spec_exempt("structural: the behaviour exemptions only shrink")
def test_the_behaviour_exemptions_only_shrink(tests: list[Test]) -> None:
    faults = behaviour_faults(tests, BEHAVIOUR_EXEMPT, BEHAVIOUR_CEILING)
    assert not faults, f"behaviour exemptions that grew or went stale: {faults[:5]}"


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
    write_tree(root, _LIVING, delta)
    (root / "tests").mkdir()
    (root / "tests" / "test_cap.py").write_text(tests)
    return root


@pytest.mark.spec_exempt("structural: twin of test_every_key_has_a_test")
def test_a_key_with_no_test_is_caught(tmp_path: Path) -> None:
    root = _tree(tmp_path, _TESTS.replace('"cap:gone:gone"', '"cap:kept:kept"'))
    assert unbound(demanded(root), marked_tests(root)) == ["cap:gone:gone"]


@pytest.mark.spec_exempt("structural: twin of test_every_marker_names_a_key")
def test_a_marker_naming_no_key_is_caught(tmp_path: Path) -> None:
    root = _tree(tmp_path, _TESTS.replace("cap:gone:gone", "cap:gone:typo"))
    assert unknown(nameable(root), marked_tests(root)) == [
        "tests/test_cap.py::test_gone -> cap:gone:typo"
    ]


@pytest.mark.spec_exempt("structural: twin of test_every_marker_names_a_key")
def test_a_marker_on_a_removed_key_is_not_stray(tmp_path: Path) -> None:
    removed = """\
## REMOVED Requirements

### Requirement: Gone
**Reason**: replaced.
"""
    root = _tree(tmp_path / "a", delta=removed)
    assert unknown(nameable(root), marked_tests(root)) == []
    assert unknown(spec_keys(root), marked_tests(root)) == [
        "tests/test_cap.py::test_gone -> cap:gone:gone"
    ]
    nowhere = _tree(tmp_path / "b", _TESTS.replace("cap:gone:gone", "cap:nowhere:x"))
    assert unknown(nameable(nowhere), marked_tests(nowhere)) == [
        "tests/test_cap.py::test_gone -> cap:nowhere:x"
    ]


@pytest.mark.spec_exempt(
    "structural: twin of test_every_test_carries_its_keys_or_its_exemption"
)
def test_a_test_with_no_marker_or_an_exemption_beside_another_is_caught(
    tmp_path: Path,
) -> None:
    tests = """\
import pytest

KEY = "cap:kept:kept"


def test_kept():
    pass


@pytest.mark.spec("cap:gone:gone")
def test_gone():
    pass


@pytest.mark.spec("cap:kept:kept")
@pytest.mark.spec("cap:gone:gone")
def test_two_keys():
    pass


@pytest.mark.spec("cap:kept:kept")
@pytest.mark.spec_exempt("structural")
def test_both():
    pass


@pytest.mark.spec_exempt("structural")
@pytest.mark.spec_exempt("structural")
def test_two_exemptions():
    pass


@pytest.mark.spec("cap:gone:gone")
@pytest.mark.spec(KEY)
def test_built():
    pass
"""
    root = _tree(tmp_path, tests)
    assert unmarked(marked_tests(root)) == [
        "tests/test_cap.py::test_both",
        "tests/test_cap.py::test_built",
        "tests/test_cap.py::test_kept",
        "tests/test_cap.py::test_two_exemptions",
    ]


@pytest.mark.spec_exempt("structural: the active deltas' keys")
def test_an_added_key_is_known_and_neither_it_nor_a_removed_one_is_demanded(
    tmp_path: Path,
) -> None:
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
    assert unbound(demanded(root), marked_tests(root)) == []
    assert unknown(nameable(root), marked_tests(root)) == []
    archived = root / "openspec" / "changes" / "archive" / "0000-y" / "specs" / "cap"
    archived.mkdir(parents=True)
    (archived / "spec.md").write_text(delta.replace("cap:new:new", "cap:old:old"))
    assert "cap:old:old" not in spec_keys(root)


@pytest.mark.spec_exempt(
    "structural: twin of test_every_test_carries_its_keys_or_its_exemption"
)
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


@pytest.mark.spec_exempt("structural: the active deltas' keys")
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


@pytest.mark.spec_exempt("structural: the active deltas' keys")
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


_VITEST = """\
import { spec } from '../test/spec'

spec('cap:kept:kept', () => {})

spec("cap:gone:typo", async () => {})

spec(KEY, () => {})

test('bare', () => {})

spec(['cap:kept:kept', "cap:gone:gone"], () => {})

spec(['cap:kept:kept', KEY], () => {})
"""


@pytest.mark.spec_exempt("structural: twin of test_every_marker_names_a_key")
def test_a_vitest_key_with_no_living_key_is_caught(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    (root / "ui" / "src" / "composables").mkdir(parents=True)
    (root / "ui" / "src" / "composables" / "x.test.ts").write_text(_VITEST)
    found = vitest_tests(root)
    assert unknown(nameable(root), found) == [
        "ui/src/composables/x.test.ts::line 5 -> cap:gone:typo"
    ]
    assert unbound({"cap:kept:kept", "cap:gone:gone"}, found) == []
    assert [markers for _, at, markers in found if at == "line 11"] == [
        [("spec", "cap:kept:kept"), ("spec", "cap:gone:gone")]
    ]
    assert unmarked(found) == [
        "ui/src/composables/x.test.ts::line 13",
        "ui/src/composables/x.test.ts::line 7",
        "ui/src/composables/x.test.ts::line 9",
    ]


_LAYERED = """\
## Requirements

### Requirement: Shown
#### Scenario: no key
- **Layers:** unit

#### Scenario: no layers
- **Key:** `cap:shown:no-layers`

#### Scenario: both layers
- **Key:** `cap:shown:both-layers`
- **Layers:** both

#### Scenario: whole
- **Key:** `cap:shown:whole`
- **Layers:** e2e
"""


@pytest.mark.spec_exempt(
    "structural: twin of test_every_scenario_names_its_key_and_its_layer"
)
def test_a_scenario_without_its_key_or_layer_is_caught(tmp_path: Path) -> None:
    root = write_tree(tmp_path, _LAYERED)
    assert scenario_faults(root) == [
        "cap: both layers: Layers `both` is not unit or e2e",
        "cap: no key: no Key",
        "cap: no layers: no Layers",
    ]
    assert scenarios(root)[-1] == ("cap", "whole", "cap:shown:whole", "e2e")


_BY_LAYER = """\
## Requirements

### Requirement: Shown
#### Scenario: page
- **Key:** `cap:shown:page`
- **Layers:** e2e

#### Scenario: rule
- **Key:** `cap:shown:rule`
- **Layers:** unit

#### Scenario: placed
- **Key:** `cap:shown:placed`
- **Layers:** unit
"""

_BOUND = """\
import pytest


@pytest.mark.spec("{key}")
def test_{name}():
    pass
"""


_SKIPPED_PAGE = """\
import pytest


@pytest.mark.spec("cap:shown:page")
@pytest.mark.skip(reason="disabled")
def test_page():
    pass
"""


@pytest.mark.spec_exempt("structural: twin of test_every_key_has_a_test_on_its_layer")
def test_a_key_whose_only_test_is_on_the_other_layer_is_caught(tmp_path: Path) -> None:
    root = write_tree(tmp_path, _BY_LAYER)
    (root / "tests" / "e2e").mkdir(parents=True)
    for file, key, name in (
        ("test_page.py", "cap:shown:page", "page"),
        ("e2e/test_rule.py", "cap:shown:rule", "rule"),
        ("test_placed.py", "cap:shown:placed", "placed"),
    ):
        (root / "tests" / file).write_text(_BOUND.format(key=key, name=name))
    assert layer_faults(root, marked_tests(root)) == [
        "cap:shown:page (e2e)",
        "cap:shown:rule (unit)",
    ]
    # A skipped binder on the right layer beside a running one on the wrong layer.
    masked = write_tree(tmp_path / "masked", _BY_LAYER)
    (masked / "tests" / "e2e").mkdir(parents=True)
    (masked / "tests" / "e2e" / "test_page.py").write_text(_SKIPPED_PAGE)
    (masked / "tests" / "test_unit.py").write_text(
        _BOUND.format(key="cap:shown:page", name="unit")
    )
    (masked / "tests" / "test_rule.py").write_text(
        _BOUND.format(key="cap:shown:rule", name="rule")
    )
    (masked / "tests" / "test_placed.py").write_text(
        _BOUND.format(key="cap:shown:placed", name="placed")
    )
    assert layer_faults(masked, running(marked_tests(masked), skipped(masked))) == [
        "cap:shown:page (e2e)"
    ]


_SKIPS_TREE = """\
import pytest


@pytest.mark.spec("cap:kept:kept")
@pytest.mark.skipif(True, reason="never runs")
def test_kept_skipped():
    pass


@pytest.mark.spec("cap:gone:gone")
@pytest.mark.skipif(True, reason="never runs")
def test_gone_skipped():
    pass


@pytest.mark.spec("cap:gone:gone")
def test_gone_runs():
    pass
"""


_CLASS_SKIP = """\
import pytest


@pytest.mark.skip(reason="disabled")
class TestPage:
    @pytest.mark.spec("cap:kept:kept")
    def test_kept(self):
        pass


@pytest.mark.spec("cap:gone:gone")
def test_gone_runs():
    pass
"""

_MODULE_SKIP = """\
import pytest

pytestmark = pytest.mark.skip(reason="disabled")


@pytest.mark.spec("cap:kept:kept")
def test_kept():
    pass
"""

_MODULE_LIST_SKIP = """\
import pytest

pytestmark = [pytest.mark.slow, pytest.mark.skipif(True, reason="disabled")]


@pytest.mark.spec("cap:kept:kept")
def test_kept():
    pass
"""

_NESTED_SKIP = """\
import pytest


class TestOuter:
    pytestmark = pytest.mark.skip(reason="disabled")

    class TestInner:
        @pytest.mark.spec("cap:kept:kept")
        def test_kept(self):
            pass
"""


@pytest.mark.spec_exempt("structural: twin of test_no_key_rests_only_on_skipped_tests")
def test_a_key_whose_every_test_is_skipped_is_caught(tmp_path: Path) -> None:
    root = _tree(tmp_path, _SKIPS_TREE)
    assert skipped(root) == {
        ("tests/test_cap.py", "test_kept_skipped"),
        ("tests/test_cap.py", "test_gone_skipped"),
    }
    assert rests_on_skips(demanded(root), marked_tests(root), skipped(root)) == [
        "cap:kept:kept"
    ]
    for inherited in (_CLASS_SKIP, _MODULE_SKIP, _MODULE_LIST_SKIP, _NESTED_SKIP):
        (root / "tests" / "test_cap.py").write_text(inherited)
        assert rests_on_skips(demanded(root), marked_tests(root), skipped(root)) == [
            "cap:kept:kept"
        ], inherited


@pytest.mark.spec_exempt(
    "structural: twin of test_every_test_carries_its_keys_or_its_exemption"
)
def test_a_blank_exemption_reason_is_caught(tmp_path: Path) -> None:
    tests = """\
import pytest


@pytest.mark.spec_exempt("  ")
def test_blank():
    pass
"""
    root = _tree(tmp_path, tests)
    assert unmarked(marked_tests(root)) == ["tests/test_cap.py::test_blank"]


@pytest.mark.spec_exempt(
    "structural: twin of test_every_exemption_reason_is_a_rule_or_a_twin_of_a_test"
)
def test_a_reason_off_both_forms_or_naming_no_test_is_caught(tmp_path: Path) -> None:
    tests = """\
import pytest


@pytest.mark.spec_exempt("x")
def test_bare():
    pass


@pytest.mark.spec_exempt("twin of test_here")
def test_unprefixed():
    pass


@pytest.mark.spec_exempt("structural: twin of test_nowhere")
def test_names_nothing():
    pass


@pytest.mark.spec_exempt("structural: ")
def test_blank():
    pass


@pytest.mark.spec_exempt("structural: twin of test_here and test_nowhere")
def test_names_one_of_two():
    pass


@pytest.mark.spec_exempt("structural: the rule alone")
def test_here():
    pass


@pytest.mark.spec_exempt("structural: twin of test_here and test_bare")
def test_names_two():
    pass
"""
    root = _tree(tmp_path, tests)
    assert reason_faults(marked_tests(root)) == [
        "tests/test_cap.py::test_bare: `x` does not begin `structural: `",
        "tests/test_cap.py::test_blank: no rule after `structural:`",
        "tests/test_cap.py::test_names_nothing: "
        "names no collected test: ['test_nowhere']",
        "tests/test_cap.py::test_names_one_of_two: "
        "names no collected test: ['test_nowhere']",
        "tests/test_cap.py::test_unprefixed: "
        "`twin of test_here` does not begin `structural: `",
    ]


@pytest.mark.spec_exempt(
    "structural: twin of test_the_behaviour_exemptions_only_shrink"
)
def test_a_stale_row_or_a_table_past_its_ceiling_is_caught(tmp_path: Path) -> None:
    tests = """\
import pytest


@pytest.mark.spec_exempt("structural: waits")
def test_waits():
    pass


@pytest.mark.spec("cap:kept:kept")
def test_bound():
    pass
"""
    found = marked_tests(_tree(tmp_path, tests))
    waits, bound, gone = (
        f"tests/test_cap.py::test_{n}" for n in ("waits", "bound", "gone")
    )
    assert behaviour_faults(found, {waits: "cap"}, 1) == []
    assert behaviour_faults(found, {waits: "cap", bound: "cap", gone: "cap"}, 3) == [
        f"{bound}: bound to a key",
        f"{gone}: no such test",
    ]
    assert behaviour_faults(found, {waits: "cap"}, 0) == [
        "the table holds 1 rows, past its ceiling 0"
    ]
