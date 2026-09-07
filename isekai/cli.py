"""Argument parsing and the `main` entry point: flags in, a configured `run` out."""

import argparse
import json
import os
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from isekai.comfy_client import ComfyClient
from isekai.comfy_types import Overrides
from isekai.pipeline import run
from isekai.workflow import PIPELINE_PATH

# `-o` named a file up to v0.7. Accepting the old form would silently create a
# directory called `out.png` full of images, so a value that looks like an image
# is refused at parse time instead.
_IMAGE_SUFFIXES = frozenset(
    {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
)

_VARIATIONS = 5
_MAX_VARIATIONS = 25

# The ceiling on the two provenance strings recorded verbatim into `run.json`.
# A registry reference and a git commit are both short; 256 is generous for
# either, and short enough that nothing can bury a report under one.
_MAX_PROVENANCE = 256


def _provenance(flag: str) -> Callable[[str], str]:
    """Build an argparse type for a value recorded verbatim and printed verbatim.

    `--pod-image` and `--comfy-commit` are the only two values that travel from
    the operator's shell (or from `$RUNPOD_IMAGE`) into `run.json` and back out
    onto the terminal and into `eval.txt` untouched. `json.dumps` escapes the
    manifest correctly, so the exposure is the *report*: a newline injects a line
    indistinguishable from a real header, and a control sequence reaches stdout
    unescaped. Both are refused here, at the one place either value can arrive,
    rather than escaped at each of the several places they are read back.

    Printable ASCII, and bounded. Neither a registry reference nor a commit has
    any business outside that alphabet, so a value that leaves it is a mistake
    far more often than it is a tag. `argparse` applies this to a **string**
    default too, so `$RUNPOD_IMAGE` is bounded on the same line the flag is.
    """

    def provenance(value: str) -> str:
        if len(value) > _MAX_PROVENANCE:
            raise argparse.ArgumentTypeError(
                f"{flag} must be at most {_MAX_PROVENANCE} characters, got {len(value)}"
            )
        if any(not (" " <= character <= "~") for character in value):
            raise argparse.ArgumentTypeError(
                f"{flag} must be printable ASCII: it is recorded verbatim and "
                "printed verbatim, and a control character there rewrites a report"
            )
        return value

    return provenance


def _bounded[T: (int, float)](
    parse: Callable[[str], T], lo: T, hi: T
) -> Callable[[str], T]:
    """Build an argparse type that parses a value and rejects one outside [lo, hi].

    One factory for every ranged dial and for --variations, so the rejection
    wording -- which the suite pins -- has a single spelling.
    """

    def bounded(value: str) -> T:
        v = parse(value)
        if not (lo <= v <= hi):
            raise argparse.ArgumentTypeError(f"must be in [{lo}, {hi}], got {v}")
        return v

    return bounded


def _output_directory(value: str) -> Path:
    """Parse -o as a directory, refusing a value that names an image file."""
    path = Path(value)
    if path.suffix.lower() in _IMAGE_SUFFIXES:
        raise argparse.ArgumentTypeError(
            f"-o now names a directory, not an image file; {value!r} looks like a "
            f"file. A run writes its images into <dir>/<UTC instant>/."
        )
    return path


def parse_args() -> argparse.Namespace:
    """Parse the command line, rejecting out-of-range and unusable flag values."""
    p = argparse.ArgumentParser(description="Photo -> anime via ComfyUI.")
    p.add_argument("input", help="input photo (jpg/png)")
    p.add_argument(
        "-o",
        "--output",
        type=_output_directory,
        default=Path("./outputs"),
        help="output directory; each run writes into <dir>/<UTC instant>/",
    )
    p.add_argument(
        "--server",
        default="http://127.0.0.1:8188",
        help="ComfyUI base URL (reached via the SSH tunnel)",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="RNG seed for reproducible variation (random if unset)",
    )
    p.add_argument(
        "--variations",
        type=_bounded(int, 1, _MAX_VARIATIONS),
        default=_VARIATIONS,
        help=f"number of varied outputs to generate [1, {_MAX_VARIATIONS}]",
    )
    p.add_argument(
        "--denoise",
        type=_bounded(float, 0.0, 1.0),
        default=None,
        help="denoise base value [0, 1] (jitter window for --variations)",
    )
    p.add_argument(
        "--cfg",
        type=_bounded(float, 0.0, 30.0),
        default=None,
        help="CFG scale base value [0, 30]",
    )
    p.add_argument(
        "--ip-weight",
        type=_bounded(float, 0.0, 1.0),
        default=None,
        help="InstantID ip_weight base value [0, 1]",
    )
    p.add_argument(
        "--cn-strength",
        type=_bounded(float, 0.0, 1.0),
        default=None,
        help="InstantID cn_strength base value [0, 1] (the keypoint route)",
    )
    p.add_argument(
        "--pod-image",
        type=_provenance("--pod-image"),
        default=os.environ.get("RUNPOD_IMAGE"),
        help="the container image the ComfyUI being driven is running, recorded "
        "verbatim into the run's manifest; defaults to $RUNPOD_IMAGE, the same "
        "variable infra/up.sh boots the pod from. Unset means the run records "
        "that it does not know, which is not the same as knowing it was :latest",
    )
    p.add_argument(
        "--comfy-commit",
        type=_provenance("--comfy-commit"),
        default=None,
        help="the ComfyUI commit the server being driven is running -- what "
        "`git -C /opt/ComfyUI rev-parse HEAD` reports on the pod -- recorded "
        "verbatim into the run's manifest. No environment default: nothing in "
        "infra/ or .env.example exports it, and inventing a variable for it "
        "would be a second place to keep in step. Unset records that the run "
        "does not know",
    )
    p.add_argument(
        "--fixed-dials",
        action="store_true",
        help="render the graph's committed dials, jittering nothing; each "
        "variation still draws its own sampler seed",
    )

    return p.parse_args()


def _run_directory(output_dir: Path) -> Path:
    """Resolve this run's own directory: <output-dir>/<UTC instant>/.

    Compact basic ISO -- colons are legal on APFS but Finder renders them as `/`
    and they are illegal on Windows checkouts. Resolved HERE rather than inside
    `run`, so `run` draws no clock and stays a pure function of its arguments
    (design.md D4).
    """
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return output_dir / stamp


def main() -> None:
    """Run one conversion: parse the flags, resolve the run directory, drive it."""
    args = parse_args()
    workflow = json.loads(PIPELINE_PATH.read_text())
    client = ComfyClient(args.server)

    overrides: Overrides = {}
    if args.denoise is not None:
        overrides["denoise"] = args.denoise
    if args.cfg is not None:
        overrides["cfg"] = args.cfg
    if args.ip_weight is not None:
        overrides["ip_weight"] = args.ip_weight
    if args.cn_strength is not None:
        overrides["cn_strength"] = args.cn_strength

    run(
        client,
        workflow,
        args.input,
        _run_directory(args.output),
        seed=args.seed,
        variations=args.variations,
        overrides=overrides or None,
        fixed_dials=args.fixed_dials,
        pod_image=args.pod_image,
        comfy_commit=args.comfy_commit,
    )
