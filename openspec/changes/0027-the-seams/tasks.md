# Tasks — 0027 the seams

Structural phases: the declarations first, then the checks, then each move, then the docs. The checks land
before the moves they hold ([D13](design.md#d13)).

## Progress

- [x] 1 — Declare once: the gate and the encoder window
- [ ] 2 — The checks: layers, held-by names, the vocabulary
- [ ] 3 — `foundation` imports nothing above it
- [ ] 4 — Pin verification moves into `boundary`
- [ ] 5 — The ComfyUI transport becomes `boundary/comfy/`
- [ ] 6 — The approval state moves into `pipeline/review.py`
- [ ] 7 — The docs follow the code

Line numbers are `9b3fca2`'s; find each site by the text it names.

## 1 — Declare once: the gate and the encoder window

- [x] 1.1 **HALT CHECK** — `Makefile` already runs the gate's whole list.
  Verify: `make -n gate | wc -l | tr -d ' '` prints `6`.
- [x] 1.2 **HALT CHECK** — nothing reads `.minions/minions.toml`; only prose names it.
  Verify: `git grep -l 'minions.toml' -- ':!CHANGELOG.md' ':!openspec/changes' | sort | tr '\n' ' '` prints `.github/workflows/ci.yml .gitignore CLAUDE.md Makefile README.md scripts/typecheck_ui.sh `.
- [x] 1.3 `git rm .minions/minions.toml`; rewrite `.gitignore:4-9` to ignore `.minions/` whole, per [D1](design.md#d1).
  Verify: `test ! -e .minions/minions.toml && git check-ignore -q .minions/minions.toml && echo ok` prints `ok`.
- [x] 1.4 Move `CLAUDE.md:42-48`'s note on each command into `Makefile` as a comment above it, and rewrite `Makefile:1-6`'s header, per [D1](design.md#d1).
  Verify: `grep -c -e 'from the tracked lock' -e 'refuses by name' Makefile` prints `2`, and `grep -c minions Makefile` prints `0`.
- [x] 1.5 Rewrite the gate's other mentions per [D1](design.md#d1)'s table: `CLAUDE.md:38-59` and `:168-170`, `README.md:289-310` and `:352`, `.github/workflows/ci.yml:41-44`, `scripts/typecheck_ui.sh:7-11`, `pyproject.toml:57`.
  Verify: `git grep -n -e 'minions.toml' -e 'gate. array' -e 'the array' -- ':!CHANGELOG.md' ':!openspec/changes' ':!isekai/boundary/wd14.py'` prints nothing.
- [x] 1.6 Add `"window": ENCODER_WINDOW` to `isekai/interface/ui/app.py`'s `_budget`, and `test_the_budget_carries_the_encoder_window` to `tests/test_ui_api.py`, per [D2](design.md#d2).
  Verify: `grep -c -e '"window": ENCODER_WINDOW' -e '^def test_the_budget_carries_the_encoder_window' isekai/interface/ui/app.py tests/test_ui_api.py | paste -sd' ' -` prints `isekai/interface/ui/app.py:1 tests/test_ui_api.py:1`.
- [x] 1.7 Read the window from the budget in `ui/src/types.ts`, `ui/src/components/TokenBudget.vue`, `ui/src/components/RunManifest.vue` and `ui/src/ReviewApp.vue`, per [D2](design.md#d2).
  Verify: `grep -rn ENCODER_WINDOW ui/src` prints nothing, and `grep -c 'window: number' ui/src/types.ts` prints `2`.

## 2 — The checks: layers, held-by names, the vocabulary

- [ ] 2.1 **HALT CHECK** — the allowlist's edges exist where [the design's Context](design.md#context) puts them.
  Verify: `grep -n -e '^from isekai.boundary.comfy_types import Workflow$' -e '^from isekai.shared.atomic_write import' -e 'from isekai.evaluation.eval_models import' isekai/foundation/flow.py isekai/foundation/run.py isekai/shared/vocabulary.py isekai/boundary/wd14.py | cut -d: -f1,2 | tr '\n' ' '` prints `isekai/foundation/flow.py:41 isekai/foundation/run.py:42 isekai/shared/vocabulary.py:120 isekai/boundary/wd14.py:242 `.
- [ ] 2.2 Write `tests/test_layers.py`: the AST checker, [D3](design.md#d3)'s rule tests by their names, the exact allowlist and its test, and a twin per rule named `test_the_check_catches_…`.
  Verify: `grep -c -e '^def test_every_import_points_down(' -e '^def test_nothing_in_the_package_imports_evaluation(' -e '^def test_no_stage_imports_another(' -e '^def test_no_import_cycle_inside_a_layer(' -e '^def test_a_layer_init_holds_only_a_docstring(' -e '^def test_a_subpackage_is_reached_only_through_its_front_door(' tests/test_layers.py` prints `6`.
- [ ] 2.3 In `tests/test_layers.py`, give each rule test a twin and add `test_the_allowlist_names_only_imports_that_exist`, per [D3](design.md#d3).
  Verify: `grep -c '^def test_the_check_catches_' tests/test_layers.py` prints `6`, and `grep -c '^def test_the_allowlist_names_only_imports_that_exist(' tests/test_layers.py` prints `1`.
- [ ] 2.4 Write `tests/test_principles.py` per [D4](design.md#d4): every named test exists, one *Held by* per principle, and a twin for each.
  Verify: `grep -c -e '^def test_every_test_a_principle_names_exists(' -e '^def test_every_principle_has_one_held_by_line(' tests/test_principles.py` prints `2`.
- [ ] 2.5 Add `require_vocabulary` to `tests/conftest.py`, and use it at `tests/test_field_map.py:33-40`, `tests/test_vocabulary.py:85-86` and `tests/test_wd14.py:69-75`, comments included, per [D5](design.md#d5).
  Verify: `grep -n -e 'is not provisioned in this environment' -e 'is not provisioned; run' tests/test_field_map.py tests/test_vocabulary.py tests/test_wd14.py` prints nothing.
- [ ] 2.6 Add the twins for `require_vocabulary` to `tests/test_vocabulary.py`, and `ISEKAI_VOCABULARY: absent` to `.github/workflows/ci.yml`'s `Gate` step, per [D5](design.md#d5).
  Verify: `grep -c 'ISEKAI_VOCABULARY: absent' .github/workflows/ci.yml` prints `1`, and `grep -c 'ISEKAI_VOCABULARY' tests/conftest.py` prints a number above `0`.

## 3 — `foundation` imports nothing above it

- [ ] 3.1 `git mv isekai/shared/atomic_write.py isekai/foundation/atomic_write.py`; update `isekai/foundation/run.py`, `isekai/pipeline/generate.py` and `tests/test_run_directory.py:17`, `:214`; drop run.py's allowlist entry. [D6](design.md#d6).
  Verify: `test -f isekai/foundation/atomic_write.py && ! git grep -q 'shared.atomic_write' -- isekai tests scripts && echo ok` prints `ok`.
- [ ] 3.2 Move `Workflow` into `isekai/foundation/flow.py` and update every importer [D6](design.md#d6) lists; drop flow.py's allowlist entry.
  Verify: `grep -rn --include='*.py' '^Workflow = ' isekai | cut -d: -f1` prints `isekai/foundation/flow.py`, and `grep -c comfy_types isekai/foundation/flow.py` prints `0`.
- [ ] 3.3 Update the `atomic_write.py` rows in `isekai/README.md`, `isekai/shared/README.md` and `isekai/foundation/README.md`, per [D12](design.md#d12).
  Verify: `grep -c atomic_write isekai/shared/README.md` prints `0`, and `grep -c atomic_write isekai/foundation/README.md` prints a number above `0`.

## 4 — Pin verification moves into `boundary`

- [ ] 4.1 **HALT CHECK** — `isekai/interface/wiring.py` is the only production caller of the vocabulary loader.
  Verify: `git grep -n 'shared.vocabulary import load' -- isekai | cut -d: -f1,2` prints `isekai/interface/wiring.py:36`.
- [ ] 4.2 Move `entry_for`, `resolve` and their exceptions into `isekai/boundary/provision.py`; pass the eval manifest at `isekai/evaluation/eval_backends.py:159`, `:374`, `:545`; update `tests/test_eval_manifest.py:17-27`. [D7](design.md#d7).
  Verify: `grep -c -e '^def entry_for(' -e '^def resolve(' -e '^class UnknownArtifact' isekai/boundary/provision.py isekai/evaluation/eval_models.py | paste -sd' ' -` prints `isekai/boundary/provision.py:3 isekai/evaluation/eval_models.py:0`.
- [ ] 4.3 Import `entry_for` and `resolve` from `provision` in `isekai/boundary/wd14.py`'s `verified_paths()`; patch `provision.resolve` at `tests/test_wd14.py:41`, `:255`; drop wd14.py's allowlist entry. [D7](design.md#d7).
  Verify: `grep -c eval_models isekai/boundary/wd14.py tests/test_wd14.py | paste -sd' ' -` prints `isekai/boundary/wd14.py:0 tests/test_wd14.py:0`.
- [ ] 4.4 Make `vocabulary.load(path, entry)` and add `wiring.load_vocabulary`, per [D8](design.md#d8); drop vocabulary.py's allowlist entries, leaving it empty.
  Verify: `grep -c -e 'isekai.boundary' -e 'isekai.evaluation' isekai/shared/vocabulary.py` prints `0`, and `grep -c '^def load_vocabulary(' isekai/interface/wiring.py` prints `1`.
- [ ] 4.5 Call `wiring.load_vocabulary` at `scripts/derive_field_map.py:625`, `tests/test_field_map.py:35-40`, `tests/test_vocabulary.py:83-87`, `tests/test_vocabulary_manifest.py:35` and `:290`. [D8](design.md#d8).
  Verify: `git grep -l 'wiring import.*load_vocabulary' -- scripts tests | sort | tr '\n' ' '` prints `scripts/derive_field_map.py tests/test_field_map.py tests/test_vocabulary.py tests/test_vocabulary_manifest.py `.
- [ ] 4.6 Update the rows for `provision.py`, `eval_models.py` and `wiring.py` in `isekai/boundary/README.md`, `isekai/evaluation/README.md` and `isekai/interface/README.md`, per [D12](design.md#d12).
  Verify: `grep -c shared/vocabulary.py isekai/boundary/README.md isekai/evaluation/README.md | paste -sd' ' -` prints `isekai/boundary/README.md:0 isekai/evaluation/README.md:0`.

## 5 — The ComfyUI transport becomes `boundary/comfy/`

- [ ] 5.1 **HALT CHECK** — the CLI's wrapper is used only at `cli.py:522` and by one test.
  Verify: `git grep -n '_Reporting(' -- isekai tests | cut -d: -f1,2 | tr '\n' ' '` prints `isekai/interface/cli.py:522 tests/test_generate.py:735 `.
- [ ] 5.2 `git mv` the transport into `isekai/boundary/comfy/` as `contract.py`, `client.py` and `multipart.py`, and write its `__init__.py` front door, per [D9](design.md#d9)'s tree.
  Verify: `ls isekai/boundary/comfy | grep -v __pycache__ | tr '\n' ' '` prints `__init__.py client.py contract.py multipart.py `.
- [ ] 5.3 Point every importer [D9](design.md#d9) lists at the front door; `tests/test_multipart.py` imports `isekai.boundary.comfy.multipart`.
  Verify: `git grep -n -e comfy_types -e comfy_client -e 'boundary.multipart' -- isekai tests probe` prints nothing.
- [ ] 5.4 Move `_reported()` from `isekai/interface/cli.py:569-586` into `client.py` around every `ComfyClient` method; delete `_Reporting` and its use at `cli.py:522`. [D9](design.md#d9).
  Verify: `grep -c -e _Reporting -e _reported -e urllib.error isekai/interface/cli.py` prints `0`, and `grep -c 'with _reported():' isekai/boundary/comfy/client.py` prints `4`.
- [ ] 5.5 Drive a real `ComfyClient` with `urlopen` patched at `tests/test_generate.py:715-740` and `tests/test_resume.py:545-578`, assertions and bindings unchanged. [D9](design.md#d9).
  Verify: `grep -c -e _Reporting -e 'class Dead' tests/test_generate.py tests/test_resume.py | paste -sd' ' -` prints `tests/test_generate.py:0 tests/test_resume.py:0`.
- [ ] 5.6 Pay `comfy-transport:boundary`: `test_multipart_content_type_declares_the_boundary` builds a body with parts, per [D9](design.md#d9).
  Verify: `grep -c 'build_multipart(fields={}, files={})' tests/test_multipart.py` prints `0`.
- [ ] 5.7 Update the transport's rows in `isekai/README.md`, `isekai/boundary/README.md` and `isekai/foundation/README.md`, per [D12](design.md#d12).
  Verify: `grep -c -e comfy_types -e comfy_client isekai/README.md isekai/boundary/README.md isekai/foundation/README.md | paste -sd' ' -` prints `isekai/README.md:0 isekai/boundary/README.md:0 isekai/foundation/README.md:0`.

## 6 — The approval state moves into `pipeline/review.py`

- [ ] 6.1 **HALT CHECK** — `review.is_complete` has no production caller.
  Verify: `git grep -n 'is_complete' -- isekai | cut -d: -f1,2` prints `isekai/pipeline/review.py:78`.
- [ ] 6.2 Move `Status` and `Batch.state`'s body into `isekai/pipeline/review.py` as `state(directory)`; `Batch.state` passes it the review directory. [D11](design.md#d11).
  Verify: `grep -c '^def state(' isekai/pipeline/review.py` prints `1`, and `grep -c -e 'Status = ' -e approved_versions isekai/interface/ui/batch.py` prints `0`.
- [ ] 6.3 Call `run.is_approved` at `isekai/interface/run_view.py:101`, per [D11](design.md#d11).
  Verify: `grep -c 'group("label") == APPROVED' isekai/interface/run_view.py` prints `0`.
- [ ] 6.4 Delete `review.is_complete`; `tests/test_review.py:172` and `:202` assert `state(directory)`, names and bindings unchanged. [D11](design.md#d11).
  Verify: `git grep -n is_complete -- isekai tests` prints nothing.

## 7 — The docs follow the code

- [ ] 7.1 Rewrite `docs/modules.md`'s edges, lazy edges, cycles and *Reading this graph* to the new graph, per [D12](design.md#d12).
  Verify: `grep -c -e comfy_types -e 'foundation ⇄' -e 'known break' docs/modules.md` prints `0`, and `grep -c test_layers docs/modules.md` prints a number above `0`.
- [ ] 7.2 Apply [D12](design.md#d12)'s table to `docs/principles.md`.
  Verify: `grep -c -e 'decides which transport failures' -e 'written in more than one place' -e 'declared twice' -e 'until the layer test lands' docs/principles.md` prints `0`, and `grep -c 'tests/test_layers.py::' docs/principles.md` prints `7`.
- [ ] 7.3 Edit the preambles [D10](design.md#d10) names: `openspec/specs/comfy-transport/spec.md:8-10`, `:13`, and `openspec/specs/run-directory/spec.md:11`.
  Verify: `grep -n -e comfy_types -e 'boundary/comfy_client' -e 'boundary/multipart' openspec/specs/comfy-transport/spec.md; grep -n shared/atomic_write openspec/specs/run-directory/spec.md` prints nothing.
- [ ] 7.4 Delete the allowlist, `test_the_allowlist_names_only_imports_that_exist`, and every reference to them in `tests/test_layers.py`, per [D3](design.md#d3).
  Verify: `grep -c -i allowlist tests/test_layers.py` prints `0`.
- [ ] 7.5 Re-flow `CLAUDE.md:63`, `:102` and `:127` to the file's wrap (`v0.22.3 review/R10`, residual), per [D12](design.md#d12).
  Verify: `awk 'length > 110 && !/^ *\|/ {print NR}' CLAUDE.md` prints nothing.
- [ ] 7.6 No live file names a moved module by its old path.
  Verify: `git grep -n -e comfy_types -e 'boundary.comfy_client' -e 'boundary/comfy_client' -e 'shared.atomic_write' -e 'shared/atomic_write' -e is_complete -e _Reporting -- ':!CHANGELOG.md' ':!openspec/changes' ':!openspec/specs/comfy-transport/spec.md' ':!pyproject.toml'` prints nothing.
