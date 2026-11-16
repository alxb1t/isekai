# The version limit — tasks

One phase: `next_version` refuses the number no artifact's name can spell, and tests hold it. Design: [design](design.md).

## Progress

- [ ] 1 — Refuse the number no name can spell · moderate

## 1 — Refuse the number no name can spell

- [ ] 1.1 In `next_version` of `isekai/foundation/layout.py`, per [D1](design.md#d1) and [D3](design.md#d3): take `number = (latest(directory) or 0) + 1`, and `raise Refusal` when `not is_version(number)`, else return `number`. Amend its docstring to say it refuses, with `e.g. a directory holding 999.json -> Refusal`.
  Verify: `git grep -n -F "if not is_version(number):" -- isekai/foundation/layout.py` prints one line.
- [ ] 1.2 Write the message of [D2](design.md#d2) in that `Refusal`: `f"{where} holds version {number - 1}, the last a three-digit name can spell; move {where} out of the run, then run the command again"`, with `where = f"{directory.parent.name}/{directory.name}"`.
  Verify: `git grep -n -F "three-digit name" -- isekai/foundation/layout.py` prints a line.
- [ ] 1.3 In `tests/test_run_directory.py`, after `test_each_stage_numbers_within_its_own_directory`, add `test_a_directory_holding_version_999_refuses_the_next_number` and `test_the_number_after_998_is_still_taken`, each marked `@pytest.mark.spec("run-directory:numbering:a-full-directory-refuses-a-new-version")`. The first writes `artifact_name(999)` into `tmp_path / "captions"` with `write_json`, expects `Refusal` from `next_version`, asserts its text holds `f"{tmp_path.name}/captions"` and `move`, and asserts `sorted(os.listdir(directory)) == ["999.json"]`. The second writes `artifact_name(998)` and asserts `next_version(directory) == 999`.
  Verify: `uv run pytest tests/test_run_directory.py -k "version_999 or after_998"` exits 0.
- [ ] 1.4 Hold the neighbours the refusal reaches: the stages that number through `next_version` and the resume test.
  Verify: `uv run pytest tests/test_run_directory.py tests/test_resume.py tests/test_caption.py tests/test_tagging.py` exits 0.
