# The evaluator seams — tasks

Each phase gives one entry point or one function a parameter, switches its tests to pass a fake, and removes the module's row from the ratchet. Design: [design](design.md).

## Progress

- [x] 1 — The embedder, a parameter of the evaluator's main · moderate
- [ ] 2 — The reader, a parameter of the recall's main · moderate
- [ ] 3 — The manifest, a parameter of the embedder · moderate

## 1 — The embedder, a parameter of the evaluator's main

- [x] 1.1 In `evaluation/__main__.py`, give `main` the keyword-only parameter `embedder: Callable[[Path], Embed] = _embedder` ([D1](design.md#d1)), and change its line `embed = _embedder(args.models)` to `embed = embedder(args.models)`.
  Verify: `git grep -n -F "embedder: Callable" -- evaluation/__main__.py` prints one line.
- [x] 1.2 In `tests/test_evaluation_cli.py`, delete each `monkeypatch.setattr(entry, "_embedder", …)` line and pass its lambda as `embedder=` to the `entry.main` call below it. Drop the `monkeypatch` parameter from each test that no longer uses it.
  Verify: `git grep -n -F '"_embedder"' -- tests/test_evaluation_cli.py` prints nothing.
- [x] 1.3 In `tests/test_ratchets.py`, delete the row `"evaluation.__main__": 5,` from `PATCHED_MODULES`.
  Verify: `git grep -n -F "evaluation.__main__" -- tests/test_ratchets.py` prints nothing.
- [x] 1.4 In `tests/test_ratchets.py`, set `PATCHED_ROWS = 23`.
  Verify: `git grep -n -e "^PATCHED_ROWS = 23" -- tests/test_ratchets.py` prints one line.
- [x] 1.5 Run the evaluator's tests and the ratchet with the row gone.
  Verify: `uv run pytest tests/test_evaluation_cli.py tests/test_eval_manifest.py tests/test_ratchets.py` exits 0.

## 2 — The reader, a parameter of the recall's main

- [ ] 2.1 In `evaluation/recall.py`, give `main` the keyword-only parameter `reader: Callable[[Path], tuple[Read, dict[str, str]]] = _reader` ([D1](design.md#d1)), and change its line `read_tags, pins = _reader(args.models)` to `read_tags, pins = reader(args.models)`.
  Verify: `git grep -n -F "reader: Callable" -- evaluation/recall.py` prints one line.
- [ ] 2.2 In `tests/test_recall_cli.py`, drop `monkeypatch` from the parameters of `_run` and pass `reader=lambda models: (tagger, PINS)` to its `recall.main` call in place of its line `monkeypatch.setattr(recall, "_reader", …)`. Change each `_run(monkeypatch, …)` call to `_run(…)`, and drop the `monkeypatch` parameter from each test that used it for `_run` alone. The tests that patch `wiring` or `wd14` keep it.
  Verify: `git grep -n -F -e '"_reader"' -e "_run(monkeypatch" -- tests/test_recall_cli.py` prints nothing.
- [ ] 2.3 In `tests/test_ratchets.py`, delete the row `"evaluation.recall": 1,` from `PATCHED_MODULES`.
  Verify: `git grep -n -F "evaluation.recall" -- tests/test_ratchets.py` prints nothing.
- [ ] 2.4 In `tests/test_ratchets.py`, set `PATCHED_ROWS = 22`.
  Verify: `git grep -n -e "^PATCHED_ROWS = 22" -- tests/test_ratchets.py` prints one line.
- [ ] 2.5 Run the recall's tests and the ratchet with the row gone.
  Verify: `uv run pytest tests/test_recall_cli.py tests/test_ratchets.py` exits 0.

## 3 — The manifest, a parameter of the embedder

- [ ] 3.1 In `evaluation/__main__.py`, add `Manifest` to the import `from isekai.boundary.provision import entry_for`. Give `_embedder` the keyword-only parameter `manifest: Manifest | None = None` ([D2](design.md#d2)). In `_embedder` alone, not in `_models`, replace its line `manifest = load_eval_manifest()` with `if manifest is None:` and, under it, `manifest = load_eval_manifest()`. Leave the function's own imports as they are.
  Verify: `git grep -n -F "manifest: Manifest | None = None" -- evaluation/__main__.py` prints one line.
- [ ] 3.2 In `tests/test_eval_manifest.py`, delete each `monkeypatch.setattr(eval_models, "load_eval_manifest", …)` line and pass `manifest=eval_manifest` to the `entry_point._embedder` call of each such test. Drop the `monkeypatch` parameter of those tests and the import `from evaluation import eval_models`.
  Verify: `git grep -n -F -e "eval_models, " -e "import eval_models" -- tests/test_eval_manifest.py` prints nothing.
- [ ] 3.3 In `tests/test_ratchets.py`, delete the row `"evaluation.eval_models": 2,` from `PATCHED_MODULES`.
  Verify: `git grep -n -F "evaluation.eval_models" -- tests/test_ratchets.py` prints nothing.
- [ ] 3.4 In `tests/test_ratchets.py`, set `PATCHED_ROWS = 21`.
  Verify: `git grep -n -e "^PATCHED_ROWS = 21" -- tests/test_ratchets.py` prints one line.
- [ ] 3.5 Run the tests the phases touched, with the layer, docs and spec guards.
  Verify: `uv run pytest tests/test_evaluation_cli.py tests/test_recall_cli.py tests/test_eval_manifest.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_spec_bindings.py` exits 0.
- [ ] 3.6 Run the standing mutants over the edits file.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
