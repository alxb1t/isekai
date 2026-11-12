# The refactor's rails — tasks

Tests, tools and documents alone: the stage rule, the ratchets, the importer tables, then the frozen files and the stale claims. Decisions are in [design](design.md).

## Progress

- [x] 4 — The stage rule · moderate
- [x] 5 — The ratchets · moderate
- [x] 6 — The importer tables · moderate
- [x] 7 — The frozen files and the documents · moderate

## 4 — The stage rule

- [x] 4.1 In `tests/test_layers.py`, rewrite `stage_imports` per [D1](design.md#d1): add `def _stage(dotted)`, which returns the segment after `isekai.pipeline.`, and flag an edge when importer and module both have a stage and the stages differ. Reword the docstring to say so.
  Verify: `git grep -n -F "def _stage(" -- tests/test_layers.py` prints the definition.

- [x] 4.2 In `tests/test_layers.py`, add `test_a_stage_package_may_import_its_own_modules`, whose `_package` tree holds `isekai/pipeline/review/__init__.py` importing `isekai.pipeline.review.drafts` and expects `set()`, and `test_the_check_catches_a_stage_package_importing_another`, whose tree has `review/drafts.py` importing `isekai.pipeline.generate` and `generate.py` importing the package `isekai.pipeline.review`, and expects both edges. Each carries `spec_exempt("structural: twin of test_no_stage_imports_another")`.
  Verify: `uv run pytest tests/test_layers.py -k stage_package -q` exits 0.

- [x] 4.3 **HALT CHECK** Run the repository's guard after the rewrite: a red `test_no_stage_imports_another` means a stage package already stands that the plan did not read. Edit nothing and stop.
  Verify: `uv run pytest tests/test_layers.py -k no_stage_imports_another -q` exits 0.

- [x] 4.4 In `docs/principles.md`, add the sentence of [D2](design.md#d2) to the component principle, after *a package earns its place when the contract needs more than one file*, linking `decisions.md#d55--a-stage-may-be-a-package`.
  Verify: `git grep -n -F "a stage is the first segment under" -- docs/principles.md` prints the edited line.

- [x] 4.5 In `docs/decisions.md`, add D55 under *Code and environment*, after D48 and before `## Infrastructure`, with the text of [D2](design.md#d2).
  Verify: `git grep -n -F "### D55 · A stage may be a package" -- docs/decisions.md` prints the heading.

## 5 — The ratchets

- [x] 5.1 Create `tests/test_ratchets.py` with a module docstring, `REPO_ROOT`, the ceilings `FILE_LINES`, `FUNCTION_LINES`, `POSITIONAL` and `UI_FILE_LINES` of [D4](design.md#d4), and `ratchet_faults(measured, listed, rows)` of [D3](design.md#d3). Add `test_the_ratchet_catches_each_way_a_table_goes_wrong`, asserting an unlisted offender, a stale row and a row count off its ceiling, each its own fault, with `spec_exempt("structural: a ratchet reads each way a table goes wrong")`.
  Verify: `uv run pytest tests/test_ratchets.py -k ratchet_catches -q` exits 0.

- [x] 5.2 In `tests/test_ratchets.py`, add `long_files(root)` per [D4](design.md#d4), the guard `test_no_long_file_is_unlisted` over `REPO_ROOT`, and its twin `test_the_check_catches_a_long_file`, whose `tmp_path` tree holds a file at the ceiling and one past it, with the reasons of [Tests](design.md#tests). Print the offenders with `uv run python -c "from pathlib import Path; from tests.test_ratchets import long_files; print(long_files(Path('.')))"`, write them as `LONG_FILES`, and set `FILE_ROWS` to its length.
  Verify: `uv run pytest tests/test_ratchets.py -k long_file -q` exits 0.

- [x] 5.3 In `tests/test_ratchets.py`, add `long_functions(root)` per [D4](design.md#d4), the guard `test_no_long_function_is_unlisted` and its twin `test_the_check_catches_a_long_function`, whose tree holds a method and a nested function past the ceiling and a decorated one at it, with the reasons of [Tests](design.md#tests). Print with `long_functions`, write `LONG_FUNCTIONS` and set `FUNCTION_ROWS`, as in 5.2.
  Verify: `uv run pytest tests/test_ratchets.py -k long_function -q` exits 0.

- [x] 5.4 In `tests/test_ratchets.py`, add `wide_functions(root)` per [D4](design.md#d4), the guard `test_no_wide_function_is_unlisted` and its twin `test_the_check_catches_a_wide_function`, whose tree holds a method with `self` and a full list, one with `*args` and keyword-only parameters past the list, and a positional-only one, with the reasons of [Tests](design.md#tests). Write `WIDE_FUNCTIONS` and set `WIDE_ROWS`, as in 5.2.
  Verify: `uv run pytest tests/test_ratchets.py -k wide_function -q` exits 0.

- [x] 5.5 In `tests/test_ratchets.py`, add `big_ui_files(root)` per [D4](design.md#d4), the guard `test_no_big_ui_file_is_unlisted` and its twin `test_the_check_catches_a_big_ui_file`, whose `ui/src` tree holds a `.vue`, a `.css` and a `.test.ts` past the ceiling, with the reasons of [Tests](design.md#tests). Write `BIG_UI_FILES` and set `UI_ROWS`, as in 5.2.
  Verify: `uv run pytest tests/test_ratchets.py -k big_ui_file -q` exits 0.

- [x] 5.6 In `tests/test_ratchets.py`, add `patched_modules(root)` per [D5](design.md#d5), the guard `test_no_patched_module_is_unlisted` and its twin `test_the_check_catches_a_patched_module`, whose tree patches a name through each form of [D5](design.md#d5), a name the module does not bind, an unresolved target and a module of `evaluation`, with the reasons of [Tests](design.md#tests). Write `PATCHED_MODULES` from its output and set `PATCHED_ROWS`, as in 5.2.
  Verify: `uv run pytest tests/test_ratchets.py -k patched_module -q` exits 0.

- [x] 5.7 In `docs/decisions.md`, add D56 under *Code and environment*, after D55, with the text of [D6](design.md#d6).
  Verify: `git grep -n -F "### D56 · Size and patches are held by ratchets" -- docs/decisions.md` prints the heading.

## 6 — The importer tables

- [x] 6.1 Create `tools/import_graph.py` per [D7](design.md#d7): `PACKAGES`, `Edge`, and `module_name`, `is_module`, `sources`, `imports` and `edges`, moved from `tests/test_layers.py` with their bodies, stdlib only.
  Verify: `uv run python -c "import tools.import_graph"` exits 0.

- [x] 6.2 In `tests/test_layers.py`, import the graph from `tools.import_graph`, delete `def _edges` and the other definitions it replaces, rename each reader of `_edges`, `_module_name`, `_is_module`, `_sources` and `_imports` to the public name, and update the module docstring to say the graph lives in the tool.
  Verify: `git grep -n -F "def _edges" -- tests/test_layers.py` prints nothing and exits 1.

- [x] 6.3 Create `tools/derive_imported_by.py` per [D8](design.md#d8): `TABLES`, the note, `derive(root, readme)` and a `main` that writes each table in `TABLES`, run as `python -m tools.derive_imported_by`.
  Verify: `uv run python -c "import tools.derive_imported_by"` exits 0.

- [x] 6.4 Run `uv run python -m tools.derive_imported_by`, which replaces each note that begins `Named, not counted` and writes the table of each README it names. Move the prose of the old cell of the boundary table's `pod_start.py` row into a note under the table, and read each README's diff against its old cells before keeping it.
  Verify: `git grep -n -F "Named, not counted" -- isekai/foundation/README.md isekai/shared/README.md isekai/boundary/README.md isekai/pipeline/README.md isekai/interface/README.md evaluation/README.md` prints nothing and exits 1.

- [x] 6.5 The tests column is gone from each table the deriver wrote.
  Verify: `git grep -n -E '^\|.*.tests/' -- isekai/foundation/README.md isekai/shared/README.md isekai/boundary/README.md isekai/pipeline/README.md isekai/interface/README.md evaluation/README.md` prints nothing and exits 1.

- [x] 6.6 In `isekai/interface/README.md`, replace the `ui/app.py` row's route list, which begins `GET /api/library`, with what [D10](design.md#d10) says.
  Verify: `git grep -n -F "GET /api/library" -- isekai/interface/README.md` prints nothing and exits 1.

- [x] 6.7 In the `derive` recipe of `Makefile`, which is not the `gate` recipe, add the deriver's line after the `derive_field_map` line and before the `$(MAKE) drift` line, and say so in the comment above:
  ```diff
  - # vocabulary, then the fetched ones.
  + # vocabulary, the READMEs' importer tables, then the fetched ones.
  + 	uv run python -m tools.derive_imported_by
  ```
  Verify: `git grep -n -F "tools.derive_imported_by" -- Makefile` prints the added line.

- [x] 6.8 In `docs/principles.md`, add the test of 6.9 that re-derives each table, `test_every_imported_by_table_is_the_one_the_deriver_writes` of `tests/test_docs.py`, to the *Held by* of *Configuration is declared, never computed, and declared once*, in the form its other lines take.
  Verify: `git grep -n -F "test_every_imported_by_table_is_the_one_the_deriver_writes" -- docs/principles.md` prints the added line.

- [x] 6.9 In `tests/test_docs.py`, per [D9](design.md#d9), add `test_every_imported_by_table_is_the_one_the_deriver_writes`, parametrized over each README the deriver names, the guard `test_every_readme_with_an_imported_by_table_is_derived`, and the twins `test_the_deriver_catches_a_stale_table` and `test_the_deriver_refuses_a_row_naming_no_module`, over `tmp_path` trees that hold `isekai`, `evaluation` and `tools`. Each carries `spec_exempt("structural: …")`, a twin `structural: twin of <the guard>`.
  Verify: `uv run pytest tests/test_docs.py -k "imported_by or deriver" -q` exits 0.

## 7 — The frozen files and the documents

- [x] 7.1 In `AGENTS.md`, add one bullet to *Guardrails* with the text of [D11](design.md#d11), naming each file `config/image.json` records in backticks and linking `docs/pins.md`.
  Verify: `git grep -n -F "isekai/boundary/pod_start.py" -- AGENTS.md` prints the bullet.

- [x] 7.2 In `tests/test_infra.py`, add `record_failure(faults)` per [D11](design.md#d11), make `test_the_build_record_agrees_with_the_tree` assert its fault list against `record_failure(...)` as the message, and add `test_the_record_failure_names_the_files_and_the_recipe`, asserting a fault, `tools.image_record` and `docs/pins.md` in the message, with the reasons of [Tests](design.md#tests).
  Verify: `uv run pytest tests/test_infra.py -k record_failure -q` exits 0.

- [x] 7.3 In `tests/test_infra.py`, add `unnamed_frozen_files(text, config)`, the guard `test_agents_names_every_file_the_image_record_holds` over `AGENTS.md` and `IMAGE_CONFIG`, and its twin `test_the_guardrail_check_catches_a_file_left_out`, over a text that names all but one, with the reasons of [Tests](design.md#tests).
  Verify: `uv run pytest tests/test_infra.py -k "guardrail or every_file_the_image_record" -q` exits 0.

- [x] 7.4 In `docs/principles.md`, add the *Known breaks* and *Not yet held* entries of [D12](design.md#d12) to the principles it names.
  Verify: `git grep -n -F "_refuse_bad_source" -- docs/principles.md` prints the entry.

- [x] 7.5 In `ARCHITECTURE.md` and `docs/principles.md`, correct the layer roles of `shared` and `foundation`, and in `docs/principles.md` the role of `boundary`, as [D13](design.md#d13) says.
  Verify: `git grep -n -F "the placement's maths" -- ARCHITECTURE.md docs/principles.md` prints a line in each file.

- [x] 7.6 In `docs/modules.md`, correct the lazy edge of `wiring.py` and the delete's sentence, as [D13](design.md#d13) says.
  Verify: `git grep -n -F "DigestMismatch" -- docs/modules.md` prints the edited line.

- [x] 7.7 In `isekai/interface/README.md`, replace the sibling paragraph with the text of [D13](design.md#d13).
  Verify: `git grep -n -F "the UI imports no CLI module" -- isekai/interface/README.md` prints the edited line.

- [x] 7.8 In `docs/pins.md`, add `tools/derive_eval_manifest.py` and `evaluation/eval_models.json` to *A model manifest*, and in the docstring of `write` in `tools/manifest.py`, say *every manifest deriver*.
  Verify: `git grep -n -F "tools/derive_eval_manifest.py" -- docs/pins.md` prints the added line.
