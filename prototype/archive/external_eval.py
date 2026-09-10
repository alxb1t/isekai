#!/usr/bin/env python3
"""PROTOTYPE — score a render this pipeline did not produce.

Not a version. Not spec-bound. Written to answer one question before a change is
cut: **can the evaluator compare our output against a third-party tool's at all?**

`evaluate.py` takes a run directory and reads `run.json` for provenance. An
external render has no `run.json`, and fabricating one would put a false `base`
and meaningless `dials` into a record whose whole purpose is to say where a
number came from. So this wires the same backends by hand and passes the
external render's provenance as what it is: **unknown**.

    uv run --extra eval python prototype/external_eval.py \
        --photo inputs/baseline/s1_control_blonde.png \
        --render ~/Downloads/fotor/s1...jpg \
        --tool "fotor:ai-art-effects" --subject s1_control_blonde

Two deliberate choices, both arguable, both stated:

- **`render_base` is `None`, not a made-up string.** That makes
  `refuse_embedding_axes_across_bases` fire, which is the designed behaviour for
  a render whose generator is unknown. The refusal is the finding, not a bug to
  route around.
- **`--force-embeddings` runs the same comparison with the refusal suppressed**,
  so the numbers can be *seen* while remaining unusable as measurements. Every
  such run is tagged `EXPLORATORY` in the output. It exists because "the axis
  refused" and "the axis refused and would have said X" are different amounts of
  information at prototype time.

The render is resampled to the canvas the injector computes from the photograph,
with Lanczos, non-uniformly if the aspect differs -- which is exactly what
`ImageScale` with `crop: disabled` does to our own inputs.
"""

import argparse
import json
import sys
from pathlib import Path

from isekai.evaluate import (
    AUTHORITATIVE_GUARD_METHOD,
    Refusal,
    canvas_for,
    score_render,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--photo", required=True, type=Path)
    p.add_argument("--render", required=True, type=Path)
    p.add_argument("--subject", required=True)
    p.add_argument("--tool", required=True, help="what produced the render, for the record")
    p.add_argument("--models", type=Path, default=Path("models"))
    p.add_argument("--out", type=Path, default=Path("prototype/derived"))
    p.add_argument("--guard", choices=("iou", "centroid"), default=AUTHORITATIVE_GUARD_METHOD)
    p.add_argument(
        "--force-embeddings",
        action="store_true",
        help="suppress the cross-base refusal; output is tagged EXPLORATORY",
    )
    return p.parse_args()


def resampled(render: Path, canvas, derived_dir: Path) -> Path:
    """Write the render at the canvas's exact size and return the path."""
    from PIL import Image

    derived_dir.mkdir(parents=True, exist_ok=True)
    dest = derived_dir / f"{render.stem}.canvas.png"
    with Image.open(render) as im:
        im.convert("RGB").resize((canvas.width, canvas.height), Image.LANCZOS).save(dest)
    return dest


def main() -> None:
    args = parse_args()
    canvas = canvas_for(str(args.photo))
    render = resampled(args.render, canvas, args.out)

    from isekai.eval_backends import (
        AnimeFaceDetector,
        ArcFaceEncoder,
        DwPoseReader,
        MaskSampler,
        SegformerParser,
        StyleIdEncoder,
    )

    parser = SegformerParser(args.models)
    detector = AnimeFaceDetector(args.models, canvas)
    style = StyleIdEncoder(args.models, canvas)
    arcface = ArcFaceEncoder(args.models, canvas)
    sampler = MaskSampler(parser, str(args.photo), canvas)
    pose = DwPoseReader(args.models, canvas)

    # The one line this whole script exists to vary. `None` is the honest value
    # for a tool whose generator we cannot name; forcing it to match the
    # photograph's is a claim we have no basis for and is why the output says so.
    photo_base = "unknown-external-comparison"
    render_base = photo_base if args.force_embeddings else None

    try:
        report = score_render(
            str(args.photo),
            str(render),
            detector=detector,
            style_encoder=style,
            recognizer=arcface,
            parser=parser,
            sampler=sampler,
            pose=pose,
            subject=args.subject,
            photo_base=photo_base,
            render_base=render_base,
            image=args.render.name,
            guard_method=args.guard,
        )
    except Refusal as refused:
        sys.exit(f"REFUSED: {refused}")

    record = report.as_record()
    record["_prototype"] = {
        "tool": args.tool,
        "source_render": str(args.render),
        "source_size": _size(args.render),
        "canvas": [canvas.width, canvas.height],
        "embeddings": "EXPLORATORY — cross-base refusal suppressed"
        if args.force_embeddings
        else "refused by design (render's generator unknown)",
    }
    dest = args.out / f"{args.subject}.{'forced' if args.force_embeddings else 'honest'}.json"
    dest.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


def _size(path: Path) -> list[int]:
    from PIL import Image

    with Image.open(path) as im:
        return list(im.size)


if __name__ == "__main__":
    main()
