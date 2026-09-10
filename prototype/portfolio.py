#!/usr/bin/env python3
"""PROTOTYPE — N29: the decided flow, on inputs no dial was ever tuned against.

**Every number in this project so far comes from ten synthetic portraits and six
baseline subjects that every dial was chosen on.** Two rounds of tuning either
generalise or were fitted to those faces, and nothing has been able to tell the
difference. These ten portraits are the first inputs the flow has never seen.

**It runs the flow as decided, not as a sweep.** Every dial here was settled by
measurement on at least two axes, and this run changes none of them:

    InstantID + OpenPose + the full criteria sheet, pose tags INCLUDED   F38
    cn_strength 0.8 · cfg 5                                             F25, F26
    hires pass at denoise 0.35                                          F39

A sweep would ask which setting is best. This asks whether the settings we have
survive contact with a face they were not chosen on -- so a variable moved here
would answer neither question.

**Flow `D` renders beside it**, unchanged, because the N-way identification test
needs both to say anything: `D`'s score is the clean one (it never touches the
recognizer InstantID optimises against) and `A`'s is read against it.

---

**Four attributes this set carries that the tuned-on ten did not**, which is what
makes it a real held-out test rather than more of the same:

    14_00   age            grey hair, visible lines, `mature female`
    10_01   dark skin      `dark skin, dark-skinned female`
    03_01   eyewear        `glasses`; 05_01 also
    19_01   male           `1boy, solo` -- first use since the field existed

**Three predictions, recorded before the render** so the run can falsify them:

1. **`14_00` loses the age.** `grey hair` is a *fantasy* hair colour on Danbooru
   with 529,760 posts -- it means silver-haired character, not older person. F26
   found an age drift no wording of the age tag fixed, and `wrinkled skin` at
   2,115 posts is probably under-learnt.
2. **`10_01`'s braids simplify.** `cornrows` is not in the vocabulary at all;
   `single braid` is the nearest canonical tag and means something else.
3. **The tight headshots render wider than the photograph.** `portrait` is a much
   rarer framing in the corpus than `upper body`.

If those land, the finding is about **vocabulary limits**, not about the flow.

**Pose geometry will be weak here and that is expected**: eight of the ten are
upper body or headshot, so DWPose has no legs to read and will drop most
keypoints. `15_01` and `16_01` are the only full-body subjects. Face likeness,
attribute adherence and the style axes all read normally.

    PYTHONPATH=. uv run python prototype/portfolio.py --dry-run
    PYTHONPATH=. uv run python prototype/portfolio.py --server http://127.0.0.1:8188
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

PHOTOS = Path("prototype/inputs/synthetic/portfolio")

# The id is the generating prompt slot; `MANIFEST.json` beside the photographs
# maps each back to the filename `synthetic_portraits` produced it under.
SUBJECTS = (
    "02_00",
    "03_01",
    "05_01",
    "06_01",
    "08_00",
    "10_01",
    "14_00",
    "15_01",
    "16_01",
    "19_01",
)

# F39: 0.35 for both flows. `A` changed from 0.50 on 2026-09-10 -- that value was
# set by F35 on style alone, before either identity instrument existed.
HIRES_DENOISE = 0.35

ARMS = {
    "1_a": ("A", "full", HIRES_DENOISE),
    "2_d": ("D", "full", HIRES_DENOISE),
}


def main() -> None:
    """Render both flows on the held-out portraits, at the settled dials."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--out", type=Path, default=render_dir("n29_portfolio"))
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

            print(f"\n=== {arm} / {sid} ===  flow {flow} · {width}x{height}")
            if client is None:
                continue

            # Injected before the hires stage exists: `inject` resolves
            # `find_node(class_type="ImageScale")` and the hires resize is a
            # second one -- see `hires.py`.
            inject(g, client.upload_image(str(photo)), str(photo))
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
