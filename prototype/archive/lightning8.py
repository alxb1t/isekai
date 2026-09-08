#!/usr/bin/env python3
"""PROTOTYPE — T14: the 8-step-native Lightning, against the 4-step one we misuse.

`qwen-flatcel` runs `Qwen-Image-Edit-2511-Lightning-**4steps**` at **8 steps** --
off-distribution by construction. F18 measured its linework spanning 0.028-0.113
across ten portraits, a 4x spread where `notile-d045` spanned about 2x, and that
inconsistency is the strongest argument against the preset.

**The prediction, recorded before the render:**

    spread narrows toward ~2x  -> the inconsistency was OUR error, a fixable
                                  mismatch between a 4-step LoRA and 8 steps
    spread stays at ~4x        -> it is inherent to Qwen-Image-Edit at this task,
                                  and is a real property to report

**It should NOT move the register.** Step distillation changes fidelity and
consistency, not style. If linework's *median* jumps toward Fotor's 0.040, suspect
the measurement rather than celebrate.

Renders the same ten portraits F18 used, so the comparison is like-for-like against
renders that already exist.

    python prototype/lightning8.py --server http://127.0.0.1:8188 [--dry-run]
"""

import argparse
import copy
import json
from pathlib import Path

from prototype.archive.qwen_path import configure, LORA
from prototype.archive.qwen_sweep import INSTRUCTIONS, POSITIVE, render

LORA_8 = "Qwen-Image-Edit-2511-Lightning-8steps-V1.0-bf16.safetensors"
SRC = Path("inputs/synthetic")
OUT = Path("prototype/ladder/80_lightning8")
SEED = 403402840318143


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    base = json.loads(Path("prototype/styles/qwen-lightning.json").read_text())
    g = configure(base, 8, 2.0, True)               # the chosen preset's path
    g[LORA]["inputs"]["lora_name"] = LORA_8         # ...with the native 8-step LoRA
    g[POSITIVE]["inputs"]["prompt"] = INSTRUCTIONS["5_recovered_keepall"]

    subjects = sorted(SRC.glob("*.png"))
    if a.dry_run:
        print(f"{len(subjects)} renders, lora={g[LORA]['inputs']['lora_name']}")
        print(f"steps={g['102:3']['inputs']['steps']} cfg={g['102:3']['inputs']['cfg']}")
        return

    from isekai.comfy_client import ComfyClient

    client = ComfyClient(a.server)
    for photo in subjects:
        dest = OUT / photo.stem
        if (dest / "0.png").exists():
            print(f"skip {dest}"); continue
        wf = copy.deepcopy(g); wf["102:3"]["inputs"]["seed"] = SEED
        print(f"\n=== {photo.stem} ===")
        render(client, wf, str(photo), dest)


if __name__ == "__main__":
    main()
