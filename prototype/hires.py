#!/usr/bin/env python3
"""PROTOTYPE — N19: the hires pass WAI recommends and this pipeline has never run.

F32 and F34 between them spent every documented *prompt* lever. Flow `A` sits at
0.363 posterisation and there is nothing left to type. What
remains is structural, and the publisher's own page names it:

    "Upscale with R-ESRGAN 4x+ Anime6B, 20 steps, and a Denoising strength of
     0.35~0.5"

A second sampler pass over an upscaled render. Three new arms; the two
no-hires references already exist in `renders/n18_position/` at the identical
prompt, so they are reused rather than re-rendered.

    2_hires_035   flow A + hires at denoise 0.35   (the recommendation's floor)
    3_hires_050   flow A + hires at denoise 0.50   (its ceiling)
    5_d_hires_035 flow D + hires at denoise 0.35

**The first-pass guard is not weakened.** `check_graph` refuses a graph containing
a `VAEEncode`, because in the *first* pass that would mean the photograph is back
in the latent -- which is the whole architecture. The hires pass legitimately
encodes the *render*, so the guard runs against the base graph **before** this
module appends anything, and a separate check below asserts the new encode reads
the first pass's own decode.

    PYTHONPATH=. uv run python prototype/hires.py --server http://127.0.0.1:8188
"""

import argparse
import json
from pathlib import Path

from isekai.comfy_client import ComfyClient
from isekai.pipeline import _render
from isekai.workflow import image_dimensions, inject, working_resolution
from prototype.combined import CFG, CN_STRENGTH
from prototype.face_ladder import INSTANTID, SAMPLER
from prototype.fromnoise import (
    GRAPH,
    LATENT,
    NEGATIVE,
    PHOTOS,
    POSITIVE,
    SEED,
    SUGGESTED,
    check_graph,
    prompts_of,
)
from prototype.ladder_position import build
from prototype.paths import render_dir, sheet_path

CHECKPOINT = "1"
DECODE = "11"  # the first pass's VAEDecode
SAVE = "12"
UPSCALER = "RealESRGAN_x4plus_anime_6B.pth"
HIRES_SCALE = 1.5  # WAI's example: 1024x1344 at hires 1.5
HIRES_STEPS = 20

# High ids, so they cannot collide with the base graph's 1-23.
LOADER, UPSCALE, RESIZE, ENCODE, SAMPLER2, DECODE2 = "30", "31", "32", "33", "34", "35"


def add_hires(graph: dict, width: int, height: int, denoise: float) -> None:
    """Append the second pass, and repoint SaveImage at it.

    The upscaler returns 4x, which is then resampled to the 1.5x target rather
    than sampled at 4x -- that is what "hires 1.5" means, and sampling a 4096-wide
    latent would cost far more than the recommendation asks for.
    """
    target = (round(width * HIRES_SCALE), round(height * HIRES_SCALE))
    for side in target:
        # SDXL's VAE needs a multiple of 8; 1.5x of a /64 canvas always is, and
        # this asserts it rather than trusting it.
        if side % 8:
            raise SystemExit(f"hires target {target} is not a multiple of 8")

    first = graph[SAMPLER]["inputs"]
    graph[LOADER] = {
        "inputs": {"model_name": UPSCALER},
        "class_type": "UpscaleModelLoader",
        "_meta": {"title": "R-ESRGAN 4x+ Anime6B"},
    }
    graph[UPSCALE] = {
        "inputs": {"upscale_model": [LOADER, 0], "image": [DECODE, 0]},
        "class_type": "ImageUpscaleWithModel",
        "_meta": {"title": "Upscale the first pass 4x"},
    }
    graph[RESIZE] = {
        "inputs": {
            "upscale_method": "lanczos",
            "width": target[0],
            "height": target[1],
            "crop": "disabled",
            "image": [UPSCALE, 0],
        },
        "class_type": "ImageScale",
        "_meta": {"title": f"Down to {HIRES_SCALE}x"},
    }
    graph[ENCODE] = {
        # The render, not the photograph. That distinction is the whole reason
        # `check_graph` runs before this function is called.
        "inputs": {"pixels": [RESIZE, 0], "vae": [CHECKPOINT, 2]},
        "class_type": "VAEEncode",
        "_meta": {"title": "Encode the upscaled render"},
    }
    graph[SAMPLER2] = {
        "inputs": {
            "seed": first["seed"],
            "steps": HIRES_STEPS,
            "cfg": first["cfg"],
            "sampler_name": first["sampler_name"],
            "scheduler": first["scheduler"],
            "denoise": denoise,
            # Same model patch and same conditioning as the first pass, so the
            # only thing this arm changes is that a second pass happens at all.
            "model": first["model"],
            "positive": first["positive"],
            "negative": first["negative"],
            "latent_image": [ENCODE, 0],
        },
        "class_type": "KSampler",
        "_meta": {"title": f"Hires pass, denoise {denoise}"},
    }
    graph[DECODE2] = {
        "inputs": {"samples": [SAMPLER2, 0], "vae": [CHECKPOINT, 2]},
        "class_type": "VAEDecode",
        "_meta": {"title": "Decode the hires pass"},
    }
    graph[SAVE]["inputs"]["images"] = [DECODE2, 0]


