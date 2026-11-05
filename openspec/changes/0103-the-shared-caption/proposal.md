---
bump: minor
---

# 0103 — the shared caption

A photograph's caption and its tag lists are written once, under `runs/<id>/photo/`, and read by every flow; the
borrow between flows goes, and `isekai migrate` copies the existing runs' descriptions into place.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision, and the tests it costs |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `caption`, `cli`, `run-directory`, `sheet`, `tagging`, `ui` |

```
1 the store    photo/ and photo_of in run.py; Run.flows leaves it out, `photo` reserved; an unmigrated run refused;
               `isekai migrate`; the reader and taggers resolved with no flow
2 the switch   caption and tag write photo/, --flow refused; Prepare captions and tags once per photograph;
               the sheet fill, Review's payload, the hub's "tagged", show and Compare read photo/;
               tagger_of, sheet_source, listed_from and caption_from deleted
3 the page     the source pane's "· from" and caption_from leave the UI
4 the record   D1, D17, D31, D38; docs/data-flow.md, docs/modules.md, README.md, the group READMEs
```

## Why

**Every flow reads the same photograph the same way, and still keeps its own copy of what it read.** Since the one
briefing, every flow is captioned under one briefing on one model and tagged by one pinned WD14 and one prompt, so
six flows hold six copies of one description. A flow drafted from another holds none and borrows along `tags_from`,
sheet to sheet. One description per photograph, stored once, removes the copies and the borrow.

## What Changes

