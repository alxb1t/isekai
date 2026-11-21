# The ONNX opener — design

A session is made by `cpu_session` and the telemetry switch is `silence_onnxruntime`, both in `isekai/boundary/onnx.py`, each caller keeping its own import of the runtime and its own text for an absent wheel. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

An ONNX session is opened by `wd14`, `pose`, `sam2` and `face` today, each with its own seam for the runtime:

```
wd14.py   OnnxSession.__init__   silence → _require("onnxruntime") → InferenceSession(path, providers=…)
pose.py   OnnxPoseFinder         runtime given, or silence → import_module → two InferenceSession(path, providers=…)
sam2.py   OnnxSegmenter          the same, for the encoder and the decoder
face.py   _session               _import("onnxruntime") → SessionOptions → InferenceSession(path, options, providers=…)
```

`silence_onnxruntime` is `wd14.py`'s, which `pose.py`, `sam2.py` and `face.py` import. The switch is read when `onnxruntime` loads, so it is set before the import, never after. Tests pin each seam: `wd14._require` and `face._import` are patched to watch the switch at the import, and `open_pose` and `open_segmenter` take a recording runtime.

`tests/test_wd14.py` holds a scan, `session_openers`, that every module calling a name `InferenceSession` also calls `silence_onnxruntime`. After this version `onnx.py` is the only such module.

```
before:  four modules ─ InferenceSession(path, providers=["CPUExecutionProvider"])   (spelt at each)
after:   four modules ─ cpu_session(runtime, path[, options]) ─ InferenceSession     (spelt once)
```

## Goals / Non-Goals

