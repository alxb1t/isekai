# Tasks — 0053 the evaluation mechanism

The arithmetic, the encoder, the entry point, then the deletion, per [design](design.md).
The delta holds every new scenario; each task below adds the tests that bind them.

## Progress

- [x] 1 — The arithmetic
- [ ] 2 — The encoder
- [ ] 3 — The entry point
- [ ] 4 — The deletion

Line numbers are `20ef5a7`'s. Every new test carries `@pytest.mark.spec` with the key its task names. The batch and
its record are the operator's, after the release.

## 1 — The arithmetic

- [x] 1.1 **HALT CHECK** — the entry point reads the old shape, no current render exists, the local SFace is the published one, and the provisioner pins Hugging Face alone.
  Verify: `grep -c photo_sha256 evaluation/__main__.py` prints `5`, `find .data -name '*.render.json' | wc -l` prints `0`, `shasum -a 256 models/opencv_face/sface.onnx | cut -c1-16` prints `0ba9fbfa01b5270c`, and `grep -q 'huggingface' isekai/boundary/provision.py && echo ok` prints `ok`.
- [x] 1.2 Write `evaluation/cohort.py`: `Photograph`, `Cohort`, `load_cohort`, `rank`, `hits`, `chance`, `record` and `table`, per [D1](design.md#d1), [D2](design.md#d2) and [D4](design.md#d4); stdlib and `isekai.boundary.provision.digest_of` alone.
  Verify: `grep -cE '^def (load_cohort|rank|hits|chance|record|table)\(' evaluation/cohort.py` prints `6`, and `grep -c '^import numpy\|^from PIL' evaluation/cohort.py` prints `0`.
- [x] 1.3 Add `tests/test_cohort.py` binding `evaluation:cohort:a-run-is-matched-by-digest`, `evaluation:cohort:a-run-outside-the-cohort-is-reported`, `evaluation:counts:photograph-level-hit`, `evaluation:counts:person-level-excludes-the-source`, `evaluation:counts:chance-is-reported`, `evaluation:counts:no-average-no-percentage`, `evaluation:table:one-column-per-flow` and `evaluation:table:the-table-re-derives-from-the-record`, on vectors written by hand.
  Verify: `grep -c 'pytest.mark.spec("evaluation:' tests/test_cohort.py` prints `8`.

## 2 — The encoder

- [ ] 2.1 In `tools/derive_eval_manifest.py`, add `"opencv"` to `PUBLISHERS`, add the two `Spec`s of [D3](design.md#d3) with the revisions in [design](design.md#context), set `PINNED` to today, and run `uv run python -m tools.derive_eval_manifest`.
  Verify: `grep -c '"dest": "opencv_face/' evaluation/eval_models.json` prints `2`, and `grep -c '0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79\|8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4' evaluation/eval_models.json` prints `2`.
- [ ] 2.2 Write `evaluation/face.py`: `Detector`, `Encoder`, `align`, `embed` and the `python -m evaluation.face <image>…` probe, per [D3](design.md#d3); `onnxruntime` imported inside the constructors after `silence_onnxruntime()`.
  Verify: `grep -cE '^def (align|embed)\(|^class (Detector|Encoder)' evaluation/face.py` prints `4`, `grep -c 'silence_onnxruntime()' evaluation/face.py` prints `2`, and `grep -c '^import onnxruntime' evaluation/face.py` prints `0`.
- [ ] 2.3 Add `tests/test_face.py` binding `evaluation:encoder:the-crop-is-aligned` (the template's own points give the identity transform; a shifted copy gives the shift back) and `evaluation:encoder:no-face-is-its-own-outcome` (`embed` with a detector that finds nothing returns `None`).
  Verify: `grep -c 'pytest.mark.spec("evaluation:encoder:' tests/test_face.py` prints `2`.
- [ ] 2.4 **HALT CHECK** — land the two models with `bash tools/download_models.sh evaluation/eval_models.json`, then probe `.data/v0.30.1`: the three upper-body photographs and their `summon-anime-wai` renders each report a face; the full-body run is reported, not required. A miss on an upper-body render takes the fallback of [D3](design.md#d3) and records it in `design.md`.
  Verify: `uv run python -m evaluation.face .data/v0.30.1/runs/{187ec7dce855,28c3bb7ce031,d2043248d6e1}*/photo.png .data/v0.30.1/runs/{187ec7dce855,28c3bb7ce031,d2043248d6e1}*/summon-anime-wai/outputs/001/*.png | grep -c '^face '` prints `6`.

## 3 — The entry point

- [ ] 3.1 Rewrite `evaluation/__main__.py` per [D5](design.md#d5): `runs`, `--cohort`, `--models`, `--flows`; `Run` and `run_view.rendered` for the runs and the seeds; `evaluation.json` beside the runs; the table on stdout.
  Verify: `grep -c photo_sha256 evaluation/__main__.py` prints `0`, `grep -c '"--cohort"' evaluation/__main__.py` prints `1`, and `grep -c 'sys.exit' evaluation/__main__.py` prints `0`.
- [ ] 3.2 Add `tests/test_evaluation_cli.py` binding `evaluation:cohort:a-faceless-photograph-is-refused` and `evaluation:table:a-failure-is-a-row`, on a batch under `tmp_path` made with `open_run` and a fake embedder; one render with no face, one photograph never rendered, every other row written.
  Verify: `grep -c 'pytest.mark.spec("evaluation:' tests/test_evaluation_cli.py` prints `2`.
- [ ] 3.3 In `docs/decisions.md`, restate D22 per [D6](design.md#d6) and add D37 per [D7](design.md#d7); in `docs/principles.md`, add `## Measurement` after *Privacy* with its three principles and the tests that hold them.
  Verify: `grep -c '^### D37' docs/decisions.md` prints `1`, `grep -c 'only optional extra' docs/decisions.md` prints `0`, and `grep -c '^## Measurement' docs/principles.md` prints `1`.

## 4 — The deletion

- [ ] 4.1 Delete `evaluation/evaluate.py`, `evaluation/eval_backends.py`, `evaluation/ciede2000.py`, `evaluation/labels.py`, `evaluation/baseline/`, `tests/test_evaluate.py`, `tests/test_labels.py`, `tests/test_ciede2000.py` and `tests/eval_fakes.py`, per [D8](design.md#d8).
  Verify: `ls evaluation/evaluate.py evaluation/eval_backends.py evaluation/ciede2000.py evaluation/labels.py evaluation/baseline tests/test_evaluate.py tests/test_labels.py tests/test_ciede2000.py tests/eval_fakes.py 2>&1 | grep -c 'No such file'` prints `9`.
- [ ] 4.2 In `evaluation/eval_models.py`, replace `SHARED_WITH_THE_GRAPH`, `RECOGNIZER` and `shared_entries_that_differ` with `DETECTOR`, `ENCODER` and `shared_with_the_graph`; `__main__` refuses on a non-empty result; in `tools/derive_eval_manifest.py`, drop the copied entries, the old `Spec`s and the old publishers, and re-run it.
  Verify: `grep -c '^def shared_with_the_graph' evaluation/eval_models.py` prints `1`, `grep -c 'glintr100\|styleid\|segformer\|anime_face' evaluation/eval_models.json` prints `0`, and `grep -c '"dest"' evaluation/eval_models.json` prints `2`.
- [ ] 4.3 In `tests/test_eval_manifest.py`, delete the tests binding `recognizer-matches-the-generators-pin` and add one binding `evaluation:encoder:shares-no-pin-with-the-generator`; re-point `tests/test_wd14.py:371-375` at `evaluation.face`.
  Verify: `grep -c 'recognizer-matches' tests/test_eval_manifest.py` prints `0`, `grep -c 'shares-no-pin-with-the-generator' tests/test_eval_manifest.py` prints `1`, and `grep -c 'eval_backends' tests/test_wd14.py` prints `0`.
- [ ] 4.4 In `pyproject.toml`, delete the optional-dependencies table with its comment, the ruff line for `eval_backends.py` and the `ty` override, per [D6](design.md#d6); run `uv lock`.
  Verify: `grep -c 'optional-dependencies\|eval_backends\|unresolved-import' pyproject.toml` prints `0`, and `grep -c '^name = "torch"' uv.lock` prints `0`.
- [ ] 4.5 Rewrite `evaluation/README.md` for the cohort evaluator; replace `docs/modules.md:74`'s `eval_backends.py` line; restate `README.md:313-314` and `:383-385` per [D6](design.md#d6).
  Verify: `grep -rc 'eval_backends\|\[eval\]' evaluation/README.md docs/modules.md README.md | grep -v ':0'` prints nothing.
- [ ] 4.6 In this change's `specs/evaluation/spec.md`, add `## REMOVED Requirements` for every requirement the [proposal](proposal.md) lists as REMOVED, each with **Reason** and **Migration**, and `## MODIFIED Requirements` with *Every model the scorer loads is pinned and verified* minus its last SHALL sentence and its `recognizer-matches-the-generators-pin` scenario; rewrite `openspec/specs/evaluation/spec.md:3-13` — *Purpose*, *Source*, *Tests* — to the cohort evaluator; `openspec validate 0053-the-evaluation-mechanism --strict`.
  Verify: `grep -c '^## REMOVED Requirements' openspec/changes/0053-the-evaluation-mechanism/specs/evaluation/spec.md` prints `1`, `grep -c '^### Requirement:' openspec/changes/0053-the-evaluation-mechanism/specs/evaluation/spec.md` prints `13`, and `grep -c 'blind human labelling' openspec/specs/evaluation/spec.md` prints `0`.
