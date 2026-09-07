#!/usr/bin/env python3
"""PROTOTYPE — T1: is a style axis buildable?

The missing half of the trade-off. Four axes measure similarity-to-photograph and
nothing measures *style*, so a less-stylized render wins by construction
(FINDINGS.md F5).

**The calibration set is free and owes nothing to any tuning we are about to do.**
Three points whose order is not in dispute:

    the photograph   <   isekai now   <   Fotor
    photographic         semi-realistic    flat cel

Run this BEFORE tuning: a style metric built afterwards is a metric built to agree
with whatever we picked.

**Answer: yes, and it takes two numbers, not one** (FINDINGS.md F7).

    posterisation   share of pixels in the 32 commonest colour bins. F3's finding
                    generalised: cel art fills flat, photographs graduate.
    linework        share of pixels on a strong luminance gradient. Cel art draws
                    lines; a blurred render draws none.

Two candidates were tried and dropped, recorded so they are not re-tried:
`flat_fraction` (share of near-zero-gradient neighbourhoods) orders the three
correctly but conflates *cel flatness* with *blur* -- both score high for
opposite reasons -- and `unique_ratio` (distinct bins per pixel) does not order
them at all.

    uv run --extra eval python prototype/style_axis.py
"""

from pathlib import Path

from isekai.evaluate import canvas_for
from isekai.eval_backends import load_canvas_pixels

STRONG_GRADIENT = 32.0
QUANT = 8  # 32 levels per channel, as `_dominant_lab` uses
TOP_BINS = 32


def style(pixels) -> dict[str, float]:
    """Return the two style measures for one image."""
    import numpy as np

    grey = pixels.astype("float32") @ np.array([0.2126, 0.7152, 0.0722], dtype="float32")
    gy, gx = np.gradient(grey)

    quant = (pixels // QUANT).astype("int32")
    keys = quant[..., 0] * 1024 + quant[..., 1] * 32 + quant[..., 2]
    _, counts = np.unique(keys.ravel(), return_counts=True)

    return {
        "posterisation": float(sum(sorted(counts)[-TOP_BINS:]) / keys.size),
        "linework": float((np.hypot(gx, gy) > STRONG_GRADIENT).mean()),
    }


def resampling_control(photo: str, canvas) -> dict[str, float]:
    """Send the photograph down Fotor's own resampling path and re-measure.

    Fotor returns 1968x2880 from our 832x1216, so its render reaches the canvas by
    a *downscale* where ours arrives natively and the photograph arrives by an
    upscale. If that path alone moved these numbers, the comparison would be
    measuring the resampler. It does not -- every measure lands within 0.4% -- and
    this stays in the file so the objection is answered by a command rather than
    by a claim.
    """
    import numpy as np
    from PIL import Image

    with Image.open(photo) as im:
        up = im.convert("RGB").resize((1968, 2880), Image.LANCZOS)
        return style(np.asarray(up.resize((canvas.width, canvas.height), Image.LANCZOS)))


SUBJECTS = {
    "s1_control_blonde": "s1_control_blonde-fotor-ai-art-effects-20260907125511",
    "s2_control_brunette": "s2_control_brunette-fotor-ai-art-effects-20260907130103",
}


def main() -> None:
    names = ["posterisation", "linework"]
    for subject, fotor_stem in SUBJECTS.items():
        photo = f"inputs/baseline/{subject}.png"
        canvas = canvas_for(photo)
        rows = [("photo", style(load_canvas_pixels(photo, canvas)))]
        rows.append(("  ↳ via Fotor's path", resampling_control(photo, canvas)))
        for i in range(5):
            rows.append(
                (f"isekai {i}", style(load_canvas_pixels(f"outputs/baseline/{subject}/{i}.png", canvas)))
            )
        fotor = Path("prototype/out") / f"{fotor_stem}.canvas.png"
        if fotor.exists():
            rows.append(("FOTOR", style(load_canvas_pixels(str(fotor), canvas))))

        print(f"\n=== {subject} ===")
        print(f"{'':22s}" + "".join(f"{n:>16s}" for n in names))
        for label, m in rows:
            print(f"{label:22s}" + "".join(f"{m[n]:16.4f}" for n in names))


if __name__ == "__main__":
    main()
