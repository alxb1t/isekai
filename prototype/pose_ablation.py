#!/usr/bin/env python3
"""PROTOTYPE — N25: does flow `A` need pose tags, or does OpenPose carry the body.

Flow `A` places the body **twice**: a DWPose skeleton conditions the render, and
the criteria sheet's `pose` field says the same thing in Danbooru tags. Nobody has
removed one and looked, and two facts make it worth the render:

- **Pose is the reader's weakest field on both real and synthetic photographs**
  (0.57 / 0.58) -- the only field indifferent to input type, which points at a
  vocabulary limit rather than a reading limit.
- **F27 measured that the legs compete with the tags.** Dropping InstantID moved
  posterisation 0.358 -> 0.518. A tag the skeleton already carries is not free; it
  is paid for in style.

**The variable is the `pose` field and nothing else.**

    1_a_control    A   pose tags + OpenPose    the reference
    2_a_no_pose    A   OpenPose alone          the question
    3_d            D   pose tags alone         no skeleton exists in `D`
    4_a_hires_035  A   + the hires pass        N28, paired against 1_a_control

**`framing` stays in every arm, deliberately.** `full body` is on all ten sheets,
so it varies with nothing and can explain nothing -- it is a control, not a
confound. Keeping it also sharpens the failure: with the crop still stated, a bad
render is unambiguously *a full-body figure in the wrong pose*. Drop both and a
bust comes back with no way to tell whether the crop tag or the skeleton was what
failed. Whether DWPose carries the crop is a real question and a different one;
it gets a cleaner answer after this arm resolves.

**`D` is a reference, not an arm.** It has no skeleton, so removing its pose tags
is a guaranteed loss that measures nothing. It renders once, unchanged, to show
what "no pose mechanism at all" looks like beside the two that have one.

**The tags are dropped from the PROMPT, never from the sheet.** The sheet is the
evaluator's ground truth: delete field 13 and the scoreboard no longer knows what
the pose was, so *did the skeleton carry it* becomes unanswerable at the moment it
is asked. `sheet.py build` writes both prompt blocks from the one table, and
`prompts_of(sheet, variant)` picks between them.

**Ten deliberately varied poses**, `prototype/inputs/synthetic/pose/`, and their
filenames are the ground truth a later pose-geometry evaluation needs. Standing,
arms up, arms wide, kneeling, sitting cross-legged, walking, running, and a
turned back. Three subjects are men, which is why `count` became a sheet field.

    PYTHONPATH=. uv run python prototype/pose_ablation.py --dry-run
    PYTHONPATH=. uv run python prototype/pose_ablation.py --server http://127.0.0.1:8188
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
    prompts_of,
)
from prototype.hires import RESIZE, add_hires, check_hires
from prototype.ladder_position import build
from prototype.paths import render_dir, sheet_path

PHOTOS = Path("prototype/inputs/synthetic/pose")

# Named for the pose, because the name is the label a pose-geometry evaluation
# will score against -- there is no separate annotation to keep in sync.
SUBJECTS = (
    "arms_on_hips",
    "arms_on_hips_legs_wide",
    "arms_up",
    "arms_up_legs_crossed",
    "arms_wide",
    "legs_crossed",
    "running",
    "sitting_on_knees",
    "standing_turn",
    "walking",
)

# arm -> (flow, which positive prompt block, hires denoise or None)
ARMS = {
    "1_a_control": ("A", "full", None),
    "2_a_no_pose": ("A", "no_pose", None),
    "3_d": ("D", "full", None),
    # N28, added 2026-09-10 after the first three had rendered. `1_a_control` is
    # its paired control -- same seed, same prompt, same dials, already on disk --
    # so this arm is the only thing that needs a pod, and the pair differs by the
    # second sampler pass and nothing else.
    "4_a_hires_035": ("A", "full", 0.35),
}

# **0.35, not the 0.50 the settled configuration carries for flow `A`.** That
# value was chosen by F35 on *style alone*, before either identity instrument
# existed, and three axes now point the other way: linework +43% against +25%
# (F35), face identification 5/6 against 4/6 (F37), and pose angle error tying
# no-hires rather than losing a degree (F38's scorer, run on F35's own renders).
# 0.50 wins posterisation by 0.014 and loses everything else.

# **N28's hypothesis, and it is the only one the existing renders could not
# settle.** Scoring F35's six subjects on the pose instrument showed hires costing
# nothing on five of them and a great deal on ONE -- `00050`, the hardest pose in
# that set, 38.7 degrees to 57.0. Hires did not break it; it deepened a failure
# that was already there. Whether that generalises needs hard poses, and these ten
# are hard poses with their labels in their filenames.


def main() -> None:
    """Render the pose ablation: two flow-`A` arms and the flow-`D` reference."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--out", type=Path, default=render_dir("n25_pose"))
    p.add_argument("--subjects", nargs="*", default=list(SUBJECTS))
    p.add_argument("--only", default=None, help="render one arm")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    base = json.loads(GRAPH.read_text())
    check_graph(base)
    client = None if args.dry_run else ComfyClient(args.server)

    for sid in args.subjects:
        photo = PHOTOS / f"{sid}.png"
        sheet = sheet_path(sid)
        if not photo.exists():
            raise SystemExit(f"{photo} is missing")
        if not sheet.exists():
            raise SystemExit(f"{sheet} is missing")
        width, height = working_resolution(*image_dimensions(str(photo)))

        for arm, (flow, variant, hires) in ARMS.items():
            if args.only and arm != args.only:
                continue
            dest = args.out / arm / sid
            if (dest / "0.png").exists():
                print(f"skip {dest}")
                continue

            prompt, negative = prompts_of(sheet, variant)
            g = build(base, flow)
            g[POSITIVE]["inputs"]["text"] = prompt
            g[NEGATIVE]["inputs"]["text"] = negative
            g[LATENT]["inputs"].update(width=width, height=height)
            if INSTANTID in g:
                g[INSTANTID]["inputs"]["cn_strength"] = CN_STRENGTH
            g[SAMPLER]["inputs"].update(cfg=CFG, seed=SEED)

            label = f"hires {hires}" if hires else "no hires"
            print(
                f"\n=== {arm} / {sid} ===  "
                f"flow {flow} · {variant} · {label} · {width}x{height}"
            )
            if client is None:
                continue

            # Injected before the hires stage exists: `inject` resolves
            # `find_node(class_type="ImageScale")` and the hires resize is a
            # second one -- see `hires.py`.
            inject(g, client.upload_image(str(photo)), str(photo))
            if hires is not None:
                add_hires(g, width, height, hires)
                check_hires(g)
                t = g[RESIZE]["inputs"]
                print(f"    hires -> {t['width']}x{t['height']} at denoise {hires}")
            dest.mkdir(parents=True, exist_ok=True)
            _render(client, g, dest / "0.png")
            (dest / "arm.json").write_text(
                json.dumps(
                    {
                        "arm": arm,
                        "subject": sid,
                        "flow": flow,
                        "prompt_variant": variant,
                        "hires_denoise": hires,
                        "photo": str(photo),
                        "sheet": str(sheet),
                        "prompt": prompt,
                        "negative": negative,
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
            print(f"    -> {dest / '0.png'}")


if __name__ == "__main__":
    main()
