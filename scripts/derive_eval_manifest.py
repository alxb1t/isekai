#!/usr/bin/env python3
"""Re-derive `scripts/eval_models.json` from the authored source spec below.

The sibling of `derive_manifest.py`, and deliberately a sibling rather than a
second half of it: `models.json` is the manifest of what **the graph** needs on
the pod, and this one is the manifest of what **the scorer** loads on the
operator's own machine (design.md D18). Merging them would make one file answer
two questions.

Same rule as its sibling: the manifest is *derived*, never transcribed. Run it
from the repository root:

    uv run python scripts/derive_eval_manifest.py

It rewrites `scripts/eval_models.json` in place, and re-running without editing
the spec must leave the file byte-identical --
`git diff --exit-code scripts/eval_models.json` is the check.

Two things it does that its sibling does not, each because the scorer's stack is
shaped differently from the graph's:

- **Three entries are copied out of `scripts/models.json`, byte for byte.** The
  scorer's ArcFace must be the artifact the generator injects identity *with*, or
  design.md D8's claim about self-grading describes two different models. Copying
  rather than re-deriving is what makes the two files unable to drift apart:
  there is one derivation, and this one reads its output.
- **A small non-LFS file is hashed by fetching it.** Hugging Face publishes a
  SHA-256 only for LFS objects, and `config.json` / `preprocessor_config.json` /
  `labels.json` are plain git blobs -- but a scorer that loads a model's
  architecture and its input normalisation from unpinned bytes is pinning the
  weights and not the model. The URL already addresses an immutable revision, so
  the bytes are fixed; this records what they are. The size cap is what stops
  that path from ever quietly downloading a checkpoint. That strategy is no
  longer this file's: it lives in `scripts/manifest.py` alongside the LFS one,
  where every deriver reaches for whichever an artifact needs (design.md D10).
"""

import json
import sys
from pathlib import Path

from manifest import Manifest, ManifestEntry, Source, Spec, entry_for, write

# Run as a script from the repository root, `scripts/` is on the path and the
# root is not -- the same hop `probe/build_inputs.py` makes, for the same reason.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from isekai.evaluation.eval_models import SHARED_WITH_THE_GRAPH  # noqa: E402

MANIFEST_PATH = Path(__file__).resolve().parent / "eval_models.json"
GRAPH_MANIFEST_PATH = Path(__file__).resolve().parent / "models.json"

# The date the revisions below were taken. Bumping a revision means bumping this.
PINNED = "2026-09-06"

# Hugging Face orgs that publish the artifact they serve. A primary source outside
# this set is a mirror and must declare an alternate -- which is the rule the three
# copied entries are already carried under in `models.json`.
PUBLISHERS = (
    "kwanY",
    "mattmdjaga",
    "deepghs",
)

# StyleID, the primary face axis: a CLIP image encoder with LoRA adapters merged.
# `kwanyun/StyleID`, SIGGRAPH 2026. Non-commercial research use -- a recorded
# deviation, and the reason it may not be the sole carrier of the face axis
# (design.md D16, and `scripts/eval_licences.md`).
STYLEID = "1967c354f339a636e5b3e16ecab3d0075aa27ab1"

# The human parser the region masks come from (design.md D7). NVIDIA Source Code
# License, inherited from SegFormer -- non-commercial, a recorded deviation. The
# `onnx/` export is pinned rather than the safetensors: the scorer runs it through
# `onnxruntime`, which is the same runtime the detector below needs.
SEGFORMER = "584abc1e1d260e23c0fc627c5217a09b2b461046"

# The anime-face detector the guard's box-IoU method needs (design.md D9).
#
# NOT `Fuyucchi/yolov8_animeface`, which design.md D19 names. That repository
# publishes no ONNX at all -- its HF tree and its single GitHub release both carry
# only `yolov8x6_animeface.pt` under `library_name: ultralytics` -- so D19's stated
# mechanism, "loaded through `onnxruntime`, and `ultralytics` is never imported",
# has no artifact to point at. Resolved 2026-09-06 in favour of this one, which is
# an ONNX export under MIT and therefore dissolves D19's AGPL problem rather than
# routing around it. The `_s` variant is the larger of the two the repo ships.
ANIMEFACE = "784dc4c0bb692351ddcdbe6131a050b17d3025d5"

