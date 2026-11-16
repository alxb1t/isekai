# The version limit — tasks

Two phases: `next_version` refuses the number no artifact's name can spell, and tests hold it; then its way out keeps the whole run together. Design: [design](design.md).

## Progress

- [x] 1 — Refuse the number no name can spell · moderate
- [ ] 2 — Send the whole run out, not the directory · moderate

## 1 — Refuse the number no name can spell

- [x] 1.1 In `next_version` of `isekai/foundation/layout.py`, per [D1](design.md#d1) and [D3](design.md#d3): take `number = (latest(directory) or 0) + 1`, and `raise Refusal` when `not is_version(number)`, else return `number`. Amend its docstring to say it refuses, with `e.g. a directory holding 999.json -> Refusal`.
  Verify: `git grep -n -F "if not is_version(number):" -- isekai/foundation/layout.py` prints one line.
- [x] 1.2 Write the message of [D2](design.md#d2) in that `Refusal`: `f"{where} holds version {number - 1}, the last a three-digit name can spell; move {where} out of the run, then run the command again"`, with `where = f"{directory.parent.name}/{directory.name}"`. Its way out is replaced by 2.1's.
  Verify: `git grep -n -F "three-digit name" -- isekai/foundation/layout.py` prints a line.
- [x] 1.3 In `tests/test_run_directory.py`, after `test_each_stage_numbers_within_its_own_directory`, add `test_a_directory_holding_version_999_refuses_the_next_number` and `test_the_number_after_998_is_still_taken`, each marked `@pytest.mark.spec("run-directory:numbering:a-full-directory-refuses-a-new-version")`. The first writes `artifact_name(999)` into `tmp_path / "captions"` with `write_json`, expects `Refusal` from `next_version`, asserts its text holds `f"{tmp_path.name}/captions"` and `move`, and asserts `sorted(os.listdir(directory)) == ["999.json"]`. The second writes `artifact_name(998)` and asserts `next_version(directory) == 999`.
  Verify: `uv run pytest tests/test_run_directory.py -k "version_999 or after_998"` exits 0.
- [x] 1.4 Hold the neighbours the refusal reaches: the stages that number through `next_version` and the resume test.
  Verify: `uv run pytest tests/test_run_directory.py tests/test_resume.py tests/test_caption.py tests/test_tagging.py` exits 0.

## 2 — Send the whole run out, not the directory

Adversarial S1 of round 1: moving a flow's `review/` alone restarts approval numbering beside the `prompts/` and `outputs/` numbered from it, so a new approval 001 takes the old prompt and counts the old render. The way out of [D2](design.md#d2) sends the whole run out instead.

- [ ] 2.1 In `next_version` of `isekai/foundation/layout.py`, make the `Refusal`'s text `f"{where} holds version {number - 1}, the last a three-digit name can spell; move the whole run that holds it out of its runs root, then start that photograph again as a new run"`, `where` as in 1.2. Nothing else in the function changes.
  Verify: `git grep -n -F "out of its runs root, then start that photograph again" -- isekai/foundation/layout.py` prints one line.
- [ ] 2.2 In `tests/test_run_directory.py`, after `test_the_number_after_998_is_still_taken`, add `test_a_full_review_directory_sends_the_whole_run_out`, marked `@pytest.mark.spec("run-directory:numbering:a-full-directory-refuses-a-new-version")`. Under `flow = tmp_path / "conjure-anime-wai"` it writes `artifact_name(999, APPROVED)` into `flow / REVIEW`, `artifact_name(1)` into `flow / PROMPTS` with `write_json`, and an image file `flow / OUTPUTS / "001" / "1.png"` holding any bytes; it records `sorted(str(p.relative_to(flow)) for p in flow.rglob("*"))`, expects `Refusal` from `next_version(flow / REVIEW)`, asserts its text holds `"conjure-anime-wai/review"` and `"the whole run"` and does not hold `"move conjure-anime-wai/review"`, and asserts the flow's listing is unchanged. Import the names it needs from `isekai.foundation.run`, as the file already does.
  Verify: `uv run pytest tests/test_run_directory.py -k "version_999 or after_998 or full_review"` exits 0.
- [ ] 2.3 Hold the neighbours the refusal reaches, as 1.4.
  Verify: `uv run pytest tests/test_run_directory.py tests/test_resume.py tests/test_caption.py tests/test_tagging.py` exits 0.
