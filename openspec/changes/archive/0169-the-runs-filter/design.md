# The runs filter — design

The shared run listing gains a name predicate, and the library passes its separator test through it, so an unreadable folder that is no run no longer fails the hub. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`runs_in(root)` in `isekai/foundation/rundir.py` lists every child of a runs root whose `run.json` is a file. The library's `_runs` in `isekai/interface/ui/library.py` calls it, then keeps the runs whose id has the separator after the digest.

The probe comes first, and `Path.is_file` on Python 3.12.14, the pinned one, raises `PermissionError` for a folder it cannot enter. The server turns `Refusal` into an answer and nothing else, so a folder named `private` at mode `000` fails Home, the hub and `run_named`.

```
before 0165   _runs:  name test  ->  frame probe        private is dropped by its name
now           _runs:  frame probe -> name test          private is probed, and raises
this change   runs_in(named=test):  name test -> frame probe
```

The mutator ran over `isekai/foundation/rundir.py:154-162` with `tests/test_run_directory.py` at the cut, and no mutant survived: every mutant of those lines was killed.

## Goals / Non-Goals

- Goal: a folder whose name is no run's is never probed, on every Python.
- Goal: the library lists through the helper, with no private listing of its own.
- Non-goal: any change to what the other sites list. With `named` absent, `runs_in` is as it was.
- Non-goal: a folder that bears a run's name and cannot be read. It raises, as it did before the shared helper.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `runs_in(root, *, named=None)`: the predicate takes a child's name and runs ahead of the frame probe | the card's own fix; one keyword leaves every other call as it is | a second helper for the library; the library listing the folder itself |
| [D2](#d2) | `_runs` passes the separator test as `named` and drops its own filter | D65's rule stands, that a site lists through the helper | keeping the filter after the helper, where the probe has already run |
| [D3](#d3) | an unreadable folder named like a run stays an error, and `run_at` is untouched | it raised before the shared helper too; a catch in the helper changes what the other sites do | catching `OSError` in `runs_in` |
| [D4](#d4) | one scenario under the hub's requirement, `ui:hub:a-folder-that-is-no-run-is-ignored`, in a MODIFIED delta; no `skip_specs` | a behaviour fix must be required by an existing requirement, and the hub's says the rest of the grid is still shown | a new requirement |
| [D5](#d5) | the tests make the folder unreadable with a real `chmod(0o000)`, restored in `finally`; no patch of `is_file`, no skip for root | the tattoo library's test does the same; a patch would hold the mock, not the order | patching `Path.is_file` |
| [D6](#d6) | D65 is amended, and no decision is added | the rule itself stands; its *Why* names the library's filter | a new decision |
| [D7](#d7) | the mutator over `runs_in`'s lines as phase 1 leaves them | `CONTRIBUTING.md`'s pre-flight, over a single range | a range read from the cut's base |

### D1

`runs_in` is written exactly as below, so that it starts at line 154 of `rundir.py` and ends at line 165, which phase 1's closing run reads.
The import line becomes `from collections.abc import Callable, Mapping`. `named` is keyword-only and takes a child's name; with `None` every child is probed.

```python
def runs_in(root: Path, *, named: Callable[[str], bool] | None = None) -> list[Run]:
    """Return the runs under `root`, by id; a root that is no directory holds none.

    With `named`, a child whose name it rejects is left out before its frame is probed.
    """
    if not root.is_dir():
        return []
    return [
        Run(path.name, path)
        for path in sorted(root.iterdir())
        if (named is None or named(path.name)) and (path / FRAME_NAME).is_file()
    ]
```

The order of the name test and the frame probe is the fix: `and` short-circuits, so a rejected name never reaches `is_file`.

### D2

`_runs` becomes the text below. The other sites call `runs_in(root)` and are not edited: `run_ids` in `isekai/interface/render.py`, the compare page's `_runs` in `isekai/interface/compare_view.py`, the CLI's listing in `isekai/interface/cli.py`, and the verbs' lookups in `isekai/interface/verbs/common.py`, which call `run_at`.

```python
def _runs(runs: Path) -> dict[str, Run]:
    """Return the runs under `runs` that hold a frame, by their identifier's digest."""
    return {
        run.id[:ID_DIGEST_CHARS]: run
        for run in runs_in(
            runs, named=lambda name: name[ID_DIGEST_CHARS:].startswith(ID_SEPARATOR)
        )
    }
```

`ID_DIGEST_CHARS` and `ID_SEPARATOR` stay imported in `library.py`: the lambda and the key read them. The file's ratchet row in `tests/test_ratchets.py` is a listed offender, which may grow, and stays.

### D3

A folder named `<digest>-<name>` that holds an unreadable `run.json`, or cannot be entered, still raises `PermissionError`. That matches the code before the shared helper existed, and the debt card asks for no more. Python 3.14's `is_file` swallows the error, which settles it there.

### D4

The delta carries the hub's requirement and each of its scenarios as they stand, and adds the scenario after *an unreadable run file marks its cell alone*. The scenario is one WHEN, one THEN and one AND, and no reasons. `ui:hub:a-folder-that-is-no-run-is-ignored` is bound by the hub's test of D5; `runs_in`'s cases keep their `structural:` exemption.

### D5

Each case is written before the line it holds, and each fails first: the helper's cases with `TypeError` (`named` is unknown), the hub's with `PermissionError` on the pinned Python as an ordinary user. The helper's first case holds the predicate on any Python, its second the order of the name test and the probe on the pinned one. Phase 1 adds these after `test_runs_in_holds_none_of_a_root_that_is_no_directory` in `tests/test_run_directory.py`:

```python
@pytest.mark.spec_exempt("structural: the one rule for which folder is a run")
def test_runs_in_leaves_out_a_framed_folder_its_name_predicate_rejects(
    tmp_path: Path,
) -> None:
    for name in ("abc123-ada", "private"):
        (tmp_path / name).mkdir()
        (tmp_path / name / FRAME_NAME).write_text("{}")

    found = runs_in(tmp_path, named=lambda name: "-" in name)

    assert [run.id for run in found] == ["abc123-ada"]


@pytest.mark.spec_exempt("structural: the one rule for which folder is a run")
def test_runs_in_does_not_probe_a_child_its_name_predicate_rejects(
    tmp_path: Path,
) -> None:
    (tmp_path / "abc123-ada").mkdir()
    (tmp_path / "abc123-ada" / FRAME_NAME).write_text("{}")
    private = tmp_path / "private"
    private.mkdir()
    private.chmod(0o000)
    try:
        found = runs_in(tmp_path, named=lambda name: "-" in name)
    finally:
        private.chmod(0o700)

    assert [run.id for run in found] == ["abc123-ada"]
```

Phase 2 adds this after `test_an_unreadable_run_file_marks_its_cell_alone` in `tests/test_ui_library.py`:

```python
@pytest.mark.spec("ui:hub:a-folder-that-is-no-run-is-ignored")
def test_a_folder_that_is_no_run_and_cannot_be_read_is_ignored(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    folder = _collection(tmp_path, "b", "ada.jpg")
    _approved(_run(folder, "ada.jpg"), vocabulary)
    private = folder / "runs" / "private"
    private.mkdir()
    private.chmod(0o000)
    try:
        grid = library.hub(folder, OFFERED, FLOWS_DIR)
    finally:
        private.chmod(0o700)

    assert [one.name for one in grid.sources] == ["ada.jpg"]
    assert grid.sources[0].cells[SUMMON].stage == "approved"
```

No existing test's assertion changes.

### D6

D65's *Why* ends `The library keeps its separator filter and its key over `runs_in`, so the hub is unchanged.` It becomes `The library passes its separator filter to `runs_in` as `named`, so a folder with another name is never probed, and keeps its key; the hub is unchanged.` Its *Made by* becomes `` `0165`, `0169` ``. The rule, its *Accepts* line and the foundation README's `rundir.py` row stand: the row names `runs_in` and `run_at`, and `named` is a parameter of the first.

### D7

Phase 1 closes with `uv run python -m tools.mutate isekai/foundation/rundir.py:154-165 --tests tests/test_run_directory.py`, the range D1 fixes.

Its mutants die as follows. Flipping `named is None` fails every case that passes no predicate. The outer `and` becoming `or` lets a framed rejected folder and a folder with no frame through. The call of `named` fails the first case.

A survivor gets a case in `tests/test_run_directory.py` that kills it, before the phase ends. A range the mutator refuses as holding no mutant is no survivor.

## Tests

The change adds unit tests and no browser test (`T1`): the predicate is a function of names, and the hub's grid is read from `library.hub`, so nothing needs a page. The helper's cases sit in the file of `runs_in`'s other cases (`T2`), and the hub's case beside the hub's other cases. No test is deleted or merged, so there is no `I16` table.

| layer | added | removed | the base count's command |
|---|---|---|---|
| unit, `runs_in` | the predicate case and the unreadable-child case, 6 → 8 | none | `git grep -c "^def test_runs_in_" -- tests/test_run_directory.py` prints `tests/test_run_directory.py:6` |
| unit, hub | the folder-that-is-no-run case, 27 → 28 | none | `git grep -c "^def test_" -- tests/test_ui_library.py` prints `tests/test_ui_library.py:27` |
| end-to-end | none, 0 tests × 0 engines | none | |

## Dependencies

None.

## Risks / Trade-offs

- A run as `root` reads a mode-`000` folder, so the helper's second case and the hub's case pass without the fix there. The first case holds the predicate on any Python and as any user, and CI runs as an ordinary user.
- The lambda's line sits close to the formatter's limit. A formatter that wraps it differently moves `library.py` by a line, which its ratchet row allows.
- The closing mutation run walks the whole of `tests/test_run_directory.py` for each mutant. The range is small, so the run stays well under the plan check's limit.

## Verdict

Ready to build. The change is `runs_in`, `_runs`, the helper's and the hub's cases and D65's text; each phase ends on a green `make check`, the last on a green gate.
