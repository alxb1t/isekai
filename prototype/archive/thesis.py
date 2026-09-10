#!/usr/bin/env python3
"""PROTOTYPE — plot retention against stylization, for both architectures.

**The architecture thesis, made falsifiable.** Our stack trades style against
identity along `denoise`: more anime costs accessories, colours and background
(F9). The claim for an instruction-edit model is that it does *not* -- that it can
be stylized and faithful at once, because it preserves by construction rather than
by conditioning strength.

Two curves in one space settle it:

    x = linework            how stylized (F7)
    y = background_detail   how much survived. F16 establishes this is the ONE
                            retention axis valid across style registers -- the
                            colour axes systematically flatter whichever render
                            stylized least.

    a curve that slopes DOWN  = a trade-off = the architecture buys nothing
    a curve that stays FLAT   = no trade-off = it buys exactly what was hoped

Only `s1` is plotted: `s4`'s studio backdrop has too little detail for the ratio
to mean anything and the axis correctly refuses there (F14).

    uv run --extra eval python prototype/thesis.py
"""

from pathlib import Path

from isekai.ciede2000 import delta_e_2000
from isekai.evaluate import canvas_for
from isekai.eval_backends import SegformerParser, load_canvas_pixels
from prototype.archive.retention import retention
from prototype.paths import resolve_render
from prototype.style_axis import style
import prototype.archive.hair_colour as hc

SUBJ = "s1_control_blonde"
PHOTO = f"inputs/baseline/{SUBJ}.png"


def points() -> list[tuple[str, str, str]]:
    """(series, label, path) for everything with a render on disk."""
    out = [("photo", "the photograph", PHOTO), ("fotor", "FOTOR", f"prototype/archive/fotor/canvas/{SUBJ}-fotor.canvas.png")]
    for d, lab in (("22_notile_d035", "d0.35"), ("21_notile_d045", "d0.45"), ("20_notile_d065", "d0.65")):
        path = resolve_render(f"prototype/renders/{d}/{SUBJ}/0.png")
        out.append(("ours", f"notile {lab}", str(path)))
    sweep = resolve_render("prototype/renders/50_qwen_path")
    if sweep.exists():
        for d in sorted(sweep.iterdir()):
            out.append(("qwen", f"qwen {d.name}", str(d / SUBJ / "0.png")))
    return out


def main() -> None:
    from PIL import Image

    parser = SegformerParser(Path("models"))
    canvas = canvas_for(PHOTO)
    mask = parser.mask_for(PHOTO, canvas, 2)
    ref = load_canvas_pixels(PHOTO, canvas)[mask]

    rows = []
    for series, label, path in points():
        p = Path(path)
        if not p.exists():
            continue
        # Foreign renders do not land on our canvas; resample exactly as Fotor's
        # is, so both foreign generators get identical treatment.
        if p.suffix == ".png" and Image.open(p).size != canvas.size:
            dest = p.with_name("canvas.png")
            if not dest.exists():
                with Image.open(p) as im:
                    im.convert("RGB").resize(canvas.size, Image.LANCZOS).save(dest)
            p = dest
        px = load_canvas_pixels(str(p), canvas)
        st = style(px)
        r = retention(PHOTO, str(p), parser)
        rows.append(
            (
                series,
                label,
                st["linework"],
                st["posterisation"],
                r["background_detail"],
                delta_e_2000(hc.stat_mean(ref), hc.stat_mean(px[mask])),
            )
        )

    print(f"{'':22s}{'linework':>10s}{'poster':>9s}{'bgDetail':>10s}{'hairΔE':>9s}")
    for series, label, lw, po, bg, de in rows:
        b = "   —" if bg is None else f"{bg:10.3f}"
        print(f"{label:22s}{lw:10.4f}{po:9.3f}{b:>10s}{de:9.2f}")

    # --- the plot: retention (y) against stylization (x) -------------------
    pts = [(s, la, lw, bg) for s, la, lw, _, bg, _ in rows if bg is not None and s != "photo"]
    if not pts:
        return
    xs = [p[2] for p in pts]
    ys = [p[3] for p in pts]
    W, H = 58, 16
    lo_x, hi_x = 0.0, max(xs) * 1.1
    lo_y, hi_y = 0.0, max(max(ys) * 1.1, 1.2)
    grid = [[" "] * W for _ in range(H)]
    marks = {"ours": "o", "qwen": "q", "fotor": "F"}
    for series, label, x, y in pts:
        cx = min(W - 1, int((x - lo_x) / (hi_x - lo_x) * (W - 1)))
        cy = min(H - 1, int((y - lo_y) / (hi_y - lo_y) * (H - 1)))
        grid[H - 1 - cy][cx] = marks.get(series, "?")

    print(f"\n   background_detail (retention)          o = ours   q = qwen   F = fotor")
    for r, line in enumerate(grid):
        y = hi_y - (r / (H - 1)) * (hi_y - lo_y)
        rail = "─" if abs(y - 1.0) < (hi_y - lo_y) / (2 * (H - 1)) else "│"
        print(f"   {y:5.2f} {rail}" + "".join(line))
    print("         " + "─" * W)
    print(f"         {lo_x:.3f}{' ' * (W - 12)}{hi_x:.3f}   linework (stylization)")
    print("\n   a curve sloping DOWN = a trade-off; FLAT = none.")


if __name__ == "__main__":
    main()
