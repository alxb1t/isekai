#!/usr/bin/env python3
"""PROTOTYPE — T1: is a style axis buildable?

The missing half of the trade-off. Four axes measure similarity-to-photograph and
nothing measures *style*, so a less-stylized render wins by construction
(notes/FINDINGS.md F5).

**Answer: yes, and it takes two numbers, not one** (notes/FINDINGS.md F7).

    posterisation   share of pixels in the 32 commonest colour bins. F3's finding
                    generalised: cel art fills flat, photographs graduate.
    linework        share of pixels on a strong luminance gradient. Cel art draws
                    lines; a blurred render draws none.

**Both are ABSOLUTE.** They describe the render and nothing else -- no photograph,
no reference image, no competitor. That is what lets them be read against *our own
previous number*, which is the only comparison this prototype makes as of
2026-09-10. It was calibrated in round 1 against a third-party stylizer, which is
recorded in F7 and is now history: the artifacts are in `archive/fotor/` and
nothing live reads them.

Two candidates were tried and dropped, recorded so they are not re-tried:
`flat_fraction` (share of near-zero-gradient neighbourhoods) orders the three
correctly but conflates *cel flatness* with *blur* -- both score high for
opposite reasons -- and `unique_ratio` (distinct bins per pixel) does not order
them at all.

    uv run --extra eval python prototype/style_axis.py
"""


from isekai.eval_backends import load_canvas_pixels
from isekai.evaluate import canvas_for

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
    """Send the photograph up to 1968x2880 and back down, then re-measure.

    **The axes are resolution-sensitive** (F35, where reading hires natively
    flipped linework's sign), so the standing objection is that a number could be
    measuring the resampler rather than the render. It is not -- a round trip
    through a much larger canvas lands every measure within 0.4% -- and this stays
    in the file so the objection is answered by a command rather than by a claim.

    The specific size is inherited from round 1's third-party comparison and is
    kept only because that is the size the 0.4% was established at.
    """
    import numpy as np
    from PIL import Image

    with Image.open(photo) as im:
        up = im.convert("RGB").resize((1968, 2880), Image.LANCZOS)
        return style(np.asarray(up.resize((canvas.width, canvas.height), Image.LANCZOS)))


SUBJECTS = ("s1_control_blonde", "s2_control_brunette")


def main() -> None:
    """Print both axes for each calibration subject: the photograph, then v0.12."""
    names = ["posterisation", "linework"]
    for subject in SUBJECTS:
        photo = f"inputs/baseline/{subject}.png"
        canvas = canvas_for(photo)
        rows = [("photo", style(load_canvas_pixels(photo, canvas)))]
        rows.append(("  ↳ resampling control", resampling_control(photo, canvas)))
        for i in range(5):
            render = f"outputs/baseline/{subject}/{i}.png"
            rows.append((f"isekai {i}", style(load_canvas_pixels(render, canvas))))

        print(f"\n=== {subject} ===")
        print(f"{'':22s}" + "".join(f"{n:>16s}" for n in names))
        for label, m in rows:
            print(f"{label:22s}" + "".join(f"{m[n]:16.4f}" for n in names))


if __name__ == "__main__":
    main()
