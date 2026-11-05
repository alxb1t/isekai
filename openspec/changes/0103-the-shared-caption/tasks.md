# Tasks — 0103 the shared caption

The store and the migration, then the switch, then the page, then the record, per [design](design.md). Paths are from
the repository root.

## Progress

- [x] 1 — The store
- [x] 2 — The switch
- [x] 3 — The page
- [ ] 4 — The record

## 1 — The store

- [x] 1.1 In `isekai/foundation/run.py`, per [D1](design.md#d1): add `PHOTO = "photo"` and
  `DESCRIPTION = (CAPTIONS, WD14, TAGS)` beside the stage names; the layout comment above them says the description
  sits in `photo/` and every other stage under a flow; `Run.flows` leaves `PHOTO` out, its docstring saying so.
  Verify: `uv run python -c 'from isekai.foundation.run import PHOTO, DESCRIPTION; print(PHOTO, DESCRIPTION)'` prints `photo ('captions', 'wd14', 'tags')`.
- [x] 1.2 In `isekai/foundation/run.py`, `assign` refuses `PHOTO` before it touches the run, with
  [D1](design.md#d1)'s text.
  Verify: `grep -c "a name a run keeps for its photograph's description" isekai/foundation/run.py` prints `1`.
- [x] 1.3 In `isekai/foundation/run.py`, add `unmigrated(run)`, `migrate_command(run)` and `photo_of(run, stage)` per
  [D2](design.md#d2), [D3](design.md#d3) and [the refusal](design.md#the-refusal).
  Verify: `uv run python -c 'from isekai.foundation.run import photo_of, migrate_command, unmigrated'` exits 0.
- [x] 1.4 In `tests/test_run_directory.py`, add `test_photo_is_no_flow` (`run-directory:layout:photo-is-no-flow`):
  `Run.flows` over a run holding `photo/` and one flow lists the flow alone, and `assign(run, PHOTO)` is refused.
  Verify: `uv run pytest tests/test_run_directory.py -k photo_is_no_flow` exits 0.
- [x] 1.5 In `tests/test_run_directory.py`, add `test_an_unmigrated_run_is_refused_naming_migrate`
  (`run-directory:migration:an-unmigrated-run-is-refused`): a flow's `wd14/001.json` and no `photo/`; `photo_of`
  refuses naming the run id and `python -m isekai migrate --runs`, and the run's files are unchanged.
  Verify: `uv run pytest tests/test_run_directory.py -k unmigrated_run_is_refused` exits 0.
- [x] 1.6 In `tests/test_run_directory.py`, add `test_a_migrated_run_reads_photo`
  (`run-directory:migration:a-migrated-run-reads-photo`): with the flow's copies and `photo/` holding each kind,
  `photo_of` returns `photo/<kind>` for each and the flow's copies are unchanged.
  Verify: `uv run pytest tests/test_run_directory.py -k migrated_run_reads_photo` exits 0.
- [x] 1.7 In `tests/test_flow.py`, add `test_no_tracked_flow_is_named_photo`, bound to
  `run-directory:layout:photo-is-no-flow`, asserting `PHOTO not in tracked_flows()`.
  Verify: `uv run pytest tests/test_flow.py -k named_photo` exits 0.
- [x] 1.8 Write `isekai/foundation/migrate.py`, `migrate(run) -> str`, per [D4](design.md#d4) and
  [the migration](design.md#the-migration). It imports `artifacts.py`, `run.py` and `refusal.py` alone; its module
  docstring says it copies and never deletes a source, and that a list keeps its number (D32).
  Verify: `uv run python -c 'from isekai.foundation.migrate import migrate'` exits 0.
- [x] 1.9 In `isekai/interface/ui/__init__.py`, add `collection_runs()` per [D5](design.md#d5): the `runs/` of every
  collection in the library `library.root()` names, refusing a library git can reach as `open_library` does.
  Verify: `uv run python -c 'from isekai.interface.ui import collection_runs'` exits 0.
- [x] 1.10 In `isekai/interface/cli.py`, add the `migrate` verb per [D5](design.md#d5): its parser, `--runs` defaulting
  to none, and `_migrate`, importing `collection_runs` from `isekai.interface.ui` inside the function. In
  `isekai/interface/wiring.py`'s `wiring`, a `None` runs root is `RUNS_ROOT`; one given is checked as now.
  Verify: `uv run python -m isekai migrate --help` exits 0.
- [x] 1.11 In `tests/test_pipeline_cli.py`, `EXPECTED_VERBS` gains `"migrate"` after `"compare"`, and
  `test_each_verb_is_reachable_as_a_subcommand`'s `own` gains `"migrate": []`.
  Verify: `uv run pytest tests/test_pipeline_cli.py -k "verbs or subcommand"` exits 0.
- [x] 1.12 In `isekai/interface/cli.py`'s module docstring, per [D12](design.md#d12): the verb table gains `migrate`,
  "copy each run's per-flow description into photo/"; the paragraph opening "**Schema migration is not a verb.**" →
  "**`migrate` moves a layout, not a schema.** Every run file kind is at its first version, so nothing upgrades one;
  `migrate` copies a run's per-flow description into `photo/` (D17)."
  Verify: `grep -n "Schema migration is not a verb" isekai/interface/cli.py` prints nothing.
- [x] 1.13 **HALT CHECK** The verb line still imports with site-packages off the path, the library reached only inside
  `_migrate` ([D5](design.md#d5)).
  Verify: `uv run pytest tests/test_pipeline_cli.py -k site_packages_off_the_path` exits 0.
- [x] 1.14 Write `tests/test_migrate.py`: one test per `cli:migrate:*` key in [the key moves](design.md#the-key-moves),
  over a library of two collections under `tmp_path`, through `cli.main`, with `ISEKAI_LIBRARY` and `RUNS_ROOT`, where
  `_migrate` reads it, pointed under `tmp_path` by `monkeypatch`. The first runs `migrate` twice and asserts every
  file's bytes after the second run equal those after the first.
  Verify: `uv run pytest tests/test_migrate.py` exits 0.
- [x] 1.15 In `isekai/interface/wiring.py`, per [D7](design.md#d7): `reader`, `tagger` and `hosted_tagger` are
  `Callable[[], …] | None`; `reader_for`, `tagger_for` and `hosted_tagger_for` take no argument, and their docstrings
  and the comments above the fields lose "takes a `Flow` and reads nothing from it" and "per flow".
  Verify: `git grep -n -E "def (reader_for|tagger_for|hosted_tagger_for)[(]flow" isekai` prints nothing.
- [x] 1.16 In `isekai/interface/cli.py`'s `_per_item`, call each seam with no flow: the `tagger` thunk takes nothing,
  its docstring's paragraph opening "One slot, because `wiring.tagger_for` takes a `Flow`" goes, and the caption and
  hosted steps call `_seam(...)()`; the caption step's comment "**Resolved per flow, not once per invocation.**…" goes.
  Verify: `grep -n -E "def tagger[(]flow|[)][(]flow[)]|tagger_for[(]flow[)]" isekai/interface/cli.py` prints nothing.
- [x] 1.17 In `tests/stages.py`, `Always.__call__(self)` takes no flow, its docstring "hands every caller the same
  double"; `tests/test_tagging.py`'s `_unopenable` and `unopenable`, and the `Callable[[Flow], LocalTagger]` annotations
  of `_wired`'s `tagger` and the parametrised `resolver`, take none.
  Verify: `git grep -n -E "def __call__[(]self, flow|def _?unopenable[(]flow" tests` prints nothing.
- [x] 1.18 In `tests/test_tagging.py` and `tests/test_pipeline_cli.py`, every call of `reader_for`, `tagger_for` or
  `hosted_tagger_for` passes nothing; the tagging tests resolve once, per [the tests' tables](design.md#tests):
  `test_the_hosted_tagger_runs_the_configured_model` unparametrised, the two renamed.
  Verify: `uv run pytest tests/test_tagging.py -k "hosted_tagger or local_tagger_resolves"` exits 0.
- [x] 1.19 In `tests/test_pipeline_cli.py`, `_caption_with_one_refusing` and its `reader(flow)` give way to
  `_review_with_one_refusing(tmp_path, refusing)`: the other flow alone holds a sheet, and `review --flow flow-a --flow
  flow-b` refuses `refusing`, naming it, and drafts the other; both tests bound to it assert that, per
  [Tests](design.md#tests).
  Verify: `uv run pytest tests/test_tagging.py tests/test_pipeline_cli.py` exits 0.
- [x] 1.20 No seam double in `tests/` takes a flow ([D7](design.md#d7)).
  Verify: `git grep -n -E "def reader[(]flow" tests` prints nothing.

## 2 — The switch

- [x] 2.1 In `isekai/foundation/run.py`, per [D6](design.md#d6): `refusal_for`'s `flow` is `str | None`; `None` names
  `photo/<area>/<record>` and a command with no `--flow`. Its docstring's paragraph opening "**`flow` is threaded in"
  says a stage on a flow threads it in and the photograph's stages pass `None`; `stage_command`'s example names
  `sheet`, not `tag --flow f`.
  Verify: `grep -n -e "verb requires .--flow." -e "tag --flow f" isekai/foundation/run.py` prints nothing.
- [x] 2.2 In `isekai/pipeline/caption.py`, `caption(run, reader, *, briefing_path, new_version=False)` writes
  `photo_of(run, CAPTIONS)` and passes `None` to `refusal_for`; its docstring's first paragraph → "**The caption is the
  photograph's.** … written once, under `photo/`, and every flow reads it (D17)."
  Verify: `grep -n -e "belongs to the flow" -e "run.directory(flow" isekai/pipeline/caption.py` prints nothing.
- [x] 2.3 In `isekai/pipeline/tagging.py`, `tag_wd14(run, open_tagger, *, new_version=False)` and
  `tag_hosted(run, tagger, *, new_version=False)` write `photo_of(run, WD14)` and `photo_of(run, TAGS)`, passing `None`
  to `refusal_for`; a docstring or comment naming a flow's directory names `photo/`.
  Verify: `grep -n "run.directory(flow" isekai/pipeline/tagging.py` prints nothing.
- [x] 2.4 In `isekai/interface/cli.py`, per [D6](design.md#d6) and [the verbs](design.md#the-verbs): `caption` and
  `tag` leave the required `--flow` loop and keep it hidden; `dispatch` refuses one; `_require_tagged` is deleted.
  Verify: `git grep -n _require_tagged isekai` prints nothing.
- [x] 2.5 In `isekai/interface/cli.py`'s `_per_item`, `caption` and `tag` run once per identifier with no flow;
  `_Reporter.item` takes `flow: str | None` and leaves `flow` out of a line for `None`; a run that will not open
  reports one `refused` line naming no flow.
  Verify: `grep -n -e "def caption_flow" -e "def tag_flow" isekai/interface/cli.py` prints nothing.
- [x] 2.6 In `isekai/interface/cli.py`, the comment above the `--flow` loop, the module docstring's "The stage verbs
  and `assign` take `--flow` repeatably", `_per_item`'s docstring and `_flows_for`'s "The parser has already refused a
  stage verb naming none" say `tag` and `caption` take no flow ([D14](design.md#d14)).
  Verify: `grep -n "Every stage but the inspection one is per flow" isekai/interface/cli.py` prints nothing.
- [x] 2.7 In `isekai/pipeline/sheet.py`, per [D8](design.md#d8) and [the readers](design.md#the-readers): the fill,
  `_superseded` and `_route` read `photo_of(run, WD14)`; `_from_source`, `tagger_of` and `sheet_source` are deleted;
  `tags_from` is recorded only; the refusals and remedies name `photo/wd14/` and `python -m isekai tag`.
  Verify: `grep -n -w -e tagger_of -e sheet_source -e _from_source -e listed_from isekai/pipeline/sheet.py` prints nothing.
- [x] 2.8 In `isekai/pipeline/sheet.py`'s docstrings: the module's "the flow decides only which directory is read and
  written" → "the flow decides only which directory is written"; `sheet`'s and `prepare_sheet`'s say `tags_from` is
  recorded and never read for the fill.
  Verify: `grep -n "which directory is read and written" isekai/pipeline/sheet.py` prints nothing.
- [x] 2.9 In `isekai/foundation/artifacts.py`, `SheetProducer` loses `listed_from`, and the comment above it says
  `tags_from` names the flow a draft drew a first sheet from (D17).
  Verify: `grep -n listed_from isekai/foundation/artifacts.py` prints nothing.
- [x] 2.10 In `isekai/interface/drafting.py`, `draft_across`'s docstring: "has its sheet filled first from the tag
  list `source` leads to (`tagger_of`)" → "has its sheet filled first from the photograph's tag list, recording
  `source`".
  Verify: `grep -n tagger_of isekai/interface/drafting.py` prints nothing.
- [x] 2.11 In `isekai/interface/ui/app.py`, per [D9](design.md#d9): `_caption` and `_listed` and the import of
  `sheet_source` and `tagger_of` go; the payload reads `photo_of`, loses `caption_from` and its comment; `_prose`,
  `_remedy` and `_command` name no flow for `tag` and `caption`.
  Verify: `grep -n -e caption_from -e tagger_of -e sheet_source -e "def _listed" isekai/interface/ui/app.py` prints nothing.
- [x] 2.12 In `isekai/interface/ui/app.py`, `cell_event` returns a list of events per [Prepare's
  plan](design.md#prepares-plan), and its docstring says a line naming no flow gives one per assigned flow.
  Verify: `grep -n -F "Callable[[Mapping[str, Any]], dict[str, Any] | None]" isekai/interface/ui/app.py` prints nothing.
- [x] 2.13 In `isekai/interface/ui/jobs.py`, per [D10](design.md#d10): `Step.flow` is `str | None`, `plan`,
  `isekai_command`, `Command`, `_Job.asked`, `_Job.complete`, `Jobs.prepare`'s `cell`, `_run` and its failure message
  follow [Prepare's plan](design.md#prepares-plan); the comment above `PREPARE` says tag and caption run once.
  Verify: `uv run python -c 'from isekai.interface.ui.jobs import plan; print([(s.flow, s.verb, s.runs) for s in plan({"a": ["r1"], "b": ["r1", "r2"]}, {"a": True, "b": True})])'` prints `[(None, 'tag', ('r1', 'r2')), (None, 'caption', ('r1', 'r2')), ('a', 'sheet', ('r1',)), ('b', 'sheet', ('r1', 'r2'))]`.
- [x] 2.14 In `isekai/interface/ui/library.py`'s `stage`, "tagged" reads `photo_of(run, WD14)` inside the cell's `try`
  ([D9](design.md#d9)).
  Verify: `grep -n "run.directory(flow, WD14)" isekai/interface/ui/library.py` prints nothing.
- [x] 2.15 In `isekai/interface/run_view.py`, per [the readers](design.md#the-readers): `STAGES` gives way to
  `photo/`'s `DESCRIPTION`, listed first, and a flow's `(SHEETS, REVIEW, PROMPTS)`; `unread` reads `photo/` and names a
  flow's description directories; `_producer_of` prints `from NNN`; the comment above the stages states the layout.
  Verify: `grep -n -e listed_from -e tagged_from -e "Every one of them is a flow's own" isekai/interface/run_view.py` prints nothing.
- [x] 2.16 In `isekai/interface/compare_view.py`'s `_entry`, one caption per run from `photo_of(run, CAPTIONS)`, naming
  no flow; its docstring says so.
  Verify: `grep -n "run.directory(name, CAPTIONS)" isekai/interface/compare_view.py` prints nothing.
- [x] 2.17 In `tests/stages.py`, `caption` and `write_wd14` take no `flow` and write `photo/`; `sheet` calls
  `write_wd14` with none.
  Verify: `uv run python -c 'import inspect, tests.stages as s; print([n for f in (s.caption, s.write_wd14) for n in inspect.signature(f).parameters if n == "flow"])'` prints `[]`.
- [x] 2.18 In `tests/test_caption.py`, per [Tests](design.md#tests): the two second-flow tests go and
  `test_every_flow_reads_the_one_caption` (`caption:output:every-flow-reads-one-caption`) is added; every other test
  calls `caption` with no flow and reads `photo/captions/`.
  Verify: `uv run pytest tests/test_caption.py` exits 0.
- [x] 2.19 In `tests/test_tagging.py`: the two untagged-flow refusals go, and their twin
  `test_tagging_the_tagged_flow_alone_from_that_root_succeeds` runs `tag <photo>` over `_untagged_flows`; `test_tagging_a_tracked_flow_resolves_and_runs_the_local_tagger`
  becomes `test_tagging_resolves_and_runs_the_local_tagger_with_no_flow` (`cli:resolution:the-pinned-tagger-needs-no-flow`);
  every other test tags with no flow, reads `photo/` and expects commands with no `--flow`.
  Verify: `uv run pytest tests/test_tagging.py` exits 0.
- [x] 2.20 In `tests/test_sheet_stage.py`, per [Tests](design.md#tests): the three borrow tests go, the two named there
  are rewritten in place, no test naming `listed_from` or `tagger_of`; every other test reads the list from
  `photo/wd14/` and expects `photo/wd14/` in its text.
  Verify: `uv run pytest tests/test_sheet_stage.py` exits 0.
- [x] 2.21 In `tests/test_pipeline_cli.py`: `STAGE_VERBS` is `("sheet", "review", "approve", "generate")`;
  `test_the_photographs_verbs_refuse_a_flow` over `caption` and `tag` and `test_a_photographs_progress_line_names_no_flow`
  are added, per [the key moves](design.md#the-key-moves); `tag` and `caption` argv name no flow.
  Verify: `uv run pytest tests/test_pipeline_cli.py` exits 0.
- [x] 2.22 In `tests/test_run_directory.py`, the layout tests assert [the layout](design.md#the-layout), and
  `test_every_flow_reads_the_description` (`run-directory:layout:every-flow-reads-the-description`) is added; the
  failure tests read `photo/`.
  Verify: `uv run pytest tests/test_run_directory.py` exits 0.
- [x] 2.23 In `tests/test_resume.py`, `tests/test_review.py`, `tests/test_progress.py`, `tests/test_generate.py` and
  `tests/test_artifact_bytes.py`, `tag`, `caption`, `tag_wd14`, `tag_hosted` and `stages.caption` name no flow, and the
  description is read from `photo/`.
  Verify: `uv run pytest tests/test_resume.py tests/test_review.py tests/test_progress.py tests/test_generate.py tests/test_artifact_bytes.py` exits 0.
- [x] 2.24 In `tests/test_run_view.py`, `show`'s tests follow [the readers](design.md#the-readers), and
  `test_the_description_is_listed_once` (`cli:show:the-description-is-listed-once`) is added; in
  `tests/test_compare.py`, each run carries one caption.
  Verify: `uv run pytest tests/test_run_view.py tests/test_compare.py` exits 0.
- [x] 2.25 In `tests/test_ui_api.py`, per [Tests](design.md#tests): the three borrow tests and `_two_hops` go;
  `test_every_flow_shows_the_photographs_caption` and `test_every_flow_shows_the_photographs_lists` are added; the
  missing-caption test expects a command naming no flow.
  Verify: `uv run pytest tests/test_ui_api.py` exits 0.
- [x] 2.26 In `tests/test_ui_jobs.py`, `test_a_photograph_is_described_once` (`ui:prepare:a-photograph-is-described-once`)
  is added and the totals test counts photographs and cells; in `tests/test_ui_library.py`,
  `test_a_photograph_tagged_once_is_tagged_in_every_flow` (`ui:hub:a-tagged-photograph-is-tagged-in-every-flow`);
  `tests/test_ui.py`'s `Step` takes `None` for a photograph's stage; `tests/test_ui_jobs.py`'s `_Script.__call__` takes
  `flow: str | None`, and the `cell` doubles in `tests/test_ui.py` and `tests/test_ui_jobs.py` return a list.
  Verify: `uv run pytest tests/test_ui_jobs.py tests/test_ui_library.py tests/test_ui.py` exits 0.
- [x] 2.27 The borrow is gone from the Python side.
  Verify: `git grep -n -w -e tagger_of -e sheet_source -e _from_source -e listed_from -- isekai tests` prints nothing.

## 3 — The page

- [x] 3.1 In `ui/src/types.ts`, `caption_from` and the comment above it go; in `ui/src/views/Review.vue`, the
  `:caption-from` binding goes ([D11](design.md#d11)).
  Verify: `git grep -n -e caption_from -e caption-from -- ui/src/types.ts ui/src/views/Review.vue` prints nothing.
- [x] 3.2 In `ui/src/components/SourcePanel.vue`, the `captionFrom` prop and `:from="captionFrom"` go; in
  `ui/src/components/CaptionPanel.vue`, the `from` prop, its comment and `<template v-if="from"> · {{ from }}</template>` go.
  Verify: `git grep -n -e captionFrom -e "v-if=\"from\"" -- ui/src/components` prints nothing.
- [x] 3.3 In `ui/src/composables/useSheet.test.ts`, the fixture's `caption_from: null` goes.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [x] 3.4 In `tests/e2e/test_render.py`'s `test_conjure_from_this_opens_review`,
  `to_contain_text(f"caption · {FLOW}")` → `to_have_text("② caption")` on `[data-caption-heading]`.
  Verify: `grep -c 'to_have_text("② caption")' tests/e2e/test_render.py` prints `1`.
- [x] 3.5 The source pane's borrow is gone, as the brief's check states.
  Verify: `git grep -n -e tagger_of -e listed_from -e caption_from -- isekai ui/src` prints nothing.

## 4 — The record

- [ ] 4.1 In `docs/decisions.md`, amend D1, D17, D31 and D38 per [the record](design.md#the-record), each `Made by:`
  gaining `` `0103` ``.
  Verify: `grep -c "Made by:.*0103" docs/decisions.md` prints `4`.
- [ ] 4.2 In `docs/data-flow.md`: the diagram (`:14-42`) writes `tag` and `caption` into `photo/`; the `--flow`
  paragraph (`:77-92`) and Prepare's (`:94-97`) say `tag` and `caption` take no flow; the run directory (`:137-160`)
  draws [the layout](design.md#the-layout) and names `isekai migrate`.
  Verify: `grep -n "isekai migrate" docs/data-flow.md` prints the line naming it.
- [ ] 4.3 In `README.md`: the verbs (`:97-113`) and the batch (`:222-228`) run `tag` and `caption` with no `--flow`;
  the layout (`:121-124`) names `photo/`; the draft (`:154-162`) fills from the photograph's tags; the flags
  (`:305-310`) say `--flow` is for a stage on a flow; a line names `isekai migrate`.
  Verify: `grep -n -E "(tag|caption) --flow" README.md` prints nothing.
- [ ] 4.4 In `docs/modules.md`, `:44`'s jobs line says tag and caption run once per photograph, `:48-52` drop the
  borrow, and `foundation/migrate.py` is in the graph.
  Verify: `grep -n "migrate.py" docs/modules.md` prints the line naming it.
- [ ] 4.5 In `isekai/foundation/README.md`, `run.py`'s row names `photo/` and `photo_of`, a `migrate.py` row is added,
  and the "Imported by" table names `migrate.py`'s importers.
  Verify: `grep -c -E "^[|] .migrate[.]py. [|]" isekai/foundation/README.md` prints `2`, its row in each table.
- [ ] 4.6 In `isekai/pipeline/README.md` (`:6-8`, `:25`), `isekai/interface/README.md` (`:18`, `:26`) and
  `isekai/interface/ui/README.md` (`:9`, `:25`), the description is the photograph's and tag and caption run once.
  Verify: `git grep -n -e "resolves the reader and the two taggers per flow" -e "Every stage is per flow" -- isekai` prints nothing.
