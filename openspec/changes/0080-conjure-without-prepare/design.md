# Design — 0080 conjure without Prepare

How a target flow with no sheet gets one from its source's tags, and how the page and the verb draft in one act.
**Verdict: feasible** — the sheet stage already routes a tag list through a schema; it learns to read the named
source's, and the interface layer runs sheet and draft in order, as no stage may call another; the sheet's write
assigns the target, after the source's approval is checked whole.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `6f86b9a` (`v0.52.0`):

- **The sheet stage:** `sheet(run, flow, schema, vocabulary, field_map, *, tagged, flow_digest, new_version)`
  (`isekai/pipeline/sheet.py:87`) reads the flow's own `wd14/` (`:165`, `:200`) and refuses naming `tag` when it is
  absent (`:200–206`); an untagged flow's sheet is every field empty (`:124–129`). `SheetProducer` records `from` and
  `floor` (`isekai/foundation/artifacts.py:146`, `:153–154`).
- **Assigning:** `assign(run, flow)` makes the flow's empty directory (`isekai/foundation/run.py:409`).
- **Drafting across flows:** `draft_from` (`isekai/pipeline/review.py:210`) refuses a target with no sheet (`:228–233`)
  and a waiting draft with edits of its own (`:249–254`, `_edited` `:270`). No stage imports another
  (`test_no_stage_imports_another`, `tests/test_layers.py:214`).
- **The verb:** `review_flow` calls `draft_from` (`isekai/interface/cli.py:907–922`); `sheet_flow` calls `sheet`
  with the flow's `tagger` and `digest` (`:888–902`).
- **The page:** `read_render`'s targets are the sheet-alone flows assigned to any run of the batch
  (`isekai/interface/ui/app.py:956–990`, `sheet_alone` `:443`); `post_draft_from` calls `draft_from` (`:825–839`);
  `read_input` reads the flow's own caption (`:675`, `:685–689`) and computes `drafted` for a draft only (`:673`).
  The large view posts `draftFrom` (`ui/src/views/RenderLarge.vue:116`); Review marks against `drafted.fields`
  (`ui/src/views/Review.vue:56`, `:596`); the caption pane is `SourcePanel.vue`'s `CaptionPanel`
  (`ui/src/components/SourcePanel.vue:120`).
- **The fixture:** the `conjured` batch fills a conjure sheet before the test (`tests/e2e/conftest.py:229`).

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_sheet_stage.py` | 32 | `grep -c "def test_" tests/test_sheet_stage.py` |
| tests in `tests/test_pipeline_cli.py` | 36 | `grep -c "def test_" tests/test_pipeline_cli.py` |
| tests in `tests/test_ui_api.py` | 72 | `grep -c "def test_" tests/test_ui_api.py` |
| e2e tests | 32 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |

## Goals / Non-Goals

**Goals:** a conjure draft from any summon image in one press. **Non-Goals:** running the tagger or Ollama for the
target; changing the review stage's refusals.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | **`sheet(…, tags_from: str \| None = None)`**: with `tags_from`, the tag list read is `run.directory(tags_from, WD14)`'s newest, routed through the target's schema, vocabulary and field map; absent, every field is written empty, as untagged; the producer records `tags_from`, `SheetProducer` gaining `"tags_from": NotRequired[str]`; a kept sheet whose producer names `tags_from` gives no superseded-list warning, and `show` prints its `from` as `<flow>/NNN` | the same pinned tagger read the same photograph; D32 adds a recording key without a version; a borrowed sheet is built from the source's approval, not from a tag list it should track | the target's own tags first; weighing a borrowed sheet against either flow's later lists |
| [D2](#d2) | **`isekai/interface/drafting.py`** `draft_across(run, target: Flow, source, version, vocabulary, field_map) -> Path`: `drafting_approval` checks the source's approval whole; where the target holds no sheet, `sheet(…, tagged=target.tagger, flow_digest=target.digest, tags_from=source)`, whose write assigns the target; then `draft_from`; `review_flow` and `post_draft_from` call it | no stage calls another; one sequence for the verb and the page; nothing is written before the source is checked | a stage calling the sheet stage |
| [D3](#d3) | **`review.waiting_edit(run, flow) -> Path \| None`** — the waiting draft whose fields differ from its sheet, from `_edited`; `post_draft_from` answers it as `{draft, waiting: true}`, writing nothing; an unedited waiting draft is replaced as today; `review_flow` keeps `draft_from`'s refusal | the edited draft is the work in hand; the CLI asks for a draft | refusing on the page |
| [D4](#d4) | **targets:** `sheet_alone()` less the image's flow, with no reading of the batch's runs | the press assigns | assigned flows only |
| [D5](#d5) | **`drafted` after approve:** `read_input` computes `drafted` for the approval it shows as for a draft; `Review.vue` keeps it read-only; *Discard draft* on a draft only | an approved revision keeps its marks since `v0.51.0` | |
| [D6](#d6) | **the borrowed caption:** where the flow holds no caption and its sheet's producer names `tags_from`, `read_input` serves that flow's newest caption's prose and `caption_from: <flow>`, no command; `SourcePanel` heads the pane `caption · <flow>` | no caption is written for the target | the missing-caption line |
| [D7](#d7) | **the docs:** `README.md`'s *on review: draft each --flow from that flow's approval* gains `, assigning and filling a target with no sheet from the source's tags`; `docs/data-flow.md`'s `review --from` line names `the source's tag list where no sheet`; `ui/design/spec.md`'s large-view bullet `Each flow of the batch drafted from a sheet alone` → `Each offered flow drafted from a sheet alone, assigned or not,` | the docs name what the verb does | |

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | `sheet:tags-from:filled-from-the-sources-tag-list`; `sheet:tags-from:no-source-tag-list-gives-an-empty-sheet`; `sheet:superseded:a-borrowed-sheet-is-silent` — a newer list under the source or the target; `cli:review-from:a-target-with-no-sheet-is-filled-first`; `ui:conjure-from:a-waiting-edit-is-opened`; `ui:conjure-from:an-approved-draft-keeps-its-marks`; `ui:source:a-borrowed-sheet-shows-its-sources-caption` | `ui:conjure-from:the-large-view-names-its-targets` — no source assigned conjure; `ui:conjure-from:a-refused-draft-writes-nothing` — a version the source does not hold; `cli:show:producers-are-reported` — a borrowed sheet names its source flow | `tests/test_sheet_stage.py`, `tests/test_pipeline_cli.py`, `tests/test_ui_api.py`, `tests/test_run_view.py` |
| e2e | none | `test_conjure_from_this_opens_review` — its source unassigned, the caption named as summon's | `tests/e2e/conftest.py`, `tests/e2e/test_render.py` |

**End-to-end runs added:** none. The existing conjure test reaches the large view; its fixture loses the conjure sheet,
so it now proves the press with no Prepare (T2).

**Removed or merged:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** a target whose schema names a field the source's tags fill differently → the target's own field map
  routes them, and approve validates every tag against the target's vocabulary.
- **[Trade-off]** the target's caption is the source's → its Review names the source, and Prepare still writes the
  target's own when the operator runs it.

## Verdict

**Feasible.** One keyword on the sheet stage, one sequence in the interface layer, one page answer.
