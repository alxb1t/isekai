#!/usr/bin/env python3
"""PROTOTYPE — T10b: sweep the INSTRUCTION, not the architecture.

F13: the recovered Qwen render did not fail to reach the register, it **overshot**
it -- linework 0.075 against Fotor's 0.040 and the photograph's 0.038 -- landing in
inked manga rather than cel anime. And the instruction it was given asked for
*"clean line art"* in as many words.

So the lever is a string. This sweeps six of them against the two style measures
(`prototype/style_axis.py`) and the retention axes (`prototype/retention.py`), on
two subjects chosen for what they can show: `s1` has a detailed meadow behind the
subject, so `background_detail` is scoreable; `s4` has a necklace and a flat
studio, so colour retention is visible and the background axis correctly refuses.

Runs on the **Lightning** graph -- 4 steps against 20 -- because a sweep wants
breadth, and the winner is re-run at full quality afterwards.

**The renders do not land on our canvas.** Qwen's graph scales to 1.5 megapixels
rather than to the injector's target, so output is resampled afterwards exactly as
Fotor's is (`external_eval.py`). Both foreign generators get identical treatment,
which is the only reason comparing them is fair.

    python prototype/qwen_sweep.py --server http://127.0.0.1:8188
"""

import argparse
import copy
import json
import time
from pathlib import Path

POSITIVE = "102:76"
LOADIMAGE = "78"
SAVE = "60"
SUBJECTS = ["s1_control_blonde", "s4_multitone_bob"]
OUT = Path("prototype/ladder/40_qwen_sweep")

KEEP = "Keep the person's face, hairstyle, clothing, accessories, and background exactly as they are."

INSTRUCTIONS = {
    # The control: what was deleted at v0.8, overshooting at 0.075 linework.
    "1_recovered": (
        "Turn this photo into an anime illustration. Anime style, clean line art, "
        "cel shading, vibrant colors. Keep the person's face, hairstyle, and pose "
        "recognizable."
    ),
    # Drop "clean line art" -- the phrase F13 blames -- and name the target register.
    "2_screencap": f"Turn this photo into an anime screencap. Cel shading, flat colors, soft thin outlines. {KEEP}",
    # Say the quiet part: forbid the failure mode explicitly.
    "3_no_heavy_lines": f"Turn this photo into anime. Cel shading with soft thin outlines and no heavy black linework. {KEEP}",
    # Name a medium rather than a technique, and let the model infer the rest.
    "4_tv_anime": f"Redraw this photo as a frame from a modern anime television series. Natural colors, flat cel shading. {KEEP}",
    # The recovered register, with the preservation clause widened to the things
    # F12 says we lose: accessories, background, garment colour.
    "5_recovered_keepall": (
        "Turn this photo into an anime illustration. Anime style, cel shading, "
        f"vibrant colors. {KEEP}"
    ),
    # How much does it do unprompted? The floor for everything above.
    "6_minimal": "Make this an anime screencap.",
}


def render(client, graph: dict, photo: str, dest: Path) -> None:
    """Submit one graph for one photo and save the image it returns."""
    from urllib import error

    name = client.upload_image(photo)
    wf = copy.deepcopy(graph)
    wf[LOADIMAGE]["inputs"]["image"] = name
    dest.mkdir(parents=True, exist_ok=True)
    try:
        prompt_id = client.submit(wf)
    except error.HTTPError as e:
        raise SystemExit(f"ComfyUI rejected the graph ({e.code}):\n{e.read().decode()}")
    while prompt_id not in client.history(prompt_id):
        time.sleep(1)
    outputs = client.history(prompt_id)[prompt_id]["outputs"]
    images = [i for o in outputs.values() for i in o.get("images", [])]
    if not images:
        raise SystemExit(f"no image returned for {dest}")
    (dest / "0.png").write_bytes(client.view(images[0]))
    print(f"saved {dest}/0.png")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--graph", default="prototype/styles/qwen-lightning.json")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    base = json.loads(Path(args.graph).read_text())
    if args.dry_run:
        print(f"{len(INSTRUCTIONS) * len(SUBJECTS)} renders, graph={args.graph}")
        for k, v in INSTRUCTIONS.items():
            print(f"  {k:20s} {v[:88]}")
        return

    from isekai.comfy_client import ComfyClient

    client = ComfyClient(args.server)
    for key, instruction in INSTRUCTIONS.items():
        g = copy.deepcopy(base)
        g[POSITIVE]["inputs"]["prompt"] = instruction
        for subj in SUBJECTS:
            dest = OUT / key / subj
            if (dest / "0.png").exists():
                print(f"skip {dest}")
                continue
            print(f"\n=== {key} / {subj} ===")
            render(client, g, f"inputs/baseline/{subj}.png", dest)
            (dest / "instruction.txt").write_text(instruction + "\n")


if __name__ == "__main__":
    main()
