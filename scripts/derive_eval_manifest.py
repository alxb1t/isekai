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
  that path from ever quietly downloading a checkpoint.
"""

import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from typing import NamedTuple

from derive_manifest import Manifest, ManifestEntry, Source, published_digest

# Run as a script from the repository root, `scripts/` is on the path and the
# root is not -- the same hop `probe/build_inputs.py` makes, for the same reason.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from isekai.eval_models import SHARED_WITH_THE_GRAPH  # noqa: E402

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

# Above this, a file is not a config and something is wrong with the spec. Every
# non-LFS file pinned here is a few kilobytes; the cap exists so a mistake in the
# spec fails loudly instead of pulling a checkpoint through the hashing path.
BLOB_CAP_BYTES = 1 << 20

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


class Spec(NamedTuple):
    """A destination under the scorer's models tree, and the source that fills it.

    `lfs` says which of the two digest routes applies: an LFS object publishes its
    SHA-256 as its object id, and a plain git blob has to be fetched and hashed.
    It is stated in the spec rather than sniffed, so a file silently moving out of
    LFS is a loud failure rather than a silent switch to the slower path.
    """

    dest: str
    source: Source
    lfs: bool = True


SPECS: tuple[Spec, ...] = (
    Spec(
        "styleid/model.safetensors",
        Source("kwanY/styleid", STYLEID, "model.safetensors"),
    ),
    Spec(
        "styleid/config.json",
        Source("kwanY/styleid", STYLEID, "config.json"),
        lfs=False,
    ),
    Spec(
        "styleid/preprocessor_config.json",
        Source("kwanY/styleid", STYLEID, "preprocessor_config.json"),
        lfs=False,
    ),
    Spec(
        "segformer_b2_clothes/model.onnx",
        Source("mattmdjaga/segformer_b2_clothes", SEGFORMER, "onnx/model.onnx"),
    ),
    Spec(
        "segformer_b2_clothes/config.json",
        Source("mattmdjaga/segformer_b2_clothes", SEGFORMER, "onnx/config.json"),
        lfs=False,
    ),
    Spec(
        "segformer_b2_clothes/preprocessor_config.json",
        Source(
            "mattmdjaga/segformer_b2_clothes",
            SEGFORMER,
            "onnx/preprocessor_config.json",
        ),
        lfs=False,
    ),
    Spec(
        "anime_face_detection/model.onnx",
        Source(
            "deepghs/anime_face_detection", ANIMEFACE, "face_detect_v1.4_s/model.onnx"
        ),
    ),
    Spec(
        "anime_face_detection/labels.json",
        Source(
            "deepghs/anime_face_detection", ANIMEFACE, "face_detect_v1.4_s/labels.json"
        ),
        lfs=False,
    ),
    Spec(
        "anime_face_detection/threshold.json",
        Source(
            "deepghs/anime_face_detection",
            ANIMEFACE,
            "face_detect_v1.4_s/threshold.json",
        ),
        lfs=False,
    ),
)


def blob_digest(source: Source) -> tuple[str, int]:
    """Return the SHA-256 and size of a non-LFS file, by fetching and hashing it.

    Capped, so this path can never be the one a checkpoint arrives through. The
    revision in the URL is what makes the result a pin rather than a snapshot of
    whatever `main` served today.
    """
    request = urllib.request.Request(
        source.url(), headers={"User-Agent": "isekai-derive"}
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        body: bytes = response.read(BLOB_CAP_BYTES + 1)
    if len(body) > BLOB_CAP_BYTES:
        raise SystemExit(
            f"{source.url()}: larger than {BLOB_CAP_BYTES} bytes; "
            "a file this size should be pinned through its LFS object id"
        )
    return hashlib.sha256(body).hexdigest(), len(body)


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
    for spec in SPECS:
        sha256, size = (
            published_digest(spec.source) if spec.lfs else blob_digest(spec.source)
        )
        entries.append(
            {
                "dest": spec.dest,
                "sha256": sha256,
                "bytes": size,
                "sources": [spec.source.url()],
            }
        )
    return {
        "pinned": PINNED,
        "publishers": list(PUBLISHERS),
        "entries": entries,
    }


def main() -> None:
    """Derive the eval manifest and write it to `scripts/eval_models.json`."""
    manifest = derive()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    entries = manifest["entries"]
    total = sum(entry["bytes"] for entry in entries)
    print(
        f"wrote {MANIFEST_PATH.name}: {len(entries)} entries, {total / 2**30:.1f} GiB"
    )


if __name__ == "__main__":
    main()
