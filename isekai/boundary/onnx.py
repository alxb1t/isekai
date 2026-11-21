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
    e.g. cpu_session(ort, Path("m.onnx")) -> ort.InferenceSession("m.onnx", providers=…)
    """
    silence_onnxruntime()
    providers = ["CPUExecutionProvider"]
    if options is None:
        return runtime.InferenceSession(str(model), providers=providers)
    return runtime.InferenceSession(str(model), options, providers=providers)
