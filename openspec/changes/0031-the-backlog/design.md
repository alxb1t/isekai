# Design — 0031 the backlog

Each deferred row this patch takes, the rule that selected it, and how it is fixed. **Verdict: `feasible`.**
Every file, symbol and line below was re-checked at `main` `3278647`.

## Context

- **The selection rule:** a behaviour fix needs an existing requirement that demands it; a documentation, test
  or structural fix needs none.
- **v0.22.8's families, each with a member left:**
  - `isekai/boundary/comfy/client.py:124` catches `(ValueError, KeyError)`; a JSON list or `null` raises
    `TypeError` at `client.py:49`, `:62`, and a numeric history answer raises it at
    `isekai/pipeline/generate.py:504` (`prompt_id not in history`).
  - Missing keys still raise in `isekai/pipeline/review.py` — `:173-174` (`carried["vocabulary"]`,
    `["fields"]`), `:226`, `:238` (`body["fields"]` in `save_draft`), `:341` (`body["sheet"]`), `:346`
    (`body["producer"]`), `:352` (`body["vocabulary"]`), `:377` (`_differs`) — and in
    `isekai/pipeline/sheet.py:125`, `:137-139` (`listed["tags"]`, `listed["producer"]`).
  - A damaged `run.json` is refused with `read`'s generic remedy (`isekai/foundation/artifacts.py:327`,
    *"delete {path}, then run the stage that wrote it again"*); a stage verb given the run id then fails at
    `isekai/interface/cli.py:261`. Offering the photograph by its path works: `isekai/foundation/run.py:275-283`
    skips a run with no frame.
  - `post_approve` (`isekai/interface/ui/app.py:343-352`) calls `approve` outside `_DRAFT_UPDATE` (`:73`,
    taken at `:323` by `put_draft`), so an autosave can write after `approve` unlinks the draft.
- **Rules held by nothing:** `exhausted` (`run.py:479-484`) and `check_budget` (`run.py:487-513`) each decide
  *last record permanent, or count at budget*; `write` (`artifacts.py:308-315`) checks a file's keys only when
  its caller annotates the dict; the golden test's comment (`tests/test_artifact_bytes.py:92`) says `save_draft`'s
  rewrite is pinned, and no golden captures it.
- **Line numbers are `3278647`'s.** A builder re-resolves each by the text it names.

## Goals / Non-Goals

**Goals**

- Each v0.22.8 family is closed: no traceback, a remedy that works, no update after an approval.
- The retry rule is declared once; `write`'s annotation is enforced; `save_draft`'s bytes are pinned.
- The documentation describes the tree as it is.

**Non-Goals**

