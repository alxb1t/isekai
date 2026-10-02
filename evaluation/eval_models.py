"""The evaluator's pinned models, and the check that they are not the generator's.

`evaluation/eval_models.json` decides which bytes the evaluator scores with. It is a
sibling of `config/models.json`, never a section of it: that file is what the graph
needs on the pod, and these run on the operator's machine.

A model both files carry would let the generator's own recognizer grade the
adapter trained to satisfy it, so `shared_with_the_graph` names any such
destination and the entry point refuses on it (D37). Refusal on a bad digest is
`isekai.boundary.provision.resolve`'s.
"""

import json
from pathlib import Path
from typing import Any

from isekai.boundary.provision import Manifest

EVAL_MANIFEST_PATH = Path(__file__).resolve().parent / "eval_models.json"

# The face detector and the encoder the cohort is ranked with (D37).
DETECTOR = "opencv_face/face_detection_yunet_2023mar.onnx"
ENCODER = "opencv_face/face_recognition_sface_2021dec.onnx"


def load_eval_manifest(path: Path = EVAL_MANIFEST_PATH) -> Manifest:
    """Read and parse the tracked eval manifest."""
    parsed: Any = json.loads(path.read_text())
    return parsed


def shared_with_the_graph(evaluation: Manifest, graph: Manifest) -> list[str]:
    """Return every destination both manifests carry, in the evaluator's order."""
    theirs = {entry["dest"] for entry in graph["entries"]}
    return [entry["dest"] for entry in evaluation["entries"] if entry["dest"] in theirs]
