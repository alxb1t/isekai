# The contract covered — tasks

One phase: a test that every name of `VERSIONS` has a golden, and its twin.

## Progress

- [ ] 1 — The coverage test and its twin · moderate

## 1 — The coverage test and its twin

- [ ] 1.1 In `tests/test_artifact_bytes.py`, add `VERSIONS` to the `isekai.foundation.artifacts` import and add `kinds_without_golden(names, directory)` after `test_an_edit_record_holds_whatever_level_its_png_was_deflated_at`, as [D1](design.md#d1) says.
  Verify: `git grep -n -e "^def kinds_without_golden" -- tests/test_artifact_bytes.py` prints one line.
- [ ] 1.2 **HALT CHECK** Add `test_every_artifact_kind_has_a_golden` after it: `assert kinds_without_golden(VERSIONS, GOLDEN) == set()`, marked `@pytest.mark.spec_exempt("structural: every kind of the contract has a golden")` ([D2](design.md#d2), [D3](design.md#d3)).
  Verify: `uv run pytest tests/test_artifact_bytes.py::test_every_artifact_kind_has_a_golden` exits 0.
- [ ] 1.3 Add its twin `test_the_check_catches_a_kind_with_no_golden` as [D2](design.md#d2) says, marked `@pytest.mark.spec_exempt("structural: twin of test_every_artifact_kind_has_a_golden")`.
  Verify: `uv run pytest tests/test_artifact_bytes.py::test_the_check_catches_a_kind_with_no_golden` exits 0.
- [ ] 1.4 Keep the test and its twin under the names of [D2](design.md#d2), and rename no existing test in `tests/test_artifact_bytes.py`.
  Verify: `git grep -n -e "^def test_every_artifact_kind_has_a_golden" -e "^def test_the_check_catches_a_kind_with_no_golden" -- tests/test_artifact_bytes.py` prints two lines.
