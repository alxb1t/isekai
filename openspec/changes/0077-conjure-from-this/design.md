# Design — 0077 conjure from this

How a draft is written from another flow's approval, what it records, and where the act shows.
**Verdict: feasible** — the review stage already writes drafts from sheets and from approvals; this one reads one of
each.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `3c0561c` (`v0.49.0`):

- **The schemas:** conjure declares every summon field by name and adds `bangs`, `eyelashes`, `nose`, `lips` and
  `facial_hair` (`flows/summon-anime-wai/schema.json`, `flows/conjure-anime-wai/schema.json`).
- **A flow's inputs:** conjure `["sheet"]`; summon and control `["photo", "sheet"]` (`flows/*/flow.json`), read as
  `Flow.inputs` (`isekai/foundation/flow.py:262`).
- **The draft writer:** `_write_draft(run, flow, came_from, source, carried, sheet_version, renders, version)`
  (`isekai/pipeline/review.py:456`) writes the producer `{implementation, from, source}` (`:472`). `review` drafts
  from the newest sheet (`:142`); `revise` from an approval (`:194`).
- **The producer:** `ChainProducer = {implementation, from: int, source}` (`isekai/foundation/artifacts.py:158`);
  `CopiedFrom = {flow, approval}` (`:164`); `ApprovedProducer` adds `edited`, `approved_from`, `copied_from` (`:171`).
- **`came_from(body)`** (`review.py:880`) reads `source: review` + `from` as an approval of the flow's own. It drives
  `_refuse_unchanged` on approve (`:679`), Review's `revision` payload (`_revision`,
  `isekai/interface/ui/app.py:1140`) and the version's kind (`_origin`, `isekai/interface/ui/library.py:429`).
- **A copy:** `approve --from` writes `copied_from` (`review.py:714`); cancel deletes a copy (`:327`); generate reads
  one (`isekai/pipeline/generate.py:421`). `approve` records `edited` against the sheet (`review.py:685`).
- **A waiting draft:** `current_draft` (`review.py:100`); `discard` (`:279`); the option `DISCARD` (`:86`).
- **The verb:** `--flow` on `review` (`isekai/interface/cli.py:225`), `--new-version` (`:267`), `--discard`
  (`:273`), `--from` on `approve` only (`:241`); `review_flow` (`:865`).
- **The surface:** `read_render` (`app.py:904`) serves the large view; `read_input`'s `revision` (`:688`); routes are
  listed in `app.py`'s docstring (`:25`). `RenderLarge.vue` declares `e`, `c`, `⇧C`, `esc` (`ui/src/views/RenderLarge.vue:93`);
  `KeyF` is used only as `⇧F` on Review (`ui/src/views/Review.vue:442`). Review marks against `revision.fields`
  (`Review.vue:588`), names it in `kicker` (`:166`) and offers Discard on a revision (`:625`).

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_review.py` | 67 | `grep -c "def test_" tests/test_review.py` |
| tests in `tests/test_pipeline_cli.py` | 34 | `grep -c "def test_" tests/test_pipeline_cli.py` |
| tests in `tests/test_ui_api.py` | 68 | `grep -c "def test_" tests/test_ui_api.py` |
| e2e tests | 29 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |

## Goals / Non-Goals

**Goals:** a target's draft from a source's approval, finished and approved as any draft. **Non-Goals:** a new file
kind; a copy; a draft that keeps the source's seeds.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `review.draft_from(run, flow, source, version, schema) -> Path`: `version` `None` is the source's newest approval; every field `schema` and the source approval both hold is the source's, every other field of `schema` the target's newest sheet's; vocabulary, schema document and field map are the sheet's; no `renders`, as a draft from a sheet | the target's own fields and records stay the target's | the source's `renders` — its seeds are another flow's |
| [D2](#d2) | the producer is `{implementation: review, from: <sheet N>, source: sheets, drafted_from: {flow, approval}}`; `ChainProducer` gains `drafted_from: NotRequired[CopiedFrom]`; `approve` carries it through `**producer` and never writes `copied_from` | `came_from` returns `None`, so nothing compares it with the target's approvals; cancel and generate see an ordinary approval, cancel restoring its draft with `drafted_from`; it holds its source approval's cancel, as a copy does; no format version moves | `from: {flow, approval}` — `from` is an `int` to every reader |
| [D3](#d3) | refusals, checked before anything is written: the target holds no sheet → names `stage_command(run, "assign", flow)`, then Prepare; no approval `version` in the source → names it and the source's approve command; a waiting draft (`current_draft`) whose fields differ from its own sheet's, or whose `renders` are other than one drawn seed → names it and `stage_command(run, "review", flow, options=DISCARD)`; a waiting draft equal to its sheet, rendering one drawn seed, is overwritten at its number | no work lost; Prepare is the one path to a sheet | refusing every waiting draft |
| [D4](#d4) | `isekai review --from FLOW [--version N]`: `--from` with dest `source` and `--version` with dest `approval` on `review`; `review_flow` calls `draft_from` per run and flow, each answered on its own, and says `<run>: review drafted <flow>/<draft> from <source> v<N>`; refused before any run is read: `--from` beside `--discard` or `--new-version`, `--version` without `--from`, a source among `--flow` or no tracked flow | the verb composes the stage | a new verb |
| [D5](#d5) | `read_render` adds `targets`: the tracked flows assigned to any run of the batch whose `inputs` are `("sheet",)`, less the image's own flow, sorted; `POST /api/b/{batch}/review/{digest}/{flow}/draft-from {source, version}` calls `draft_from` under `_DRAFT_UPDATE`, answering `{draft}` or a refusal | the server owns which flows read a sheet alone | the browser naming `conjure-anime-wai` |
| [D6](#d6) | `RenderLarge.vue` shows a button per target, labelled the flow's first word capitalised plus `from this` — *Conjure from this*; the first is `f` (id `draft-from`); it posts, then opens Review on the target; a refusal shows under the actions; no confirm | a draft is one *Discard draft* away and costs nothing | a confirm, as Revise's selection needs |
| [D7](#d7) | `read_input` adds `drafted: {flow, approval, fields}` — the target sheet's fields — for a waiting draft whose producer has `drafted_from`, else `null`; `Review.vue` marks against `revision?.fields ?? drafted?.fields`, its kicker reads `from <flow> v<N>`, and `discardable` holds on a drafted draft too | the marks show what the source changed; Discard is the way out D3 names | an image beside the photograph — the approval names no seed |

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | every `review:draft-from:` scenario of the [review](specs/review/spec.md) delta; both `cli:review-from:` scenarios; the three unit `ui:conjure-from:` scenarios | `_image` in `tests/test_review.py` takes a flow | `tests/test_review.py`, `tests/test_pipeline_cli.py`, `tests/test_ui_api.py` |
| e2e | `ui:conjure-from:conjure-from-this-opens-review` | `tests/e2e/conftest.py` gains a batch whose run holds summon rendered at seed 7 and a conjure sheet | `tests/e2e/test_render.py` |

**End-to-end runs added:** one, on Chromium only (T4) — the key, the navigation and the marks are a browser's (T1).
No test reaches a conjure sheet beside a summon render, so `test_revise_opens_review_on_the_revision` cannot carry
the step (T2); its own batch keeps Revise's batch untouched (T3).

**Removed or merged:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** a field both flows declare with different vocabularies → approve validates every tag against the target's
  schema and vocabulary, as for any draft.
- **[Trade-off]** an unedited drafted draft differs from its sheet, so drafting it again refuses → *Discard draft* is
  on its page.

## Verdict

**Feasible.** One stage function, one flag, one route and one button over code that already writes drafts.
