#!/usr/bin/env python3
"""PROTOTYPE — N37: whether Illustrious reads prose, or only tags.

**The plan, the prediction and the bars are in the evaluation's own README** —
`prototype/evaluations/2026-09-12/descriptive_and_booru/README.md`. This file
only renders it. Read the plan first; every number it states was stated before
this ran.

Four arms over five photographs, one seed, flow `A` at the settled
configuration. **The only thing that differs between arms is the body of the
positive prompt.** WAI's quality ladder leads all four, the count tag follows it,
the shipped trailer closes it — so a prose arm that loses cannot have lost
because it was denied the structure F34 measured at +0.013.

| arm | body |
|---|---|
| `1_descriptive` | JoyCaption's `descriptive` caption, verbatim |
| `2_straightforward` | JoyCaption's `straightforward` caption, verbatim |
| `3_booru` | a sixteen-field sheet Claude routed from the `descriptive` caption |
| `4_baseline` | the operator's reviewed sheet — **the anchor** |

### Why the baseline renders here rather than being read off F41

It has to be in the same session. GPU nondeterminism across pods is ±2/255 mean
pixel |Δ|, and F41's run used its own seed — so comparing a prose arm against a
render made on a different pod on a different day measures the pods as much as
the prompts. Five extra renders cost $0.022 and buy the only anchor that means
anything.

### The prompts are read, not built

`prompts.json` is written before the pod exists and reviewed by the operator as
`render_prompts.html` — `README.md` §7 step ⑤ is that gate. This file reads that
file. **Rebuilding the prompts here would mean the reviewed text and the rendered
text could differ with nothing saying so**, which is the same argument
`fromnoise.prompts_of` makes for reading a sheet rather than reassembling it.

### Photographs are downscaled before upload, and that is a step not an optimisation

F41: N30's photographs are 21–28 MB and the uploads, not the GPU, made 34
renders take 27 minutes against the ~17 the GPU time predicts. Two of these five
are 21 MB and 24 MB. `--prepare` writes the downscaled copies; the render reads
them.

    PYTHONPATH=. uv run --extra eval python prototype/prose_render.py --prepare
    PYTHONPATH=. uv run python prototype/prose_render.py --dry-run
    PYTHONPATH=. uv run python prototype/prose_render.py --server http://127.0.0.1:8188
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
    POSITIVE,
    SEED,
    check_graph,
)
from prototype.hires import add_hires, check_hires
from prototype.joycaption import EVAL, EVAL_SUBJECTS
from prototype.ladder_position import build
from prototype.sheet import photo_for

HIRES_DENOISE = 0.35  # F39

# Arm order is the render order and the column order on every page, numbered so
# `ls` sorts them the way they are read. The baseline is last because it is the
# reference the other three are read against, not a competitor among them.
ARMS = (
    ("1_descriptive", "descriptive"),
    ("2_straightforward", "straightforward"),
    ("3_booru", "booru"),
    ("4_baseline", "baseline"),
    # Added 2026-09-12 after the first session. `5_qwen` is the open router's
    # sheet -- Qwen3-8B few-shot plus `tagmap`, 0.482 -- with the operator's
    # corrections applied, standing in for N41's review step. `6_claude` is the
    # hand-routed sheet with its one corrected field, and it renders for ONE
    # subject: only `00003`'s gaze changed, and re-rendering four unchanged
    # prompts would spend a pod to reproduce images already on disk.
    ("5_qwen", "5_qwen"),
    ("6_claude", "6_claude"),
)

# The working resolution is computed from the photograph's own header, so the
# downscaled copy must not change the aspect ratio -- only the byte count.
UPLOAD_LONG_SIDE = 1600


def prepare(evaluation: Path) -> None:
    """Write downscaled copies of the five photographs for upload.

    1600 px on the long side, not the 1024 the captioner got: `working_resolution`
    puts the short side at 1024 and rounds both to a multiple of 64, so the
    upload must still be at least that after aspect is preserved. 1600 leaves
    headroom on every aspect ratio in the set and still turns 24 MB into ~1 MB.
    """
    from PIL import Image
    from PIL.Image import Resampling

    out = evaluation / "upload"
    out.mkdir(parents=True, exist_ok=True)
    for sid in EVAL_SUBJECTS:
        source = Path(photo_for(sid))
        if not source.exists():
            raise SystemExit(f"no photograph for {sid} (resolved to {source})")
        dest = out / f"{sid}{source.suffix}"
        with Image.open(source) as image:
            image = image.convert("RGB")
            scale = UPLOAD_LONG_SIDE / max(image.size)
            if scale < 1:
                size = (round(image.width * scale), round(image.height * scale))
                image = image.resize(size, Resampling.LANCZOS)
            image.save(dest, quality=95)
        before = source.stat().st_size / 2**20
        after = dest.stat().st_size / 2**20
        print(f"  {sid:22s} {before:6.1f} MB -> {after:5.2f} MB  {image.size}")


def upload_path(evaluation: Path, sid: str) -> Path:
    """Return the downscaled copy, or say that `--prepare` has not been run."""
    hits = sorted((evaluation / "upload").glob(f"{sid}.*"))
    if not hits:
        raise SystemExit(
            f"no downscaled copy for {sid}; run --prepare before the pod exists"
        )
    return hits[0]


def main() -> None:
    """Render the four prompt arms over the evaluation's five photographs."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--evaluation", type=Path, default=EVAL)
    p.add_argument("--subjects", nargs="*", default=list(EVAL_SUBJECTS))
    p.add_argument("--only", default=None, help="render one arm")
    p.add_argument("--prepare", action="store_true", help="downscale and exit")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if args.prepare:
        prepare(args.evaluation)
        return

    prompts = json.loads((args.evaluation / "prompts.json").read_text())
    missing = [s for s in args.subjects if s not in prompts]
    if missing:
        raise SystemExit(f"prompts.json has no entry for {missing}")

    base = json.loads(GRAPH.read_text())
    check_graph(base)
    client = None if args.dry_run else ComfyClient(args.server)
    out = args.evaluation / "renders"

    for sid in args.subjects:
        photo = upload_path(args.evaluation, sid)
        width, height = working_resolution(*image_dimensions(str(photo)))
        entry = prompts[sid]

        for arm, key in ARMS:
            if args.only and arm != args.only:
                continue
            dest = out / arm
            if (dest / f"{sid}.png").exists():
                print(f"skip {dest / f'{sid}.png'}")
                continue

            if key not in entry["arms"]:
                continue
            prompt = entry["arms"][key]["positive"]
            negative = entry["negative"]
            g = build(base, "A")
            g[POSITIVE]["inputs"]["text"] = prompt
            g[NEGATIVE]["inputs"]["text"] = negative
            g[LATENT]["inputs"].update(width=width, height=height)
            if INSTANTID in g:
                g[INSTANTID]["inputs"]["cn_strength"] = CN_STRENGTH
            g[SAMPLER]["inputs"].update(cfg=CFG, seed=SEED)

            tokens = entry["arms"][key]["estimated_clip_tokens"]
            print(f"\n=== {arm} / {sid} ===  {width}x{height} · ~{tokens} tokens")
            if client is None:
                print(f"    {prompt[:160]}...")
                continue

            # Injected before the hires stage exists: `inject` resolves
            # `find_node(class_type="ImageScale")` and the hires resize is a
            # second one -- see `hires.py`.
            inject(g, client.upload_image(str(photo)), str(photo))
            add_hires(g, width, height, HIRES_DENOISE)
            check_hires(g)

            dest.mkdir(parents=True, exist_ok=True)
            _render(client, g, dest / f"{sid}.png")
            (dest / f"{sid}.json").write_text(
                json.dumps(
                    {
                        "arm": arm,
                        "prompt_key": key,
                        "subject": sid,
                        "flow": "A",
                        "hires_denoise": HIRES_DENOISE,
                        "photo": str(photo),
                        "prompt": prompt,
                        "negative": negative,
                        "estimated_clip_tokens": tokens,
                        "seed": SEED,
                        "cfg": CFG,
                        "cn_strength": CN_STRENGTH,
                        "width": width,
                        "height": height,
                    },
                    indent=2,
                )
                + "\n"
            )
            print(f"    -> {dest / f'{sid}.png'}")


if __name__ == "__main__":
    main()
