# The render names — tasks

`render_image` and `render_record` name a render's image and record, and the sites that only build a name call them. Each phase is green on its own; the design is [design](design.md).

## Progress

- [x] 1 — The builders · moderate
- [x] 2 — The stage · moderate
- [x] 3 — The other sites · moderate
- [x] 4 — The documents · moderate

## 1 — The builders

- [x] 1.1 **HALT CHECK** The stage still spells the record by hand where [D2](design.md#d2) says; if it does not, the plan is stale.
  Verify: `git grep -c -F "{SIDECAR}" -- isekai/pipeline/generate.py` prints `2`.
- [x] 1.2 In `tests/test_generate.py`, add `is_render`, `is_sidecar`, `render_image` and `render_record` to the import from `isekai.foundation.run`. After `test_each_render_is_named_by_the_seed_that_produced_it`, add `test_render_image_names_a_seeds_file_in_its_group`: `render_image(tmp_path, 42, ".png") == tmp_path / "42.png"` and the same for `".webp"`. Then `test_render_record_names_a_seeds_sidecar_in_its_group`: `render_record(tmp_path, 42) == tmp_path / "42.render.json"`. Mark each `@pytest.mark.spec_exempt("structural: a render's file is named by one builder")` ([D4](design.md#d4)).
  Verify: `git grep -q -F "test_render_record_names_a_seeds_sidecar_in_its_group" -- tests/test_generate.py` exits 0.
- [x] 1.3 In `tests/test_generate.py`, after those two, add `test_a_built_name_is_what_the_listing_reads`, marked the same way: `is_render(render_image(tmp_path, 42, ".png"), ".png")` and `is_sidecar(render_record(tmp_path, 42))` both hold.
  Verify: `git grep -q -F "test_a_built_name_is_what_the_listing_reads" -- tests/test_generate.py` exits 0.
- [x] 1.4 The cases fail before the builders exist.
  Verify: `uv run pytest tests/test_generate.py -k "test_render_image or test_render_record or test_a_built_name"` exits 2, an ImportError at collection, before 1.5 and 1.6 build the names.
- [x] 1.5 In `isekai/foundation/layout.py`, after `is_sidecar`, add `render_image` and `render_record` as [D1](design.md#d1) writes them, each with its docstring.
  Verify: `git grep -n -e "^def render_image" -e "^def render_record" -- isekai/foundation/layout.py` prints two lines.
- [x] 1.6 In `isekai/foundation/run.py`, import `render_image` and `render_record` from `isekai.foundation.layout` and add both to `__all__`, after `render_groups` and before `rendered`.
  Verify: `git grep -n -F "render_record" -- isekai/foundation/run.py` prints two lines.
- [x] 1.7 The cases pass.
  Verify: `uv run pytest tests/test_generate.py -k "test_render_image or test_render_record or test_a_built_name"` exits 0.

## 2 — The stage

- [x] 2.1 Before editing `isekai/pipeline/generate.py`, pre-flight `image_of`'s return, the one site of the stage where `tools.mutate` finds a mutant; a survivor is handled as [D4](design.md#d4) says.
  Verify: `uv run python -m tools.mutate isekai/pipeline/generate.py:190-191 --tests tests/test_generate.py tests/test_ui_api.py` exits 0.
- [x] 2.2 In `isekai/pipeline/generate.py`, add `render_image` and `render_record` to the import from `isekai.foundation.run`.
  Verify: `git grep -n -e "^    render_image,$" -e "^    render_record,$" -- isekai/pipeline/generate.py` prints two lines.
- [x] 2.3 In `image_of`, return `render_image(group_of(run, flow.id, version), seed, flow.output_suffix)`. In `discard_render`, set `record = render_record(group, seed)`; `seed` is read above by `*_, seed = rendered_at(image)` ([D2](design.md#d2)).
  Verify: `git grep -n -F "record = render_record(group, seed)" -- isekai/pipeline/generate.py` prints one line.
- [x] 2.4 In `render`'s loop, set `output = render_image(directory, seed, flow.output_suffix)` and `provenance = render_record(directory, seed)`.
  Verify: `git grep -n -F "provenance = render_record(directory, seed)" -- isekai/pipeline/generate.py` prints one line.
- [x] 2.5 Remove `SIDECAR` from the import from `isekai.foundation.artifacts`, which nothing in the file reads now.
  Verify: `git grep -n -e "^    SIDECAR,$" -- isekai/pipeline/generate.py` prints nothing.
- [x] 2.6 Run the pre-flight again over `image_of`'s return, which the import edits moved down.
  Verify: `uv run python -m tools.mutate isekai/pipeline/generate.py:191 --tests tests/test_generate.py tests/test_ui_api.py` exits 0.
- [x] 2.7 The stage's file leaves no hand-built image name, the sites of [D2](design.md#d2).
  Verify: `git grep -n -F "output_suffix}" -- isekai/pipeline/generate.py` prints nothing.
- [x] 2.8 The stage's tests stay green.
  Verify: `uv run pytest tests/test_generate.py tests/test_resume.py tests/test_ui_api.py` exits 0.

## 3 — The other sites

- [x] 3.1 Before editing `isekai/interface/compare_view.py`, pre-flight `_renders`' group line, the one site of the phase where `tools.mutate` finds a mutant ([D4](design.md#d4)).
  Verify: `uv run python -m tools.mutate isekai/interface/compare_view.py:140-141 --tests tests/test_compare.py` exits 0.
- [x] 3.2 In `isekai/pipeline/review.py`, add `render_image` to the import from `isekai.foundation.run` and set `draft_from`'s `image` to `render_image(group_of(run, source, approval), seed, OUTPUT_SUFFIX)`. `OUTPUT_SUFFIX` stays imported: `source_copy` reads it ([D2](design.md#d2)).
  Verify: `git grep -n -F "{seed}{OUTPUT_SUFFIX}" -- isekai/pipeline/review.py` prints nothing.
- [x] 3.3 In `isekai/interface/compare_view.py`, import `group_of` and `render_image` from `isekai.foundation.run` and drop `OUTPUTS`. In `_renders`, set `directory = group_of(run, name, approved[-1])`, then `suffix = flow.output_suffix`; read `suffix` in the `rendered_seeds` call and link `render_image(directory, seed, suffix)`, which keeps the line under the length limit ([D2](design.md#d2)).
  Verify: `git grep -n -F -e "output_suffix}" -e ":03d}" -- isekai/interface/compare_view.py` prints nothing.
- [x] 3.4 In `evaluation/recall.py`, import `group_of` and `render_image` from `isekai.foundation.run`, drop `OUTPUTS`, and read the render as `render_image(group_of(run, flow, group), seed, suffix)` ([D2](design.md#d2)).
  Verify: `git grep -n -F -e "{seed}{suffix}" -e ":03d}" -- evaluation/recall.py` prints nothing.
- [x] 3.5 In `evaluation/__main__.py`, make the same import and the same call, as [D2](design.md#d2) lists; `OUTPUTS` goes from its import.
  Verify: `git grep -n -F -e "{seed}{suffix}" -e ":03d}" -- evaluation/__main__.py` prints nothing.
- [x] 3.6 Run the pre-flight again over `_renders`' group and suffix lines, which the import edit moved down.
  Verify: `uv run python -m tools.mutate isekai/interface/compare_view.py:141-142 --tests tests/test_compare.py` exits 0.
- [x] 3.7 The tests of the sites stay green, the evaluator's own among them.
  Verify: `uv run pytest tests/test_evaluation_cli.py tests/test_recall_cli.py tests/test_compare.py tests/test_review.py tests/test_ui_api.py` exits 0.
- [x] 3.8 The standing mutants stay killed.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.

## 4 — The documents

- [x] 4.1 In `docs/decisions.md`, add to D69's bold line, after the stage's kept names: `A render's image and record are named there by `render_image(group, seed, suffix)` and `render_record(group, seed)`.`
  Verify: `git grep -q -F "render_record(group, seed)" -- docs/decisions.md` exits 0.
- [x] 4.2 In D69's *Accepts*, replace its first sentence with: `The sites that test for a render by a name still name its files by hand: `drafting_approval`, `refuse_revision` and `_refuse_unchanged` in `review.py`, and `Surface.rendered` in `surface.py`.` Replace its last sentence with `Reopen when one rule says a seed is rendered.` Make *Made by* read `0174`, `0175`.
  Verify: `git grep -q -F "Reopen when one rule says a seed is rendered." -- docs/decisions.md` exits 0.
- [x] 4.3 In the docstring of `isekai/foundation/layout.py`, add `the names of a render's image and record,` after `the seeds a render's file is named for,`.
  Verify: `git grep -q -F "the names of a render's image and record" -- isekai/foundation/layout.py` exits 0.
- [x] 4.4 In `isekai/foundation/README.md`, the `layout.py` row of *Files* reads `numbering and completion, the seeds, the names of a render's image and record, a render group's listing and the edit files`.
  Verify: `git grep -q -F "the names of a render's image and record" -- isekai/foundation/README.md` exits 0.
- [x] 4.5 Derive the *Imported by* tables.
  Verify: `uv run python -m tools.derive_imported_by` exits 0.
- [x] 4.6 The documents and the guards hold.
  Verify: `uv run pytest tests/test_docs.py tests/test_layers.py tests/test_ratchets.py tests/test_spec_bindings.py` exits 0.
