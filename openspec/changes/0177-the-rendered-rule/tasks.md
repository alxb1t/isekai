# The rendered rule — tasks

One rule says a seed is rendered when its image is a file in its group; each phase writes its cases first, then switches the sites that ask it ([design](design.md)).

## Progress

- [x] 1 — The rule · moderate
- [x] 2 — The revision · moderate
- [ ] 3 — The draft · moderate
- [ ] 4 — The listings and the app's sites · moderate
- [ ] 5 — The documents · moderate

## 1 — The rule

- [x] 1.1 In `tests/test_generate.py`, after `test_a_built_name_is_what_the_listing_reads`, write `test_a_seed_is_rendered_when_its_image_is_a_file`, `spec_exempt("structural: a seed is rendered when its image is a file")`, importing `is_rendered` from `isekai.foundation.run`. It is parametrized over a group with both files, an image alone, a record alone, and a group of failure records alone ([D1](design.md#d1)).
  Verify: `git grep -c -F "test_a_seed_is_rendered_when_its_image_is_a_file" -- tests/test_generate.py` prints `tests/test_generate.py:1`.
- [x] 1.2 In `isekai/foundation/layout.py`, after `render_record`, add `is_rendered(group: Path, seed: int, suffix: str) -> bool` as [D1](design.md#d1) gives it: a one-line docstring, then `return render_image(group, seed, suffix).is_file()`.
  Verify: `git grep -n -e "^def is_rendered" -- isekai/foundation/layout.py` prints one line.
- [x] 1.3 In `isekai/foundation/run.py`, import `is_rendered` from `isekai.foundation.layout` and add `"is_rendered"` to `__all__`, in the order the neighbours keep.
  Verify: `git grep -c -F "is_rendered" -- isekai/foundation/run.py` prints `isekai/foundation/run.py:2`.
- [x] 1.4 Run the rule's test, then run `uv run python -m tools.mutate` over the line of `is_rendered`'s `return`, read by `git grep -n -F "is_file()" -- isekai/foundation/layout.py`, with `--tests tests/test_generate.py`. A range the tool refuses with exit 2 holds no mutant.
  Verify: `uv run pytest tests/test_generate.py -k test_a_seed_is_rendered_when_its_image_is_a_file -q` exits 0.

## 2 — The revision

- [x] 2.1 In `tests/test_review.py`, after `test_an_unchanged_revision_is_refused_naming_the_images_it_would_reproduce`, write these tests, each bound by `pytest.mark.spec` to its key in [the delta](specs/review/spec.md): `test_a_revision_of_a_lone_record_is_refused`, `test_a_revision_of_a_lone_image_is_written`, `test_an_unchanged_revision_over_a_lone_record_is_approved`, `test_an_unchanged_revision_over_a_lone_image_is_refused`. Each arranges its folder with `_image`. The revision tests delete the image or the record before `revise`; the unchanged-revision tests delete it after `revise`, then call `approve`, as `test_a_revision_whose_seed_no_render_wrote_is_approved` does.
  Verify: `git grep -c -E "^def test_(a_revision|an_unchanged_revision)_.*_lone_" -- tests/test_review.py` prints `tests/test_review.py:4`.
- [x] 2.2 **HALT CHECK** The cases fail on the code as it stands; one that passes means the site already answers by the image and the plan is wrong.
  Verify: `uv run pytest tests/test_review.py -k "_lone_ and revision" -q` exits 1.
- [x] 2.3 In `isekai/pipeline/review.py`, import `is_rendered` from `isekai.foundation.run`; in `refuse_revision` replace the test of the record's path with `not is_rendered(group_of(run, flow, version), seed, OUTPUT_SUFFIX)` ([D2](design.md#d2)), the refusal's text as it is.
  Verify: `git grep -n -F "is_rendered(group_of(run, flow, version), seed, OUTPUT_SUFFIX)" -- isekai/pipeline/review.py` prints one line.
- [x] 2.4 In `_refuse_unchanged`, make the condition of the `made` comprehension `if is_rendered(group, seed, OUTPUT_SUFFIX)`, where it tested the record's file.
  Verify: `git grep -n -F "if is_rendered(group, seed, OUTPUT_SUFFIX)" -- isekai/pipeline/review.py` prints one line.
- [x] 2.5 In `tests/test_ui_api.py`, in `test_a_revision_of_an_untracked_flow_is_refused_and_nothing_is_written`, replace the lines that make the group `made.directory(FLOW, "outputs", "001")` and write its `7.render.json` with `rendered_image(made, 1, 7)`, which writes the image and the record as a render does and is already imported there; the test's `image` dict, requests and assertions stand. The tracked flow's seed 7 had a record and no image, which `refuse_revision` refuses once it asks the image, and the test wants it revisable. `test_the_drafts_refusal_fits_draft_refused` keeps its lone record, which only checks a refusal's shape.
  Verify: `git grep -c -F "rendered_image(made, 1, 7)" -- tests/test_ui_api.py` prints `tests/test_ui_api.py:1`.
- [x] 2.6 Run the cases and the file, then `uv run python -m tools.mutate` over each site's lines in `isekai/pipeline/review.py`, read by `git grep -n -F "is_rendered(" -- isekai/pipeline/review.py`, one run a range, with `--tests tests/test_review.py`. A range the tool refuses with exit 2 holds no mutant.
  Verify: `uv run pytest tests/test_review.py -q` exits 0.

## 3 — The draft

- [ ] 3.1 In `tests/test_review.py`, after `test_a_draft_naming_a_seed_its_approval_never_rendered_is_refused`, write `test_a_draft_from_a_lone_image_is_written`, bound to `review:draft-from:an-image-without-its-record-is-drafted-from`. It deletes the record of a seed `_image` wrote, drafts from that seed, and asserts the draft's seeds and the source copy's bytes as the test bound to `review:draft-from:a-draft-from-an-image-copies-it` does.
  Verify: `git grep -c -F "test_a_draft_from_a_lone_image_is_written" -- tests/test_review.py` prints `tests/test_review.py:1`.
- [ ] 3.2 **HALT CHECK** The case fails on the code as it stands, which refuses an image whose record is gone; the existing case of a record kept and an image gone stands as the lone record's.
  Verify: `uv run pytest tests/test_review.py -k "a_draft_from_a_lone_image" -q` exits 1.
- [ ] 3.3 In `drafting_approval`, replace the test of the record and the image with `not is_rendered(group, seed, OUTPUT_SUFFIX)` ([D3](design.md#d3)), the refusal's text as it is. Then remove `SIDECAR` from the imports from `isekai.foundation.artifacts`, which no line of `isekai/pipeline/review.py` reads.
  Verify: `git grep -n -F "SIDECAR" -- isekai/pipeline/review.py` prints nothing.
- [ ] 3.4 Run the file, then `uv run python -m tools.mutate` over `drafting_approval`'s changed lines, read by `git grep -n -F "is_rendered(" -- isekai/pipeline/review.py`, with `--tests tests/test_review.py`. A range the tool refuses with exit 2 holds no mutant.
  Verify: `uv run pytest tests/test_review.py -q` exits 0.

## 4 — The listings and the app's sites

- [ ] 4.1 In `copied_renders`, read `rendered = rendered_seeds(group, OUTPUT_SUFFIX)` in place of its sorted comprehension and its `group.is_dir()` test; import `rendered_seeds` from `isekai.foundation.run` ([D4](design.md#d4)).
  Verify: `git grep -n -F "rendered = rendered_seeds(group, OUTPUT_SUFFIX)" -- isekai/pipeline/review.py` prints one line.
- [ ] 4.2 In `_first_image`, return `min((render_image(group, seed, OUTPUT_SUFFIX) for seed in rendered_seeds(group, OUTPUT_SUFFIX)), default=None)`, so it names the file it named; remove `is_seed` from the imports `review.py` no longer reads.
  Verify: `git grep -n -w "is_seed" -- isekai/pipeline/review.py` prints nothing.
- [ ] 4.3 In `Surface.rendered` in `isekai/interface/ui/surface.py`, ask `is_rendered(image.parent, seed, one.output_suffix)` where it asked `image.is_file()`, and name the record by `render_record(image.parent, seed)`. Import both from `isekai.foundation.run` and drop the import of `SIDECAR`; the texts stay.
  Verify: `git grep -n -F "SIDECAR" -- isekai/interface/ui/surface.py` prints nothing.
- [ ] 4.4 In `_revision` in `isekai/interface/ui/routes/reviewing.py`, test each seed by `is_rendered(group_of(one.run, one.flow.id, version), seed, one.flow.output_suffix)` where it called `image_of(...).is_file()`; import `group_of` and `is_rendered` from `isekai.foundation.run`. `post_draft`'s `image_of` stays.
  Verify: `git grep -n -F "is_rendered(" -- isekai/interface/ui/routes/reviewing.py` prints one line.
- [ ] 4.5 Run `uv run pytest tests/test_review.py tests/test_generate.py tests/test_resume.py tests/test_ui_api.py tests/test_pipeline_cli.py tests/test_layers.py tests/test_ratchets.py -q`, then `uv run python -m tools.mutate` over each switched site's lines under `isekai/`, read by `git grep -n -F "is_rendered(" -- isekai`, one run a range, with the test file that holds the site. A range the tool refuses with exit 2 holds no mutant.
  Verify: `uv run pytest tests/test_review.py tests/test_generate.py tests/test_resume.py tests/test_ui_api.py tests/test_pipeline_cli.py tests/test_layers.py tests/test_ratchets.py -q` exits 0.

## 5 — The documents

- [ ] 5.1 In `docs/decisions.md`, after D69, add `### D70 · A seed is rendered when its image is a file in its group` in D69's form, with *Made by* `0177`: the rule is `is_rendered` in `layout.py`, asked by review and the app ([D7](design.md#d7)).
  Verify: `git grep -n -F "### D70" -- docs/decisions.md` prints one line.
- [ ] 5.2 In D69's *Accepts*, drop its first sentence, the one that says the sites that test for a render still name its files by hand, and its last, `Reopen when one rule says a seed is rendered`. Rewrite its second to `The other definitions of "rendered", `_holds_render` and `rendered_at`, stand.`; keep the sentences on `render_groups` and `trackable`.
  Verify: `git grep -n -F "still name its files by hand" -- docs/decisions.md` prints nothing.
- [ ] 5.3 Add "the rule that a seed is rendered" to the `layout.py` row of `isekai/foundation/README.md` and to `layout.py`'s module docstring, after the names of a render's image and record, each on one line.
  Verify: `git grep -n -F "the rule that a seed is rendered" -- isekai/foundation/README.md isekai/foundation/layout.py` prints two lines.
- [ ] 5.4 Run the standing mutants over the whole change.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
