# The render ref — design

`RenderRef` and `EditRef` in `isekai/foundation/layout.py` are what `rendered_at` and `edit_at` return, and `version_of` reads a version off a name, with every answer unchanged. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`rendered_at(image)` in `isekai/foundation/run.py` returns `tuple[Run, str, int, int]`: the run, the flow, the approval's number and the seed. `edit_at(image)` in `isekai/foundation/layout.py` returns `tuple[Run, str, int, int, int]`: the same four and the edit's number. Callers read them by index, by slice, by star-unpack or by unpacking whole. Review's `Revision` is the four-tuple as an alias, and a route builds one by hand.

A version is read off an artifact's name by `int(<path>.name[:3])`, at sites that each wrote a name themselves. `isekai/foundation/run.py` re-exports every name of `layout.py` under `__all__` ([D62](../../../docs/decisions.md#d62--the-run-directory-is-runpy-its-siblings-imported-through-it)), and a module outside the foundation reads them from there. `rendered_at` stays in `run.py`, because it reads `stage_command`, which reads the patched `RUNS_ROOT`.

## Goals / Non-Goals

**Goals:**

- A named, flat, ordered type for what each function returns, so a caller reads a field by name.
- One function that reads the version an artifact's name spells.
- Behaviour unchanged: every ref holds what the tuple held, and no existing assertion changes.

**Non-Goals:**

