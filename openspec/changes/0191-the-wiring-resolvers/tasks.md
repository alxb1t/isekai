# The wiring's resolvers — tasks

The proposer's cache, the evaluator's roots and the tagging openers become keywords, and the wiring's row leaves the patch ratchet.

## Progress

- [x] 1 — The cache · moderate
- [x] 2 — The roots · moderate
- [ ] 3 — The openers and the ratchet row · moderate

## 1 — The cache

- [x] 1.1 **HALT CHECK** `isekai/interface/wiring.py` holds the global [D1](design.md#d1) replaces, and the ratchet stands at its base value.
  Verify: `git grep -n -e "^_proposer" -e "^_PROPOSER_OPENING" -e "^PATCHED_ROWS = 19" -- isekai/interface/wiring.py tests/test_ratchets.py` prints a line for each pattern.
- [x] 1.2 In `tests/test_propose.py`, add `from isekai.boundary import sam2 as sam2_boundary` and, after `test_propose_wiring_a_missing_model_refuses_naming_the_fetch_and_is_not_kept`, add `test_propose_wiring_the_default_cache_opens_the_boundary_models` marked `@pytest.mark.spec_exempt("structural: the default cache opens the boundary's models")`, per [D5](design.md#d5). It imports `PROPOSERS` inside the function and asserts its `open_pose` and `open_segmenter` are the boundary's.
  Verify: `uv run pytest tests/test_propose.py -k default_cache` exits 1, on the missing `PROPOSERS`.
- [x] 1.3 In `isekai/interface/wiring.py`, import `PoseFinder` beside `open_pose` and `Segmenter` beside `open_segmenter`, add `Proposers` and `PROPOSERS`, and replace the body of `proposer_for`, exactly as [D1](design.md#d1) gives them. `_proposer`, `_PROPOSER_OPENING` and `global _proposer` go.
  Verify: `git grep -n -e "^_proposer" -e "^_PROPOSER_OPENING" -e "global _proposer" -- isekai/interface/wiring.py` prints nothing.
- [x] 1.4 In `tests/test_propose.py`, import `Proposers` first in the `isekai.interface.wiring` import line, and delete the autouse fixture `_unopened`, which sets `"_proposer"` to `None`, and the imports `Iterator` and `wiring` once nothing reads them. `_opening(monkeypatch)` builds `Proposers(open_pose=pose, open_segmenter=segmenter)` and returns `(cache, opened)`, annotated `tuple[Proposers, list[str]]`; its caller unpacks it.
  Verify: `git grep -n -F '"_proposer"' -- tests/test_propose.py` prints nothing.
- [x] 1.5 In `tests/test_propose.py`, move the cases `test_propose_wiring_the_models_open_once_for_two_proposals`, `test_propose_wiring_overlapping_first_proposals_open_the_models_once`, `test_propose_wiring_a_damaged_model_refuses_naming_the_file_and_the_fetch` and `test_propose_wiring_a_missing_model_refuses_naming_the_fetch_and_is_not_kept` onto a cache of their own, as [D1](design.md#d1) ends. Each passes `replace(wiring_from(runs=…), proposer=cache)` to `proposer_of`, so the patches of `"open_pose"` and `"open_segmenter"` go; `wired.proposer is proposer_for` is still asserted, on the wiring `wiring_from` built, and no other assertion changes. The helpers `damaged` and `absent` are annotated `-> PoseFinder`, imported from `isekai.boundary.pose`, so `ty` accepts them as openers.
  Verify: `git grep -n -e '"open_pose"' -e '"open_segmenter"' -- tests/test_propose.py` prints nothing.
- [x] 1.6 Run the proposer's cases and the placement tests over the cache.
  Verify: `uv run pytest tests/test_propose.py tests/test_ui_propose.py tests/test_ui_placement.py` exits 0.
- [x] 1.7 Lint what the phase changed.
  Verify: `uv run ruff check isekai/interface/wiring.py tests/test_propose.py` exits 0.

## 2 — The roots

- [x] 2.1 **HALT CHECK** `trackable` and `destination` take no keyword yet.
  Verify: `git grep -n -e "^def trackable(directory: Path) -> bool:" -e "^def destination(runs: Path, name: str) -> Path:" -- isekai/interface/wiring.py evaluation/record.py` prints a line for each pattern.
- [x] 2.2 In `tests/test_evaluation_cli.py`, in `test_a_record_inside_the_working_tree_and_outside_the_ignored_root_is_refused`, delete the patches of the wiring's roots and the `monkeypatch` parameter, and pass `repository=repository, data_root=repository / ".data"` to `entry.main`. Drop the `wiring` import, which nothing else reads. No assertion changes.
  Verify: `uv run pytest tests/test_evaluation_cli.py -k inside_the_working_tree` exits 1, on the unexpected keyword.
- [x] 2.3 In `tests/test_recall_cli.py`, give `_run` a `**roots: Path` it passes to `recall.main`, and in `test_a_record_inside_the_working_tree_and_outside_the_ignored_root_is_refused` delete the patches of the wiring's roots and the `monkeypatch` parameter, and call `_run(tagger, runs, repository=repository, data_root=repository / ".data")`. Drop the `wiring` import, which nothing else reads. No assertion changes.
  Verify: `uv run pytest tests/test_recall_cli.py -k inside_the_working_tree` exits 1, on the unexpected keyword.
- [x] 2.4 In `isekai/interface/wiring.py`, replace `trackable` exactly as [D2](design.md#d2) gives it. `_check_run_root` still calls `trackable(resolved)`.
  Verify: `git grep -n -F "repository: Path = REPOSITORY, data_root: Path = DATA_ROOT" -- isekai/interface/wiring.py` prints one line.
- [x] 2.5 In `evaluation/record.py`, give `destination` the keywords of [D2](design.md#d2) and pass them to `trackable`. It takes the roots from `isekai.foundation.run`, which it already imports from.
  Verify: `git grep -n -F "trackable(target.parent," -- evaluation/record.py` prints one line.
- [x] 2.6 In `evaluation/__main__.py` and `evaluation/recall.py`, give each `main` the keywords of [D2](design.md#d2) after its existing ones and pass them to `destination`. Each takes the roots from `isekai.foundation.run`, beside the names it already imports from there.
  Verify: `git grep -l -F "data_root=data_root" -- evaluation/__main__.py evaluation/recall.py` prints both paths.
- [x] 2.7 Run the evaluators' cases and the structure tests over the keywords.
  Verify: `uv run pytest tests/test_evaluation_cli.py tests/test_recall_cli.py tests/test_run_directory.py tests/test_layers.py tests/test_docs.py` exits 0.
- [x] 2.8 Lint what the phase changed.
  Verify: `uv run ruff check isekai/interface/wiring.py evaluation tests/test_evaluation_cli.py tests/test_recall_cli.py` exits 0.

## 3 — The openers and the ratchet row

- [ ] 3.1 **HALT CHECK** only the tagger's opener and the caption config's loader are still patched.
  Verify: `git grep -n -F "setattr(wiring," -- tests` prints a line in each of `tests/test_tagging.py` and `tests/test_pipeline_cli.py`, and none elsewhere.
- [ ] 3.2 In `tests/test_tagging.py`, call `wiring.tagger_for(open_session=lambda *_a, **_k: opened)` in `test_the_local_tagger_resolves_with_no_flow`, and pass `tagger=lambda: wiring.tagger_for(open_session=swapped)` in `test_a_pin_that_does_not_match_is_a_refusal_and_the_hosted_list_is_written`. Delete both patches of `"open_session"` and each `monkeypatch` parameter nothing else reads. No assertion changes.
  Verify: `uv run pytest tests/test_tagging.py -k "resolves_with_no_flow or pin_that_does_not_match"` exits 1, on the unexpected keyword.
- [ ] 3.3 In `tests/test_pipeline_cli.py`, in `test_prepare_refuses_when_a_pin_does_not_match` pass `tagger=lambda: wiring.tagger_for(open_session=swapped)`, and in `test_a_flow_resolves_to_a_reader_running_the_configured_model` call `wiring.reader_for(config=lambda: configured)` and `wiring.hosted_tagger_for(config=lambda: configured)`. Delete the patches of `"open_session"` and `"load_caption_config"` and each `monkeypatch` parameter nothing else reads. No assertion changes.
  Verify: `uv run pytest tests/test_pipeline_cli.py -k "refuses_when_a_pin or reader_running_the_configured"` exits 1, on the unexpected keyword.
- [ ] 3.4 In `isekai/interface/wiring.py`, import `CaptionConfig` beside `load_caption_config`, and give `reader_for` and `hosted_tagger_for` the keyword `config`, called in place of `load_caption_config()`, as [D3](design.md#d3) gives them, wrapped where `ruff format` wraps. Their docstrings keep what they say.
  Verify: `git grep -n -F "config: Callable[[], CaptionConfig] = load_caption_config" -- isekai/interface/wiring.py` prints a line for each function.
- [ ] 3.5 In `isekai/interface/wiring.py`, give `tagger_for` the keyword `open_session`, called in place of `open_session()`, as [D3](design.md#d3) gives it. The `except DigestMismatch as swapped:` line is not touched.
  Verify: `git grep -n -F "def tagger_for(open_session: Callable[[], LocalTagger] = open_session) -> LocalTagger:" -- isekai/interface/wiring.py` prints one line.
- [ ] 3.6 No test calls `monkeypatch.setattr(wiring` any more.
  Verify: `git grep -n -F "monkeypatch.setattr(wiring" -- tests` prints nothing.
- [ ] 3.7 In `tests/test_ratchets.py`, delete the row `"isekai.interface.wiring": 13,` from `PATCHED_MODULES`, per [D4](design.md#d4).
  Verify: `git grep -n -e "^    .isekai\.interface\.wiring.: [0-9]" -- tests/test_ratchets.py` prints nothing.
- [ ] 3.8 In `tests/test_ratchets.py`, set `PATCHED_ROWS = 18`.
  Verify: `git grep -n -e "^PATCHED_ROWS = 18" -- tests/test_ratchets.py` prints one line.
- [ ] 3.9 Run the cases of every file the change touched, and the structure tests.
  Verify: `uv run pytest tests/test_propose.py tests/test_tagging.py tests/test_pipeline_cli.py tests/test_evaluation_cli.py tests/test_recall_cli.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_spec_bindings.py` exits 0.
- [ ] 3.10 Replay the standing mutants over the edited files; `BD-1b` finds its line in `tagger_for`.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.
