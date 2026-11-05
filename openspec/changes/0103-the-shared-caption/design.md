# Design — 0103 the shared caption

The photograph's caption and tag lists move from each flow's directory to `runs/<id>/photo/`, reached by one path in
`run.py`; `isekai migrate` copies the existing runs; the writers and readers switch together, and the borrow goes.
**Verdict: feasible.**

## Context

Every stage writes under `runs/<id>/<flow>/<stage>/`, through `Run.directory(flow, stage)`
(`isekai/foundation/run.py:318`), with the stage names `CAPTIONS`, `WD14` and `TAGS` at `run.py:129-131`. `Run.flows`
lists every directory under a run as a flow (`run.py:306-316`). `MANIFEST_VERSION` is 5 and the caption's briefing and
model are `config/caption.json`'s (`isekai/foundation/caption_config.py`), so every flow already reads a photograph the
same way.

The writers are `caption()` (`isekai/pipeline/caption.py:231-296`), `tag_wd14` and `tag_hosted`
(`isekai/pipeline/tagging.py:247-398`), dispatched once per flow by `_per_item` (`isekai/interface/cli.py:750-964`).
The readers are the sheet fill (`isekai/pipeline/sheet.py:217`, `:254`, `:366`), Review's payload
(`isekai/interface/ui/app.py:725-748`, `_caption` and `_listed` at `:1300-1321`, `_wd14` at `:1577`, `_tags` at
`:1609`), the hub's "tagged" (`isekai/interface/ui/library.py:617-619`), `show` (`isekai/interface/run_view.py:59`,
`:178-275`) and Compare (`isekai/interface/compare_view.py:174-176`).

A flow drafted from another holds no tag list and borrows: `prepare_sheet` takes `tags_from` and fills through
`_from_source` and `tagger_of` (`sheet.py:152-325`), recording `tags_from` and `listed_from`; Review follows
`sheet_source` and `tagger_of` to another flow's caption and lists. `isekai/pipeline/review.py:524-546`'s
`_drafting_wrote` reads `tags_from` for a different job: it tells a first sheet a draft wrote, which `discard` takes
back with the draft, from one Prepare wrote.

`artifacts.read` checks a file's kind and version only (`isekai/foundation/artifacts.py:488-534`), so a sheet holding
a key no `TypedDict` declares still reads. The hosted tagger samples at temperature 0, seed 1
(`tagging.py:97-100`), and so does the reader (`caption.py:88-91`).

## Goals / Non-Goals

**Goals:** one description per photograph under `photo/`, read by every flow; one path to it, refusing an unmigrated
run by name; `isekai migrate`, copying and never moving; no borrow left; every phase green.

