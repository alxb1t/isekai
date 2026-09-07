#!/usr/bin/env python3
"""PROTOTYPE — T10d: sweep the sampling path, and test the architecture thesis.

F15 found the register is set by **steps / cfg / the Lightning LoRA**, not by the
instruction, and that the two settings already run **bracket** the target:
4-step Lightning overshoots to linework 0.072, 20-step full undershoots to 0.020,
and Fotor sits at 0.040 between them.

**This is not a hunt for the prettiest setting.** It answers one question:

    Does Qwen trade style against identity the way our stack does?

Our stack trades them along `denoise` -- more anime costs accessories, colours and
background (F9). If Qwen's sampling path does the same, the architecture buys
nothing. If Qwen can sit at Fotor-like stylization *while* keeping the necklace,
the hair and the background, it buys exactly what was hoped.

So every setting is scored on **stylization** (linework, posterisation) against
**retention** (`background_detail`, which F16 establishes is the one retention axis
that survives a cross-register comparison), and the shape of that curve is the
result.

The instruction is held fixed at the one the operator picked by eye, so the sweep
varies one family of things.

    python prototype/qwen_path.py --server http://127.0.0.1:8188 [--dry-run]
"""

import argparse
import copy
import json
from pathlib import Path

from prototype.qwen_sweep import INSTRUCTIONS, POSITIVE, SUBJECTS, render

KSAMPLER = "102:3"
MODEL_IN = "102:66"  # ModelSamplingAuraFlow -- what the LoRA is wired in front of
LORA = "102:89"
UNET = "102:37"
OUT = Path("prototype/ladder/50_qwen_path")
INSTRUCTION = INSTRUCTIONS["5_recovered_keepall"]

# (name, steps, cfg, lightning). The two ends are the bracket already measured;
# everything between is new. Lightning at more steps and full at fewer steps
# approach each other from opposite sides, which is what distinguishes "one
# continuous dial" from "two different modes".
SETTINGS = [
    ("a_light_4_cfg1", 4, 1.0, True),  # = F15's over-transforming end
    ("b_light_8_cfg1", 8, 1.0, True),
    ("c_light_8_cfg2", 8, 2.0, True),
    ("d_full_8_cfg25", 8, 2.5, False),
    ("e_full_12_cfg25", 12, 2.5, False),
    ("f_full_20_cfg4", 20, 4.0, False),  # push cfg past the under-transforming end
    ("g_full_20_cfg25", 20, 2.5, False),  # = F15's under-transforming end
]


def configure(base: dict, steps: int, cfg: float, lightning: bool) -> dict:
    """Return the graph at one sampling setting, LoRA wired in or bypassed."""
    g = copy.deepcopy(base)
    g[KSAMPLER]["inputs"]["steps"] = steps
    g[KSAMPLER]["inputs"]["cfg"] = cfg
    g[POSITIVE]["inputs"]["prompt"] = INSTRUCTION
    if lightning:
        g[LORA]["inputs"]["model"] = [UNET, 0]
        g[MODEL_IN]["inputs"]["model"] = [LORA, 0]
    else:
        g[MODEL_IN]["inputs"]["model"] = [UNET, 0]
        g.pop(LORA, None)
    return g


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    # Start from the Lightning graph so the LoRA node exists to wire or drop.
    base = json.loads(Path("prototype/styles/qwen-lightning.json").read_text())

    if args.dry_run:
        print(f"{len(SETTINGS) * len(SUBJECTS)} renders")
        for name, steps, cfg, light in SETTINGS:
            g = configure(base, steps, cfg, light)
            wired = g[MODEL_IN]["inputs"]["model"][0] == LORA
            print(f"  {name:18s} steps={steps:<3} cfg={cfg:<4} lightning={light!s:5} wired={wired}")
        print(f"\ninstruction held fixed: {INSTRUCTION[:80]}...")
        return

    from isekai.comfy_client import ComfyClient

    client = ComfyClient(args.server)
    for name, steps, cfg, light in SETTINGS:
        g = configure(base, steps, cfg, light)
        for subj in SUBJECTS:
            dest = OUT / name / subj
            if (dest / "0.png").exists():
                print(f"skip {dest}")
                continue
            print(f"\n=== {name} / {subj} ===")
            render(client, g, f"inputs/baseline/{subj}.png", dest)
            (dest / "setting.json").write_text(
                json.dumps({"steps": steps, "cfg": cfg, "lightning": light}, indent=2) + "\n"
            )


if __name__ == "__main__":
    main()
