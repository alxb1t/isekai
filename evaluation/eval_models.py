"""The scorer's pinned artifacts, and the checks that keep them honest.

`evaluation/eval_models.json` decides which bytes the evaluator scores with. It is a
**sibling** of `config/models.json`, never a section of it: that file is the
manifest of what the graph needs provisioned onto the pod, and these run locally
on the operator's machine (design.md D18).

This module owns the eval manifest and its binding to the graph's own manifest,
and deliberately nothing about any axis. The recognizer the scorer reports as a
sanity channel must be the artifact the generator injects identity *with*
(design.md D8). `shared_entries_that_differ` is what makes "the two manifests
cannot drift apart unnoticed" a check rather than a comment.

**Refusal on a bad digest is `isekai.boundary.provision.resolve`'s**, which the
scorer passes this manifest to: a score produced by an unverified model is a
number from an unknown thing.

Not on `python -m isekai`'s import graph, and not on the scorer's axes either.
It would reach no wheel even if it were: this module is `json`, `pathlib` and
`isekai.boundary.provision`.
"""

import json
from pathlib import Path
from typing import Any

from isekai.boundary.provision import MANIFEST_PATH, Manifest

EVAL_MANIFEST_PATH = Path(__file__).resolve().parent / "eval_models.json"

# The destinations `config/models.json` and `evaluation/eval_models.json` both
# carry, which must be byte-identical in the two files. `glintr100` is the
# load-bearing one: design.md D8's claim is about the generator's *own*
# recognizer, and a different build of ArcFace would make that claim describe two
# different models. The two DWPose artifacts ride along for the same reason.
SHARED_WITH_THE_GRAPH = (
    "insightface/models/antelopev2/glintr100.onnx",
    "annotator_ckpts/yzd-v/DWPose/yolox_l.onnx",
    "annotator_ckpts/hr16/DWPose-TorchScript-BatchSize5/dw-ll_ucoco_384_bs5.torchscript.pt",
)

# The one the report marks as falsifying-only (design.md D8).
RECOGNIZER = "insightface/models/antelopev2/glintr100.onnx"


def load_eval_manifest(path: Path = EVAL_MANIFEST_PATH) -> Manifest:
    """Read and parse the tracked eval manifest."""
    parsed: Any = json.loads(path.read_text())
    return parsed


def shared_entries_that_differ(
    eval_manifest: Manifest | None = None,
    graph_manifest_path: Path = MANIFEST_PATH,
) -> list[str]:
    """Return the shared destinations the two manifests do not agree on, exactly.

    Whole-entry equality rather than digest equality: a digest that matched while
    the sources had diverged would mean the two files describe the same bytes
    arriving from different places, which is the drift the copy exists to prevent.
    A destination missing from either file counts as a difference.
    """
    eval_manifest = load_eval_manifest() if eval_manifest is None else eval_manifest
    graph: Manifest = json.loads(graph_manifest_path.read_text())
    ours = {entry["dest"]: entry for entry in eval_manifest["entries"]}
    theirs = {entry["dest"]: entry for entry in graph["entries"]}
    return [
        dest
        for dest in SHARED_WITH_THE_GRAPH
        if dest not in ours or dest not in theirs or ours[dest] != theirs[dest]
    ]