**Non-Goals:** a run-file kind's version moving; any change under `flows/` or `config/`; `Hub.vue` or `ui/src/cells.ts`;
deleting the per-flow copies a migration leaves.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `run.py` declares `PHOTO = "photo"` and `DESCRIPTION = (CAPTIONS, WD14, TAGS)`. `Run.flows` lists every directory but `PHOTO`. `assign` refuses `PHOTO`: `photo: a name a run keeps for its photograph's description, never a flow`. `tests/test_flow.py` holds that no tracked flow is named `photo` | Q2: one name to leave out. `Run.flows` is what inspection and render walk, and a directory no flow answers for refuses `show` (`run-directory:inspection:an-unanswerable-directory-refuses-first`) | a dot-directory: `show` and the hub would not list it; the check in `load_flow`: `flow.py` imports nothing from `run.py`, and a flow that cannot be assigned can never collide |
| <a id="d2"></a>**D2** | `photo_of(run, stage)` in `run.py` returns `run.directory(PHOTO, stage)` once the run passes [D3](#d3)'s check. Every reader and writer of the description goes through it, except `show` and `migrate`, which read `run.directory(PHOTO, …)` | one path holds the refusal for every caller; `show` reads a run in any state (`cli:show`), and `migrate` is the fix | a check in each caller: a missed one reads an unmigrated run as never tagged |
| <a id="d3"></a>**D3** | A run is **unmigrated** when a flow's `captions/`, `wd14/` or `tags/` holds an artifact and `photo/` holds none of that kind; an error record alone is no artifact. `photo_of` refuses it, per [the refusal](#the-refusal). `migrate_command(run)` is `python -m isekai migrate`, with ` --runs <root>` when the run's root is not `RUNS_ROOT`, as `stage_command` names a root | Q4: refused by name, naming the verb; a stage-by-stage rule lets a migration stopped half way finish on a rerun | a marker file: a second record of what the listing already says; a fallback reader: Q4 rejected it |
| <a id="d4"></a>**D4** | `isekai/foundation/migrate.py`'s `migrate(run) -> str` copies per [the migration](#the-migration): the tag lists only where every flow agrees, under their own numbers; the newest caption as `001.json`; each kind whole or not at all; nothing left behind deleted | Q10. A list keeps its number, so a sheet's `from` names the same list under `photo/` and no kind's meaning moves (D32) | the newest list alone: a sheet's `from: 1` would name nothing; comparing producers: the list is the description, and a producer records options |
| <a id="d5"></a>**D5** | The `migrate` verb in `cli.py`: no flag walks `RUNS_ROOT` when it is a directory, then each collection's `runs/` in the library `ISEKAI_LIBRARY` names, which `isekai/interface/ui/__init__.py`'s new `collection_runs()` returns (`library.root`, `listed`, `is_collection`), imported inside the verb as `_ui` imports `serve`; `--runs DIR` walks that root alone, and `wiring()` reads a `None` root as `RUNS_ROOT`. A run is a directory holding `run.json`, by name. One line per run, `<root's parent name>/<root name>/<run-id>: <outcome>`; a refused run's outcome is `refused: <message>`, and any refusal exits 1. A library git can reach is refused as `open_library` refuses it (D18) | Q10: every collection walked, a line a run. The refusal of [D3](#d3) names `--runs` for a root that is not the default, so every run it can refuse is reachable | a collection argument: the operator migrates once, everything; a top-level import of the library: `tests/test_pipeline_cli.py`'s `-S` guard; importing `ui.library` itself: `tests/test_layers.py` reaches a sub-package through its front door |
| <a id="d6"></a>**D6** | `tag` and `caption` lose `--flow` from the required loop (`cli.py:250-258`) and keep it hidden (`help=argparse.SUPPRESS`), so `dispatch` refuses it before any run is opened, per [the verbs](#the-verbs). `_require_tagged` is deleted. Each runs once per identifier, its writer called with no flow; `_Reporter.item` takes `flow: str \| None` and leaves `flow` out of a line where it is `None`. `refusal_for` takes `flow: str \| None`: `None` names `photo/<area>/` and a command with no `--flow` | Q7: a stale command is refused with the verb's new form, not argparse's `unrecognized arguments`; the photograph's verbs name no flow, so no tag invocation can name an untagged one (D31 amended) | `--flow` dropped outright: exit 2 naming nothing the operator can paste |
| <a id="d7"></a>**D7** | `Wiring.reader`, `tagger` and `hosted_tagger` become `Callable[[], …]`; `reader_for()`, `tagger_for()` and `hosted_tagger_for()` take nothing; `_per_item`'s `tagger` thunk takes nothing. Every double follows: `tests/stages.py`'s `Always.__call__(self)`, `tests/test_tagging.py`'s `_unopenable` and `unopenable`, `tests/test_pipeline_cli.py:516`'s `reader`, which goes with `_caption_with_one_refusing` | a verb that names no flow has none to pass, and the seams already read nothing from it (0102's D3 kept the parameter while every caller had a flow) | a placeholder flow: a lie in the call |
| <a id="d8"></a>**D8** | The sheet fills a tagged flow from `photo_of(run, WD14)`, an untagged one empty. `tags_from` stays a parameter of `sheet` and `prepare_sheet` and a key of the sheet's producer, **recorded only**: the source a draft drew a first sheet for, which `_drafting_wrote` and `_superseded` read as before. `_from_source`, `tagger_of` and `sheet_source` are deleted; `listed_from` leaves `SheetProducer`, `sheet.py` and `run_view.py`. A first sheet a draft writes is the sheet `sheet` would write: a tagged target with no `photo/wd14/` list refuses, naming `tag` | Q5: nothing is left to borrow. An old sheet's `tags_from` was written by a draft and still says so, so no reader misreads it (D32); `discard` keeps taking back the sheet a draft wrote | `tags_from` deleted: `discard` would delete a sheet Prepare wrote, or keep one a draft wrote; an empty first sheet when the list is absent: a second rule for one fill |
| <a id="d9"></a>**D9** | The readers go through `photo_of`, per [the readers](#the-readers). Review's payload loses `caption_from`; `_caption` and `_listed` are deleted; the payload's commands for `tag` and `caption` name no flow. A refusal there is the page's refusal, and in the hub an unreadable cell's | Q5, Q8; the refusal of [D3](#d3) reaches the operator wherever the description is read | a payload that names a source anyway: there is one description |
| <a id="d10"></a>**D10** | Prepare plans per [Prepare's plan](#prepares-plan): one `tag` step and one `caption` step over the photographs, then a `sheet` step per flow; `Step.flow` is `str \| None`, and `isekai_command` leaves `--flow` out for `None`. `cell_event` turns a line naming no flow into one event per offered flow the run is assigned to; a job counts a photograph's stage once | Q6. The verbs already skip a described photograph, so "a photograph already captioned and tagged skips them" is the verbs' own idempotence (`cli:explicit-versions:repeat-invocation-is-a-no-op`) | reading `photo/` in the plan to drop described runs: a second copy of the verb's rule |
| <a id="d11"></a>**D11** | The source pane loses `caption_from`: `ui/src/types.ts`'s field, `Review.vue`'s `:caption-from`, `SourcePanel.vue`'s `captionFrom` prop and `:from`, `CaptionPanel.vue`'s `from` prop and its `· {{ from }}`. `tests/e2e/test_render.py:337` asserts the heading `② caption` | Q5's "the UI's '· from' removed"; the payload stopped sending it in phase 2, and `?? null` reads its absence | keeping the prop for a later use: nothing sends it |
| <a id="d12"></a>**D12** | `docs/decisions.md`, per [the record](#the-record): D1, D17, D31 and D38 amended in place, each `Made by:` gaining `` `0103` ``. `cli.py`'s module docstring loses "Schema migration is not a verb", in phase 1 | a decision in force is edited where it lives (`A7`); D32 holds as it stands, since no kind's version moves | a new decision for `photo/`: it is D17's layout |
| <a id="d13"></a>**D13** | A requirement that loses or retitles a scenario is REMOVED and ADDED under a new title, per [the key moves](#the-key-moves) | `openspec validate --strict` refuses a MODIFIED block that omits a scenario the living spec has (0102's D7) | a stale scenario title kept to satisfy the validator |
| <a id="d14"></a>**D14** | A comment, docstring or refusal text a phase makes false is rewritten in that phase, each named in a task | a comment states what holds, in the present tense | one sweep at the end: earlier phases would commit false comments |

### The layout

```
runs/<input-id>/
├── run.json, photo.<ext>          the input and its frame
├── photo/                         PHOTO: the photograph's description, every flow's
│   ├── captions/001.json
│   ├── wd14/001.json
│   └── tags/001.json
└── <flow-id>/                     Run.flows: every directory but photo/
    ├── sheets/ review/ prompts/ outputs/
    └── captions/ wd14/ tags/      only in a migrated run: left in place, read by nothing
```

### The refusal

`photo_of` refuses, naming the kinds in `DESCRIPTION`'s order:

```
0d4b7e6fb2a8_ada: its captions and wd14 sit under its flows, not in photo/; run `python -m isekai migrate`, which
copies them there
```

The kinds join with `, ` and a final ` and `. It runs before any write, so a stage that refuses leaves the run as it
found it.

### The migration

`migrate(run)` for one run, in this order:

```
for each kind in DESCRIPTION:
    holders = the flows whose <flow>/<kind>/ holds an artifact
    photo/<kind>/ holds an artifact, or no holders  ─▶ skip the kind
    wd14, tags: holders hold different version numbers,
                or one version's `tags` differ       ─▶ refuse the run, copy nothing
caption: the newest of each holder's latest caption, by st_mtime_ns, a tie to the first flow by id
copy each kind left: delete photo/.<kind>.partial/ if a stopped run left one; write the files into it
                     byte for byte; rename it to photo/<kind>/
```

- **wd14, tags:** the first holder's artifact files, by id, under their own names. Error records are not copied.
- **The caption:** its bytes as `photo/captions/001.json`.
- **Outcomes:** `migrated <kinds>` naming the kinds copied, `already migrated` where every kind any flow holds is in
  `photo/`, `nothing to migrate` where no flow holds any.
- **The refusal for lists that differ:** `<run-id>: its <kind> lists differ between <flow>, <flow>; keep one — delete
  the others' <flow>/<kind>/ — then run `<migrate_command(run)>` again`.

### The verbs

| invocation | at HEAD | after |
|---|---|---|
| `isekai tag <ids>` | refused by argparse: `--flow` required | tags each photograph once, into `photo/` |
| `isekai caption --flow F <ids>` | captions under `F/` | refused: `` `caption` takes no --flow: it writes the photograph's prose, which every flow reads; run `python -m isekai caption <ids>` `` |
| `isekai tag --flow F --runs R --new-version <ids>` | tags under `F/` | refused, naming `python -m isekai tag --runs R --new-version <ids>` |
| `isekai migrate` | no such verb | walks `.data/runs` and the library's collections, per [D5](#d5) |

`tag`'s refusal says "its tags". The command repeats `--runs` and `--new-version` where given, and the identifiers;
`--progress` is the job's and is not repeated.

### Prepare's plan

`plan(todo, tagged)`, `todo` being `library.unprepared`'s runs per flow:

```
{"summon": ["r1"], "conjure": ["r1", "r2"]}, both tagged
  ─▶ Step(None, "tag", (r1, r2)), Step(None, "caption", (r1, r2)),
     Step("summon", "sheet", (r1,)), Step("conjure", "sheet", (r1, r2))
```

The photographs are the union of `todo`'s runs, in first-seen order; `tag` takes only the runs of a flow `tagged`
names, and is left out when that leaves none. `_Job.asked` keys a photograph's stage `(None, run)`, and `complete`
reads a line's `flow` as given, `None` when absent. `cell_event` returns a list: a line naming a flow gives that
cell's event, a line naming none one event per offered flow whose directory the run holds, and an unknown run or flow
none. `complete` counts a line when any of its events reached the stage `REACHED` names. A step failing silently
names `<verb> on <flow>`, or `<verb>` for a photograph's step.

### The readers

| reader | at HEAD | after |
|---|---|---|
| sheet fill, `_superseded`, `_route` (`sheet.py`) | `run.directory(flow, WD14)`, else the borrowed flow's | `photo_of(run, WD14)`; the refusal and remedies name `photo/wd14/` and `python -m isekai tag` |
| Review's payload (`app.py`) | `_caption`, `_listed`: own, else the tagger's | `latest_artifact(photo_of(one.run, CAPTIONS \| WD14 \| TAGS))`; no `caption_from` |
| hub "tagged" (`library.py:617`) | the flow's `wd14/` | `photo_of(run, WD14)`, inside the cell's `try` |
| `show` (`run_view.py`) | six stages per flow | `photo/`'s three listed first, then `sheets`, `review`, `prompts` per flow; a flow's `captions/`, `wd14/`, `tags/` named "not read"; a sheet's `from NNN` names no flow |
| Compare (`compare_view.py`) | each flow's caption, named | one caption per run, `photo_of(run, CAPTIONS)`'s, naming no flow |
| `evaluation/recall.py` | tags each render itself | unchanged |

### The record

| decision | at HEAD | after |
|---|---|---|
| D1 | `tag` writes the WD14 tags, then the JoyCaption tags; `caption` writes the prose | the same, then: "Both write the photograph's, under `photo/`, once for every flow." |
| D17 | **`runs/<input>/<flow>/<stage>/`.** | **`runs/<input>/photo/` holds the photograph's caption and tag lists, read by every flow; `runs/<input>/<flow>/<stage>/` holds each flow's own work.** Why: one briefing, one model and one pinned tagger read a photograph alike, so its description is written once; a flow still adds one subtree, and reads another's work only when the operator names it (D38) |
| D31 | `tag` refuses a flow that declares `false` | `tag` names no flow; `sheet` fills an untagged flow's sheet empty, and Prepare tags a photograph only for a flow that declares `true` |
| D38 | A stage reads another flow only when the operator names it as a source. | A stage reads another flow's work only when the operator names it as a source; the photograph's description is every flow's (D17). |

### The key moves

| capability | old | new | test |
|---|---|---|---|
| `run-directory` | *…input above, flow below…* | *…the input and its photograph's description above…*, its keys kept, `layout:every-flow-reads-the-description` and `layout:photo-is-no-flow` added | `tests/test_run_directory.py` |
| `run-directory` | — | `migration:an-unmigrated-run-is-refused`, `migration:a-migrated-run-reads-photo` | `tests/test_run_directory.py` |
| `caption` | `output:caption-belongs-to-one-flow` | `output:every-flow-reads-one-caption` | `tests/test_caption.py` |
| `tagging` | `declaration:a-flow-without-a-tagger-is-refused`, `declaration:only-untagged-flows-name-the-next-verb` | removed | — |
| `sheet` | `superseded:a-borrowed-sheet-is-silent` | `superseded:a-drafted-sheet-is-silent` | `tests/test_sheet_stage.py` |
| `sheet` | `tags-from:filled-from-the-sources-tag-list`, `tags-from:no-source-tag-list-gives-an-empty-sheet`, `tags-from:a-source-without-a-list-leads-on` | `output:a-drafted-sheet-names-its-source` | `tests/test_sheet_stage.py` |
| `cli` | — | `flow-selection:the-photographs-verbs-refuse-a-flow`, `progress:a-photographs-line-names-no-flow`, `show:the-description-is-listed-once` | `tests/test_pipeline_cli.py`, `tests/test_run_view.py` |
| `cli` | `resolution:a-pinned-seam-resolves-for-every-flow-that-declares-it` | `resolution:the-pinned-tagger-needs-no-flow` | `tests/test_tagging.py` |
| `cli` | — | `migrate:a-second-run-changes-nothing`, `migrate:the-old-files-stay`, `migrate:differing-lists-refuse-the-run`, `migrate:the-newest-caption-is-kept`, `migrate:a-list-keeps-its-number`, `migrate:every-collection-is-walked`, `migrate:a-kind-is-copied-whole` | `tests/test_migrate.py` |
| `ui` | `source:a-borrowed-sheet-shows-the-taggers-lists` | `source:every-flow-shows-the-photographs-lists` | `tests/test_ui_api.py` |
| `ui` | `source:a-borrowed-sheet-shows-its-sources-caption`, `source:a-two-hop-sheet-shows-the-taggers-caption` | `source:every-flow-shows-the-photographs-caption` | `tests/test_ui_api.py` |
| `ui` | — | `hub:a-tagged-photograph-is-tagged-in-every-flow`, `prepare:a-photograph-is-described-once` | `tests/test_ui_library.py`, `tests/test_ui_jobs.py` |

Each key prefix is its capability's; the full key is `<capability>:<group>:<slug>`. `tests/test_spec_bindings.py`
demands no key a delta removes and lets a marker name one a delta adds, so each test re-binds in the phase that edits
it.

## Tests

| layer | adds | removes |
|---|---|---|
| unit | `tests/test_migrate.py`, new: one test per `cli:migrate:*` key; `tests/test_run_directory.py`: `photo` as no flow, the unmigrated refusal, the migrated read; `tests/test_caption.py`, `tests/test_sheet_stage.py`, `tests/test_ui_api.py`, `tests/test_ui_library.py`, `tests/test_ui_jobs.py`, `tests/test_run_view.py`, `tests/test_pipeline_cli.py`: a test per added key | the borrow's tests and the untagged-flow refusals, per the table below |
| end-to-end | none | none; `tests/e2e/test_render.py:337` changes one assertion |

Counted with `uv run pytest <file> --collect-only -q | tail -1` at `6376b929`, and as planned:

| file | at `6376b929` | planned |
|---|---|---|
| `tests/test_migrate.py` | 0 | 7 |
| `tests/test_run_directory.py` | 88 | 92 |
| `tests/test_caption.py` | 53 | 52 |
| `tests/test_flow.py` | 99 | 100 |
| `tests/test_tagging.py` | 50 | 38 |
| `tests/test_sheet_stage.py` | 47 | 44 |
| `tests/test_pipeline_cli.py` | 61 | 61 |
| `tests/test_run_view.py` | 37 | 38 |
| `tests/test_ui_api.py` | 96 | 95 |
| `tests/test_ui_jobs.py` | 27 | 28 |
| `tests/test_ui_library.py` | 23 | 24 |
| the suite, `uv run pytest --ignore=tests/e2e --collect-only -q` | 1490 | 1488 |
| `tests/e2e`, `uv run pytest tests/e2e --collect-only -q` | 19 | 19 |

`tests/test_pipeline_cli.py` loses the `caption` and `tag` rows of two tests parametrised over `STAGE_VERBS`, and gains
a `[migrate]` row of `test_each_verb_is_reachable_as_a_subcommand`, `test_the_photographs_verbs_refuse_a_flow`
parametrised over `caption` and `tag`, and `test_a_photographs_progress_line_names_no_flow`.
`tests/test_tagging.py`'s tests parametrised over `tracked_flows()` to resolve a seam per flow resolve it once.

**Deleted or merged**, each mapped to the test that carries its assertion (`I16`):

| test | carried by |
|---|---|
| `tests/test_caption.py::test_a_second_flow_produces_its_own_caption` | retired by [D1](#d1): a second flow reads the one caption; `test_every_flow_reads_the_one_caption` holds that, `caption:output:every-flow-reads-one-caption` |
| `tests/test_caption.py::test_a_flows_caption_is_neither_read_nor_changed_by_another` | the same |
| `tests/test_tagging.py::test_tagging_a_flow_that_declares_no_tagger_is_refused_before_any_work` | retired by [D6](#d6): `tag` names no flow; `test_the_photographs_verbs_refuse_a_flow` holds the refusal of `--flow` |
| `tests/test_tagging.py::test_only_untagged_flows_name_the_next_verb` | retired by [D6](#d6) |
| `tests/test_sheet_stage.py::test_a_source_with_no_tag_list_gives_an_empty_sheet_naming_it` | retired by [D8](#d8): a draft's first sheet is the ordinary fill; `test_an_absent_tag_list_is_refused_naming_the_verb_that_writes_it` holds its refusal |
| `tests/test_sheet_stage.py::test_a_source_without_a_list_leads_on_to_the_flow_that_tagged` | retired by [D8](#d8): no walk |
| `tests/test_sheet_stage.py::test_the_walk_that_leads_on_ends_at_a_list_and_at_a_loop` | retired by [D8](#d8): `tagger_of` is deleted |
| `tests/test_ui_api.py::test_a_sheet_filled_from_another_flows_tags_shows_that_flows_caption` | `test_every_flow_shows_the_photographs_caption`, `ui:source:every-flow-shows-the-photographs-caption` |
| `tests/test_ui_api.py::test_a_sheet_two_flows_from_its_tags_shows_the_taggers_caption`, and its helper `_two_hops` | the same |
| `tests/test_ui_api.py::test_a_borrowed_sheet_shows_the_taggers_lists` | `test_every_flow_shows_the_photographs_lists`, `ui:source:every-flow-shows-the-photographs-lists` |
| `tests/test_tagging.py::test_the_hosted_tagger_runs_the_configured_model`, a row per tracked flow | the same test, one row: no flow selects the seam ([D7](#d7)) |
| `tests/test_tagging.py::test_tagging_a_tracked_flow_resolves_and_runs_the_local_tagger`, a row per tracked flow | `test_tagging_resolves_and_runs_the_local_tagger_with_no_flow`, one test, `cli:resolution:the-pinned-tagger-needs-no-flow` |
| `tests/test_pipeline_cli.py::test_a_stage_verb_without_a_flow_is_refused[caption]`, `[tag]`; `::test_every_stage_verb_accepts_the_flag[caption]`, `[tag]` | `test_the_photographs_verbs_refuse_a_flow`, `cli:flow-selection:the-photographs-verbs-refuse-a-flow` |

**Rewritten in place**, same scenario or its successor:

| file | before | after |
|---|---|---|
| `tests/test_sheet_stage.py` | `test_a_sheet_is_filled_from_the_named_flows_tag_list` | `test_a_drafted_sheet_is_filled_from_the_photographs_list_and_names_its_source`, `sheet:output:a-drafted-sheet-names-its-source` |
| `tests/test_sheet_stage.py` | `test_a_sheet_filled_from_another_flows_tags_is_never_weighed` | `test_a_sheet_a_draft_wrote_is_never_weighed`, `sheet:superseded:a-drafted-sheet-is-silent` |
| `tests/test_tagging.py` | `test_the_local_tagger_resolves_identically_for_every_tracked_flow` | `test_the_local_tagger_resolves_with_no_flow` |
| `tests/test_tagging.py` | `test_each_flow_gets_a_hosted_tagger_on_its_readers_model` | `test_the_hosted_tagger_runs_the_readers_model` |
| `tests/test_caption.py` | `test_a_second_flow_produces_its_own_caption`'s place | `test_every_flow_reads_the_one_caption` |
| `tests/test_tagging.py` | `test_tagging_the_tagged_flow_alone_from_that_root_succeeds`, `tag --flow FLOW` | the same test, `tag <photo>` over the root holding an untagged flow |
| `tests/test_pipeline_cli.py` | `test_one_flows_refusal_leaves_the_others` and `test_a_refusal_after_the_first_flow_leaves_it_written`, over `_caption_with_one_refusing` | the same tests over `_review_with_one_refusing`: `review` refuses the flow with no sheet and drafts the other, `cli:flow-selection:one-flows-refusal-leaves-the-others` kept |

## Dependencies

None.

## Risks / Trade-offs

- [A run's lists differ across its flows, and `migrate` refuses it] → the refusal names the kind and the flows and the
  deletion that settles it; the operator decides which list holds, and a rerun migrates the rest.
- [The newest caption by `st_mtime_ns` is a copied or touched file's time] → captions differ in wording only, so a wrong
  pick costs a reading, and `caption --new-version` writes a fresh one.
- [Old per-flow copies stay on disk] → `show` names each as not read, so the operator sees what can go; nothing reads
  them.
- [Phase 2 is wide: the writers, every reader and Prepare] → a writer and its readers share fixtures
  (`tests/stages.py`'s `caption`, `write_wd14`, `sheet`), so they cannot be green apart (`I8`); its tasks go file by
  file.
- [`photo_of` lists every flow's three directories on each call] → a run holds a handful of flows; Review reads it three
  times per payload.

## Migration Plan

After the release the operator runs `uv run python -m isekai migrate` once. Every refused run is named with its fix;
a rerun after the fix migrates it, and changes nothing else. Rollback is the previous release: it reads the per-flow
copies `migrate` left in place, and ignores `photo/` as a flow it does not track — `show` there refuses until
`photo/` is moved aside.

## Moved since the brief

The brief cites `22291a5f`; every fact was re-read at `6376b929`, after `0097`, `0098`, `0101` and `0102` were
released. The run layout, writer and reader facts stand at their lines. These moved, and the plan carries the value
at `6376b929`:

- `MANIFEST_VERSION` is 5 (`flow.py:52`); the briefing and model are `config/caption.json`'s, and `SIBLINGS` is
  `(GRAPH_NAME, SCHEMA_NAME)` (`flow.py:66`). This change edits nothing under `flows/`, so nothing is re-pinned.
- The run-directory requirement's sentence reads "A caption written for one flow can never be picked up by another
  flow" (`openspec/specs/run-directory/spec.md:382-383`).
- The verb line is `isekai/interface/cli.py`; its docstring's `:8-10` reads "Schema migration is not a verb. Every run
  file kind is at its first version…". No `migrate` verb exists.
- `app.py`'s payload is `:725-748`, `_caption` and `_listed` `:1300-1321`; `jobs.py`'s `plan` is `:144-156`, and
  `refusal()` and `_Slot.refused` (`:79-90`, `:246-247`) are `0097`'s, released; `Hub.vue`'s segments are `:84-99`.
- `docs/decisions.md`: D1 `:50-59`, D14 `:233-241`, D31 `:252-260`, D38 `:261-271`, D17 `:305-312`, D32 `:323-333`.
- `review.py`'s `_drafting_wrote` reads `tags_from` to take back a draft's sheet, a reader the brief did not list;
  [D8](#d8) keeps the key as a record for it.
- The brief's phases put the writers in 1 and the readers in 3. At `6376b929` a writer and its readers share
  `tests/stages.py`'s helpers, so phase 1 would end red. They switch together in phase 2; migrate still comes first,
  in four phases, as Q11 settled. Q11's `openspec validate 0101-the-shared-caption` reads `0103` here.

## Verdict

**Feasible.** Every premise behind Q1–Q11 holds at `6376b929`: the six flows share one briefing, one model and one
tagger, sampled at temperature 0; no flow file and no kind's version moves.
