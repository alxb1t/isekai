#!/usr/bin/env python3
"""PROTOTYPE — T10f: the chosen Qwen setting across every synthetic portrait.

The operator picked `c_light_8_cfg2` from the T10d sheet (F17): Lightning LoRA,
**8 steps, cfg 2.0**, denoise 1.0, instruction `5_recovered_keepall`. Flat cel --
the register Fotor occupies and our own stack cannot reach (F17).

Same shape as `notile`'s gallery (T6c) so the two presets are comparable: every
portrait on hand, plus extra seeds on one subject, because F11 measured a real
per-render spread and a single draw is not a subject's result.

    python prototype/qwen_gallery.py --server http://127.0.0.1:8188 [--sheet-only]
"""

import argparse
import copy
import json
from pathlib import Path

from prototype.qwen_path import configure
from prototype.qwen_sweep import render

SRC = Path("inputs/synthetic")
OUT = Path("prototype/ladder/60_qwen_gallery")
KSAMPLER = "102:3"
SEEDS = [403402840318143, 20260907]
STEPS, CFG, LIGHTNING = 8, 2.0, True
STABILITY = "synthetic_portrait_00003_"


def subjects():
    return sorted(SRC.glob("*.png"))


def jobs():
    out = [(p, p.stem, SEEDS[0], "seed0") for p in subjects()]
    stab = SRC / f"{STABILITY}.png"
    if stab.exists():
        out.append((stab, STABILITY, SEEDS[1], "seed1"))
    return out


def sheet(height=300):
    from PIL import Image

    rows = []
    for p in subjects():
        cells = [p] + [q for q in [OUT / p.stem / "seed0" / "0.png"] if q.exists()]
        if len(cells) > 1:
            rows.append(cells)
    thumbs = [[Image.open(c).convert("RGB") for c in row] for row in rows]
    thumbs = [[t.resize((max(1, round(t.width * height / t.height)), height), Image.LANCZOS) for t in r] for r in thumbs]
    w = max(sum(t.width for t in r) for r in thumbs)
    img = Image.new("RGB", (w, height * len(thumbs)), "white")
    for i, r in enumerate(thumbs):
        x = 0
        for t in r:
            img.paste(t, (x, i * height)); x += t.width
    dest = Path("prototype/out/gallery_qwen_c_light_8_cfg2.png")
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest)
    print(f"{len(thumbs)} subjects -> {dest} ({img.width}x{img.height})")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--sheet-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    plan = jobs()
    if a.dry_run:
        print(f"{len(plan)} renders, steps={STEPS} cfg={CFG} lightning={LIGHTNING}")
        for _, stem, seed, tag in plan:
            print(f"  {stem:34s} {tag} seed={seed}")
        return
    if not a.sheet_only:
        from isekai.comfy_client import ComfyClient
        base = json.loads(Path("prototype/styles/qwen-lightning.json").read_text())
        g0 = configure(base, STEPS, CFG, LIGHTNING)
        client = ComfyClient(a.server)
        for photo, stem, seed, tag in plan:
            dest = OUT / stem / tag
            if (dest / "0.png").exists():
                print(f"skip {dest}"); continue
            g = copy.deepcopy(g0); g[KSAMPLER]["inputs"]["seed"] = seed
            print(f"\n=== {stem} {tag} ===")
            render(client, g, str(photo), dest)
    sheet()


if __name__ == "__main__":
    main()
