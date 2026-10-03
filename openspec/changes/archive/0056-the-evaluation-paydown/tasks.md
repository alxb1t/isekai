# Tasks — 0056 the evaluation paydown

The run ids, then the scenario, per [design](design.md). The delta holds every new scenario; each task below
adds or rebinds the tests that bind them.

## Progress

- [x] 1 — The run ids
- [x] 2 — The scenario

Line numbers are `7f61f56`'s. Every new test carries `@pytest.mark.spec` with the key its task names.

## 1 — The run ids

- [x] 1.1 **HALT CHECK** — both commands write a run's full id, and the fixtures hold full ids.
  Verify: `grep -c '"run": run.id' evaluation/recall.py` prints `1`, `grep -c 'run.id, seed' evaluation/__main__.py` prints `3`, and `grep -c '5f3a9c1e2b7d-p1-1' tests/cohort/evaluation.json` prints `1`.
- [x] 1.2 Add `run_prefix` to `evaluation/record.py` and call it in `evaluation/__main__.py:133-138` and `evaluation/recall.py:304`; drop the slice at `evaluation/recall.py:197`, per [D1](design.md#d1).
  Verify: `grep -c '^def run_prefix(' evaluation/record.py` prints `1`, `grep -c 'run_prefix(run.id)' evaluation/__main__.py` prints `3`, `grep -c 'run_prefix(run.id)' evaluation/recall.py` prints `1`, and `grep -c '\[:12\]' evaluation/recall.py` prints `0`.
- [x] 1.3 Shorten each run value in `tests/cohort/evaluation.json` and `tests/recall/recall.json` to its first twelve characters, and write `tests/cohort/evaluation.txt` and `tests/recall/recall.txt` from them with each module's `table`, per [D1](design.md#d1).
  Verify: `grep -c '5f3a9c1e2b7d-p1-1' tests/cohort/evaluation.json tests/cohort/evaluation.txt | grep -c ':0'` prints `2`, and `grep -c '187ec7dce855aaaa' tests/recall/recall.json` prints `0`.
- [x] 1.4 Make `tests/test_recall_cli.py:192` expect the prefix; add to `tests/test_recall_cli.py` a test binding `evaluation:recall:a-run-is-named-by-its-digest-prefix` and to `tests/test_evaluation_cli.py` a test binding `evaluation:table:a-run-is-named-by-its-digest-prefix`, each asserting the record and the table carry no photograph's filename.
  Verify: `grep -c 'evaluation:recall:a-run-is-named-by-its-digest-prefix' tests/test_recall_cli.py` prints `1`, and `grep -c 'evaluation:table:a-run-is-named-by-its-digest-prefix' tests/test_evaluation_cli.py` prints `1`.

## 2 — The scenario

- [x] 2.1 Bind `test_a_latest_group_holding_no_render_is_not_rendered` (`tests/test_evaluation_cli.py:166-167`) to `evaluation:table:an-empty-latest-group-is-not-rendered`, per [D2](design.md#d2).
  Verify: `grep -c 'evaluation:table:the-latest-group-is-ranked' tests/test_evaluation_cli.py` prints `1`, and `grep -c 'evaluation:table:an-empty-latest-group-is-not-rendered' tests/test_evaluation_cli.py` prints `1`.