# The destinations copied out of `scripts/models.json` byte for byte, in the order
# they are emitted. `glintr100` is the load-bearing one (design.md D8); the two
# DWPose artifacts are convenience, and are copied for the same reason anyway.
#
# Imported rather than restated. The whole purpose of this list is that the two
# manifests cannot drift apart, so keeping two copies of the list of things that
# must not drift would be the same failure one level up -- and the reader that
# enforces it at load time is the one that should own it.


SPECS: tuple[Spec, ...] = (
    Spec(
        "styleid/model.safetensors",
        (Source("kwanY/styleid", STYLEID, "model.safetensors"),),
    ),
    Spec(
        "styleid/config.json",
        (Source("kwanY/styleid", STYLEID, "config.json"),),
        lfs=False,
    ),
    Spec(
        "styleid/preprocessor_config.json",
        (Source("kwanY/styleid", STYLEID, "preprocessor_config.json"),),
        lfs=False,
    ),
    Spec(
        "segformer_b2_clothes/model.onnx",
        (Source("mattmdjaga/segformer_b2_clothes", SEGFORMER, "onnx/model.onnx"),),
    ),
    Spec(
        "segformer_b2_clothes/config.json",
        (Source("mattmdjaga/segformer_b2_clothes", SEGFORMER, "onnx/config.json"),),
        lfs=False,
    ),
    Spec(
        "segformer_b2_clothes/preprocessor_config.json",
        (
            Source(
                "mattmdjaga/segformer_b2_clothes",
                SEGFORMER,
                "onnx/preprocessor_config.json",
            ),
        ),
        lfs=False,
    ),
    Spec(
        "anime_face_detection/model.onnx",
        (
            Source(
                "deepghs/anime_face_detection",
                ANIMEFACE,
                "face_detect_v1.4_s/model.onnx",
            ),
        ),
    ),
    Spec(
        "anime_face_detection/labels.json",
        (
            Source(
                "deepghs/anime_face_detection",
                ANIMEFACE,
                "face_detect_v1.4_s/labels.json",
            ),
        ),
        lfs=False,
    ),
    Spec(
        "anime_face_detection/threshold.json",
        (
            Source(
                "deepghs/anime_face_detection",
                ANIMEFACE,
                "face_detect_v1.4_s/threshold.json",
            ),
        ),
        lfs=False,
    ),
)


def copied_entries() -> list[ManifestEntry]:
    """Return the entries `scripts/models.json` already carries, byte for byte.

    Read rather than re-derived, so the two manifests have one derivation between
    them and the recognizer the scorer loads cannot become a different build of
    the one the generator injects with (design.md D8, D18).
    """
    graph: Manifest = json.loads(GRAPH_MANIFEST_PATH.read_text())
    by_dest = {entry["dest"]: entry for entry in graph["entries"]}
    missing = [dest for dest in SHARED_WITH_THE_GRAPH if dest not in by_dest]
    if missing:
        raise SystemExit(
            f"{GRAPH_MANIFEST_PATH.name} no longer carries: {', '.join(missing)}"
        )
    return [by_dest[dest] for dest in SHARED_WITH_THE_GRAPH]


def derive() -> Manifest:
    """Build the whole eval manifest: the shared entries, then the scorer's own."""
    entries: list[ManifestEntry] = list(copied_entries())
    entries.extend(entry_for(spec) for spec in SPECS)
    return {
        "pinned": PINNED,
        "publishers": list(PUBLISHERS),
        "entries": entries,
    }


def main() -> None:
    """Derive the eval manifest and write it to `scripts/eval_models.json`."""
    write(derive(), MANIFEST_PATH)


if __name__ == "__main__":
    main()