- Goal: one function spells the CPU provider and calls `InferenceSession`, and one function sets the switch.
- Goal: every printed byte and every call a runtime double records is equal, key for key and argument for argument.
- Goal: `onnx.py` imports the standard library alone, so the `-S` guard and the layer guards hold.
- Non-goal: one import of the runtime, or one text for an absent wheel.
- Non-goal: the image maths of `pose.py` and `sam2.py`, and any image-frozen file.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `isekai/boundary/onnx.py` holds `silence_onnxruntime()` and `cpu_session(runtime, model, options=None)`, imports the standard library alone and nothing of `isekai`, and opens no runtime | `wd14.py` is on `python -m isekai`'s import graph, so the module is too ([D20](../../../docs/decisions.md#d20--the-entry-point-loads-no-third-party-package)); a runtime opened here would take each module's seam and its text | a loader passed to the opener: it moves the order of silence and import into the opener and changes when `pose.py` and `sam2.py` silence a runtime a test hands in |
| [D2](#d2) | `cpu_session` calls `silence_onnxruntime()` first, and each caller still calls it before its own import | the scan holds that a module calling `InferenceSession` also calls `silence_onnxruntime`, and no assertion may change; the switch is read at load, so the caller's call is the one that matters | editing the scan: an existing test's assertion changes; naming the call by `getattr`: it hides the call from the scan it exists for |
| [D3](#d3) | `OnnxSession`, `OnnxPoseFinder`, `OnnxSegmenter` and `_session` of `face.py` call `cpu_session`; each keeps its import of the runtime and its text for an absent wheel | tests pin each seam and what each prints; one text would change a printed byte | one shared import with one text: it changes what is printed and the seams tests patch |
| [D4](#d4) | `wd14.py` imports `silence_onnxruntime` from `onnx.py` and keeps it in `__all__`; `pose.py`, `sam2.py` and `face.py` import it from `onnx.py` | the old name still resolves for a reader of `wd14`, and `pose`, `sam2` and `face` need no tagger to set a switch | deleting the name from `wd14.py`: a reader of the old home breaks for no gain |
| [D5](#d5) | Cases for the opener are written first, in `tests/test_wd14.py`, and a mutation run over the lines of each site passes before the switch and over the opener after | byte-equal is the version's promise, and a recording runtime already holds each call | a new test file: the cases share `TELEMETRY_SWITCH` and the scan with the cases beside them |
| [D6](#d6) | The boundary README gains `onnx.py`'s row and its derived row, and its note on the switch names `onnx.py`; `docs/modules.md` names `onnx` where it named `wd14`'s switch; no decision is added and no ratchet row goes | the documents a version makes false are amended in its diff; the opener sets a rule no decision of the base states beyond [D20](../../../docs/decisions.md#d20--the-entry-point-loads-no-third-party-package) | a new decision: the opener adds no rule a reader could break |

### D1

```python
"""The one place an ONNX session is made, and the switch set before the runtime loads.

Imports the standard library alone, and is on `python -m isekai`'s import graph (D20).
"""

import os
from pathlib import Path
from typing import Any


def silence_onnxruntime() -> None:
    """Turn onnxruntime's telemetry off; call before it is first imported.

    Loading it opens an HTTPS connection to Microsoft, and the client's teardown
    at exit aborted `tag` with 134. The switch is read at load, so the
    `disable_telemetry_events()` API is too late for both.
    """
    os.environ["ORT_DISABLE_TELEMETRY"] = "1"


def cpu_session(
    runtime: Any,  # noqa: ANN401 -- onnxruntime, a wheel this module never imports
    model: Path,
    options: Any = None,  # noqa: ANN401 -- a `SessionOptions` of the same runtime
) -> Any:  # noqa: ANN401 -- the runtime's own session
    """Return `runtime`'s session over `model` on the CPU provider alone.

    `options` is a `SessionOptions` of the same runtime, handed before the providers.
    e.g. cpu_session(ort, Path("m.onnx")) -> ort.InferenceSession("m.onnx", providers=[...])
    """
    silence_onnxruntime()
    providers = ["CPUExecutionProvider"]
    if options is None:
        return runtime.InferenceSession(str(model), providers=providers)
    return runtime.InferenceSession(str(model), options, providers=providers)
```

The docstring of `silence_onnxruntime` is the one `wd14.py` has. Each call passes `str(model)` first, `providers` by keyword, and `options`, when given, positionally between them, as the sites did.

### D2

```
caller:   silence_onnxruntime()  →  import the runtime  →  cpu_session(runtime, path)
                                                              └─ silence_onnxruntime()   (sets the same value)
```

The caller's call is the one the switch needs. The call inside `cpu_session` writes the same value and makes `onnx.py` pass the scan of `tests/test_wd14.py`. It also sets the switch where `pose.py` and `sam2.py` are handed a recording runtime, which they did not before: the variable is read only when `onnxruntime` loads, and the tests that load it set it first.

### D3

| site | before | after |
|---|---|---|
| `OnnxSession.__init__` of `wd14.py` | `onnxruntime.InferenceSession(str(model), providers=["CPUExecutionProvider"])` | `cpu_session(onnxruntime, model)`, after `silence_onnxruntime()` and `_require("onnxruntime")` as they are |
| `OnnxPoseFinder.__init__` of `pose.py` | a `providers` local and two `runtime.InferenceSession(str(…), providers=providers)` | `cpu_session(runtime, detector)` and `cpu_session(runtime, estimator)` |
| `OnnxSegmenter.__init__` of `sam2.py` | the same, for the encoder and the decoder | `cpu_session(runtime, encoder)` and `cpu_session(runtime, decoder)` |
| `_session` of `evaluation/face.py` | `onnxruntime.InferenceSession(str(model), options, providers=["CPUExecutionProvider"])` | `cpu_session(onnxruntime, model, options)`, `options` built as it is, `log_severity_level` 3 |

`open_pose` and `open_segmenter` stay as they are but for the import of `silence_onnxruntime`: they set the switch only when no runtime is handed in, and import `onnxruntime` under their own text. `Detector` and `Encoder` of `face.py` still call `silence_onnxruntime()` before `_session`.

### D4

`wd14.py` replaces its definition of `silence_onnxruntime` with `from isekai.boundary.onnx import cpu_session, silence_onnxruntime`, and `import os` goes, since nothing else reads it. `__all__` keeps `"silence_onnxruntime"`. `pose.py`, `sam2.py` and `face.py` import it from `isekai.boundary.onnx` in place of `isekai.boundary.wd14`, so *Imported by* of `wd14.py` loses `pose.py`, `sam2.py` and `evaluation/face.py`.

### D5

The cases go in `tests/test_wd14.py` beside the telemetry cases, each with `spec_exempt("structural: …")`, and run against a recording runtime that holds its calls' arguments and keywords:

| case | holds |
|---|---|
| `test_the_opener_opens_the_model_on_the_cpu_provider_alone` | `cpu_session(runtime, Path("a/m.onnx"))` calls `InferenceSession("a/m.onnx", providers=["CPUExecutionProvider"])` |
| `test_the_opener_hands_the_options_before_the_providers` | with `options`, the call is `("a/m.onnx", options)` and `providers=[…]` |
| `test_the_opener_returns_the_session_the_runtime_made` | the return value is the runtime's own |
| `test_the_opener_switches_telemetry_off` | with the variable unset, `cpu_session` leaves it `"1"` |
| `test_the_opener_silence_sets_the_switch` | `silence_onnxruntime()` leaves it `"1"` |

The mutation tool mutates a line of a function's body, so the runs are one range each, before the switch over the sites and after it over the opener:

```
uv run python -m tools.mutate evaluation/face.py:<first>-<last> --tests tests/test_wd14.py tests/test_face.py tests/test_evaluation_cli.py
uv run python -m tools.mutate isekai/boundary/pose.py:<first>-<last> --tests tests/test_pose.py tests/test_propose.py
```

A survivor before the switch is killed by a case in the file of its site: `tests/test_wd14_runtime.py` for `wd14.py`, `tests/test_pose.py`, `tests/test_sam2.py`, and `tests/test_wd14.py` for `face.py`. A survivor no case can kill is named equivalent, with its reason, in the commit body. The replay of the standing mutants stops on a find an edit moved, and the version re-points it.

### D6

The row of `onnx.py` in the boundary README sits after `ollama.py`, and its *Imported by* row is `onnx.py` · `pose.py`, `sam2.py`, `wd14.py` · `evaluation/face.py`, which `tools.derive_imported_by` writes with the others. `docs/modules.md` reads "importing `provision`, `unpack`, `onnx` and `foundation/refusal.py`". The README's note that `silence_onnxruntime()` sets the switch "for both sessions" reads "for every session", and names `onnx.py`.

## Tests

The version adds cases and deletes and changes none. Counts, each from its command:

| layer | added | command |
|---|---|---|
| unit | the opener's cases, and a case for each survivor the mutation runs find | `git grep -c -e 'def test_the_opener_' -- tests/test_wd14.py` prints nothing before, and after `tests/test_wd14.py:5` |
| end-to-end | none | no browser test is touched |

| test | reason |
|---|---|
| the `test_the_opener_…` cases of D5 | the opener's contract on a recording runtime; `T1`, unit, `structural:` exempt |
| `test_every_module_that_opens_an_onnx_session_silences_telemetry` and its twin | stay as they are and now read `onnx.py` alone; `D2` keeps them green |

No test is deleted or merged, so the `I16` table is empty. The tests that read the sessions, `tests/test_wd14_runtime.py`, `tests/test_pose.py`, `tests/test_sam2.py`, `tests/test_propose.py` and `tests/test_evaluation_cli.py`, hold the calls and do not change. The standing mutants of `tests/mutants.json` are replayed.

## Dependencies

None.

## Risks / Trade-offs

| risk | answer |
|---|---|
| a call a runtime double records differs by a keyword or a position | `cpu_session` passes `providers` by keyword and `options` positionally as the sites did; the doubles of `tests/test_wd14_runtime.py`, `tests/test_pose.py` and `tests/test_sam2.py` hold them |
| the switch is set after the runtime loads | each caller keeps its call before its import, and `test_every_onnx_session_switches_telemetry_off_before_the_import` holds it for `wd14.py` and `face.py` |
| `cpu_session` writes the variable where a test hands in a runtime | it writes the value the real path writes, and nothing reads it until `onnxruntime` loads |
| `onnx.py` puts a wheel on the entry point's graph | it imports the standard library alone, and the `-S` guard of `tests/test_pipeline_cli.py` holds it |
| the derived table is stale after the imports move | the first phase adds the row and the second runs the derivation, so `tests/test_docs.py` is green at each phase end |

## Verdict

Ready to build, each phase green alone: the opener with its cases, the callers, and the documents.
