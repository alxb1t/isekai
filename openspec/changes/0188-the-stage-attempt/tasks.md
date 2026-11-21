# The stage attempt — tasks

Hold each stage's refusal whole and pin the sequences by mutation, add `attempt` and `producer_for`, call `attempt` from `caption`, `wd14`, `tags` and `sheet`, narrow `refusal_for` and take its row out, then replay the mutation and amend the documents.

## Progress

- [x] 1 — Hold each stage's refusal whole and pin the sequences by mutation · moderate
- [x] 2 — Add `attempt` and `producer_for` · moderate
- [x] 3 — Call `attempt` from the stages · moderate
- [ ] 4 — Narrow `refusal_for` and take its row out · moderate
- [ ] 5 — Replay the mutation and amend the documents · moderate

## 1 — Hold each stage's refusal whole and pin the sequences by mutation

- [x] 1.1 **HALT CHECK** The premise of [D1](design.md#d1) stands: each sequence is at its site, `caption` once, `tag_wd14` and `tag_hosted` in `tagging.py`, and `sheet.py` once.
  Verify: `git grep -n -e 'raise refusal_for' -- isekai/pipeline/caption.py isekai/pipeline/tagging.py isekai/pipeline/sheet.py` prints a line for `caption.py`, two for `tagging.py` and one for `sheet.py`.

- [x] 1.2 In `tests/test_caption.py` add `test_the_refusal_of_a_failed_read_is_held_whole`, bound to `cli:refusals:refusal-names-the-remedy`, per [D6](design.md#d6): a reader failing `StageFailure("transient", "rate limited")` gives the below-budget text, one failing `StageFailure("permanent", "the reader declined")` the exhausted text, each asserted with `==` on `str(refused.value)`, built from `run.id` and `runs_flag(run)`, imported from `tests.stages` beside `caption`. In the same case, an exhausted run called with `briefing_path=tmp_path / "absent.md"` refuses with the budget's text and not with an `OSError`, which holds [D2](design.md#d2).
  Verify: `uv run pytest tests/test_caption.py -k failed_read_is_held_whole` exits 0.

- [x] 1.3 In `tests/test_tagging.py` add `test_the_refusal_of_a_failed_hosted_tag_is_held_whole`, bound to `cli:refusals:refusal-names-the-remedy`, in the same way for `tag_hosted`: a local `Tagger` stub whose `tag` raises `StageFailure("transient", "rate limited")` and one raising `StageFailure("permanent", "the tagger declined")`, the texts of `tags` in [D6](design.md#d6).
  Verify: `uv run pytest tests/test_tagging.py -k failed_hosted_tag_is_held_whole` exits 0.

- [x] 1.4 In `tests/test_tagging.py` add `test_the_refusal_of_a_failed_local_tag_is_held_whole`, bound to the same key, for `tag_wd14` over `_unreadable`, whose text is the `wd14` row of [D6](design.md#d6) with the detail `cannot identify image file`. In the same case, an exhausted run whose `open_tagger` raises `AssertionError` refuses with `check_budget`'s text, which holds [D2](design.md#d2).
  Verify: `uv run pytest tests/test_tagging.py -k failed_local_tag_is_held_whole` exits 0.

- [x] 1.5 In `tests/test_sheet_stage.py` add `test_the_refusal_of_a_failed_sheet_is_held_whole`, bound to the same key, for the tag outside the vocabulary of `_drop_the_tag`: the whole text of the `sheet` row of [D6](design.md#d6), written out as a literal from one run of the case against the code as it stands, not read back from the record file.
  Verify: `uv run pytest tests/test_sheet_stage.py -k failed_sheet_is_held_whole` exits 0.

- [x] 1.6 Find the lines of each sequence: from its `check_budget(` line to the line of the `) from failed` that ends its call of `refusal_for`, in `caption` of `isekai/pipeline/caption.py`, `tag_wd14` and `tag_hosted` of `isekai/pipeline/tagging.py`, and `_from_tag_list` of `isekai/pipeline/sheet.py`; and `refusal_for` of `isekai/foundation/run.py`, from its `def` to one line before `def instructions_record`.
  Verify: `git grep -n -e 'check_budget(' -e '^        ) from failed$' -e '^def refusal_for' -e '^def instructions_record' -- isekai/pipeline/caption.py isekai/pipeline/tagging.py isekai/pipeline/sheet.py isekai/foundation/run.py` prints a line for each.

- [x] 1.7 Run the mutation over each sequence of 1.6, per [D6](design.md#d6), one run a range: `uv run python -m tools.mutate isekai/pipeline/caption.py:<first>-<last> --tests tests/test_caption.py tests/test_run_directory.py tests/test_resume.py`, the same over the ranges of `tag_wd14` and `tag_hosted` in `tagging.py` with `tests/test_tagging.py`, and over `_from_tag_list` in `sheet.py` with `tests/test_sheet_stage.py`. Kill each survivor with a case in the file of its stage; one no case can kill is named equivalent, with its reason, in the commit body.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.

- [x] 1.8 Run the mutation over `refusal_for`: `uv run python -m tools.mutate isekai/foundation/run.py:<first>-<last> --tests tests/test_run_directory.py tests/test_caption.py tests/test_tagging.py tests/test_sheet_stage.py tests/test_resume.py`, the survivors handled as in 1.7, the case in `tests/test_run_directory.py`.
  Verify: `uv run pytest tests/test_run_directory.py tests/test_caption.py tests/test_tagging.py tests/test_sheet_stage.py tests/test_resume.py` exits 0.

## 2 — Add `attempt` and `producer_for`

- [x] 2.1 In `tests/test_run_directory.py` add the cases of `attempt`, imported from `isekai.foundation.run`, bound to `run-directory:budget:at-budget-the-stage-refuses` and `run-directory:failure:kind-and-attempt-are-in-the-filename`: `test_attempt_checks_the_budget_before_it_opens` (a spent stage refuses, neither `opening` nor `work` called), `test_attempt_opens_outside_the_try` (a `Refusal` from `opening` propagates and records nothing) and `test_attempt_hands_what_opening_returned_to_the_work` (the work's result is returned, an `opening` returning an empty string included). The file's import of `attempt` keeps it red until 2.5.
  Verify: `git grep -n -F 'test_attempt_checks_the_budget_before_it_opens' -- tests/test_run_directory.py` prints one line.

- [x] 2.2 In the same file add `test_attempt_records_a_stage_failures_kind_and_chains_the_refusal` (a `StageFailure("transient", …)` writes `001.error.1.transient.json` and the `Refusal`'s cause is the failure), `test_attempt_records_any_other_catch_as_permanent` and `test_attempt_lets_an_uncaught_exception_through_unrecorded`, per [D1](design.md#d1), with the same keys.
  Verify: `git grep -n -F 'test_attempt_records_any_other_catch_as_permanent' -- tests/test_run_directory.py` prints one line.

- [x] 2.3 In the same file add `test_producer_for_returns_the_row_of_a_key`: each row of `PRODUCERS` is `producer_for(row.key)`, and a key no row holds raises `KeyError`. Bind it to `run-directory:budget:at-budget-the-stage-refuses`.
  Verify: `git grep -n -F 'test_producer_for_returns_the_row_of_a_key' -- tests/test_run_directory.py` prints one line.

- [x] 2.4 In `isekai/foundation/producers.py` add `producer_for(key: str) -> Producer` after `PRODUCERS`, per [D3](design.md#d3), with a docstring and an example; in `isekai/foundation/run.py` import it from `isekai.foundation.producers` and list it in `__all__`.
  Verify: `git grep -n -e '^def producer_for' -- isekai/foundation/producers.py` prints one line.

- [x] 2.5 In `isekai/foundation/run.py` add `attempt` after `refusal_for`, per [D1](design.md#d1) and [D2](design.md#d2): the positional `key`, `run`, `directory`, `version` and `work`, then the keyword-only `noun`, `catching`, `flow` and `opening`; it calls `refusal_for` in its present form, with the folder, the verb and the key read by `producer_for`. List it in `__all__`, and give it a docstring with an example.
  Verify: `uv run pytest tests/test_run_directory.py` exits 0.

## 3 — Call `attempt` from the stages

- [x] 3.1 In `caption` of `isekai/pipeline/caption.py` replace the block from `check_budget(STAGE, …)` to `) from failed` with one call, per [D1](design.md#d1) and [D7](design.md#d7): `attempt(STAGE, run, directory, version, …)` whose work reads `run.photo` with the briefing it is handed, with `noun="reader"`, `catching=(StageFailure,)` and `opening=briefing_path.read_text`. Keep the guard and `next_version` as they are.
  Verify: `git grep -n -F 'refusal_for(' -- isekai/pipeline/caption.py` prints nothing.

- [x] 3.2 In `tag_wd14` of `isekai/pipeline/tagging.py` make the same replacement, from `check_budget(WD14, …)`, with `opening=open_tagger`, `noun="tagger"` and `catching=(Refusal, OSError)`; the work returns the scores with `tagger.pins`, and the artifact's `artifacts` reads those pins. Keep the comment that the kind is always permanent beside the call, and in the docstring say `attempt` calls `open_tagger` after the budget's check and outside its `try`.
  Verify: `git grep -n -F 'check_budget(WD14' -- isekai/pipeline/tagging.py` prints nothing.

- [x] 3.3 In `tag_hosted` of the same file make the same replacement, the `record_failure(` call and the refusal going with the block, with `catching=(StageFailure,)`, `noun="tagger"` and no `opening`.
  Verify: `git grep -n -F 'record_failure(' -- isekai/pipeline/tagging.py` prints nothing.

- [x] 3.4 In `_from_tag_list` of `isekai/pipeline/sheet.py` replace the block from `check_budget(STAGE, …)` to the `return fields, made_by` with one call, its `record_failure(` call and refusal going with the block, per [D7](design.md#d7): `attempt(STAGE, run, directory, version, …)`, `flow=flow`, `noun="sheet"`, `catching=(Refusal,)`, its work the `_route` call and the `validate` call, returning the fields and `made_by`. The `remedy` assignment moves above the call, since the work reads it; its strings and the draft branch stay as they are.
  Verify: `git grep -n -F 'record_failure(' -- isekai/pipeline/sheet.py` prints nothing.

- [x] 3.5 In `isekai/pipeline/tagging.py` delete `VERB` and the comment above it, which nothing reads now.
  Verify: `git grep -n -w -e VERB -- isekai/pipeline/tagging.py` prints nothing.

- [x] 3.6 Drop from `caption.py`, `tagging.py` and `sheet.py` each import `ruff` names unused, and import `attempt` from `isekai.foundation.run`.
  Verify: `uv run ruff check isekai/pipeline` exits 0.

## 4 — Narrow `refusal_for` and take its row out

- [ ] 4.1 **HALT CHECK** The premise of [D4](design.md#d4) stands: the one test that calls `refusal_for` is in `tests/test_run_directory.py`, and no other file under `tests` or `evaluation` reads it but `tests/test_ratchets.py`'s row.
  Verify: `git grep -n -w -e refusal_for -- tests evaluation` prints the import and the call in `tests/test_run_directory.py` and the row in `tests/test_ratchets.py`.

- [ ] 4.2 In `test_a_record_that_refuses_the_next_run_names_its_deletion` of `tests/test_run_directory.py` call `refusal_for("caption", Run("aunt-ada", RUNS_ROOT / "aunt-ada"), kinds[-1], "timed out", record, None, noun="reader")`, per [D4](design.md#d4); the assertions stand.
  Verify: `git grep -n -F -A7 'refusal = refusal_for(' -- tests/test_run_directory.py` prints the call over eight lines, `"caption",` its first argument and `noun="reader",` its last, with no `"captions",` among them.

- [ ] 4.3 In `refusal_for` of `isekai/foundation/run.py` take `(key, run, kind, detail, record, flow, *, noun)`, bind `producer = producer_for(key)` and read `producer.folder`, `producer.verb` and `key` where the body read `area`, `verb` and `budget`, and `noun` where it read `stage`; the strings it builds are not edited. Rewrite the docstring's "both stages" and its paragraphs on `area` and `budget` to name the row.
  Verify: `git grep -n -e '^    area: str' -e '^    budget: str' -- isekai/foundation/run.py` prints nothing.

- [ ] 4.4 In `attempt` of the same file call `refusal_for(key, run, kind, detail, record, flow, noun=noun)`.
  Verify: `uv run pytest tests/test_run_directory.py tests/test_caption.py tests/test_tagging.py tests/test_sheet_stage.py tests/test_resume.py` exits 0.

- [ ] 4.5 In `tests/test_ratchets.py` remove the row `"isekai/foundation/run.py::refusal_for": 9,` from `WIDE_FUNCTIONS`.
  Verify: `git grep -n -F 'run.py::refusal_for' -- tests/test_ratchets.py` prints nothing.

- [ ] 4.6 In `tests/test_ratchets.py` set `WIDE_ROWS = 12`.
  Verify: `git grep -n -e '^WIDE_ROWS = 12' -- tests/test_ratchets.py` prints one line.

## 5 — Replay the mutation and amend the documents

- [ ] 5.1 Find the lines of the narrowed function and of the new one in `isekai/foundation/run.py`: `refusal_for` runs from its `def` to one line before `def attempt`, and `attempt` from its `def` to one line before `def instructions_record`.
  Verify: `git grep -n -e '^def attempt' -e '^def refusal_for' -e '^def instructions_record' -- isekai/foundation/run.py` prints a line for each.

- [ ] 5.2 Run the mutation over `attempt` and over `refusal_for`, per [D6](design.md#d6), one run a range: `uv run python -m tools.mutate isekai/foundation/run.py:<first>-<last> --tests tests/test_run_directory.py tests/test_caption.py tests/test_tagging.py tests/test_sheet_stage.py tests/test_resume.py`. Kill each survivor with a case in `tests/test_run_directory.py`; one no case can kill is named equivalent, with its reason, in the commit body.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.

- [ ] 5.3 In `docs/decisions.md` amend D73 per [D8](design.md#d8): the statement gains a sentence naming `attempt` in `run.py` as the sequence of `caption`, `wd14`, `tags` and `sheet`, read by `producer_for`; the *Accepts* drops "the sequence inside a stage" and says the paid stages keep their own; the *Made by* gains `0188`. No decision is added.
  Verify: `git grep -n -F 'the sequence inside a stage' -- docs/decisions.md` prints nothing.

- [ ] 5.4 In `isekai/foundation/README.md` name `attempt` in the *Files* row of `run.py`, beside `refusal_for`.
  Verify: `git grep -n -w -e attempt -- isekai/foundation/README.md` prints one line.

- [ ] 5.5 In the same file name `producer_for` in the *Files* row of `producers.py`.
  Verify: `git grep -n -F 'producer_for' -- isekai/foundation/README.md` prints one line.
