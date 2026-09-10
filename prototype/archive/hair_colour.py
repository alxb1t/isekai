#!/usr/bin/env python3
"""PROTOTYPE — T2: what statistic can represent a hair colour on BOTH sides?

`hair_colour_delta_e` takes the **mode** of a coarse RGB histogram. On a
photograph the histogram is flat -- the winning bin held 1.21% of pixels and
landed on a shadow, reading blonde hair as L* 4.5 (FINDINGS.md F3). On flat cel
art the mode is real. So the axis compares a noise bin against a genuine one and
penalises the more stylized image.

**The acceptance test needs no labels.** Take the photograph's own hair, apply a
shift whose size we chose, and ask each candidate what it sees:

    L+15, L-15, a+15, b+15   a good statistic reports roughly the shift
    posterise (cel-shade)    a good statistic reports roughly the TRUE shift,
                             which is printed beside it

The posterisation case is the confound in miniature: cel-shading a photograph
changes its histogram from continuous to discrete and its colour hardly at all.
**It indicts the mode. It does not select the replacement** -- see `posterised`.

    uv run --extra eval python prototype/hair_colour.py
"""

import numpy as np

from isekai.ciede2000 import delta_e_2000
from isekai.evaluate import canvas_for
from isekai.eval_backends import SegformerParser, load_canvas_pixels

HAIR_LABEL = 2
QUANT = 8


# --- sRGB -> Lab, vectorised over N pixels ---------------------------------
def to_lab(rgb: np.ndarray) -> np.ndarray:
    """Convert an (N,3) uint8 sRGB array to (N,3) CIE L*a*b* under D65."""
    srgb = rgb.astype("float64") / 255.0
    linear = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
    m = np.array(
        [
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041],
        ]
    )
    xyz = linear @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack(
        [116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])],
        axis=1,
    )


def from_lab(lab: np.ndarray) -> np.ndarray:
    """Inverse of `to_lab`, for building the synthetic shifts."""
    fy = (lab[:, 0] + 16) / 116
    fx, fz = fy + lab[:, 1] / 500, fy - lab[:, 2] / 200
    f = np.stack([fx, fy, fz], axis=1)
    xyz = np.where(f**3 > 216 / 24389, f**3, (116 * f - 16) / (24389 / 27))
    xyz *= np.array([0.95047, 1.0, 1.08883])
    m = np.array(
        [
            [3.2404542, -1.5371385, -0.4985314],
            [-0.9692660, 1.8760108, 0.0415560],
            [0.0556434, -0.2040259, 1.0572252],
        ]
    )
    linear = xyz @ m.T
    srgb = np.where(linear <= 0.0031308, 12.92 * linear, 1.055 * np.abs(linear) ** (1 / 2.4) - 0.055)
    return np.clip(srgb * 255, 0, 255).astype("uint8")


# --- the candidates --------------------------------------------------------
def stat_mode(rgb: np.ndarray) -> tuple[float, float, float]:
    """What ships today: the mode of a 32-level-per-channel RGB histogram."""
    q = (rgb // QUANT).astype("int32")
    keys = q[:, 0] * 1024 + q[:, 1] * 32 + q[:, 2]
    values, counts = np.unique(keys, return_counts=True)
    winner = values[int(np.argmax(counts))]
    return tuple(to_lab(rgb[keys == winner].mean(axis=0, keepdims=True).astype("uint8"))[0])


def stat_mean(rgb: np.ndarray) -> tuple[float, float, float]:
    """The mean in Lab. Robust to a flat histogram; blends a bimodal one."""
    return tuple(to_lab(rgb).mean(axis=0))


def stat_median(rgb: np.ndarray) -> tuple[float, float, float]:
    """The per-channel median in Lab. Robust to outliers and to shadow tails."""
    return tuple(np.median(to_lab(rgb), axis=0))


def stat_cluster2(rgb: np.ndarray, iters: int = 12) -> tuple[float, float, float]:
    """The larger of two k-means clusters in Lab.

    Multi-tone hair is the norm in this aesthetic rather than an edge case, so a
    single representative colour is the wrong shape for the axis in the long run.
    Two clusters is the smallest thing that can *see* a base and an underlayer;
    this returns the larger one so it stays a drop-in for the current signature,
    and the full pair is what a real version should report.
    """
    lab = to_lab(rgb)
    lo, hi = np.percentile(lab[:, 0], [25, 75])
    centres = np.array([lab[np.argmin(np.abs(lab[:, 0] - lo))], lab[np.argmin(np.abs(lab[:, 0] - hi))]])
    for _ in range(iters):
        which = np.argmin(((lab[:, None, :] - centres[None]) ** 2).sum(axis=2), axis=1)
        for k in (0, 1):
            if (which == k).any():
                centres[k] = lab[which == k].mean(axis=0)
    sizes = [(which == k).sum() for k in (0, 1)]
    return tuple(centres[int(np.argmax(sizes))])


CANDIDATES = {"mode": stat_mode, "mean": stat_mean, "median": stat_median, "cluster2": stat_cluster2}


# --- the known-answer set --------------------------------------------------
def shifted(rgb: np.ndarray, dL: float = 0, da: float = 0, db: float = 0) -> np.ndarray:
    """Return the pixels moved by a known amount in Lab."""
    lab = to_lab(rgb) + np.array([dL, da, db])
    return from_lab(lab)


def posterised(rgb: np.ndarray, levels: int = 5) -> np.ndarray:
    """Flatten to a few bands per channel -- what cel-shading does to a photograph.

    **Plain quantisation, with no correction.** An earlier version added back the
    mean difference so the case would be "colour kept" by construction -- which
    made `mean` score zero by definition and turned the test circular. It is left
    uncorrected, and the true shift is printed beside the candidates so the reader
    can see how much colour actually moved.

    So this test **indicts the mode**; it does not **select** its replacement.
    """
    step = 256 // levels
    return ((rgb // step) * step + step // 2).clip(0, 255).astype("uint8")


def main() -> None:
    photo = "inputs/baseline/s1_control_blonde.png"
    canvas = canvas_for(photo)
    parser = SegformerParser(__import__("pathlib").Path("models"))
    mask = parser.mask_for(photo, canvas, HAIR_LABEL)
    hair = load_canvas_pixels(photo, canvas)[mask]

    cases = {
        "identical": (hair, 0.0),
        "L +15": (shifted(hair, dL=15), 15.0),
        "L -15": (shifted(hair, dL=-15), 15.0),
        "a +15": (shifted(hair, da=15), None),
        "b +15": (shifted(hair, db=15), None),
        "posterised (cel-shaded)": (posterised(hair), None),
    }

    print(f"hair pixels: {len(hair)}\n")
    true = delta_e_2000(
        tuple(to_lab(hair).mean(axis=0)), tuple(to_lab(posterised(hair)).mean(axis=0))
    )
    print(f"{'case':26s}" + "".join(f"{n:>12s}" for n in CANDIDATES) + "   want")
    for label, (variant, want) in cases.items():
        row = ""
        for fn in CANDIDATES.values():
            row += f"{delta_e_2000(fn(hair), fn(variant)):12.2f}"
        note = "~%.0f" % want if want is not None else ""
        if label.startswith("posterised"):
            note = f"true colour shift {true:.2f}"
        print(f"{label:26s}{row}   {note}")

    print(f"\n{'':26s}" + "".join(f"{n:>12s}" for n in CANDIDATES))
    print(f"{'photo hair L*':26s}" + "".join(f"{fn(hair)[0]:12.1f}" for fn in CANDIDATES.values()))


if __name__ == "__main__":
    main()
