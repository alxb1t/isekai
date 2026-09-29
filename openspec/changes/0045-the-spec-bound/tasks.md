# Tasks — 0045 the spec bound

The rebindings, so the gate can hold them; then the checker, per [design](design.md).

## Progress

- [x] 1 — The bindings
- [ ] 2 — The checker

Line numbers are `be1e2bb`'s. Every new test carries `@pytest.mark.spec` with the key its task names, or
`spec_exempt` as a twin or a structural check.

## 1 — The bindings

- [x] 1.1 **HALT CHECK** — the orphan key has no test, the no-scan key does not exist, and there is no checker.
  Verify: `grep -c 'a-prefix-collision-refuses' tests/test_run_directory.py` prints `0`, `grep -c 'a-scan-no-one-answers-is-refused' tests/test_infra.py` prints `0`, and `ls tests/test_spec_bindings.py` fails.
- [x] 1.2 In `tests/test_run_directory.py`, bind `test_a_digest_prefix_collision_is_refused_rather_than_mixed` to `run-directory:identity:a-prefix-collision-refuses`, per [D3](design.md#d3).
  Verify: `grep -c 'run-directory:identity:a-prefix-collision-refuses' tests/test_run_directory.py` prints `1`.
- [x] 1.3 In `tests/test_infra.py`, bind `test_a_scan_no_one_answers_is_refused_as_such` to `pod-image:host-key:a-scan-no-one-answers-is-refused`, and split `test_a_failed_teardown_claims_none_and_names_no_re_run` by key, per [D4](design.md#d4).
  Verify: `grep -c 'pod-image:host-key:a-scan-no-one-answers-is-refused' tests/test_infra.py` prints `2`, and `grep -c -e '^def test_a_failed_teardown_after_a_mismatch_claims_none' -e '^def test_a_failed_teardown_after_an_unanswered_scan_claims_none' tests/test_infra.py` prints `2`.
- [x] 1.4 In `tests/test_infra.py`, make `test_the_hold_ends_on_its_own_well_inside_the_session_ceiling` check that the hold ends in the stop, per [D5](design.md#d5).
  Verify: `sed -n '/^def test_the_hold_ends_on_its_own_well_inside_the_session_ceiling/,/^def /p' tests/test_infra.py | grep -c 'STOP_POD'` prints `1`.

## 2 — The checker

- [ ] 2.1 Write `tests/test_spec_bindings.py` with `test_every_key_has_a_test`, `test_every_marker_names_a_key` and `test_every_test_carries_one_marker`, each with its twin, per [D1](design.md#d1).
  Verify: `grep -c -e '^def test_every_key_has_a_test' -e '^def test_every_marker_names_a_key' -e '^def test_every_test_carries_one_marker' tests/test_spec_bindings.py` prints `3`.
- [ ] 2.2 Read the active changes' deltas into the key set, with a twin over an ADDED key and a REMOVED requirement, per [D2](design.md#d2).
  Verify: `grep -q 'REMOVED Requirements' tests/test_spec_bindings.py && grep -q 'ADDED Requirements' tests/test_spec_bindings.py && echo ok` prints `ok`.
- [ ] 2.3 In `CLAUDE.md`, name the checker in place of the "no checker" sentence, per [D6](design.md#d6).
  Verify: `grep -c 'no spec↔test binding checker' CLAUDE.md` prints `0`, and `grep -c 'tests/test_spec_bindings.py' CLAUDE.md` prints `1`.
