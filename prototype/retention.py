#!/usr/bin/env python3
"""PROTOTYPE — T12: the axes F12 said were missing, built before the thing they judge.

F12 found that the failures surviving the dial fix are **eye colour, idealised
proportions, simplified backgrounds and lost accessories** -- and that *nothing*
measures any of them. F13 then found an architecture that fixes exactly those.

**So the comparison cannot be run until these exist.** Building them is not a
detour from the architecture experiment; it is a precondition for it. And they are
built first, on renders whose answers are already known, so they cannot be built
to flatter a result we have already seen.

**Every axis here is ABSOLUTE and cross-base valid**, which is the other reason
they matter: `refuse_embedding_axes_across_bases` will silence both face axes
across a three-way Illustrious / Fotor / Qwen comparison, so the comparison lives
entirely on axes of this kind (FINDINGS.md F1).

    background_detail    edge density inside the photo's background mask,
                         render / photo. ~1 kept it, ~0 dissolved it to a wash.
    background_colour    mean CIEDE2000 inside the same mask. Catches a grey
                         studio turning teal.
    garment_colour       mean CIEDE2000 inside upper-clothes. Catches an
                         oatmeal tee turning blue.
    accessory_detail?    edge density in the band where necklaces and earrings
                         live. **DID NOT VALIDATE** -- the band is confounded by
                         whatever else sits in it, and a bob covering the ears
                         defeats it. Kept computed and never reported, alongside
                         T1's rejected `flat_fraction` and `unique_ratio`.

    uv run --extra eval python prototype/retention.py
"""

from pathlib import Path

import numpy as np

from isekai.ciede2000 import delta_e_2000
from isekai.evaluate import canvas_for
from isekai.eval_backends import SegformerParser, load_canvas_pixels
import prototype.hair_colour as hc

BACKGROUND, HAIR, UPPER, FACE = 0, 2, 4, 11
STRONG_GRADIENT = 32.0
MIN_REGION_AREA = 0.005

# A ratio needs a denominator worth dividing by. Measured on the six baseline
# photographs, background edge density runs 0.0001 (a flat wall) to 0.0227 (a
# meadow) -- so on a studio backdrop the ratio is noise over noise, which is F3's
# flat-histogram failure wearing different clothes. Below this floor the axis
# REFUSES rather than reporting a number.
MIN_EDGE_DENSITY = 0.005


def edge_density(pixels: np.ndarray, mask: np.ndarray) -> float | None:
    """Share of a region's pixels sitting on a strong luminance gradient."""
    if mask.sum() == 0:
        return None
    grey = pixels.astype("float32") @ np.array([0.2126, 0.7152, 0.0722], dtype="float32")
    gy, gx = np.gradient(grey)
    return float((np.hypot(gx, gy) > STRONG_GRADIENT)[mask].mean())


def accessory_band(face_mask: np.ndarray) -> np.ndarray:
    """The band where a necklace and earrings live, from the photo's own face.

    Derived from segformer's `face` class rather than from a detector, so it is
    deterministic and needs no second model. A neck box below the chin, plus two
    ear boxes flanking the face at its vertical middle.
    """
    ys, xs = np.nonzero(face_mask)
    if len(ys) == 0:
        return np.zeros_like(face_mask)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    h, w = y1 - y0, x1 - x0
    band = np.zeros_like(face_mask)
    H, W = face_mask.shape

    def box(ya, yb, xa, xb):
        band[max(0, ya) : min(H, yb), max(0, xa) : min(W, xb)] = True

    box(y1, y1 + int(0.55 * h), x0, x1)  # neck and collarbone
    box(y0 + int(0.35 * h), y0 + int(0.85 * h), x0 - int(0.30 * w), x0)  # ears
    box(y0 + int(0.35 * h), y0 + int(0.85 * h), x1, x1 + int(0.30 * w))
    return band & ~face_mask


def retention(photo: str, render: str, parser: SegformerParser) -> dict[str, float | None]:
    """Every retention axis for one pair, on the photograph's own regions."""
    canvas = canvas_for(photo)
    p, r = load_canvas_pixels(photo, canvas), load_canvas_pixels(render, canvas)
    out: dict[str, float | None] = {}

    for name, label in (("background", BACKGROUND), ("garment", UPPER)):
        mask = parser.mask_for(photo, canvas, label)
        if mask.mean() < MIN_REGION_AREA:
            out[f"{name}_colour"] = None
            if name == "background":
                out["background_detail"] = None
            continue
        out[f"{name}_colour"] = delta_e_2000(hc.stat_mean(p[mask]), hc.stat_mean(r[mask]))
        if name == "background":
            dp, dr = edge_density(p, mask), edge_density(r, mask)
            # Refuse rather than divide by a flat backdrop.
            out["background_detail"] = None if dp is None or dp < MIN_EDGE_DENSITY else dr / dp

    # UNVALIDATED -- kept computed, never reported as a result. See F14: the band
    # is confounded by whatever else occupies it. On s1 (hair back, neck clear) it
    # tracked the eye; on s4 (a bob falling into both ear zones) it scored 0.90 for
    # a render whose necklace is plainly gone. A proxy that works when the region
    # is clean and lies when it is not is not an axis yet.
    band = accessory_band(parser.mask_for(photo, canvas, FACE))
    dp = edge_density(p, band)
    out["accessory_detail?"] = (
        None
        if band.mean() < MIN_REGION_AREA or dp is None or dp < MIN_EDGE_DENSITY
        else edge_density(r, band) / dp
    )
    return out


NAMES = ["background_detail", "background_colour", "garment_colour", "accessory_detail?"]


def main() -> None:
    """Validate on pairs whose answer is already known (F11, F12, F2)."""
    parser = SegformerParser(Path("models"))
    fot = {"s1_control_blonde": "s1_control_blonde-fotor", "s4_multitone_bob": "s4_multitone_bob-fotor"}

    for subj in ("s1_control_blonde", "s4_multitone_bob"):
        photo = f"inputs/baseline/{subj}.png"
        rows = [
            ("SHIPPED (dissolves bg)", f"outputs/baseline/{subj}/0.png"),
            ("notile d0.45", f"prototype/ladder/21_notile_d045/{subj}/0.png"),
            ("FOTOR", f"prototype/out/{fot[subj]}.canvas.png"),
        ]
        print(f"\n=== {subj} ===")
        print(f"{'':24s}" + "".join(f"{n.replace('_', ' '):>19s}" for n in NAMES))
        print(f"{'':24s}" + "".join(f"{'ratio ~1 good' if 'detail' in n else 'ΔE lower good':>19s}" for n in NAMES))
        for label, render in rows:
            if not Path(render).exists():
                continue
            m = retention(photo, render, parser)
            cells = "".join(f"{'—':>19s}" if m[n] is None else f"{m[n]:19.3f}" for n in NAMES)
            print(f"{label:24s}{cells}")


if __name__ == "__main__":
    main()