- A behaviour fix no requirement demands ([proposal](proposal.md#not-in-this-change)).
- A cross-process lock.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | v0.22.8's families are finished at each site | the requirement v0.22.8 cited demands each | a catch-all |
| [D2](#d2) | the guards and test nits land without behaviour change | each closes a stated rule | leaving them to their triggers |
| [D3](#d3) | the drifted documentation is corrected | a false claim is a defect in prose | waiting for each trigger |
| [D4](#d4) | a patch | every behaviour fix is demanded by an existing requirement | a minor |
| [D5](#d5) | phases: behaviour, structure, prose | the prose describes the result | one phase |

### D1

**v0.22.8's families, finished.**

| row | fix | demanded by |
|---|---|---|
| `v0.22.8 review/R1` | `client.py:124` also catches `TypeError`; `_submit` (`generate.py:500-506`) refuses a history answer that is not an object, permanent | `run-directory:budget:one-failure-does-not-halt-the-batch` |
| `v0.22.8 review/R2` | every [Context](#context) key site refuses by name when the key is missing or the wrong type, in `review.py:154-160`'s pattern | the same; `review:validation:missing-field-refuses-approval` |
| `v0.22.8 review/R3` | `Run.frame` (`run.py:233-236`) refuses a damaged frame with its own remedy: *delete `<run>/run.json`, then offer the photograph again by its path* | `cli:refusals:refusal-names-the-remedy`; `run-directory:schema:an-unreadable-artifact-is-refused-by-name` |
| `v0.22.8 review/R5` = `security/S1` | `post_approve` holds `_DRAFT_UPDATE` around `approve`; an autosave that waited on the lock then finds the input approved and is refused (409) | the read-only SHALL (*"SHALL refuse a draft update against such an input"*) — scenario `ui:approval:an-update-overlapping-an-approval-is-refused` |

Tests: `tests/test_generate.py` (a list body and a numeric history), `tests/test_review.py` and
`tests/test_sheet_stage.py` (each missing key), `tests/test_run_directory.py` (the frame's remedy),
`tests/test_ui_api.py::test_an_update_overlapping_an_approval_is_refused`.

### D2

**Guards and test nits, no behaviour change.**

- `v0.22.8 review/R6` — `run.py` gains one predicate over an already-listed record list; `exhausted` and
  `check_budget` both use it, and `check_budget` keeps its one listing.
- `v0.22.6 review/R3` — `tests/test_artifact_bytes.py` gains `test_every_write_gets_an_annotated_artifact`, an
  AST scan of `isekai/` beside the tripwire: the artifact argument of each `write(` call is a name bound by an
  annotated assignment. A twin shows it catches a bare literal.
- `v0.22.6 review/R2` — a `draft-saved` kind in `KINDS` (`tests/test_artifact_bytes.py:117-128`) returns the draft
  after `save_draft`, with `tests/golden/draft-saved.json` captured from today's code; the comment at `:92` says
  what each golden pins.
- `v0.13 R11` — `tests/test_resume.py:279-281`: `collect(work: Callable[[], object])`, the `ty: ignore` gone.
- `v0.22.3 review/R9` — `tests/test_flow.py:692`: the unused `flow` parameter dropped.

### D3

**The drifted documentation.**

| row | before | after |
|---|---|---|
| `v0.22.5 review/R4` | `README.md:296-300`: the `npm install` note alone | plus a sentence: the gate needs `bash tools/download_models.sh config/vocabulary.json`, or `ISEKAI_VOCABULARY=absent` |
| `v0.22.6 review/R4` | `isekai/README.md:10`: *`refusal.py` · `run.py` · `flow.py` · `atomic_write.py`*; `isekai/shared/README.md:6-8`: *"Two of them do read `foundation`"* | `artifacts.py` in the row; the shared README names what each module imports from `foundation` |
| `v0.22.6 review/R5` | `docs/modules.md:122-125`: *"Every run file is written through … `write`"* | *every run file's JSON*; the photograph copy and the render image are bytes |
| `v0.22.8 review/R7` | `docs/principles.md:114`: *"by its full path"* | *"by its path in the run"* |
| `v0.22.8 review/R8` | `isekai/foundation/README.md:24-26`: the importer lists | `interface/run_view.py` on `artifacts.py`'s row, `boundary/comfy/contract.py` on `run.py`'s, `tests/test_artifact_bytes.py` on `flow.py`'s |
| `v0.22.7 review/R2` | `usage: derive_field_map.py …` and the like | `prog="python -m <module>"` in `evaluation/__main__.py:54`, `tools/derive_field_map.py:609`, `evaluation/baseline/build_contact_sheets.py:112`, `evaluation/baseline/build_subjects.py:115` |
| `v0.22.8 security/S3` | `openspec/specs/run-directory/spec.md:287`, `isekai/foundation/artifacts.py:321`: *"a format you do not know"* | *"a format this build does not know"* ([specs/](specs/run-directory/spec.md)) |
| `sheet-budget` | `run.py:154-157` gives the sheet stage a budget *"for `wd14`'s reason"* | the comment adds that the stage records no failure, so the budget never binds |

### D4

**This is a patch.**

| condition | met because |
|---|---|
| no format version moves | no kind's version, and `MANIFEST_VERSION`, changes; the new golden captures today's bytes |
| a behaviour fix is required by an existing requirement | [D1](#d1) names each |
| nothing deprecates a verb or a flag | none |
| nothing changes the product | the sheet, the prompt and the image are unchanged |

### D5

**Phases**, each green alone:

```
1 behaviour   D1: R1, R2, R3, R5/S1
2 structure   D2: R6, the annotation guard, the draft-saved golden, the test nits
3 prose       D3, and the spec's rationale
```

## Dependencies

None.

## Risks / Trade-offs

- **An approval now waits for an in-flight autosave.** → A draft write takes milliseconds; one operator.
- **A CLI `approve` in another process still races the surface.** → Out: the lock is in-process, and no
  requirement asks for more.
- **The annotation guard may flag a legitimate pattern.** → Every `write(` call today passes an annotated name.

## Verdict

**`feasible`.** Small, local fixes; each behaviour change is demanded by a requirement the spec already holds.
