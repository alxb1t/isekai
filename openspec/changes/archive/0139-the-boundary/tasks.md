# The boundary — tasks

Phases of tests and two small product fixes: the pins that refuse, a photograph that will not decode, the tagger's runtime, the pre-flight and the hosts, and the mutants that hold them. Each fix sits under a requirement that stands.

## Progress

- [x] 1 — The pins refuse · moderate
- [x] 2 — A photograph that will not decode · moderate
- [x] 3 — The tagger runs · hard
- [x] 4 — The pre-flight and the hosts · moderate
- [x] 5 — The mutants die · moderate

## 1 — The pins refuse

- [x] 1.1 **HALT CHECK** `tagger_for` returns `open_session()` bare, the line [D2](design.md#d2) wraps; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'return open_session()' isekai/interface/wiring.py` prints `1`.
- [x] 1.2 **HALT CHECK** `verified_paths` resolves both files in one loop, the line the mutant `BD-1` names; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'resolved.append(resolve(dest, models_dir, manifest))' isekai/boundary/wd14.py` prints `1`.
- [x] 1.3 In `isekai/interface/wiring.py` write [D2](design.md#d2): `tagger_for` turns `DigestMismatch` into a `Refusal`, and its docstring says so.
  Verify: `grep -c -F 'except DigestMismatch as swapped:' isekai/interface/wiring.py` prints `1`.
- [x] 1.4 In `tests/test_wd14.py` extend `test_a_half_whose_bytes_do_not_match_its_digest_stops_the_stage` in place as [D3](design.md#d3) says, and bring its comment to the design's wording.
  Verify: `grep -c -F 'ids=["the-label-index", "the-model"]' tests/test_wd14.py` prints `1`.
- [x] 1.5 In `tests/test_wd14.py` carry the key of [D3](design.md#d3) on the longer-vector and shorter-vector tests in place of the pin key, and make the shorter-vector test assert the counts and `REMEDY`.
  Verify: `grep -c -F 'tagging:pin:a-vector-that-disagrees-with-the-index-is-refused' tests/test_wd14.py` prints `2`.
- [x] 1.6 In `tests/test_tagging.py` add `test_a_pin_that_does_not_match_is_a_refusal_and_the_hosted_list_is_written` as [D2](design.md#d2) says, adding `REMEDY` to the file's `wd14` import.
  Verify: `uv run pytest tests/test_tagging.py::test_a_pin_that_does_not_match_is_a_refusal_and_the_hosted_list_is_written` passes.
- [x] 1.7 In `tests/test_pipeline_cli.py` add `test_prepare_refuses_when_a_pin_does_not_match` as [D2](design.md#d2) says, adding `REMEDY` and `provision` to the file's imports.
  Verify: `uv run pytest tests/test_pipeline_cli.py::test_prepare_refuses_when_a_pin_does_not_match` passes.
- [x] 1.8 The phase's files agree with the keys.
  Verify: `uv run pytest tests/test_tagging.py tests/test_wd14.py tests/test_pipeline_cli.py` passes.

## 2 — A photograph that will not decode

- [x] 2.1 **HALT CHECK** `prepare` opens the photograph with no catch, the line [D4](design.md#d4) wraps; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'opened = Image.open(photo)' isekai/boundary/wd14.py` prints `1`.
- [x] 2.2 **HALT CHECK** The tag stage catches a refusal and an `OSError` alone, the reason [D4](design.md#d4) converts in `prepare`; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'except (Refusal, OSError) as failed:' isekai/pipeline/tagging.py` prints `1`.
- [x] 2.3 In `isekai/boundary/wd14.py` write [D4](design.md#d4)'s `try` around the open and the load in `prepare`.
  Verify: `grep -c -F 'does not decode as an image' isekai/boundary/wd14.py` prints `1`.
- [x] 2.4 In `isekai/boundary/wd14.py` add `prepare`'s paragraph and correct `Session`'s docstring as [D4](design.md#d4) says.
  Verify: `grep -c -F 'declared dependencies the gate' isekai/boundary/wd14.py` prints `1`.
- [x] 2.5 In `tests/test_tagging.py` add `_Preparing` and `test_a_photograph_that_will_not_decode_is_a_local_failure` as [D4](design.md#d4) says, importing `prepare` and `oversized_png`.
  Verify: `uv run pytest tests/test_tagging.py::test_a_photograph_that_will_not_decode_is_a_local_failure` passes.
- [x] 2.6 The phase's files agree with the keys, and the evaluator's reader still refuses the same words.
  Verify: `uv run pytest tests/test_tagging.py tests/test_wd14.py tests/test_recall.py` passes.

## 3 — The tagger runs

- [x] 3.1 **HALT CHECK** `OnnxSession.run` hands the runtime `prepare(photo, self.dimension)`, the line the real-runtime test reads through; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'prepare(photo, self.dimension)' isekai/boundary/wd14.py` prints `1`.
- [x] 3.2 **HALT CHECK** The runtime is a declared dependency, so the real-runtime test needs no package; if it is not, the plan is wrong.
  Verify: `git grep -c -F 'onnxruntime==1.29.0' pyproject.toml` prints `1`.
- [x] 3.3 **HALT CHECK** `_planted` is `tests/test_wd14.py`'s helper that [D5](design.md#d5) takes.
  Verify: `git grep -c -F 'def _planted(' tests/test_wd14.py` prints `1`.
- [x] 3.4 Create `tests/test_wd14_runtime.py` as [D5](design.md#d5) says, its docstring giving the file's reason, with the tests of `prepare` by value.
  Verify: `uv run pytest tests/test_wd14_runtime.py::test_a_photograph_with_a_transparent_pixel_is_composited_padded_and_handed_over_blue_first tests/test_wd14_runtime.py::test_an_opaque_photograph_is_centred_on_white_in_blue_green_red` passes.
- [x] 3.5 In `tests/test_wd14_runtime.py` add the tests of `open_session` over the stub runtime, with the telemetry switch undone as [D5](design.md#d5) says.
  Verify: `uv run pytest tests/test_wd14_runtime.py::test_a_graph_whose_bytes_differ_from_its_pin_is_never_opened tests/test_wd14_runtime.py::test_the_session_opens_the_verified_path_on_the_cpu` passes.
- [x] 3.6 In `tests/test_wd14_runtime.py` add the builder of [D5](design.md#d5) as written and `test_a_tiny_graph_run_through_the_real_runtime_returns_what_prepare_handed_it`.
  Verify: `uv run pytest tests/test_wd14_runtime.py::test_a_tiny_graph_run_through_the_real_runtime_returns_what_prepare_handed_it` passes.
- [x] 3.7 The phase's files agree with the keys.
  Verify: `uv run pytest tests/test_wd14_runtime.py tests/test_wd14.py` passes.

## 4 — The pre-flight and the hosts

- [x] 4.1 **HALT CHECK** `published_digest` reads the header off the redirect's `HTTPError`, the line the mutant `BD-2b` names; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'redirected.headers.get("x-linked-etag")' isekai/boundary/provision.py` prints `1`.
- [x] 4.2 **HALT CHECK** `post` and `probe` each open through the module's `OPENER`, the seam [D7](design.md#d7) patches; if they read otherwise, the plan is wrong.
  Verify: `git grep -c -F 'OPENER.open(' isekai/boundary/ollama.py` prints `2`.
- [x] 4.3 **HALT CHECK** `crop_input` is the affine transform [D8](design.md#d8) reads by value; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'Pillow.Transform.AFFINE' isekai/boundary/pose.py` prints `1`.
- [x] 4.4 In `tests/test_provision.py` add the tests of [D6](design.md#d6), named for their rows, with the imports they need.
  Verify: `grep -c -E '^def test_(a_redirect_that_carries_the_digest|a_response_that_carries_the_digest|a_value_that_is_no_digest|the_redirect_is_kept)' tests/test_provision.py` prints `4`.
- [x] 4.5 In `tests/test_ollama.py` add `test_post_returns_an_answered_status_with_its_body`, `test_ask_over_the_real_transport_refuses_a_404_naming_the_remedy` and `test_probe_takes_any_answer_as_up` as [D7](design.md#d7) says.
  Verify: `grep -c -E '^def test_(post_returns_an_answered|ask_over_the_real_transport|probe_takes_any_answer)' tests/test_ollama.py` prints `3`.
- [x] 4.6 In `tests/test_pose.py` add `test_pose_crop_is_cut_from_the_image_where_the_box_is` and `test_pose_crop_is_black_where_it_leaves_the_image` as [D8](design.md#d8) says, importing `crop_input`.
  Verify: `grep -c -E '^def test_pose_crop_(is_cut_from|is_black_where)' tests/test_pose.py` prints `2`.
- [x] 4.7 The phase's files agree with the keys.
  Verify: `uv run pytest tests/test_provision.py tests/test_ollama.py tests/test_pose.py` passes.

## 5 — The mutants die

- [x] 5.1 **HALT CHECK** `0138-the-review-and-the-import` is merged: `tests/mutants.json` holds its entry `PA-19`, so this change appends after it.
  Verify: `grep -c -F '"finding": "PA-19"' tests/mutants.json` prints `1`.
- [x] 5.2 **HALT CHECK** The wiring's line is written as [D2](design.md#d2) quotes it, so the find of `BD-1b` stands.
  Verify: `grep -c -F 'except DigestMismatch as swapped:' isekai/interface/wiring.py` prints `1`.
- [x] 5.3 **HALT CHECK** The tagger's lines are written as [D4](design.md#d4) quotes them and as the audit found them, so the finds of `P6` and `BD-1` stand.
  Verify: `grep -c -F -e 'raise Refusal(f"{photo} does not decode as an image") from undecodable' -e 'resolved.append(resolve(dest, models_dir, manifest))' isekai/boundary/wd14.py` prints `2`.
- [x] 5.4 Append each entry of [mutants.json](mutants.json) to `tests/mutants.json`, keys and order unchanged, indented as the file is; each opens with `"finding":`.
  Verify: `grep -c -E '"finding": "(BD-1|BD-1b|BD-2a|BD-2b|BD-3a|BD-3b|BD-6|BD-6b|BD-10a|BD-10b|P6)"' tests/mutants.json` prints `11`.
- [x] 5.5 Run the replay. A line that names a survivor goes to 5.6.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits `0`.
- [x] 5.6 For each `survivor` line 5.5 printed, add in the file its entry names a test red with the mutant in place and green without it; only where no input tells the mutant from the line, give the entry `equivalent` with the reason, proven by reading the line. Never delete an entry. Where 5.5 printed none, this task holds.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits `0`.
