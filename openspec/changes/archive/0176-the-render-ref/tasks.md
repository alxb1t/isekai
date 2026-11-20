# The render ref — tasks

`rendered_at` and `edit_at` return `RenderRef` and `EditRef`, and `version_of` reads a version off an artifact's name. Each phase is green on its own; the design is [design](design.md).

## Progress

- [x] 1 — The types · moderate
- [x] 2 — The readers · moderate
- [x] 3 — The versions · moderate
- [x] 4 — The documents · moderate

## 1 — The types

- [x] 1.1 **HALT CHECK** The signatures still return the tuples [D1](design.md#d1) replaces; if one does not, the plan is stale.
  Verify: `git grep -n -F "tuple[Run, str, int, int" -- isekai` prints a line in `isekai/foundation/layout.py`, `isekai/foundation/run.py` and `isekai/pipeline/review.py`.
- [x] 1.2 Before editing `isekai/foundation/run.py`, pre-flight the slice in `refusal_for`, the line [D3](design.md#d3) lists; a survivor is handled as [D5](design.md#d5) says.
  Verify: `uv run pytest tests/test_run_directory.py` exits 0.
- [x] 1.3 In `tests/test_edit.py`, after `test_edit_names_an_image_path_names_its_run_flow_approval_seed_and_number`, add `test_edit_names_an_edit_ref_reads_by_field_name`, marked `@pytest.mark.spec_exempt("structural: an edit image's path names a ref whose fields are named")`. For `group / "42.edit-2.png"` it reads `ref = edit_at(image)` and asserts `(ref.run.id, ref.flow, ref.version, ref.seed, ref.k) == ("0123456789ab_a", "summon-anime-wai", 1, 42, 2)`, `ref._fields == ("run", "flow", "version", "seed", "k")` and `ref == (ref.run, ref.flow, ref.version, ref.seed, ref.k)`. Run it and see it fail on the tuple.
  Verify: `git grep -n -F "test_edit_names_an_edit_ref_reads_by_field_name" -- tests/test_edit.py` prints one line.
- [x] 1.4 In `tests/test_run_directory.py`, add `rendered_at` to the import from `isekai.foundation.run`, between `refusal_for` and `run_at`. After `test_the_layout_survives_one_flows_directory_being_removed`, add `test_the_layout_names_a_render_ref_reads_by_field_name`, marked `@pytest.mark.spec_exempt("structural: a render image's path names a ref whose fields are named")`. It builds `run = tmp_path / "runs" / "0123456789ab_a"` with `group = run / FLOW / OUTPUTS / "001"`, makes the group, writes `{}` to `run / FRAME_NAME` and bytes to `group / "42.png"`, reads `ref = rendered_at(image)`, and asserts `(ref.run.id, ref.flow, ref.version, ref.seed) == ("0123456789ab_a", FLOW, 1, 42)`, `ref._fields == ("run", "flow", "version", "seed")` and `ref == (ref.run, FLOW, 1, 42)`. Run it and see it fail on the tuple.
  Verify: `git grep -n -F "test_the_layout_names_a_render_ref_reads_by_field_name" -- tests/test_run_directory.py` prints one line.
- [x] 1.5 In `isekai/foundation/layout.py`, import `NamedTuple` from `typing`. Above `edit_at`, add `RenderRef` and `EditRef` as [D1](design.md#d1) writes them.
  Verify: `git grep -n -E "^class (RenderRef|EditRef)\(NamedTuple\):" -- isekai/foundation/layout.py` prints two lines.
- [x] 1.6 Make the signature of `edit_at` `def edit_at(image: Path) -> EditRef:` and return `EditRef(...)` over the same values in the same order. Its docstring example keeps its tuple, read as the ref's fields.
  Verify: `git grep -n -F "def edit_at(image: Path) -> EditRef:" -- isekai/foundation/layout.py` prints one line.
- [x] 1.7 In `isekai/foundation/run.py`, import `EditRef` and `RenderRef` from `isekai.foundation.layout`, after `EDIT_STEM`, and add both to `__all__`: `EditRef` after `Attempt`, `RenderRef` after `Kind`.
  Verify: `git grep -n -F "RenderRef" -- isekai/foundation/run.py` prints two lines.
- [x] 1.8 Make the signature of `rendered_at` `def rendered_at(image: Path) -> RenderRef:` and return `RenderRef(run, flow_directory.name, int(group.name), int(image.stem))`.
  Verify: `git grep -n -F "def rendered_at(image: Path) -> RenderRef:" -- isekai/foundation/run.py` prints one line.
- [x] 1.9 The cases of the refs pass.
  Verify: `uv run pytest tests/test_edit.py tests/test_run_directory.py -k reads_by_field_name` exits 0.

## 2 — The readers

- [x] 2.1 Before editing `isekai/pipeline/review.py`, pre-flight the slice in `current_draft`; a survivor is handled as [D5](design.md#d5) says.
  Verify: `uv run pytest tests/test_review.py` exits 0.
- [x] 2.2 Pre-flight the slice in `_waiting_number`.
  Verify: `uv run pytest tests/test_review.py` exits 0.
- [x] 2.3 Pre-flight the slice in `discard`.
  Verify: `uv run pytest tests/test_review.py` exits 0.
- [x] 2.4 Pre-flight the slice in `withdraw`.
  Verify: `uv run pytest tests/test_review.py` exits 0.
- [x] 2.5 Pre-flight the slice in `approve`.
  Verify: `uv run pytest tests/test_review.py` exits 0.
- [x] 2.6 Pre-flight the slice in `_drafted`, in `isekai/interface/ui/routes/reviewing.py`, before editing that file.
  Verify: `uv run pytest tests/test_ui_api.py` exits 0.
- [x] 2.7 In `isekai/pipeline/edit.py`, read the sites of [D2](design.md#d2) by name: `_located` returns `edit_at(source).seed` and `rendered_at(source).seed`, and `request_placed` sets `places_on = edit_at(source).k`. `discard_edit`'s unpack stays.
  Verify: `git grep -n -F "at(source)[" -- isekai/pipeline/edit.py` prints nothing.
- [x] 2.8 In `discard_render`, in `isekai/pipeline/generate.py`, replace `*_, seed = rendered_at(image)` with `seed = rendered_at(image).seed`.
  Verify: `git grep -n -F "*_, seed = rendered_at" -- isekai/pipeline/generate.py` prints nothing.
- [x] 2.9 In `run_discard`, in `isekai/interface/verbs/drafts.py`, replace the line ending `(image)[:3]` with `ref = (edit_at if edited else rendered_at)(image)` and then `run, flow, version = ref.run, ref.flow, ref.version`. `run_draft`'s pass of `rendered_at(image)` on stays.
  Verify: `git grep -n -F "(image)[:3]" -- isekai/interface/verbs/drafts.py` prints nothing.
- [x] 2.10 In `isekai/pipeline/review.py`, import `RenderRef` from `isekai.foundation.run`, before `Run`, and set `Revision = RenderRef` under its comment, which stays ([D2](design.md#d2)).
  Verify: `git grep -n -F "Revision = RenderRef" -- isekai/pipeline/review.py` prints one line.
- [x] 2.11 In `isekai/interface/ui/routes/reviewing.py`, import `RenderRef` from `isekai.foundation.run`, after `WD14`, and in `post_draft` append `RenderRef(run, flow, version, seed)` where it appended the bare tuple.
  Verify: `git grep -n -F "RenderRef(run, flow, version, seed)" -- isekai/interface/ui/routes/reviewing.py` prints one line.
- [x] 2.12 The suites that reach the readers stay green.
  Verify: `uv run pytest tests/test_edit.py tests/test_edit_session.py tests/test_generate.py tests/test_review.py tests/test_pipeline_cli.py tests/test_ui_api.py` exits 0.

## 3 — The versions

- [x] 3.1 In `tests/test_run_directory.py`, add `version_of` to the import from `isekai.foundation.run`, between `slug` and `versions`. After the render ref's case, add `test_the_layout_reads_a_version_off_an_artifacts_name`, marked `@pytest.mark.spec_exempt("structural: a version is read off an artifact's name by one function")`. It asserts `version_of(Path("review/002.draft.json")) == 2`, `version_of(Path("review/001.error.1.transient.json")) == 1` and `version_of(Path("sources/010.png")) == 10`. It fails at import until 3.2 and 3.3.
  Verify: `git grep -n -F "test_the_layout_reads_a_version_off_an_artifacts_name" -- tests/test_run_directory.py` prints one line.
- [x] 3.2 In `isekai/foundation/layout.py`, add `version_of` after `artifact_name`, as [D3](design.md#d3) writes it.
  Verify: `git grep -n -F "def version_of(path: Path) -> int:" -- isekai/foundation/layout.py` prints one line.
- [x] 3.3 In `isekai/foundation/run.py`, import `version_of` from `isekai.foundation.layout`, after `sidecars`, and add it to `__all__`, after `unmigrated` and before `versions`.
  Verify: `uv run pytest tests/test_run_directory.py -k reads_a_version_off` exits 0.
- [x] 3.4 In `isekai/pipeline/review.py`, import `version_of` from `isekai.foundation.run`, before `versions`, and call it at each site [D3](design.md#d3) lists for the file: `current_draft`, `_waiting_number`, `discard`, `withdraw` and `approve`.
  Verify: `git grep -c -F "version_of(" -- isekai/pipeline/review.py` prints `isekai/pipeline/review.py:5`.
- [x] 3.5 In `isekai/interface/ui/routes/reviewing.py`, import `version_of` from `isekai.foundation.run`, after `stage_command`, and set `version = version_of(path)` in `_drafted` ([D3](design.md#d3)).
  Verify: `git grep -n -F "version = version_of(path)" -- isekai/interface/ui/routes/reviewing.py` prints one line.
- [x] 3.6 In `refusal_for`, in `isekai/foundation/run.py`, set `version = version_of(record)`. `.name[:3]` stands once under `isekai/`, in `version_of` ([D3](design.md#d3), C15).
  Verify: `git grep -c -F ".name[:3]" -- isekai` prints `isekai/foundation/layout.py:1`.
- [x] 3.7 Run the pre-flight again over the comparison in `current_draft`, which the imports of `review.py` moved to line 132 ([D5](design.md#d5)).
  Verify: `uv run python -m tools.mutate isekai/pipeline/review.py:132 --tests tests/test_review.py` exits 0.
- [x] 3.8 Run it over the return in `_waiting_number`, which the imports moved to line 411.
  Verify: `uv run python -m tools.mutate isekai/pipeline/review.py:411 --tests tests/test_review.py` exits 0.
- [x] 3.9 The standing mutants stay killed.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
- [x] 3.10 The suites that reach the versions stay green.
  Verify: `uv run pytest tests/test_review.py tests/test_run_directory.py tests/test_resume.py tests/test_ui_api.py` exits 0.

## 4 — The documents

- [x] 4.1 In `docs/decisions.md`, add D70 after D69's *Made by* line, as [D6](design.md#d6) writes it.
  Verify: `git grep -n -F "### D70 · A render is addressed by a named type" -- docs/decisions.md` prints one line.
- [x] 4.2 In the docstring of `isekai/foundation/layout.py`, add `the refs an image's path names, the version an artifact's name spells,` after `render groups and their seeds,`, wrapped within the line limit, and `, D70` after `D69`.
  Verify: `git grep -n -F "refs an image's path names" -- isekai/foundation/layout.py` prints one line.
- [x] 4.3 In `isekai/foundation/README.md`, the `layout.py` row of *Files* reads `numbering and completion, the seeds, a render group's listing, the refs an image's path names and the edit files`.
  Verify: `git grep -n -F "the refs an image's path names" -- isekai/foundation/README.md` prints one line.
- [x] 4.4 Derive the *Imported by* tables; no importer is new, so none moves.
  Verify: `uv run python -m tools.derive_imported_by` exits 0.
- [x] 4.5 The documents and the guards hold.
  Verify: `uv run pytest tests/test_docs.py tests/test_layers.py tests/test_ratchets.py tests/test_spec_bindings.py` exits 0.
