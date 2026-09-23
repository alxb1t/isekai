#!/usr/bin/env python3
"""Build one contact sheet per row of the blind comparison sheet.

A labelling aid, and nothing more: forty judgements made by opening eighty files
by hand is forty chances to compare the wrong pair. Each output is a single image
carrying the reference photograph beside the two renders, captioned **only** with
the pair id and the letters `A` and `B`.

    uv run --extra eval python baseline/build_contact_sheets.py \
        --sheet baseline/labels/sheet.csv --out .data/labels

**It carries no score, and it cannot.** It reads `sheet.csv`, which has no metric
value in it, and it never opens a scorer record -- so it cannot leak one even by
accident. The blinding survives (design.md D10).

**It also reveals nothing about which render is which.** The sheet already
randomised which side of each pair is shown as `a`, and this preserves that order
rather than sorting it: captioning the lower-numbered render as `A` every time
would let a preference for `A` masquerade as a judgement.

The sheets are written under `.data/`, the one ignored root, because a contact
sheet pastes the reference photograph beside the renders and so holds a person's
likeness by construction. v0.14 deleted `outputs/` along with the render path that
named it; this was its other producer, and it moves rather than keeping a second
ignored root alive on its own. This repository claims reproducibility over the
recipe and never over pixels, and a contact sheet is pixels twice over.
"""

import argparse
import csv
from functools import cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Every panel is scaled to this height so the three sit on one baseline. Tall
# enough that a face crop is legible at a glance, small enough that forty of them
# do not fill a disk.
PANEL_HEIGHT = 900

# Space for the caption strip above the images, and the gap between panels.
CAPTION_HEIGHT = 64
GUTTER = 16

BACKGROUND = (18, 18, 18)
INK = (245, 245, 245)

# The reference is captioned by role rather than by filename: naming the source
# file in the caption would put the subject's identifier under the photograph and
# the render's identifier under the render, which is a difference the eye can use.
CAPTIONS = ("REFERENCE", "A", "B")


@cache
def _font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    """Return a legible font, falling back to PIL's built-in if none is installed."""
    for candidate in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


@cache
def _scaled(path: Path) -> Image.Image:
    """Open an image and scale it to the common panel height.

    Cached: forty rows draw on six reference photographs, so without this the
    same reference is decoded and LANCZOS-resized thirty-four extra times.
    """
    with Image.open(path) as handle:
        image = handle.convert("RGB")
        width = round(image.width * PANEL_HEIGHT / image.height)
        # `Image.Resampling.LANCZOS`, not `Image.LANCZOS`: the flat alias was
        # removed in Pillow 10. It went unnoticed while nothing in the gate's
        # environment had Pillow installed at all -- v0.20's `tagging` extra was
        # the first that did. v0.22.3 made Pillow a declared dependency, so the
        # gate's type check now resolves this call against the real package.
        return image.resize((width, PANEL_HEIGHT), Image.Resampling.LANCZOS)


def build_sheet(reference: Path, a: Path, b: Path, pair: str, out: Path) -> None:
    """Write one contact sheet: reference, then A, then B, in that order."""
    panels = [_scaled(p) for p in (reference, a, b)]
    width = sum(p.width for p in panels) + GUTTER * (len(panels) + 1)
    height = PANEL_HEIGHT + CAPTION_HEIGHT + GUTTER * 2

    canvas = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    title = _font(34)

    x = GUTTER
    for panel, caption in zip(panels, CAPTIONS):
        canvas.paste(panel, (x, CAPTION_HEIGHT + GUTTER))
        draw.text((x + 4, GUTTER), caption, font=title, fill=INK)
        x += panel.width + GUTTER

    draw.text(
        (width - 260, GUTTER),
        f"pair {pair}   a / b / tie",
        font=_font(26),
        fill=(150, 150, 150),
    )
    canvas.save(out)


def main() -> int:
    """Build a contact sheet for every row of the comparison sheet."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", required=True, type=Path)
    parser.add_argument("--renders", default=Path(".data/baseline"), type=Path)
    parser.add_argument("--sources", default=Path(".inputs/baseline"), type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    with args.sheet.open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    for row in rows:
        if "choice" in row and (row["choice"] or "").strip():
            # A sheet that has already been filled in is still fine to render
            # from, but say so: rebuilding aids after judging is how a second
            # pass at the same pairs starts.
            print(f"note: {row['pair']} is already answered")
        reference = args.sources / f"{row['subject']}.png"
        build_sheet(
            reference,
            args.renders / row["a"],
            args.renders / row["b"],
            row["pair"],
            args.out / f"{row['pair']}.png",
        )
    print(f"wrote {len(rows)} contact sheets to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
