#!/usr/bin/env python3
"""PROTOTYPE — N4: does the from-noise flow clear the style bar.

The bar was stated in `CRITERIA.md` §4 before the render, in the units
`style_axis.py` produces: **median linework at or above the photograph's own**,
against `notile-d045`'s 0.0030. Anything that merely beats 0.0030 without
reaching the photograph is the same failure at a smaller scale.

Three flows on the same subjects and the same canvas, so the comparison is a
comparison rather than three separate readings:

    the photograph     the input, and the bar
    notile-d045        round 1's Illustrious img2img, from `renders/30_gallery`
    qwen-flatcel       round 1's Qwen edit path, from `renders/60_qwen_gallery`
    fromnoise-v1       this round

Each render is read at its **own photograph's** canvas, which is the canvas every
one of them was generated at, so no resampling enters the numbers.

    PYTHONPATH=. uv run --extra eval python prototype/n4_measure.py
"""

import statistics
from pathlib import Path

from isekai.eval_backends import load_canvas_pixels
from isekai.evaluate import canvas_for
from prototype.paths import resolve_render
from prototype.style_axis import style

PHOTOS = Path("inputs/synthetic")
_GALLERY = "prototype/renders/{run}/synthetic_portrait_{{sid}}_/seed0/{image}"
FLOWS = {
    "fromnoise-v1": "prototype/renders/n3_fromnoise/{sid}/0.png",
    "notile-d045": _GALLERY.format(run="30_gallery", image="0.png"),
    # Qwen renders arrive off-canvas and round 1 wrote the resampled copy beside
    # the original; `canvas.png` is the one every other number was read at.
    "qwen-flatcel": _GALLERY.format(run="60_qwen_gallery", image="canvas.png"),
}
RENDERED = ("00003", "00014", "00033", "00050", "00059", "00072")


def main() -> None:
    """Print per-subject style measures and the medians the bar is read on."""
    names = ("linework", "posterisation")
    columns = ["the photograph", *FLOWS]
    gathered: dict[str, dict[str, list[float]]] = {
        c: {n: [] for n in names} for c in columns
    }

    for sid in RENDERED:
        photo = PHOTOS / f"synthetic_portrait_{sid}_.png"
        canvas = canvas_for(str(photo))
        row: dict[str, dict[str, float] | None] = {
            "the photograph": style(load_canvas_pixels(str(photo), canvas))
        }
        for flow, pattern in FLOWS.items():
            path = resolve_render(pattern.format(sid=sid))
            # A flow that never rendered this subject is absent, not zero.
            row[flow] = (
                style(load_canvas_pixels(str(path), canvas)) if path.exists() else None
            )

        print(f"\n=== {sid} ===")
        print(f"{'':16s}" + "".join(f"{n:>16s}" for n in names))
        for column in columns:
            measured = row[column]
            if measured is None:
                print(f"{column:16s}" + f"{'— not rendered':>32s}")
                continue
            print(f"{column:16s}" + "".join(f"{measured[n]:16.4f}" for n in names))
            for n in names:
                gathered[column][n].append(measured[n])

    print(f"\n=== medians over {len(RENDERED)} subjects ===")
    print(f"{'':16s}" + "".join(f"{n:>16s}" for n in names) + f"{'n':>6s}")
    for column in columns:
        values = gathered[column]
        n_seen = len(values["linework"])
        if not n_seen:
            continue
        cells = "".join(f"{statistics.median(values[n]):16.4f}" for n in names)
        print(f"{column:16s}{cells}{n_seen:6d}")

    photo_bar = statistics.median(gathered["the photograph"]["linework"])
    ours = statistics.median(gathered["fromnoise-v1"]["linework"])
    verdict = "CLEARED" if ours >= photo_bar else "MISSED"
    print(
        f"\nthe style bar: median linework >= the photograph's {photo_bar:.4f}"
        f"\nfromnoise-v1:  {ours:.4f}  -> {verdict}"
        f"\nfor scale, round 1 rejected notile-d045 at 0.0030."
    )


if __name__ == "__main__":
    main()