- A signature that takes a ref, a method on a ref ([D4](#d4)).
- The folder climbs by `parents[n]`, the `int(group.name)` reads, the server's check of a seed, a version or a bake's number.
- The page's address types, a scenario, a spec delta.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `RenderRef(run, flow, version, seed)` and `EditRef(run, flow, version, seed, k)`, `NamedTuple`s in `layout.py`, re-exported by `run.py`; `rendered_at` and `edit_at` return them | flat and ordered as the tuples were, so each caller that unpacks, and `tests/test_edit.py`'s unpack, hold | a dataclass, which breaks every unpacking site; a `Revision` of its own beside the ref |
| [D2](#d2) | The sites that index, slice or star-unpack read by field name; review's `Revision` is `RenderRef`; the drafts route builds a `RenderRef` | the index is what a reader must know by heart; the alias keeps its importers | a new name for each importer; switching the sites that unpack whole, which read well already |
| [D3](#d3) | `version_of(path)` in `layout.py` reads `int(path.name[:3])`; the sites that slice call it | one place says how wide a version is; every input is a name the code wrote, so no answer changes | validating the name, which is new behaviour; a function of a name and not a path |
| [D4](#d4) | No signature takes a ref, the ref has no method, and the server's check of a seed in a path stays | the first edits many test calls and the routes cannot take one; the spec states no answer for a bad seed in a path | a ref as an argument; a method that builds a path |
| [D5](#d5) | Proof by the suite as it stands, a case for each type and for `version_of` written first, a mutation run over each slicing site before its switch and over the lines that still hold a mutant after, and one replay of the standing mutants (C15) | a rewrite is pre-flighted; `tools.mutate` refuses a line it finds no mutant in | a run over a line with no mutant, which exits 2 |
| [D6](#d6) | `skip_specs`, and the change adds one decision, D70, in `docs/decisions.md` | no requirement fits a type for a path; a home a later version reads is a decision | amending D69, which the names version amends |

### D1

`layout.py` gains, above `edit_at`:

```python
class RenderRef(NamedTuple):
    """The run, flow, approval and seed a render's image path names."""

    run: Run
    flow: str
    version: int
    seed: int


class EditRef(NamedTuple):
    """The run, flow, approval, seed and number an edit image's path names."""

    run: Run
    flow: str
    version: int
    seed: int
    k: int
```

`edit_at` returns `EditRef(Run(...), ..., int(named.group("k")))` in the order it returns the tuple now, and `rendered_at` returns `RenderRef(run, flow_directory.name, int(group.name), int(image.stem))`. `run.py` imports both from `layout.py` and lists them in `__all__`. The version is the approval's number, as `group_of` takes it, so the field is `version`. `layout.py` imports `NamedTuple` from `typing` and nothing else new.

### D2

Each site, read at the cut:

| site | reads today | after |
|---|---|---|
| `_located`, `isekai/pipeline/edit.py:105` | `edit_at(source)[3]` | `edit_at(source).seed` |
| `_located`, `edit.py:106` | `rendered_at(source)[3]` | `rendered_at(source).seed` |
| `request_placed`, `edit.py:225` | `edit_at(source)[4]` | `edit_at(source).k` |
| `discard_render`, `isekai/pipeline/generate.py:349` | `*_, seed = rendered_at(image)` | `seed = rendered_at(image).seed` |
| `run_discard`, `isekai/interface/verbs/drafts.py:63` | `run, flow, version = (edit_at if edited else rendered_at)(image)[:3]` | `ref = (edit_at if edited else rendered_at)(image)`, then `run, flow, version = ref.run, ref.flow, ref.version` |
| `Revision`, `isekai/pipeline/review.py:432` | `tuple[Run, str, int, int]` | `RenderRef` |
| `post_draft`, `isekai/interface/ui/routes/reviewing.py:323` | `(run, flow, version, seed)` | `RenderRef(run, flow, version, seed)` |

These stay, and read well: `discard_edit` (`edit.py:335`) and the bake's route (`isekai/interface/ui/routes/rendering.py:351`) unpack an `EditRef` whole, `tests/test_edit.py:115` does too, and `run_draft` (`drafts.py:30`) passes `rendered_at`'s answer on as a `Revision`. `draft_from_image`, `refuse_drafts` and `refuse_image_drafts` unpack a `Revision` by position. `Revision` keeps its name and its importers, `drafting.py`, `drafts.py` and `reviewing.py`; a `RenderRef` unpacks as the tuple did.

### D3

`layout.py` gains, after `artifact_name`:

```python
def version_of(path: Path) -> int:
    """Return the version an artifact's name spells: its first three digits.

    e.g. review/002.draft.json -> 2; 001.error.1.transient.json -> 1
    """
    return int(path.name[:3])
```

`run.py` imports and lists it. The sites that slice and then call it:

| site | slices today | after |
|---|---|---|
| `current_draft`, `isekai/pipeline/review.py:129` | `int(draft.name[:3]) <= approved[-1]` | `version_of(draft) <= approved[-1]` |
| `_waiting_number`, `review.py:408` | `int(waiting.name[:3])` | `version_of(waiting)` |
| `discard`, `review.py:519` | `source_copy(run, flow, int(draft.name[:3]))` | `source_copy(run, flow, version_of(draft))` |
| `withdraw`, `review.py:628` | `source_copy(run, flow, int(draft.name[:3]))` | `source_copy(run, flow, version_of(draft))` |
| `approve`, `review.py:947` | `version = int(draft.name[:3])` | `version = version_of(draft)` |
| `_drafted`, `isekai/interface/ui/routes/reviewing.py:399` | `version = int(path.name[:3])` | `version = version_of(path)` |
| `refusal_for`, `isekai/foundation/run.py:443` | `version = int(record.name[:3])` | `version = version_of(record)` |

Each is a name the code itself wrote: a draft, an approval's record or an error record `NNN.error.…`. `failures.py:97` parses an error record's name whole, and stays. `.name[:3]` stands once under `isekai/`, in `version_of`, so the check that a site is switched names the other files (C15).

### D4

No function's signature changes to take a ref, and a ref has no method. A signature that took a ref would edit the test calls of each function that takes one, and the routes build their paths from a digest and a seed in a URL, not from a ref. The server's check of a seed, a version or a bake's number in a path stays as it is: the spec states no answer for a bad seed in a path, and a check is behaviour.

### D5

Each type has a case before it exists, and `version_of` has a case before it exists. No existing test's assertion changes, and `tests/test_edit.py`'s unpack of `edit_at`'s answer stays as it is.

Each slicing site is pre-flighted before its switch, as [CONTRIBUTING](../../../CONTRIBUTING.md) says a rewrite is, by `uv run python -m tools.mutate <path>:<line> --tests <files>`. The run is at the first phase that edits its file, because the phases move the lines. A survivor is killed by a case written first, or named equivalent in the phase's commit body.

After the switches only the comparison in `current_draft` and the return in `_waiting_number` still hold a mutant. The other lines only assign or call, which `tools.mutate` refuses with exit 2, and `version_of`'s cases hold its slice (C15). `uv run python -m tools.mutate --edits tests/mutants.json` replays the standing mutants once, after the switches.

### D6

The change has no spec delta, and `.openspec.yaml` says `skip_specs: true`. D70 is added to `docs/decisions.md` after D69, because a later version reads the rule: its bold line names `RenderRef`, `EditRef` and `version_of`, its *Accepts* names what stays, and *Made by* is `0176`. It reads:

```markdown
### D70 · A render is addressed by a named type, and a version is read off a name by one function

**`isekai/foundation/layout.py` holds `RenderRef(run, flow, version, seed)` and `EditRef(run, flow, version, seed, k)`, `NamedTuple`s that `rendered_at` and `edit_at` return, and `version_of(path)`, which reads the version an artifact's name spells. A caller reads a ref by field name, and `run.py` re-exports the three. Review's `Revision` is `RenderRef`.**

- **Why:** callers read the tuples by index, by slice and by star-unpack, and sliced a name's first characters to read a version. A `NamedTuple` is flat and ordered as the tuple was, so each caller that unpacks holds; a dataclass would break them. One function leaves the width of a name in one place.
- **Accepts:** no signature takes a ref, and a ref has no method. A site that unpacks a ref whole stays. The folder climbs by `parents[n]`, the reads of `int(group.name)` and the server's check of a seed, a version or a bake's number in a path stay. `failures.py` still parses an error record's name whole. Reopen when a function's signature would take the run, flow, version and seed together.
- **Made by:** `0176`.
```

[D69](../../../docs/decisions.md#d69--a-render-groups-files-are-listed-in-foundationlayoutpy-and-a-module-above-the-pipeline-reads-the-listing-from-the-foundation)'s *Accepts* is not edited here.

## Tests

The change adds unit tests and no end-to-end test; a type and a function of a name are pure, so the lowest layer holds them. No test is deleted or merged, so there is no `I16` table.

| layer | added | removed | command |
|---|---|---|---|
| unit | a case for `EditRef` in `tests/test_edit.py`, and for `RenderRef` and `version_of` in `tests/test_run_directory.py` | none | `git grep -c -E "def test_.*(reads_by_field_name\|reads_a_version_off)" -- tests/test_edit.py tests/test_run_directory.py` prints `tests/test_edit.py:1` and `tests/test_run_directory.py:2` after phase 3 |
| end-to-end | none | none | `git grep -c -E "RenderRef\|EditRef" -- tests/e2e` exits 1 |

## Dependencies

None.

## Risks / Trade-offs

- **A hand-built tuple where a ref is typed.** `Revision` is `RenderRef` now, so `ty` refuses a plain tuple passed as one; no test builds one, and the route builds a `RenderRef`.
- **An import left out fails the gate.** `ruff` and `ty` name the import a task needs; each task adds its own.
- **A mutation run's lines move with the imports.** The runs before a switch are at the first phase that edits their file, on the lines as they stand; the runs after are on lines moved by the imports `review.py` gains, and the task gives them.
- **A survivor before the switch** is an existing gap, not this change's; D5 says how it is closed, and a case for it extends [tasks](tasks.md) in the phase that finds it.
- **A merge with the names version.** `layout.py`, `run.py` and `generate.py` are edited by both; the lines are apart, and `mf-integrate` decides the decision ids and the changelog.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the types and their cases, the readers, the versions, and the documents.
