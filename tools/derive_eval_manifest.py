"""Re-derive `evaluation/eval_models.json` from the authored source spec below.

The sibling of `derive_manifest.py`, and deliberately a sibling rather than a
second half of it: `models.json` is the manifest of what **the graph** needs on
the pod, and this one is the manifest of what **the evaluator** loads on the
operator's own machine. Merging them would make one file answer two questions.

Same rule as its sibling: the manifest is *derived*, never transcribed. Run it
from the repository root:

    uv run python -m tools.derive_eval_manifest

It rewrites `evaluation/eval_models.json` in place, and re-running without editing
the spec must leave the file byte-identical --
`git diff --exit-code evaluation/eval_models.json` is the check.
"""

from evaluation.eval_models import DETECTOR, ENCODER
from evaluation.eval_models import EVAL_MANIFEST_PATH as MANIFEST_PATH
from tools.manifest import Manifest, Source, Spec, entry_for, write

# The date the revisions below were taken. Bumping a revision means bumping this.
PINNED = "2026-10-02"

# Hugging Face orgs that publish the artifact they serve. A primary source outside
# this set is a mirror and must declare an alternate.
PUBLISHERS = ("opencv",)

# The face detector and the encoder the cohort is ranked with, from OpenCV's own
# repositories: YuNet finds the face and its five landmarks, SFace embeds the
# aligned crop. Neither is a pin the generator carries (D37).
YUNET = "3cc26e7f1014a5ee5d74a42acee58bafc9d0a310"
SFACE = "3d7082438a6e4551e840c9b2bb60b71e8da4b524"

SPECS: tuple[Spec, ...] = (
    Spec(
        DETECTOR,
        (
            Source(
                "opencv/face_detection_yunet",
                YUNET,
                "face_detection_yunet_2023mar.onnx",
            ),
        ),
    ),
    Spec(
        ENCODER,
        (
            Source(
                "opencv/face_recognition_sface",
                SFACE,
                "face_recognition_sface_2021dec.onnx",
            ),
        ),
    ),
)


def derive() -> Manifest:
    """Build the whole eval manifest from the specs above."""
    return {
        "pinned": PINNED,
        "publishers": list(PUBLISHERS),
        "entries": [entry_for(spec) for spec in SPECS],
    }


def main() -> None:
    """Derive the eval manifest and write it to `evaluation/eval_models.json`."""
    write(derive(), MANIFEST_PATH)


if __name__ == "__main__":
    main()
