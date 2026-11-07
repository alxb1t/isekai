# Design — 0114 the delete's leftovers

A render group holding failure records alone counts as no render and goes with them, and a flow left with no approval
loses its own copies of the photograph's description where `photo/` holds that kind. **Verdict: feasible.**

## Context

Every line below is at `aaefd7a9`, the base. See [proposal](proposal.md) — Why.

- **The failure records** — a failed render writes `NNN.error.K.<kind>.json` into its approval's group
  (`_recorded`, `isekai/pipeline/generate.py:691-714`, called from `:630` and `:654`). `discard_render`
  (`generate.py:377-399`) removes the group only when it is empty (`:395`), and `withdraw`
  (`isekai/pipeline/review.py:584-634`) returns `[]` while the group exists (`:597`) and keeps every older approval
  whose group exists (`:599-603`). `failure_named` (`isekai/foundation/run.py:627-637`) knows a record by its name.
- **The own description** — a flow written before D17 holds its own `wd14/`, `tags/` or `captions/`
  (`isekai/foundation/run.py:120-133`). `withdraw`'s no-approval branch clears `sheets/`, `review/`, `prompts/` and
  `sources/` alone (`review.py:620-633`). `unmigrated` (`run.py:780-791`) holds a kind as present in `photo/` when
  `versions(run.directory(PHOTO, kind))` is not empty.

```
 isekai discard <image> · DELETE /api/c/…/renders/…
   ├─ discard_render(image)       image, record; group holding failure records alone: they and the group   (D1)
   └─ withdraw(run, flow, version)
         ├─ approval v, and each older one whose group is gone or holds failure records alone:
         │     prompts/NNN.json, its failure records, the group's failure records, the group, sources/NNN.png,
         │     review/NNN.approved.json                                                                     (D1)
         └─ no approval left: sheets/ review/ prompts/ sources/, then captions/ wd14/ tags/ each where
            photo/ holds that kind, outputs/ when empty ─▶ <flow>/ empty                                    (D2)
```

## Goals / Non-Goals

**Goals:**
- Deleting a flow's last render empties its folder on a run tagged before D17 and on a version with a failed render.

**Non-Goals:**
- The brief's Q1 one-off over the library: after release, dry run first, outside the change.
- A flow's own description where `photo/` lacks that kind: the run stays refused until `isekai migrate`
  (`run.py:794-812`).
