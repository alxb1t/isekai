#!/usr/bin/env python3
"""PROTOTYPE — T11: does our own stack carry a specific tattoo?

F23 found Fotor keeps tattoo *presence* -- coverage, placement, palette -- and
loses the motifs. And it put a caveat on F13's "Qwen kept the tattoos": that
render came from the under-transforming end of the bracket, so Qwen may have
preserved the ink by barely stylizing.

**That caveat is the hypothesis this tests.** Three presets on the same four
photographs, spanning the stylization range:

    notile-d045       ours, Illustrious          least stylized of the three
    qwen full 20      the under-transforming end  where F13's tattoo survived
    qwen-flatcel      the chosen flat-cel preset  most stylized

If ink fidelity falls as stylization rises, the coupling F23 names is confirmed on
a fourth system and on the project's own subject. If the flat-cel preset keeps the
motifs, `xor` has a counter-example worth a great deal.

Two of the four photographs show the ink and two have it hidden -- the hidden pair
is the control for "did the model invent tattoos".

**These are photographs of a real person.** Renders go to `prototype/ladder/`,
which is gitignored, and nothing here is committed (design.md D14).

    python prototype/tattoo_test.py --server http://127.0.0.1:8188 [--dry-run]
"""

import argparse
import copy
import json
from pathlib import Path

SRC = Path("outputs/original/darya")
OUT = Path("prototype/ladder/90_tattoo")
SEED = 20260907


def photos():
    return sorted(p for p in SRC.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    ps = photos()
    if a.dry_run:
        print(f"{len(ps) * 3} renders across 3 presets")
        for p in ps:
            print(f"  {p.name}")
        return

    from isekai.comfy_client import ComfyClient
    from isekai.pipeline import run
    from prototype.ladder import TILE
    from prototype.qwen_path import configure
    from prototype.qwen_sweep import INSTRUCTIONS, POSITIVE, render

    client = ComfyClient(a.server)
    qbase = json.loads(Path("prototype/styles/qwen-lightning.json").read_text())
    instruction = INSTRUCTIONS["5_recovered_keepall"]

    qwen = {
        "qwen_flatcel": configure(qbase, 8, 2.0, True),
        "qwen_full20": configure(qbase, 20, 2.5, False),
    }
    for g in qwen.values():
        g[POSITIVE]["inputs"]["prompt"] = instruction

    # ours: Illustrious, tile off, denoise 0.45
    ours = json.loads(Path("workflows/pipeline.json").read_text())
    ours[TILE]["inputs"]["strength"] = 0.0

    for photo in ps:
        stem = photo.stem.replace(" ", "_")
        for name, g in qwen.items():
            dest = OUT / name / stem
            if (dest / "0.png").exists():
                print(f"skip {dest}"); continue
            print(f"\n=== {name} / {stem} ===")
            wf = copy.deepcopy(g); wf["102:3"]["inputs"]["seed"] = SEED
            render(client, wf, str(photo), dest)

        dest = OUT / "notile_d045" / stem
        if (dest / "0.png").exists():
            print(f"skip {dest}"); continue
        print(f"\n=== notile_d045 / {stem} ===")
        run(client, copy.deepcopy(ours), str(photo), dest, variations=1,
            seed=SEED, overrides={"denoise": 0.45}, fixed_dials=True)


if __name__ == "__main__":
    main()
