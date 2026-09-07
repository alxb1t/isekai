#!/usr/bin/env python3
"""PROTOTYPE — T13: does a style LoRA move the register where the instruction cannot?

The operator still dislikes something in `qwen-flatcel`'s style. F15 and F17
established the two levers we have -- the instruction and the sampling path -- and
both are blunt: they move linework across a wide range but do not choose *which*
anime. A style LoRA is the instrument that does.

`raena_qwen_image_lora_v0.1`, trained words **anime, illustration**.

**Two things this has to establish before any aesthetic judgement:**

1. **Does it apply at all?** Civitai declares `baseModel: Qwen` -- Qwen-*Image* --
   and we run Qwen-Image-*Edit*. The backbone is shared so it usually loads, but
   "loads" and "does something" are different claims. Strength 0.0 is the control;
   if 1.0 is indistinguishable from it, the answer is no.
2. **Does it fight Lightning?** It has to stack with the 4-step Lightning LoRA that
   the chosen preset runs on. So the sweep covers Lightning at 8 steps *and* the
   full path at 12, and a difference between those two is the answer.

    python prototype/qwen_lora.py --server http://127.0.0.1:8188 [--dry-run]
"""

import argparse
import copy
import json
from pathlib import Path

from prototype.qwen_path import configure, LORA, MODEL_IN, UNET
from prototype.qwen_sweep import POSITIVE, SUBJECTS, render, INSTRUCTIONS

KSAMPLER = "102:3"
STYLE_LORA = "900"  # a node id the recovered graph does not use
LORA_FILE = "raena_qwen_image_lora_v0.1.safetensors"
OUT = Path("prototype/ladder/70_qwen_lora")
BASE_INSTRUCTION = INSTRUCTIONS["5_recovered_keepall"]

# (name, steps, cfg, lightning, lora_strength, instruction_suffix)
SETTINGS = [
    ("a_off_light8", 8, 2.0, True, 0.0, ""),           # control = the chosen preset
    ("b_s05_light8", 8, 2.0, True, 0.5, ""),
    ("c_s08_light8", 8, 2.0, True, 0.8, ""),
    ("d_s10_light8", 8, 2.0, True, 1.0, ""),
    ("e_s10_light8_words", 8, 2.0, True, 1.0, " anime, illustration."),
    ("f_off_full12", 12, 2.5, False, 0.0, ""),         # control for the full path
    ("g_s10_full12", 12, 2.5, False, 1.0, ""),
    ("h_s10_full12_words", 12, 2.5, False, 1.0, " anime, illustration."),
]


def with_style_lora(g: dict, strength: float) -> dict:
    """Insert the style LoRA between whatever feeds the sampler and the sampler."""
    if strength <= 0:
        return g
    upstream = g[MODEL_IN]["inputs"]["model"]
    g[STYLE_LORA] = {
        "class_type": "LoraLoaderModelOnly",
        "inputs": {
            "lora_name": LORA_FILE,
            "strength_model": strength,
            "model": upstream if isinstance(upstream, list) else [UNET, 0],
        },
    }
    g[MODEL_IN]["inputs"]["model"] = [STYLE_LORA, 0]
    return g


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    base = json.loads(Path("prototype/styles/qwen-lightning.json").read_text())

    if a.dry_run:
        print(f"{len(SETTINGS) * len(SUBJECTS)} renders")
        for n, st, cfg, light, s, suf in SETTINGS:
            g = with_style_lora(configure(base, st, cfg, light), s)
            chain, cur, seen = [], g[MODEL_IN]["inputs"]["model"], 0
            while isinstance(cur, list) and seen < 6:
                chain.append(g[cur[0]]["class_type"]); cur = g[cur[0]]["inputs"].get("model"); seen += 1
            print(f"  {n:22s} steps={st:<3} cfg={cfg:<4} light={light!s:5} lora={s:<4} chain={'<-'.join(chain)}")
        return

    from isekai.comfy_client import ComfyClient

    client = ComfyClient(a.server)
    for name, steps, cfg, light, strength, suffix in SETTINGS:
        g = with_style_lora(configure(base, steps, cfg, light), strength)
        g[POSITIVE]["inputs"]["prompt"] = BASE_INSTRUCTION + suffix
        for subj in SUBJECTS:
            dest = OUT / name / subj
            if (dest / "0.png").exists():
                print(f"skip {dest}"); continue
            print(f"\n=== {name} / {subj} ===")
            render(client, g, f"inputs/baseline/{subj}.png", dest)
            (dest / "setting.json").write_text(json.dumps(
                {"steps": steps, "cfg": cfg, "lightning": light,
                 "lora_strength": strength, "instruction": g[POSITIVE]["inputs"]["prompt"]}, indent=2) + "\n")


if __name__ == "__main__":
    main()