- **`runs/<id>/photo/`**, new: holds `captions/`, `wd14/` and `tags/`. `Run.flows` leaves it out, and `photo` is a
  reserved flow id ([D1](design.md#d1)).
- **`photo_of(run, stage)`** is the one path a reader or writer takes to the description ([D2](design.md#d2)). A run
  whose flows hold a description `photo/` lacks is refused by name, naming `isekai migrate` ([D3](design.md#d3)).
- **`isekai migrate`**, new: copies each run's per-flow caption, WD14 list and hosted tags into `photo/`, the old
  files left in place; tag lists that differ across a run's flows refuse that run; the newest caption wins; a second
  run changes nothing ([D4](design.md#d4), [D5](design.md#d5)).
- **BREAKING:** `isekai tag` and `isekai caption` take no `--flow`; one is refused, naming the command without it
  ([D6](design.md#d6)). Their progress lines name no flow.
- **The reader and both taggers** resolve with no flow ([D7](design.md#d7)).
- **The sheet** fills from `photo/wd14/`. A first sheet a draft writes records its source in `tags_from` and reads
  no other flow's list; `tagger_of`, `sheet_source`, `_from_source` and `listed_from` are deleted ([D8](design.md#d8)).
- **Review, the hub, `show` and Compare** read `photo/`; Review's `caption_from` is deleted ([D9](design.md#d9)).
- **Prepare** tags and captions once per photograph, then fills each flow's sheet ([D10](design.md#d10)).
- **The source pane** loses its "· from" heading ([D11](design.md#d11)).
- **D1, D17, D31 and D38 are amended** in `docs/decisions.md` ([D12](design.md#d12)).
- No run-file kind's version moves, and the shapes of `caption`, `wd14` and `tags` are unchanged. No flow changes, so
  nothing is re-pinned.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `run-directory` — *The run directory is input above, flow below, and every artifact is a flow's own*: removed;
  *The run directory is the input and its photograph's description above, and each flow's work below* is added, with
  scenarios for `photo/` read by every flow and `photo` as no flow.
- `run-directory` — *A run whose description sits under its flows is refused until it is migrated*: added.
- `run-directory` — *A failure is recorded as an attempt, never as a completion*: an absent tag list is the
  photograph's.
- `caption` — *The reader takes a photograph and its briefing, and returns prose for one flow*: removed; *The reader
  takes a photograph and its briefing, and returns the photograph's prose* is added, every flow reading the one
  caption.
- `tagging` — *Each tagger has its own directory, its own budget and its own idempotence*: the directories are under
  `photo/`.
- `tagging` — *Both taggers run for a flow that declares the tagger, and the hosted one runs on the reader's model*:
  removed; *Both taggers run over the photograph, and the hosted one runs on the reader's model* is added, the
  untagged-flow refusals gone.
- `sheet` — *The stage fills fields from the tag list of a flow that declares the tagger, and leaves them empty for a
  flow that declares none*: the list is the photograph's; a drafted first sheet names its source.
- `sheet` — *A kept sheet filled from a superseded tag list is named*: removed; *A kept sheet filled from a tag list
  older than the photograph's newest is named* is added, a drafted sheet silent.
- `sheet` — *A sheet is filled from another flow's tag list when the operator names it*: removed.
- `cli` — *A stage verb requires the flows it acts on, and takes more than one*: removed; *A stage verb on a flow
  requires the flows it acts on, and the photograph's verbs take none* is added.
- `cli` — *Every per-flow seam is resolved per flow, for a flow that declares its stage*: removed; *Every seam is
  resolved with no flow, on the configured model, and constructs nothing until it is asked* is added.
- `cli` — *A stage verb reports its progress as JSON lines when asked*: `tag` and `caption` lines name no flow.
- `cli` — *Inspection prints the run directory with its provenance*: `photo/` is listed once, before the flows.
- `cli` — *The draft verb drafts a flow from image paths, and writes every draft or none*: a target's first sheet is
  filled from the photograph's tags.
- `cli` — *The migrate verb copies each run's description into photo/ once, and leaves the old files*: added.
- `ui` — *Both tag lists are shown beside the prose, read-only, and neither is editable there*: removed; *Both tag
  lists are the photograph's, shown beside the prose, read-only, and neither is editable there* is added.
- `ui` — *A missing caption is shown with the command that writes it*: removed; *A photograph with no caption is
  shown with the command that writes it* is added, its command naming no flow.
- `ui` — *The hub shows each source's stage in each offered flow, and a tick assigns it*: a tagged photograph is
  tagged in every flow's cell.
- `ui` — *Prepare runs what changed as one job, and refuses before it starts when Ollama does not answer*: tagging
  and reading run once per photograph.
- `ui` — *Draft from this starts from an image, for any flow the app offers, and opens Review on the draft*: the
  target's first sheet is the photograph's tags, and its caption is the photograph's.

## Impact

- New: `isekai/foundation/migrate.py`, `tests/test_migrate.py`.
- Code: `isekai/foundation/run.py`, `isekai/foundation/artifacts.py`, `isekai/interface/wiring.py`,
  `isekai/interface/cli.py`, `isekai/pipeline/caption.py`, `isekai/pipeline/tagging.py`, `isekai/pipeline/sheet.py`,
  `isekai/interface/drafting.py`, `isekai/interface/run_view.py`, `isekai/interface/compare_view.py`,
  `isekai/interface/ui/__init__.py`, `isekai/interface/ui/app.py`, `isekai/interface/ui/library.py`,
  `isekai/interface/ui/jobs.py`.
- UI: `ui/src/types.ts`, `ui/src/views/Review.vue`, `ui/src/components/SourcePanel.vue`,
  `ui/src/components/CaptionPanel.vue`, `ui/src/composables/useSheet.test.ts`.
- Tests: `tests/stages.py`, `tests/e2e/test_render.py`, `tests/test_run_directory.py`,
  `tests/test_caption.py`, `tests/test_tagging.py`, `tests/test_sheet_stage.py`, `tests/test_pipeline_cli.py`,
  `tests/test_resume.py`, `tests/test_review.py`, `tests/test_run_view.py`, `tests/test_compare.py`,
  `tests/test_ui_api.py`, `tests/test_ui_jobs.py`, `tests/test_ui_library.py`, `tests/test_ui.py`,
  `tests/test_generate.py`, `tests/test_progress.py`, `tests/test_artifact_bytes.py`, `tests/test_flow.py`.
- Docs: `docs/decisions.md`, `docs/data-flow.md`, `docs/modules.md`, `README.md`, `isekai/foundation/README.md`,
  `isekai/pipeline/README.md`, `isekai/interface/README.md`, `isekai/interface/ui/README.md`.
- `flows/`, `config/`, `Hub.vue` and every run-file kind's version are untouched.

## Not in this change

- Deleting the per-flow copies `isekai migrate` leaves: the operator's, by hand, once the migrated runs are read.
- A second caption per photograph, one per briefing: when a flow needs a description the shared one cannot give.
- Moving any run-file kind's version: an old caption, WD14 list or tag list reads the same under `photo/`.
- `Hub.vue` and `ui/src/cells.ts`: a cell's stage is a string the server reads, so the hub changes nothing.
- `evaluation/recall.py`: it tags each render itself and reads no description.
