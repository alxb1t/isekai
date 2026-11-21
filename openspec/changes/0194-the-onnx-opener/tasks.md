# The ONNX opener — tasks

Run a mutation over each site that makes a session, add the opener with its cases, call it from `wd14`, `pose`, `sam2` and the evaluator's `face`, then amend the documents and replay the standing mutants.

## Progress

- [ ] 1 — Add the opener with its cases · moderate
- [ ] 2 — Call the opener from its callers · moderate
- [ ] 3 — Amend the documents and replay the standing mutants · moderate

## 1 — Add the opener with its cases

- [ ] 1.1 **HALT CHECK** The premise of [D1](design.md#d1) stands: `isekai/boundary/onnx.py` does not exist and no name `cpu_session` is defined.
  Verify: `git grep -n -e 'def cpu_session' -e 'boundary.onnx' -- isekai evaluation tests` prints nothing.

- [ ] 1.2 **HALT CHECK** The sites of [D3](design.md#d3) stand: `wd14.py`, `pose.py`, `sam2.py` and `face.py` open their sessions by a call named `runtime.InferenceSession(`, `wd14.py` and `face.py` through a variable named `onnxruntime`.
  Verify: `git grep -c -F 'runtime.InferenceSession(' -- isekai/boundary/wd14.py isekai/boundary/pose.py isekai/boundary/sam2.py evaluation/face.py` prints `evaluation/face.py:1`, `isekai/boundary/pose.py:2`, `isekai/boundary/sam2.py:2` and `isekai/boundary/wd14.py:1`.

- [ ] 1.3 Find the lines of each site's body: `OnnxSession.__init__` of `isekai/boundary/wd14.py` runs from its `def __init__` to one line before `@property`; `OnnxPoseFinder.__init__` of `isekai/boundary/pose.py` to one line before `def find`; `OnnxSegmenter.__init__` of `isekai/boundary/sam2.py` to one line before `def embed`; `_session` of `evaluation/face.py` from its `def` to one line before `class Detector`.
  Verify: `git grep -n -e '^def _session' -e '^class Detector' -- evaluation/face.py` prints a line for each.

- [ ] 1.4 Run the mutation over each range of 1.3 before a line moves, per [D5](design.md#d5), one run a range: `uv run python -m tools.mutate <path>:<first>-<last> --tests <files>`, the files `tests/test_wd14.py tests/test_wd14_runtime.py` for `wd14.py`, `tests/test_pose.py tests/test_propose.py` for `pose.py`, `tests/test_sam2.py tests/test_propose.py` for `sam2.py` and `tests/test_wd14.py tests/test_face.py tests/test_evaluation_cli.py` for `face.py`. Kill each survivor with a case in the file of its site, `tests/test_wd14.py` for `face.py`, each with `spec_exempt("structural: …")`; one no case can kill is named equivalent, with its reason, in the commit body.
  Verify: `uv run pytest tests/test_wd14.py tests/test_wd14_runtime.py tests/test_pose.py tests/test_sam2.py tests/test_propose.py tests/test_face.py tests/test_evaluation_cli.py` exits 0.

- [ ] 1.5 In `tests/test_wd14.py` add the cases of [D5](design.md#d5), among them `def test_the_opener_switches_telemetry_off`, after `test_the_telemetry_check_catches_an_import_with_it_on`, on a recording runtime that keeps the arguments and keywords of each `InferenceSession` call, each with `@pytest.mark.spec_exempt("structural: …")`; import `cpu_session` and `silence_onnxruntime` from `isekai.boundary.onnx`, which keeps the file red until 1.6. The cases of the switch clear it with `monkeypatch.setenv` then `monkeypatch.delenv`, as `test_every_onnx_session_switches_telemetry_off_before_the_import` does.
  Verify: `git grep -n -F 'def test_the_opener_switches_telemetry_off' -- tests/test_wd14.py` prints one line.

- [ ] 1.6 Create `isekai/boundary/onnx.py` as [D1](design.md#d1) writes it: the docstring, `silence_onnxruntime()` with `wd14.py`'s docstring, and `cpu_session(runtime, model, options=None)` calling `silence_onnxruntime()` first, then `InferenceSession` with `providers` by keyword. It imports `os`, `Path` and `Any` and nothing of `isekai`; each bare `Any` in its signature carries `# noqa: ANN401 -- <reason>`, as the repository's other bare `Any`s do, so `ruff` stays green.
  Verify: `uv run pytest tests/test_wd14.py` exits 0.

- [ ] 1.7 In `isekai/boundary/README.md` add a *Files* row for `onnx.py` after `ollama.py` — `silence_onnxruntime`, the telemetry switch set before the runtime loads, and `cpu_session`, the one maker of a session on the CPU provider alone; it imports the standard library alone — reaching `nothing`, and a row `| `onnx.py` | — | — |` to the end of *Imported by*, then run `uv run python -m tools.derive_imported_by`.
  Verify: `uv run pytest tests/test_docs.py` exits 0.

## 2 — Call the opener from its callers

- [ ] 2.1 In `isekai/boundary/wd14.py` replace `def silence_onnxruntime` and its body with `from isekai.boundary.onnx import cpu_session, silence_onnxruntime` among the `isekai` imports, drop `import os`, and in `OnnxSession.__init__` open the session with `cpu_session(onnxruntime, model)` in place of `onnxruntime.InferenceSession(…)`, per [D3](design.md#d3) and [D4](design.md#d4); the calls of `silence_onnxruntime()` and `_require("onnxruntime")` before it, and `"silence_onnxruntime"` in `__all__`, stay.
  Verify: `git grep -n -e 'def silence_onnxruntime' -e 'onnxruntime.InferenceSession(' -e '^import os' -- isekai/boundary/wd14.py` prints nothing.

- [ ] 2.2 In `isekai/boundary/pose.py` import `cpu_session` and `silence_onnxruntime` from `isekai.boundary.onnx` in place of the import from `isekai.boundary.wd14`, and in `OnnxPoseFinder.__init__` drop the `providers` local and bind `self._detector` to `cpu_session(runtime, detector)` and `self._estimator` to `cpu_session(runtime, estimator)`.
  Verify: `git grep -n -e 'runtime.InferenceSession(' -e 'isekai.boundary.wd14' -- isekai/boundary/pose.py` prints nothing.

- [ ] 2.3 In `isekai/boundary/sam2.py` import `cpu_session` and `silence_onnxruntime` from `isekai.boundary.onnx` in place of the import from `isekai.boundary.wd14`, and in `OnnxSegmenter.__init__` drop the `providers` local and bind `self._encoder` to `cpu_session(runtime, encoder)` and `self._decoder` to `cpu_session(runtime, decoder)`.
  Verify: `git grep -n -e 'runtime.InferenceSession(' -e 'isekai.boundary.wd14' -- isekai/boundary/sam2.py` prints nothing.

- [ ] 2.4 In `evaluation/face.py` import `cpu_session` and `silence_onnxruntime` from `isekai.boundary.onnx` in place of the import from `isekai.boundary.wd14`, and end `_session` with `return cpu_session(onnxruntime, model, options)`, the lines that build `options` as they are.
  Verify: `git grep -n -e 'onnxruntime.InferenceSession(' -e 'isekai.boundary.wd14' -- evaluation/face.py` prints nothing.

- [ ] 2.5 Run `uv run python -m tools.derive_imported_by`: the *Imported by* row of `wd14.py` loses `pose.py`, `sam2.py` and `evaluation/face.py`, and the row of `onnx.py` gains them and `wd14.py`.
  Verify: `uv run pytest tests/test_docs.py tests/test_layers.py tests/test_pipeline_cli.py` exits 0.

- [ ] 2.6 Run the mutation over the whole of `isekai/boundary/onnx.py`, per [D5](design.md#d5), as one run over `isekai/boundary/onnx.py:1-80` with `tests/test_wd14.py tests/test_wd14_runtime.py tests/test_pose.py tests/test_sam2.py`; the range ends past the last line, which the tool allows. Kill each survivor with a case in `tests/test_wd14.py`.
  Verify: `uv run python -m tools.mutate isekai/boundary/onnx.py:1-80 --tests tests/test_wd14.py tests/test_wd14_runtime.py tests/test_pose.py tests/test_sam2.py` exits 0.

## 3 — Amend the documents and replay the standing mutants

- [ ] 3.1 In `isekai/boundary/README.md` amend the note on the telemetry switch: `silence_onnxruntime()` of `onnx.py` sets the switch first, "for every session" in place of "for both sessions".
  Verify: `git grep -n -F 'for both sessions' -- isekai/boundary/README.md` prints nothing.

- [ ] 3.2 In `docs/modules.md` change the sentence on the proposal's pieces to read that `pose` and `sam2` each import `provision`, `unpack`, `onnx` — `boundary/onnx.py`'s — and `foundation/refusal.py`, in place of `wd14`'s `silence_onnxruntime`.
  Verify: `git grep -n -F 'silence_onnxruntime' -- docs/modules.md` prints nothing.

- [ ] 3.3 Replay the standing mutants. A find an edit moved stops the replay with an error: re-point that entry's `find` and `replace` of `tests/mutants.json` to the edited text, with the same `why`; none of the entries now names a body this version edits, so the replay is expected to need no re-point.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
