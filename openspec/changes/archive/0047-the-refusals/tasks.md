# Tasks — 0047 the refusals

The checker and the verbs, then the boundaries, then the host-key read, per [design](design.md). A task adding a
scenario writes it into `openspec/changes/0047-the-refusals/specs/<capability>/spec.md` as a MODIFIED block — the
living requirement with [the new scenario](design.md#the-new-scenarios) — beside its test.

## Progress

- [x] 1 — The checker and the verbs
- [x] 2 — The boundaries
- [x] 3 — The host-key read

Line numbers are `9995b54`'s code, unchanged at `b748c61`. Every new test carries `@pytest.mark.spec` with the key
its task names, and has a twin.

## 1 — The checker and the verbs

- [x] 1.1 **HALT CHECK** — `tag` offers only "drop `--flow`", the verbs collect per input, and the host-key check reads by `since`.
  Verify: `grep -c 'sheet --flow' isekai/interface/cli.py` prints `0`, `grep -c 'across(' isekai/interface/cli.py` prints `4`, and `grep -c 'logs?since' infra/up.sh` prints `1`.
- [x] 1.2 In `tests/test_spec_bindings.py`, demand a test only for living keys, with a twin for a delta-only key, per [D8](design.md#d8).
  Verify: `grep -c '^def living_keys' tests/test_spec_bindings.py` prints `1`.
- [x] 1.3 In `isekai/interface/cli.py`, name `sheet` when every flow `tag` is given is untagged, per [D1](design.md#d1); add the `tagging` scenario and `test_only_untagged_flows_name_the_next_verb` to `tests/test_tagging.py`.
  Verify: `grep -c 'sheet --flow' isekai/interface/cli.py` prints `1`, and `grep -c '^def test_only_untagged_flows_name_the_next_verb' tests/test_tagging.py` prints `1`.
- [x] 1.4 In `isekai/interface/cli.py`, collect each verb's refusals per flow, per [D2](design.md#d2); add the `cli` flow-selection scenario and `test_one_flows_refusal_leaves_the_others` to `tests/test_pipeline_cli.py`.
  Verify: `grep -c 'collected.extend(across(list(flows), step))' isekai/interface/cli.py` prints `1`, and `grep -c '^def test_one_flows_refusal_leaves_the_others' tests/test_pipeline_cli.py` prints `1`.
- [x] 1.5 In `isekai/pipeline/generate.py`, refuse a named flow with no approved sheet beside approved ones, per [D3](design.md#d3); add `test_a_named_unapproved_flow_is_refused_beside_an_approved_one` (`image-generation:inputs:unapproved-flow-is-refused`) to `tests/test_generate.py`.
  Verify: `grep -c '^def test_a_named_unapproved_flow_is_refused_beside_an_approved_one' tests/test_generate.py` prints `1`.

## 2 — The boundaries

- [x] 2.1 In `isekai/interface/run_view.py`, mark a frame `report` cannot read and list the rest, per [D4](design.md#d4); add the `cli` inspection scenario and `test_an_unreadable_frame_is_marked` to `tests/test_run_view.py`.
  Verify: `grep -c 'an-unreadable-frame-is-marked' openspec/changes/0047-the-refusals/specs/cli/spec.md` prints `1`, and `grep -c '^def test_an_unreadable_frame_is_marked' tests/test_run_view.py` prints `1`.
- [x] 2.2 In `isekai/boundary/ollama.py`, name `PROVISION` first in the no-record, unreadable-record and absent-model refusals, per [D5](design.md#d5); add the `caption` scenario and `test_no_record_names_the_files_first` to `tests/test_caption.py`.
  Verify: `test "$(grep -c '{_rebuild(remedy)}' isekai/boundary/ollama.py)" -ge 4 && echo ok` prints `ok`, and `grep -c '^def test_no_record_names_the_files_first' tests/test_caption.py` prints `1`.
- [x] 2.3 In `isekai/interface/wiring.py` and `isekai/boundary/wd14.py`, refuse an `UnknownArtifact` naming the manifest loaded, per [D6](design.md#d6); add the `model-provisioning` scenario and `test_an_undeclared_artifact_is_refused` to `tests/test_vocabulary_manifest.py`.
  Verify: `grep -c 'except UnknownArtifact' isekai/interface/wiring.py isekai/boundary/wd14.py` prints `isekai/interface/wiring.py:1` and `isekai/boundary/wd14.py:1`, `grep -c '^from isekai' isekai/boundary/provision.py` prints `0`, and `grep -c '^def test_an_undeclared_artifact_is_refused' tests/test_vocabulary_manifest.py` prints `1`.

## 3 — The host-key read

- [x] 3.1 In `infra/up.sh`, read the fingerprint with `tail=5000&source=container` and keep the last key line, per [D7](design.md#d7); in `tests/test_infra.py`, add `test_the_fingerprint_is_read_from_the_log_s_last_lines` (`pod-image:host-key:a-matching-key-is-kept`).
  Verify: `grep -c 'logs?since' infra/up.sh` prints `0`, `grep -c 'tail=5000&source=container' infra/up.sh` prints `1`, and `grep -c '^def test_the_fingerprint_is_read_from_the_log_s_last_lines' tests/test_infra.py` prints `1`.
- [x] 3.2 Check the script parses.
  Verify: `bash -n infra/up.sh && echo ok` prints `ok`.
