# The render listing — tasks

Move the render group's listing, then `rendered`, into `isekai/foundation/layout.py`, switch the importers, and write the rule down. Decisions are in [design](design.md).

## Progress

- [x] 1 — The listing · moderate
- [x] 2 — The importers · moderate
- [ ] 3 — The documents · moderate

## 1 — The listing

- [x] 1.1 **HALT CHECK** The flows' module imports the refusal alone of the foundation, so `layout.py` may import it without a cycle ([D1](design.md#d1)).
  Verify: `git grep -n -E "^from isekai" -- isekai/foundation/flow.py` prints one line, the import of `Refusal`.
- [x] 1.2 In `isekai/foundation/layout.py`, add `SIDECAR` to the import from `isekai.foundation.artifacts`. Cut `is_render`, `is_sidecar`, `rendered_seeds`, `sidecars` and `render_groups` from the paid stage and paste them after `_laid_out`, each body, signature and docstring unchanged ([D1](design.md#d1), [D3](design.md#d3)).
  Verify: `git grep -n -e "^def is_render" -e "^def is_sidecar" -e "^def rendered_seeds" -e "^def sidecars" -e "^def render_groups" -- isekai/foundation/layout.py` prints five lines.
- [x] 1.3 In `isekai/foundation/run.py`, add `is_render`, `is_sidecar`, `rendered_seeds`, `sidecars` and `render_groups` to the import from `isekai.foundation.layout`, and `"is_render"`, `"is_sidecar"`, `"rendered_seeds"`, `"sidecars"` and `"render_groups"` to `__all__`, each in the order the file keeps ([D1](design.md#d1)).
  Verify: `git grep -n -F "\"render_groups\"" -- isekai/foundation/run.py` prints one line.
- [x] 1.4 In `isekai/pipeline/generate.py`, add `render_groups` and `rendered_seeds` to the import from `isekai.foundation.run`. Bind `is_render`, `is_sidecar` and `sidecars` as `from isekai.foundation.run import is_render as is_render`, one line each. Remove `OUTPUTS` and `is_seed` from that import, which nothing there reads now ([D4](design.md#d4)).
  Verify: `git grep -n -e "^def is_render" -e "^def is_sidecar" -e "^def rendered_seeds" -e "^def sidecars" -e "^def render_groups" -- isekai/pipeline/generate.py` prints nothing.
- [x] 1.5 In `tests/mutants.json`, set the `path` of `FN-9` to `isekai/foundation/layout.py`; leave its `find` and `replace` as they are ([D7](design.md#d7)).
  Verify: `git grep -n -F "isekai/foundation/layout.py" -- tests/mutants.json` prints one line.
- [x] 1.6 Run `uv run python -m tools.derive_imported_by`, which rewrites the *Imported by* tables of `isekai/foundation/README.md`, `isekai/interface/README.md` and `isekai/pipeline/README.md`.
  Verify: `uv run pytest tests/test_docs.py` passes.
- [x] 1.7 Hold the move with the standing mutants, run once and over no line range ([D7](design.md#d7)).
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.

## 2 — The importers

- [x] 2.1 In `isekai/foundation/layout.py`, add `Sequence` to the `collections.abc` import and `from isekai.foundation.flow import FLOWS_DIR, load_flow`. Cut the `def rendered(` block from `isekai/interface/run_view.py` and paste it after `render_groups`, unchanged, its default `FLOWS_DIR` included ([D1](design.md#d1)).
  Verify: `git grep -n -F "def rendered(" -- isekai/foundation/layout.py` prints one line.
- [x] 2.2 In `isekai/foundation/run.py`, add `rendered` to the import from `isekai.foundation.layout` and `"rendered"` to `__all__`.
  Verify: `git grep -n -F "\"rendered\"" -- isekai/foundation/run.py` prints one line.
- [x] 2.3 In `isekai/interface/run_view.py`, add `is_render`, `is_sidecar`, `render_groups` and `rendered` to the import from `isekai.foundation.run`. Delete the import from `isekai.pipeline.generate`, and `Sequence` from the `collections.abc` import, which nothing there reads now ([D4](design.md#d4), [D5](design.md#d5)).
  Verify: `git grep -n -F "isekai.pipeline.generate" -- isekai/interface/run_view.py` prints nothing.
- [x] 2.4 In `isekai/interface/compare_view.py`, add `rendered_seeds` to the import from `isekai.foundation.run` and delete the import from `isekai.pipeline.generate` ([D5](design.md#d5)).
  Verify: `git grep -n -F "isekai.pipeline.generate" -- isekai/interface/compare_view.py` prints nothing.
- [x] 2.5 In `isekai/interface/render.py`, add `render_groups`, `rendered_seeds` and `sidecars` to the import from `isekai.foundation.run`. Write the import from the stage as `from isekai.pipeline.generate import duration, shortfall` on one line, with no trailing comma ([D5](design.md#d5)).
  Verify: `git grep -n -F "from isekai.pipeline.generate import duration, shortfall" -- isekai/interface/render.py` prints one line.
- [x] 2.6 In `isekai/interface/ui/library.py`, add `is_render` and `rendered_seeds` to the import from `isekai.foundation.run`. Write the import from the stage as `from isekai.pipeline.generate import lacks` ([D5](design.md#d5)).
  Verify: `git grep -n -F "from isekai.pipeline.generate import lacks" -- isekai/interface/ui/library.py` prints one line.
- [x] 2.7 In `isekai/pipeline/generate.py`, delete the line `from isekai.foundation.run import sidecars as sidecars`, which `render.py` no longer reads from the stage ([D4](design.md#d4)).
  Verify: `git grep -n -F "sidecars as sidecars" -- isekai/pipeline/generate.py` prints nothing.
- [x] 2.8 In `evaluation/__main__.py`, write the import from `isekai.foundation.run` as `OUTPUTS, Run, rendered` and delete `from isekai.interface.run_view import rendered`. In `evaluation/recall.py`, add `rendered` to the import from `isekai.foundation.run` and delete the same line ([D5](design.md#d5), [D6](design.md#d6)).
  Verify: `git grep -n -F "isekai.interface.run_view" -- evaluation` prints nothing.
- [x] 2.9 Run `uv run python -m tools.derive_imported_by` again, which rewrites the *Imported by* tables of the three READMEs.
  Verify: `uv run pytest tests/test_docs.py` passes.
- [x] 2.10 **HALT CHECK** The suites that read the listing pass with no test edited; a red one names a patch or an import the move strands, and the plan is wrong ([D4](design.md#d4)).
  Verify: `uv run pytest tests/test_generate.py tests/test_resume.py tests/test_edit_session.py tests/test_run_view.py tests/test_compare.py tests/test_ui_library.py tests/test_render.py tests/test_evaluation_cli.py tests/test_recall_cli.py tests/test_pipeline_cli.py tests/test_layers.py tests/test_ratchets.py tests/test_docs.py tests/test_spec_bindings.py` passes.

## 3 — The documents

- [ ] 3.1 In `docs/decisions.md`, insert the text of D69 from [design](design.md#d8) after D68's *Made by* line, before `## Infrastructure` ([D8](design.md#d8)).
  Verify: `git grep -n -F "### D69" -- docs/decisions.md` prints one line.
- [ ] 3.2 In `isekai/foundation/README.md`, change the `layout.py` row of *Files* from `numbering and completion, the seeds and the edit files` to `numbering and completion, the seeds, a render group's listing and the edit files`.
  Verify: `git grep -n -F "a render group's listing" -- isekai/foundation/README.md` prints one line.
- [ ] 3.3 In the docstring of `isekai/foundation/layout.py`, change `its seeds and its edit files.` to `its seeds, its render groups and its edit files.`, and `is named for, and the files` to `is named for, the listing of a flow's render groups and their seeds, and the files`.
  Then end its second paragraph `imports them from there (D69).` in place of `imports them from there.`, and rewrap that paragraph to lines of at most 88 characters.
  Verify: `git grep -n -F "(D69)" -- isekai/foundation/layout.py` prints one line.
- [ ] 3.4 Leave every file under `tests/` but `tests/mutants.json`, and every file under `ui/` and `tools/`, as it stands.
  Verify: `git diff --name-only 0f170216 -- tests ui tools` prints `tests/mutants.json` and no other path.
