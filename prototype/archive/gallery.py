#!/usr/bin/env python3
"""PROTOTYPE — render every synthetic portrait at the chosen setup, and sheet them.

T5 chose the register (`notile`) and F11 found its denoise (0.45). This asks the
only question left before a decision: **does it hold across subjects that were not
picked to break anything?** The baseline six were chosen adversarially; these ten
are just the portraits on hand.

Two seeds each, because F11 measured a real per-render spread (hair delta-E 2.66
to 4.24 on one subject across three seeds), so a single draw is not a subject's
result.

    python prototype/gallery.py --server http://127.0.0.1:8188   # render
    python prototype/gallery.py --sheet-only                     # build the sheet

The sheet lands under `prototype/derived/`, which is gitignored: this repository
claims reproducibility over the recipe and never over pixels, and a contact sheet
is pixels twice over.
"""

import argparse
import copy
import json
from pathlib import Path

SEEDS = [20260907, 20260909]
DENOISE = 0.45
SRC = Path("inputs/synthetic")
OUT = Path("prototype/renders/30_gallery")


def subjects() -> list[Path]:
    return sorted(SRC.glob("*.png"))


def render(server: str) -> None:
    from isekai.comfy_client import ComfyClient
    from isekai.pipeline import run
    from prototype.archive.ladder import TILE

    graph = json.loads(Path("workflows/pipeline.json").read_text())
    graph[TILE]["inputs"]["strength"] = 0.0  # the chosen register

    client = ComfyClient(server)
    for photo in subjects():
        for i, seed in enumerate(SEEDS):
            dest = OUT / photo.stem / f"seed{i}"
            if (dest / "0.png").exists():
                print(f"skip {dest}")
                continue
            print(f"\n=== {photo.stem} seed{i} ===")
            run(
                client,
                copy.deepcopy(graph),
                str(photo),
                dest,
                variations=1,
                seed=seed,
                overrides={"denoise": DENOISE},
                fixed_dials=True,
            )


def sheet(height: int = 300) -> Path:
    """One row per subject: the photograph, then each seed's render."""
    from PIL import Image

    rows = []
    for photo in subjects():
        cells = [photo]
        for i in range(len(SEEDS)):
            p = OUT / photo.stem / f"seed{i}" / "0.png"
            if p.exists():
                cells.append(p)
        if len(cells) > 1:
            rows.append(cells)

    thumbs = [[Image.open(c).convert("RGB") for c in row] for row in rows]
    thumbs = [
        [t.resize((max(1, round(t.width * height / t.height)), height), Image.LANCZOS) for t in row]
        for row in thumbs
    ]
    width = max(sum(t.width for t in row) for row in thumbs)
    sheet_img = Image.new("RGB", (width, height * len(thumbs)), "white")
    for r, row in enumerate(thumbs):
        x = 0
        for t in row:
            sheet_img.paste(t, (x, r * height))
            x += t.width

    dest = Path("prototype/archive/galleries/gallery_notile_d045.png")
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet_img.save(dest)
    print(f"{len(thumbs)} subjects -> {dest} ({sheet_img.width}x{sheet_img.height})")
    return dest


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--sheet-only", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if args.dry_run:
        n = len(subjects()) * len(SEEDS)
        print(f"{n} renders: {len(subjects())} subjects x {len(SEEDS)} seeds, tile=0.0, denoise={DENOISE}")
        for s in subjects():
            print(f"  {s.stem}")
        return
    if not args.sheet_only:
        render(args.server)
    sheet()


if __name__ == "__main__":
    main()
