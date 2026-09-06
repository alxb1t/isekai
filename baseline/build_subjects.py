r"""Build the six baseline subjects for v0.12's metered session.

`probe/build_inputs.py`'s treatment, because one version does not silently
reverse a convention the previous one wrote down (design.md D15): the pixels are
**not committed**, the recipe is, and every output's SHA-256 is recorded so that
a re-run can be checked rather than trusted. Sources and destination are
arguments, so no path outside this repository is tracked.

    python baseline/build_subjects.py --sources <dir> --out <dir>

**Six subjects, each earning its slot adversarially** (design.md D11). They are
chosen to break the metrics, not to cover humanity:

  s1_control_blonde     832x1216  uniform blonde, frontal, mid-shot
  s2_control_brunette   832x1216  brunette close-up -- a second control that
                                  differs in hair colour, so the two controls
                                  are not one case counted twice
  s3_multitone_balayage 832x1216  dark roots into blonde ends, curly. The
                                  dominant-colour metric returns one mode, and
                                  this hair has two (design.md D5)
  s4_multitone_bob      832x1216  dark brown with caramel highlights, short bob.
                                  Multi-tone again, but stressing a different
                                  thing: the hair region is small, near the
                                  scorer's area floor rather than far above it
  s5_small_face         832x1216  full-length figure whose face is a few percent
                                  of the frame. Exercises the guard's refusal
                                  path and the absent-face field
  s6_landscape          832x554   the only landscape input this project has ever
                                  rendered on a GPU -- a gap v0.11's CHANGELOG
                                  names explicitly

**Four are labelled in phase 9 and two are not.** `s1`-`s4` are the labelled set:
40 judgements is 4 subjects x 10 within-subject pairs. `s5` and `s6` are the
refusal-path subjects and carry no labels, because a subject whose axes are
expected to refuse cannot calibrate anything.

`s6` is **derived by cropping**, exactly as v0.11's landscape probe input was.
The source set is entirely portrait, and what the landscape case is for is the
injector's short-side rounding on the *height* axis: 832x554 resolves to a
1536x1024 target, an aspect ratio this pipeline has never rendered. A crop
exercises that identically to a natively-framed wide shot, and it needs no
second generation pass. The crop origin keeps the face inside the band -- a
centred crop of a standing figure is a crop of its chest, and a subject with no
face in it measures the scale node while proving nothing about the rest of the
graph.
"""

import argparse
import hashlib
import shutil
import struct
import subprocess
import sys
from pathlib import Path

# The nine synthetic sources this selection was made from, and which of them each
# subject uses. Named here rather than passed in, because *which* photograph
# fills each adversarial slot is a decision about the baseline and belongs in the
# tracked recipe -- passing them as arguments would make the recipe reproducible
# and the baseline arbitrary.
#
# Deliberately unused from that set, and why, so the selection is reviewable:
#   00060  the same person and the same shoot as 00059 (identical lace robe).
#          Two slots filled by one subject would put one person's renders on
#          both sides of a "different subject" comparison.
#   00061  a third uniform-blonde frontal portrait. It is the same easy case
#          s1 already covers; a third control measures the same thing again.
#   00072  as 00061, closer in.
SUBJECTS: dict[str, str] = {
    "s1_control_blonde": "synthetic_portrait_00003_.png",
    "s2_control_brunette": "synthetic_portrait_00004_.png",
    "s3_multitone_balayage": "synthetic_portrait_00050_.png",
    "s4_multitone_bob": "synthetic_portrait_00014_.png",
    "s5_small_face": "synthetic_portrait_00059_.png",
}

# The landscape's source and its crop, as (width, height, x, y).
#
# 00033's face sits in the upper third, so the band is taken from y=150 rather
# than from the centre. 832x554 is v0.11's own landscape geometry, reused so the
# two versions' landscape inputs are the same shape and a difference between them
# is not a difference in the crop.
LANDSCAPE_SOURCE = "synthetic_portrait_00033_.png"
LANDSCAPE_CROP = (832, 554, 0, 150)

# ImageMagick stamps a PNG with the time it wrote it, so two runs of an identical
# recipe produce different bytes and a recorded SHA-256 verifies nothing.
# Excluding the date chunks and stripping profiles makes the recipe reproducible,
# which is the only reason to record a digest for a file that is not committed.
_DETERMINISTIC = ("-strip", "-define", "png:exclude-chunks=date,time")


def _convert(*args: str) -> None:
    """Run ImageMagick, failing loudly rather than leaving a half-built subject.

    The determinism flags are spliced in ahead of the output path, because
    ImageMagick reads its arguments as a pipeline and takes the last one as the
    destination.
    """
    if shutil.which("convert") is None:
        sys.exit("ImageMagick's `convert` is not on PATH; cannot build the subjects.")
    *pipeline, destination = args
    subprocess.run(["convert", *pipeline, *_DETERMINISTIC, destination], check=True)


def png_dimensions(data: bytes) -> tuple[int, int]:
    """Return the width and height a PNG's IHDR declares."""
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def main() -> int:
    """Build all six subjects and print the table `baseline/README.md` records."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sources", required=True, help="directory holding the synthetic portraits"
    )
    parser.add_argument("--out", required=True, help="destination directory")
    args = parser.parse_args()

    sources, out = Path(args.sources), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    built: list[Path] = []
    for name, filename in SUBJECTS.items():
        source = sources / filename
        if not source.exists():
            sys.exit(f"{source} does not exist; cannot build {name}")
        destination = out / f"{name}.png"
        # Re-encoded rather than copied, so every subject including the cropped
        # one leaves this script through the same encoder. A copy and a convert
        # produce different bytes for identical pixels, and a table mixing the
        # two would record that difference as if it meant something.
        _convert(str(source), str(destination))
        built.append(destination)

    landscape_source = sources / LANDSCAPE_SOURCE
    if not landscape_source.exists():
        sys.exit(f"{landscape_source} does not exist; cannot build the landscape")
    landscape = out / "s6_landscape.png"
    width, height, x, y = LANDSCAPE_CROP
    _convert(
        str(landscape_source),
        "-crop",
        f"{width}x{height}+{x}+{y}",
        "+repage",
        str(landscape),
    )
    built.append(landscape)

    print(f"{'subject':<24} {'stored':>11}  sha256")
    for path in built:
        data = path.read_bytes()
        stored = "x".join(str(v) for v in png_dimensions(data))
        print(f"{path.name:<24} {stored:>11}  {hashlib.sha256(data).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
