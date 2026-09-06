#!/usr/bin/env python3
"""Score a run's renders against the photograph that produced them.

The second entry point, beside `convert.py`, and deliberately **not** a
subcommand of it: a subcommand would put the `[eval]` extra one misplaced import
away from breaking `convert.py`'s `dependencies = []`. The one-path rule is about
there being one way to *render*, and an evaluator is not a second way to render
(design.md D12).

    uv run --extra eval python evaluate.py outputs/final/<run>/ --photo <photo>

It reads the run's own `run.json` for provenance. The photograph is passed in
rather than read from the manifest, because the manifest records a **digest** and
never a path -- a digest of a face is not a face, and the pixels are not
committed. That digest is what makes the supplied photograph checkable rather
than trusted, and a mismatch refuses.

A manifest that predates v0.12 records no photograph, no graph and no base. In
that case this **reports what it lacks and refuses**, rather than guessing.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from isekai.evaluate import Refusal, score_render, table

# Where the scorer's own artifacts live, verified against
# `scripts/eval_models.json` before any of them is loaded. Local to the
# operator's machine: these are not what the pod provisions (design.md D18).
DEFAULT_MODELS_DIR = Path("models")


def parse_args() -> argparse.Namespace:
    """Parse the command line."""
    p = argparse.ArgumentParser(description="Score a run's renders against its photo.")
    p.add_argument("run_dir", type=Path, help="a run directory containing run.json")
    p.add_argument(
        "--photo",
        required=True,
        help="the photograph this run was rendered from; checked against the "
        "digest the manifest records",
    )
    p.add_argument(
        "--models",
        type=Path,
        default=DEFAULT_MODELS_DIR,
        help="where the pinned eval artifacts live",
    )
    p.add_argument(
        "--guard",
        choices=("iou", "centroid"),
        default="iou",
        help="which guard method is authoritative; both are always measured",
    )
    p.add_argument(
        "--subject",
        default=None,
        help="the subject this run rendered; defaults to the run directory's name",
    )
    return p.parse_args()


def missing_provenance(manifest: dict) -> list[str]:
    """Return what this manifest cannot tell the scorer, by name.

    A `run.json` written before v0.12 records `seed`, `variations`, `seeds` and
    `overrides` and nothing else, so it can confirm neither the photograph nor
    the base nor which render is which. The scorer names each thing it lacks and
    stops. **Guessing would be worse than refusing**: a comparison against the
    wrong photograph produces four plausible numbers and no way to notice one of
    them is about somebody else.
    """
    lacking: list[str] = []
    if "photo_sha256" not in manifest:
        lacking.append(
            "a digest of the photograph it was rendered from (no `photo_sha256`), "
            "so the photograph supplied cannot be confirmed to be the right one"
        )
    if "base" not in manifest:
        lacking.append("the base checkpoint (no `base`)")
    if "renders" not in manifest:
        lacking.append("the per-render provenance (no `renders`)")
    return lacking


def digest_of_file(path: str) -> str:
    """Return a file's SHA-256, read in chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    """Score one run directory, or say what it lacks."""
    args = parse_args()
    manifest_path = args.run_dir / "run.json"
    if not manifest_path.exists():
        sys.exit(f"{manifest_path} does not exist; this is not a run directory")
    manifest = json.loads(manifest_path.read_text())

    lacking = missing_provenance(manifest)
    if lacking:
        sys.exit(
            f"{manifest_path} predates v0.12's provenance record and cannot "
            "identify what it is: it does not record "
            + "; ".join(lacking)
            + ".\nRe-render it with this version. Refusing rather than guessing: "
            "a comparison against the wrong photograph produces four plausible "
            "numbers and no way to notice."
        )

    photo = args.photo
    actual = digest_of_file(photo)
    if actual != manifest["photo_sha256"]:
        sys.exit(
            f"{photo} hashes to {actual}, but this run was rendered from "
            f"{manifest['photo_sha256']}. These are different photographs."
        )

    subject = args.subject or args.run_dir.name
    base = manifest.get("base")

    # Imported here, not at module scope: this is the only import of the `[eval]`
    # extra in the tree, and `isekai.evaluate`'s rules are stdlib-only so they
    # stay testable in CI with the stack absent.
    from isekai.eval_backends import (
        AnimeFaceDetector,
        ArcFaceEncoder,
        DwPoseReader,
        MaskSampler,
        SegformerParser,
        StyleIdEncoder,
    )
    from isekai.evaluate import canvas_for

    canvas = canvas_for(photo)
    parser = SegformerParser(args.models)
    detector = AnimeFaceDetector(args.models, canvas)
    style = StyleIdEncoder(args.models, canvas)
    arcface = ArcFaceEncoder(args.models, canvas)
    sampler = MaskSampler(parser, photo, canvas)
    pose = DwPoseReader(args.models, canvas)

    reports = []
    for render in manifest["renders"]:
        render_path = args.run_dir / render["image"]
        try:
            reports.append(
                score_render(
                    photo,
                    str(render_path),
                    detector=detector,
                    style_encoder=style,
                    recognizer=arcface,
                    parser=parser,
                    sampler=sampler,
                    pose=pose,
                    subject=subject,
                    photo_base=base,
                    render_base=base,
                    image=render["image"],
                    guard_method=args.guard,
                )
            )
        except Refusal as refused:
            sys.exit(f"{render_path}: {refused}")

    # One machine-readable record per render, and one human-readable table for
    # the run. No average, no verdict, no percentage (design.md D1, D2).
    for report in reports:
        out = args.run_dir / f"{Path(report.image or report.render).stem}.eval.json"
        out.write_text(json.dumps(report.as_record(), indent=2) + "\n")

    rendered = table(
        reports, args.run_dir.name, base, manifest.get("image", "unrecorded")
    )
    (args.run_dir / "eval.txt").write_text(rendered)
    print(rendered)


if __name__ == "__main__":
    main()
