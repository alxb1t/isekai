# The stage tables — tasks

Hold the tables above the foundation to the stage record by one guard, read `_KINDS`' keys from the record, and write Prepare's order and its tag rule once, in `isekai/foundation/producers.py`. No printed byte changes.

## Progress

- [x] 1 — The guard · moderate
- [x] 2 — The kinds · moderate
- [ ] 3 — Prepare · moderate
- [ ] 4 — The documents · moderate

## 1 — The guard

- [x] 1.1 **HALT CHECK** The tables stand where [the design](design.md#context) reads them.
  Verify: `git grep -c -e "^_KINDS: " -e "^STAGES: " -e "^_WRITES: " -e "^REACHED = " -e "^_BUILDERS: " -- isekai/interface` prints `isekai/interface/cli.py:1`, `isekai/interface/run_view.py:1`, `isekai/interface/ui/jobs.py:1`, `isekai/interface/ui/library.py:1` and `isekai/interface/verbs/runner.py:1`.
- [x] 1.2 **HALT CHECK** The chain has moved `PREPARE` to `isekai/interface/progress.py` and `jobs.py` reads it from there ([D5](design.md#d5)).
  Verify: `git grep -c -e "^PREPARE[: =]" -- isekai/interface` prints `isekai/interface/progress.py:1`, and no other file.
- [x] 1.3 In `tests/test_run_directory.py` add the imports of [D1](design.md#d1), and after `test_the_stage_tables_are_read_from_the_record` add `_off_the_record`, `_tables` and the guard and its twin, as that block gives them. The guard passes on today's code.
  Verify: `uv run pytest tests/test_run_directory.py -k "each_stage_tables_keys or table_with_a_key"` exits 0.
- [x] 1.4 Run `uv run ruff check --fix tests/test_run_directory.py`, which sorts the imports, then `uv run ruff format tests/test_run_directory.py`.
  Verify: `uv run ruff format --check tests/test_run_directory.py` exits 0.
- [x] 1.5 Confirm the guard beside the suite, the layers and the types.
  Verify: `uv run pytest tests/test_run_directory.py tests/test_layers.py tests/test_ratchets.py` exits 0.
- [x] 1.6 Check the types of the guard's tables.
  Verify: `uv run ty check` exits 0.

## 2 — The kinds

- [x] 2.1 In `tests/test_ui_library.py` add `test_a_rows_kind_is_what_its_newest_stage_folder_says` after `test_collections_are_ordered_by_their_newest_file`, with that test's `spec` marker. It is parametrized by scope, folder and word: `photo`, `captions`, `caption`; `photo`, `wd14`, `tag`; `photo`, `tags`, `tag`; `SUMMON`, `sheets`, `sheet`; `SUMMON`, `review`, `review`; `SUMMON`, `prompts`, `prompt`; `SUMMON`, `outputs`, `render`. Each writes `runs/x/<scope>/<folder>/001.json` holding `b"{}"` in a collection, gives that file a later time than its source's with `os.utime`, and asserts the one row of `library.rows(tmp_path, OFFERED, FLOWS_DIR)` has `kind` equal to the word. It passes on today's code.
  Verify: `uv run pytest tests/test_ui_library.py -k a_rows_kind_is_what_its_newest_stage_folder_says` exits 0.
- [x] 2.2 In `isekai/interface/ui/library.py` replace the comment and the literal `_KINDS`, whose first line holds `CAPTIONS: "caption"`, with the block of [D2](design.md#d2), and add `PRODUCERS` to the import from `isekai.foundation.run`.
  Verify: `git grep -n -F 'CAPTIONS: "caption"' -- isekai/interface/ui/library.py` prints nothing.
- [x] 2.3 Run `uv run ruff check isekai/interface/ui/library.py`: it names `CAPTIONS`, `OUTPUTS`, `PROMPTS` and `TAGS` as unused. Delete each from the import from `isekai.foundation.run`, then run `uv run ruff format isekai/interface/ui/library.py`.
  Verify: `uv run ruff check isekai/interface/ui/library.py` exits 0.
- [x] 2.4 Confirm the kinds, the guard and the layers.
  Verify: `uv run pytest tests/test_ui_library.py tests/test_run_directory.py tests/test_ui.py tests/test_layers.py` exits 0.
- [x] 2.5 Replay the mutants the repository keeps, `UB-14` on `library.py` among them.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.

## 3 — Prepare

- [ ] 3.1 **HALT CHECK** No name of Prepare's rule is taken.
  Verify: `git grep -n -w -e tagged_runs -- isekai tests tools evaluation` prints nothing.
- [ ] 3.2 In `tests/test_ui_jobs.py` add `test_prepare_plans_tag_for_the_runs_a_tagged_flow_names` after `test_a_photograph_is_described_once`, with that test's `spec` markers, holding the plan cases of [D6](design.md#d6). Each case is `plan(...)` compared with a list of `Step`. It passes on today's code.
  Verify: `uv run pytest tests/test_ui_jobs.py -k prepare_plans_tag_for_the_runs` exits 0.
- [ ] 3.3 In `tests/test_pipeline_cli.py` add `test_prepare_tags_a_photograph_any_of_whose_flows_tags` after `test_prepare_leaves_out_tag_for_a_photograph_no_flow_tags`, with the `cli:prepare:no-tagger-no-tag-step` marker, as [D6](design.md#d6) says. It passes on today's code.
  Verify: `uv run pytest tests/test_pipeline_cli.py -k prepare_tags_a_photograph_any_of_whose_flows_tags` exits 0.
- [ ] 3.4 Before any line moves run `tools.mutate` over `plan`: `grep -n -e "^def plan" -e "^def cells_of" isekai/interface/ui/jobs.py`, then `uv run python -m tools.mutate isekai/interface/ui/jobs.py:<first>-<last> --tests tests/test_ui_jobs.py tests/test_pipeline_cli.py`, `<first>` the `def plan` line and `<last>` the last line of `plan`, which is the line before the blank lines over `def cells_of`. Kill each survivor with a case in `tests/test_ui_jobs.py`.
  Verify: `uv run pytest tests/test_ui_jobs.py tests/test_pipeline_cli.py` exits 0.
- [ ] 3.5 Before any line moves run it over the verb's steps: `grep -n -e "^    by_run: dict" -e "^        collected.extend(across(steps" isekai/interface/verbs/prepare.py`, then `uv run python -m tools.mutate isekai/interface/verbs/prepare.py:<first>-<last> --tests tests/test_pipeline_cli.py`, the numbers it printed. Kill each survivor with a case in `tests/test_pipeline_cli.py`.
  Verify: `uv run pytest tests/test_pipeline_cli.py` exits 0.
- [ ] 3.6 In `tests/test_run_directory.py` add `PREPARE` and `tagged_runs` to the import from `isekai.foundation.run`, and add `test_prepares_order_is_tag_caption_sheet_and_the_records_verbs` and `test_tagged_runs_names_each_run_a_tagged_flow_lists_once_in_its_order` of [D6](design.md#d6) after the guard's twin, each with `@pytest.mark.spec_exempt("structural: ...")`.
  Verify: `uv run pytest tests/test_run_directory.py -k "prepares_order or tagged_runs_names"` exits 2, on the import of `PREPARE`.
- [ ] 3.7 In `isekai/foundation/producers.py` add `from collections.abc import Mapping, Sequence`, then `PREPARE` and `tagged_runs` after `producer_for` exactly as [D3](design.md#d3) gives them, and a sentence naming both in the module docstring.
  Verify: `git grep -c -e "^PREPARE" -e "^def tagged_runs" -- isekai/foundation/producers.py` prints `isekai/foundation/producers.py:2`.
- [ ] 3.8 In `isekai/foundation/run.py` add both names to the import from `isekai.foundation.producers` and to `__all__`, in the order `ruff` keeps.
  Verify: `uv run pytest tests/test_run_directory.py tests/test_layers.py` exits 0.
- [ ] 3.9 Run `tools.mutate` over `tagged_runs`: `grep -n -e "^def tagged_runs" isekai/foundation/producers.py` and `grep -c "" isekai/foundation/producers.py`, then `uv run python -m tools.mutate isekai/foundation/producers.py:<first>-<last> --tests tests/test_run_directory.py`, `<first>` the first number and `<last>` the file's last line, the second. Kill each survivor with a case in `tests/test_run_directory.py`.
  Verify: `uv run pytest tests/test_run_directory.py` exits 0.
- [ ] 3.10 In `isekai/interface/ui/jobs.py` replace `plan` with the function of [D4](design.md#d4), drop `PREPARE` from its import from `isekai.interface.progress`, and add `PHOTOGRAPH_VERBS`, `PREPARE` and `tagged_runs` to its import from `isekai.foundation.run`.
  Verify: `uv run python -c "from isekai.interface.ui import jobs; from isekai.foundation.run import PREPARE; assert jobs.PREPARE is PREPARE"` exits 0.
- [ ] 3.11 Confirm the app's plan and the cases of the record.
  Verify: `uv run pytest tests/test_ui_jobs.py tests/test_run_directory.py` exits 0.
- [ ] 3.12 In `tests/test_progress.py`, which the chain adds, take `PREPARE` out of each import from `isekai.interface.progress`, read each `progress.PREPARE` as `PREPARE`, and add the line `from isekai.foundation.run import PREPARE`, as [D5](design.md#d5) says. No assertion changes.
  Verify: `git grep -c -F "from isekai.foundation.run import PREPARE" -- tests` prints `tests/test_progress.py:1`.
- [ ] 3.13 In `isekai/interface/progress.py` delete the definition of Prepare's order, its comment, and each other line of the file that names it, as [D5](design.md#d5) says.
  Verify: `git grep -n -e "^PREPARE[: =]" -- isekai/interface` prints nothing.
- [ ] 3.14 Confirm the chain's test of the declared names and the app's tests hold with the order gone from `progress.py`.
  Verify: `uv run pytest tests/test_progress.py tests/test_ui_jobs.py` exits 0.
- [ ] 3.15 In `run_prepare` of `isekai/interface/verbs/prepare.py` replace the loop over `by_run` with the lines of [D4](design.md#d4), and add `PREPARE` and `tagged_runs` to the import from `isekai.foundation.run`.
  Verify: `git grep -n -F "any(flows[flow].tagger" -- isekai/interface/verbs/prepare.py` prints nothing.
- [ ] 3.16 Run `uv run ruff check --fix` and `uv run ruff format` over `isekai` and `tests`.
  Verify: `uv run ruff format --check isekai tests` exits 0.
- [ ] 3.17 Run `tools.mutate` again over the new lines of `plan` and of the verb's steps, as 3.4 and 3.5 print their ranges, with the same tests.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
- [ ] 3.18 Confirm the verbs, the app, the guard, the chain's tests of the lines, the layers and the ratchets.
  Verify: `uv run pytest tests/test_run_directory.py tests/test_ui_jobs.py tests/test_ui_library.py tests/test_run_view.py tests/test_pipeline_cli.py tests/test_resume.py tests/test_progress.py tests/test_layers.py tests/test_ratchets.py` exits 0.
- [ ] 3.19 Check the types of the new lines.
  Verify: `uv run ty check` exits 0.

## 4 — The documents

- [ ] 4.1 In `docs/decisions.md`, in D73's bold sentence, replace "which reads the row by `producer_for`.**" with "which reads the row by `producer_for`. `PREPARE` and `tagged_runs` beside the record hold Prepare's order by verb and its tag rule, which the app's plan and the `prepare` verb read; `_KINDS` of `ui/library.py` reads its keys from the record, and a test holds the keys of `STAGES`, `_WRITES`, `PREPARE`, `REACHED` and the runner's `_BUILDERS` to it.**".
  Verify: `git grep -c -F "tagged_runs" -- docs/decisions.md` prints `docs/decisions.md:1`.
- [ ] 4.2 In D73's *Accepts* bullet put: "`STAGES`, `_WRITES`, `REACHED` and the runner's builders stay written, each held to the record by a test, the pipeline's own `STAGE` constants and the hub cell's `Stage` stay as they are, the paid stages, `assemble` and `render`, keep their own sequences, and `review` has a row with no budget. `Producer` gains no field for a table with one reader. Reopen when a second reader of one of those tables earns it a field."
  Verify: `git grep -n -F "Reopen when a second reader of one of those tables earns it a field." -- docs/decisions.md` prints one line.
- [ ] 4.3 In D73's *Made by* bullet add `0201` after `0188`.
  Verify: `git grep -n -e "Made by.*0188.*0201" -- docs/decisions.md` prints one line.
- [ ] 4.4 In `isekai/foundation/README.md` replace the `producers.py` row of *Files* with ``| `producers.py` | the stage record: a frozen `Producer` for each stage a run passes through, in `PRODUCERS`, with its key, folder, scope, verb and budget, `producer_for`, which finds a row by its key, and, beside it, `PREPARE`, Prepare's order by verb, and `tagged_runs`, its tag rule; it imports nothing of `isekai` |``.
  Verify: `git grep -n -F "tagged_runs" -- isekai/foundation/README.md` prints one line.
- [ ] 4.5 Run `uv run python -m tools.derive_imported_by`: no importer edge changes, since `producers.py` imports no module of `isekai` and `jobs.py` and `prepare.py` already import `run.py`.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [ ] 4.6 Confirm the order is written in the foundation alone and no longer in `jobs.py`.
  Verify: `git grep -n -e "^PREPARE" -- isekai/foundation` prints one line.
- [ ] 4.7 Confirm `jobs.py` holds no `PREPARE = (` literal.
  Verify: `git grep -n -F "PREPARE = (" -- isekai/interface/ui/jobs.py` prints nothing.
- [ ] 4.8 Replay the mutants the repository keeps.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
- [ ] 4.9 Confirm the suite, the layers, the docs, the bindings and the wire hold at the end.
  Verify: `uv run pytest tests/test_run_directory.py tests/test_ui_jobs.py tests/test_ui_library.py tests/test_run_view.py tests/test_pipeline_cli.py tests/test_resume.py tests/test_layers.py tests/test_docs.py tests/test_ratchets.py tests/test_spec_bindings.py tests/test_derive_wire.py` exits 0.
