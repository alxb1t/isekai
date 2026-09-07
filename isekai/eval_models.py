"""The scorer's pinned artifacts, and the checks that keep them honest.

`scripts/eval_models.json` decides which bytes the evaluator scores with. It is a
**sibling** of `scripts/models.json`, never a section of it: that file is the
manifest of what the graph needs provisioned onto the pod, and these run locally
on the operator's machine (design.md D18).

This module owns two things, and deliberately nothing about any axis:

- **Refusal on a bad digest.** A score produced by an unverified model is a number
  from an unknown thing, so `resolve` hashes the bytes before it will hand back a
  path, and raises naming the artifact and both digests when they disagree.
- **The binding to the graph's own manifest.** The recognizer the scorer reports
  as a sanity channel must be the artifact the generator injects identity *with*
  (design.md D8). `shared_entries_that_differ` is what makes "the two manifests
  cannot drift apart unnoticed" a check rather than a comment.

Not imported by `convert.py`, and not by `isekai/evaluate.py`'s axes either --
this is the gate they pass through. The runtime stays stdlib-only regardless:
this module is `json`, `pathlib` and its sibling `isekai.provision`.
"""

import json
from pathlib import Path
from typing import Any

from isekai.provision import (
    MANIFEST_PATH,
    PINNED_SOURCE,
    WHITESPACE,
    Entry,
    Manifest,
    resolve_dest,
    verify,
)

EVAL_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "eval_models.json"
)

# The destinations `scripts/models.json` and `scripts/eval_models.json` both
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


class UnknownArtifact(Exception):
    """The scorer asked for a destination the eval manifest does not declare."""


class UnpinnedArtifact(Exception):
    """A manifest entry names a source that does not address an immutable revision."""


class EscapingDestination(Exception):
    """A manifest entry's destination does not land under the models root."""


def load_eval_manifest(path: Path = EVAL_MANIFEST_PATH) -> Manifest:
    """Read and parse the tracked eval manifest."""
    parsed: Any = json.loads(path.read_text())
    return parsed


def entry_for(manifest: Manifest, dest: str) -> Entry:
    """Return the entry declaring `dest`, or raise `UnknownArtifact`.

    The lookup the scorer goes through to reach any model at all, so a typo in an
    artifact name is a named failure rather than a `None` that surfaces three
    frames later as a missing file.
    """
    for entry in manifest["entries"]:
        if entry["dest"] == dest:
            return entry
    raise UnknownArtifact(f"{dest} is not declared in {EVAL_MANIFEST_PATH.name}")


def resolve(dest: str, models_dir: Path, manifest: Manifest | None = None) -> Path:
    """Return the verified path to one artifact, or raise rather than score from it.

    Three refusals, in the order a bad manifest would trip them: an artifact the
    manifest does not declare, an entry whose sources are not pinned revisions,
    and bytes on disk that do not hash to the pin. The last one raises
    `DigestMismatch` from `isekai.provision`, whose message names the file, the
    expected digest and the computed one -- all three, because a mismatch is read
    by a human deciding whether a pin is stale or a file has been swapped.

    The pin check runs even though this function fetches nothing. The manifest is
    the only reason to believe the bytes on disk are the right ones, and an entry
    pointing at `resolve/main/` says nothing about which bytes those were.

    A fourth refusal sits under the third: the join onto `models_dir` goes through
    `isekai.provision.resolve_dest`, which is the repository's **single** site for
    the containment rule (design.md D7). Every caller here passes a literal today,
    so this is not an exploit path being closed -- it is the invariant keeping one
    enforcement site rather than two, so a destination that climbs out of the
    models root is refused here exactly as it is on the pod.
    """
    manifest = load_eval_manifest() if manifest is None else manifest
    entry = entry_for(manifest, dest)
    for source in entry["sources"]:
        if WHITESPACE.search(source) or not PINNED_SOURCE.match(source):
            raise UnpinnedArtifact(
                f"{dest}: {source!r} is not a pinned revision, so the digest "
                "beside it verifies nothing in particular"
            )
    path = resolve_dest(entry, models_dir)
    if path is None:
        raise EscapingDestination(
            f"{dest!r} does not resolve to a path under {models_dir}, so it is "
            "refused rather than loaded from"
        )
    verify(path, entry["sha256"])
    return path


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
