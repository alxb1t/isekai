#!/usr/bin/env python3
"""PROTOTYPE — flatten the recovered Qwen-Image-Edit graph into two runnable ones.

The graph recovered from `e324699^` is a ComfyUI *subgraph export*: it carries
`ComfySwitchNode` and `Primitive*` nodes that exist to toggle the 4-step Lightning
LoRA on and off in the editor. Those are frontend conveniences and are not
guaranteed to exist over the HTTP API, so they are resolved statically here rather
than submitted and hoped for.

`PrimitiveBoolean` is **false** as recovered, so the graph as deleted ran the slow
path: no LoRA, 20 steps, cfg 2.5. Both branches are emitted:

    qwen-full        no LoRA, 20 steps, cfg 2.5   -- the quality path
    qwen-lightning   LoRA,     4 steps, cfg 1.0   -- ~5x faster, for sweeping
                                                     instructions cheaply

Nothing else is changed. The instruction lives in `TextEncodeQwenImageEdit` and is
what the sweep varies; `denoise` is 1.0 and stays there, because an edit model
conditions on the image through a vision-language encoder rather than through a
partially-noised latent -- there is no img2img trade-off to tune.

    python prototype/qwen_graph.py
"""

import json
from pathlib import Path

SRC = Path("prototype/styles/qwen-image-edit.recovered.json")
SWITCH = "ComfySwitchNode"
PRIMITIVES = {"PrimitiveBoolean", "PrimitiveFloat", "PrimitiveInt"}

POSITIVE = "102:76"  # TextEncodeQwenImageEdit carrying the instruction
NEGATIVE = "102:77"  # the empty one
KSAMPLER = "102:3"


def flatten(graph: dict, lightning: bool) -> dict:
    """Resolve every switch to one branch and inline every primitive."""
    g = json.loads(json.dumps(graph))
    branch = "on_true" if lightning else "on_false"

    # A switch's chosen input, followed until it lands on something real.
    def resolve(ref):
        while isinstance(ref, list) and g.get(ref[0], {}).get("class_type") == SWITCH:
            ref = g[ref[0]]["inputs"][branch]
        if isinstance(ref, list) and g.get(ref[0], {}).get("class_type") in PRIMITIVES:
            return g[ref[0]]["inputs"]["value"]
        return ref

    for node in g.values():
        if node["class_type"] in {SWITCH} | PRIMITIVES:
            continue
        node["inputs"] = {k: resolve(v) for k, v in node["inputs"].items()}

    for nid in [n for n, v in g.items() if v["class_type"] in {SWITCH} | PRIMITIVES]:
        del g[nid]
    return g


def main() -> None:
    src = json.loads(SRC.read_text())
    for name, lightning in (("qwen-full", False), ("qwen-lightning", True)):
        g = flatten(src, lightning)
        dest = Path(f"prototype/styles/{name}.json")
        dest.write_text(json.dumps(g, indent=2) + "\n")
        ks = g[KSAMPLER]["inputs"]
        has_lora = any(v["class_type"] == "LoraLoaderModelOnly" for v in g.values())
        reaches_lora = isinstance(g["102:66"]["inputs"]["model"], list) and g[
            g["102:66"]["inputs"]["model"][0]
        ]["class_type"] == "LoraLoaderModelOnly"
        print(
            f"{name:16s} {len(g):2d} nodes  steps={ks['steps']:<3} cfg={ks['cfg']:<4} "
            f"denoise={ks['denoise']}  lora_wired={reaches_lora}"
        )
        types = {v["class_type"] for v in g.values()}
        assert not (types & ({SWITCH} | PRIMITIVES)), types
    print(f"\ninstruction: {src[POSITIVE]['inputs']['prompt']!r}")


if __name__ == "__main__":
    main()
