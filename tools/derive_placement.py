"""Re-derive `config/placement.json` -- the models that propose a placement's pairs.

Run it from the repository root:

    uv run python -m tools.derive_placement

It rewrites `config/placement.json` in place; re-running leaves it byte-identical,
and `git diff --exit-code config/placement.json` is the check.

**The fifth manifest, and it answers which models read a photograph for the
placement screen.** The pose detector and estimator are single files; the
segmenter is a zip whose encoder and decoder are declared as its members, so
`isekai.boundary.unpack` unpacks them by those names and the archive's own
names decide nothing. The detector is the file the render manifest pins for the pod,
byte for byte, and the test of the real manifest holds the two equal.
"""

from isekai.boundary.unpack import PLACEMENT_MANIFEST_PATH as MANIFEST_PATH
from tools.manifest import (
    Manifest,
    ManifestEntry,
    Source,
    Spec,
    Wanted,
    entry_for,
    write,
)

# The date the revisions below were taken. Moving a revision means moving this.
PINNED = "2026-11-11"

# Each serves its files from its own repository, so neither needs an alternate.
PUBLISHERS = ("yzd-v", "vietanhdev")

POSE_REPOSITORY = "yzd-v/DWPose"
POSE_REVISION = "1a7144101628d69ee7a3768d1ee3a094070dc388"

SEGMENT_REPOSITORY = "vietanhdev/segment-anything-2.1-onnx-models"
SEGMENT_REVISION = "6a3ac868340a3196a349050a6efae22a5acc0330"
SEGMENT_ARCHIVE = "sam2.1_hiera_small_20260221.zip"

SPECS: tuple[Spec, ...] = (
    Spec(
        "dwpose/yolox_l.onnx",
        (Source(POSE_REPOSITORY, POSE_REVISION, "yolox_l.onnx"),),
    ),
    Spec(
        "dwpose/dw-ll_ucoco_384.onnx",
        (Source(POSE_REPOSITORY, POSE_REVISION, "dw-ll_ucoco_384.onnx"),),
    ),
    Spec(
        f"sam2/{SEGMENT_ARCHIVE}",
        (Source(SEGMENT_REPOSITORY, SEGMENT_REVISION, SEGMENT_ARCHIVE),),
        unpack=(
            Wanted("encoder.onnx", "sam2/encoder.onnx"),
            Wanted("decoder.onnx", "sam2/decoder.onnx"),
        ),
    ),
)


def derive() -> Manifest:
    """Build the manifest: each file by published digest, and the archive's members."""
    entries: list[ManifestEntry] = [entry_for(spec) for spec in SPECS]
    return {"pinned": PINNED, "publishers": list(PUBLISHERS), "entries": entries}


def main() -> None:
    """Derive the placement manifest and write it to `config/placement.json`."""
    write(derive(), MANIFEST_PATH)


if __name__ == "__main__":
    main()