def check_hires(graph: dict) -> None:
    """Fail before the pod is billed if the second pass is wired to the wrong thing."""
    if graph[ENCODE]["inputs"]["pixels"] != [RESIZE, 0]:
        raise SystemExit("the hires encode does not read the upscaled render")
    if graph[UPSCALE]["inputs"]["image"] != [DECODE, 0]:
        raise SystemExit("the upscaler does not read the first pass's decode")
    if graph[SAVE]["inputs"]["images"] != [DECODE2, 0]:
        raise SystemExit("SaveImage still points at the first pass")
    encodes = [k for k, n in graph.items() if n["class_type"] == "VAEEncode"]
    if encodes != [ENCODE]:
        raise SystemExit(f"unexpected VAEEncode nodes: {encodes}")


ARMS = {
    "2_hires_035": ("A", 0.35),
    "3_hires_050": ("A", 0.50),
    "5_d_hires_035": ("D", 0.35),
}


def main() -> None:
    """Render every hires arm on every subject, at one seed."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--out", type=Path, default=render_dir("n19_hires"))
    p.add_argument("--subjects", nargs="*", default=list(SUGGESTED))
    p.add_argument("--only", default=None)
    p.add_argument("--pod-image", default=None)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    base = json.loads(GRAPH.read_text())
    check_graph(base)  # the first pass, before anything is appended
    client = None if args.dry_run else ComfyClient(args.server)

    for sid in args.subjects:
        photo = PHOTOS / f"synthetic_portrait_{sid}_.png"
        prompt, negative = prompts_of(sheet_path(sid))
        width, height = working_resolution(*image_dimensions(str(photo)))

        for name, (flow, denoise) in ARMS.items():
            if args.only and name != args.only:
                continue
            dest = args.out / name / sid
            if (dest / "0.png").exists():
                print(f"skip {dest}")
                continue

            g = build(base, flow)
            g[POSITIVE]["inputs"]["text"] = prompt
            g[NEGATIVE]["inputs"]["text"] = negative
            g[LATENT]["inputs"].update(width=width, height=height)
            g[SAMPLER]["inputs"].update(cfg=CFG, seed=SEED)
            if INSTANTID in g:
                g[INSTANTID]["inputs"]["cn_strength"] = CN_STRENGTH
            # `inject` resolves `find_node(class_type="ImageScale")`, whose
            # exactly-one contract the hires resize is a second instance of. So
            # the photo is wired in **before** the second pass exists, rather
            # than by relaxing a seam the shipped path depends on.
            if client is not None:
                inject(g, client.upload_image(str(photo)), str(photo))
            add_hires(g, width, height, denoise)
            check_hires(g)

            t = g[RESIZE]["inputs"]
            print(
                f"\n=== {name} / {sid} ===  flow {flow} · hires "
                f"{width}x{height} -> {t['width']}x{t['height']} · denoise {denoise}"
            )
            if client is None:
                continue
            dest.mkdir(parents=True, exist_ok=True)
            _render(client, g, dest / "0.png")
            (dest / "arm.json").write_text(
                json.dumps(
                    {
                        "arm": name,
                        "flow": flow,
                        "subject": sid,
                        "seed": SEED,
                        "hires_denoise": denoise,
                        "hires_steps": HIRES_STEPS,
                        "hires_target": [t["width"], t["height"]],
                        "upscaler": UPSCALER,
                        "cfg": CFG,
                        "pod_image": args.pod_image,
                    },
                    indent=2,
                )
                + "\n"
            )


if __name__ == "__main__":
    main()
