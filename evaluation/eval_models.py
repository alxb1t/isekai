"""The evaluator's pinned models, and the check that they are not the generator's.

`evaluation/eval_models.json` decides which bytes the evaluator scores with. It is a
sibling of `config/models.json`, never a section of it: that file is what the graph
needs on the pod, and these run on the operator's machine.

A model both files carry would let the generator's own recognizer grade the
adapter trained to satisfy it, so `shared_with_the_graph` names any entry whose
destination or bytes the graph's manifest carries, and the entry point refuses on
it (D37). Refusal on a bad digest is
`isekai.boundary.provision.resolve`'s.
"""

from pathlib import Path

from isekai.boundary.provision import Manifest, load_manifest

EVAL_MANIFEST_PATH = Path(__file__).resolve().parent / "eval_models.json"

# The face detector and the encoder the cohort is ranked with (D37).
DETECTOR = "opencv_face/face_detection_yunet_2023mar.onnx"
ENCODER = "opencv_face/face_recognition_sface_2021dec.onnx"


def load_eval_manifest(path: Path = EVAL_MANIFEST_PATH) -> Manifest:
    """Read and parse the tracked eval manifest."""
    return load_manifest(path)


def shared_with_the_graph(evaluation: Manifest, graph: Manifest) -> list[str]:
    """Return each evaluator destination whose name or digest the graph carries.

    In the evaluator's order. The digest is compared too, because the generator's
    bytes under another name are still the generator's.
    """
    theirs = {
        key for entry in graph["entries"] for key in (entry["dest"], entry["sha256"])
    }
    return [
        entry["dest"]
        for entry in evaluation["entries"]
        if entry["dest"] in theirs or entry["sha256"] in theirs
    ]