- A group holding a sidecar with no image beside failure records: it reads as a render cut short, and stays.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | **The failure records**: `run.py` gains `failures_alone(directory) -> list[Path] \| None` after `failure_named`. `discard_render` deletes the records and the group when it returns a list. `withdraw` holds an approval as rendered through `_holds_render`, and deletes each going approval's group records and group, per [the code](#the-code) | Brief Q2; `0111` Q7 settled that failure records go with the approval. The predicate is the run's, since the render stage and review both read it and no stage imports another (`tests/test_layers.py`) | counting a failure-only group as empty in `withdraw` alone: `discard_render` would print a group it left behind; deleting a record beside a render that stays: its budget still counts |
| <a id="d2"></a>**D2** | **The own description**: `withdraw`'s no-approval branch also clears each kind of `DESCRIPTION` for which `versions(run.directory(PHOTO, kind))` is not empty, after `sources`, per [the code](#the-code) | Brief Q1: every flow reads `photo/`'s copy. The test is `unmigrated`'s, so a kind `photo/` lacks is never deleted | deleting it whatever `photo/` holds: an unmigrated run would lose its only copy; comparing the bytes first: Q1 drops a caption that differs only in its briefing path |
| <a id="d3"></a>**D3** | **The record**, per [the record](#the-record): docs D4 and D50 in `docs/decisions.md`; `docs/principles.md`, `docs/data-flow.md`, `THREAT_MODEL.md`, and the docstrings of `isekai/foundation/migrate.py` and `isekai/interface/ui/app.py` | A7; each says what the delete takes or that per-flow copies stay | a new decision: D50 already owns what the delete takes |

## The code

### Phase 1 — the run and the render stage

`isekai/foundation/run.py`, after `failure_named`:

```python
def failures_alone(directory: Path) -> list[Path] | None:
    """Return the failure records `directory` holds when they are all it holds, sorted.

    None when it is no directory or holds anything else; an empty one gives [].
    e.g. outputs/002/ holding 002.error.1.permanent.json alone -> [that record]
    """
    if not directory.is_dir():
        return None
    held = sorted(directory.iterdir())
    if any(not path.is_file() or failure_named(path.name) is None for path in held):
        return None
    return held
```

`isekai/pipeline/generate.py` imports `failures_alone`. `discard_render`'s `if not any(group.iterdir()):` block becomes

```python
    records = failures_alone(group)
    if records is not None:
        for path in records:
            path.unlink()
        group.rmdir()
        deleted += [*records, group]
```

Its docstring's first line becomes `"""Delete a render's image, its record, and a group left with only failure records.`
and its body opens "Those records go with the group; return every path deleted, absolute." Its sentence "An empty group
would read as work made from its approval." becomes "A group left holding failure records alone would keep an approval
whose last image went." It gains a second example, on these two lines:

```
    e.g. outputs/001/7.png, the last beside 001.error.1.transient.json
    -> [.../7.png, .../7.render.json, .../001.error.1.transient.json, .../001]
```

### Phase 1 — `withdraw` and the failure records

`isekai/pipeline/review.py` imports `failures_alone`, and gains, before `withdraw`:

```python
def _holds_render(run: Run, flow: str, version: int) -> bool:
    """Return whether approval `version`'s group holds more than failure records."""
    group = group_of(run, flow, version)
    return group.exists() and failures_alone(group) is None
```

In `withdraw`:

- the early return reads `if version not in approved or _holds_render(run, flow, version):`;
- `going` keeps `one < version and not _holds_render(run, flow, one)`;
- each going approval's list becomes `prompts/NNN.json`, each `attempts(prompts, one)` path, each path of
  `failures_alone(group) or []`, `group`, `source_copy(run, flow, one)`, `approval_of(run, flow, one)`, with
  `group = group_of(run, flow, one)`;
- the delete loop removes a directory with `rmdir()` and a file with `unlink()`.

Its docstring: the summary "Delete approval `version` once its group is gone; return what went, absolute." →
"Delete approval `version` once it holds no render; return what went, absolute."; "With it go each older approval with
no group" → "With it go each older approval whose group is gone or holds failure records alone"; "each with its prompt,
failure records and source copy" → "each with its prompt, failure records, group and source copy".

### Phase 2 — `withdraw` and the own description

In `withdraw`, the no-approval loop runs over `(SHEETS, REVIEW, PROMPTS, SOURCES, *shared)`, with
`shared = [kind for kind in DESCRIPTION if versions(run.directory(PHOTO, kind))]`, `DESCRIPTION` and `PHOTO` imported
from `isekai.foundation.run`. Its docstring: "every path under sheets/, review/, prompts/ and sources/ goes" → "every
path under sheets/, review/, prompts/ and sources/ goes, and under its own captions/, wd14/ and tags/, each where
photo/ holds that kind,".

Every docstring line stays within ruff's 88 columns, rewrapped where an edit lengthens it.

## The record

`docs/decisions.md`:

- **D4** (`:91`, `:102`): "the approvals, drafts, sheets and source copies its last render leaves" → "the approvals, drafts,
  sheets, source copies and own copies of the photograph's description its last render leaves". `Made by:` gains
  `` `0114` ``.
- **D50** (`:288-297`): its bold's "its failure records and its source copy, every older approval with no render," →
  "its failure records, in its render group too, and its source copy, every older approval with no render — a group of
  failure records alone is none —"; "its sheets go too, and the photograph's tags and caption stay (D17)." → "its
  sheets go too, and so does its own copy of each kind of the photograph's description that `photo/` holds; `photo/`'s
  stay (D17)." **Why** gains ", and a failure record or a flow's own description left behind kept its folder from
  emptying" before its full stop. `Made by:` gains `` `0114` ``.

`docs/principles.md:248-252`, *Known breaks*: "and the outputs group it empties" → "and the outputs group it leaves
empty or holding failure records alone, those with it"; "deletes the prompts and failure records the generate stage
wrote, numbered for each approval it deletes, and, once the flow holds no approval, the sheets the sheet stage wrote and
the flow's emptied `outputs/`." → "deletes the prompts, failure records and render groups of failure records alone the
generate stage wrote, numbered for each approval it deletes, and, once the flow holds no approval, the sheets the sheet
stage wrote, the flow's emptied `outputs/`, and the flow's own caption and tag lists from before D17, each kind where
`photo/` holds it."

`docs/data-flow.md`: `:73`, "its image, its record, its group when emptied," → "its image, its record, its group when
that leaves it empty or holding failure records alone,". `:180-181`, "and the old files stay, which `show` names as not
read." → "and the old files stay, which `show` names as not read, until a delete leaves the flow no approval (D50)."

`THREAT_MODEL.md:58-62`, *Out of scope*: "(one queued for the next render session too)," → "(one queued for the next
render session too), its failure records with it,"; "every file under the flow's `sheets/`, `review/`, `prompts/` and `sources/`." → "every
file under the flow's `sheets/`, `review/`, `prompts/` and `sources/`, and under its own `wd14/`, `tags/` and
`captions/` where `photo/` holds that kind."

`isekai/foundation/migrate.py:5-6`: "the per-flow copies stay until the operator removes them." → "the per-flow copies
stay until the operator removes them, or a delete leaves the flow no approval (D50)."

`isekai/interface/ui/app.py:23-24`, the module docstring, repeating D4: "the approvals, drafts, sheets and source copies
its last render leaves" → "the approvals, drafts, sheets, source copies and own copies of the photograph's description
its last render leaves".

## Tests

Every new test is a unit test (`T1`), at the stage that owns the delete. No end-to-end test is added or changed: the
behaviour is files on disk, which a unit test reaches (`T1`, `T2`).

| test | file | key | asserts |
|---|---|---|---|
| `test_a_groups_failure_records_go_with_its_last_render`, new | `tests/test_generate.py` | `image-generation:discard:failure-records-go-with-the-last-render` | `prompt_artifact`, `render(…, seeds=[42, 77])`, then `record_failure(group, 1, "transient", {"stage": "render", "seed": 7, "detail": "x"})`: `discard_render` of 42 returns its image and sidecar, the record and the group staying; `discard_render` of 77 returns its image, its sidecar, the record and the group; the group is gone; the approval and the prompt are files |
| `test_an_older_approval_whose_group_holds_failure_records_alone_goes`, new | `tests/test_review.py` | `image-generation:discard:a-group-of-failure-records-is-no-render` | `_approved_source`, `_image(run, 1, 11)`, approval 002 with `outputs/002/` holding `record_failure(group, 2, "permanent", {"stage": "render", "detail": "x"})` alone, approval 003 with no group: `withdraw(run, FLOW, 3)` returns the record, the group, 002's and 003's approvals, absolute, in that order; `approved_versions` is `[1]`; 001's image is a file |
| `test_a_flows_own_description_goes_where_photo_holds_it`, new | `tests/test_review.py` | `image-generation:discard:a-flows-own-description-goes` | FLOW approved once, no group; FLOW's own `captions/001.json` and `wd14/001.json` hold the bytes of `photo/`'s, its own `tags/001.json` holds `{}`, and `photo/tags/` does not exist: after `withdraw(run, FLOW, 1)`, FLOW's directory holds `tags/` alone, its `001.json` a file, and `photo/`'s snapshot is unchanged |

Counted with `uv run pytest <file> --collect-only -q | tail -1` at `aaefd7a9`, and as planned:

| file | at `aaefd7a9` | planned |
|---|---|---|
| `tests/test_generate.py` | 105 | 106 |
| `tests/test_review.py` | 112 | 114 |
| the suite, `uv run pytest --ignore=tests/e2e --collect-only -q` | 1509 | 1512 |
| `tests/e2e`, `uv run pytest tests/e2e --collect-only -q` | 19 | 19 |

No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- A failure record beside a render that stays is kept, so the next render's budget still counts it, as now.
- A flow whose own description differs from `photo/`'s loses it on the delete: brief Q1 settles that every flow reads
  `photo/`'s.
- A run never migrated keeps the flow's copy of a kind `photo/` lacks, so its folder does not empty until
  `isekai migrate` and the Q1 one-off.

## Verdict

Feasible at `aaefd7a9`: every symbol named exists, and no dependency is added.
