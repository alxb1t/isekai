#!/usr/bin/env python3
"""PROTOTYPE — N27's last item: the decided flow on photographs of real people.

**Every identity number in this project is measured on generated faces.** The six
baselines, round 2's ten portraits, N29's held-out ten — all synthetic: evenly
lit, frontal, one face, no lens. **The product's input is a photograph of a real
person**, and whether the instruments and the flow hold up on one has never been
tested.

That is N27's fourth sub-item, and until 2026-09-11 it was **blocked on data**
rather than on work: the previous real subject was withdrawn and the set was down
to two, where the identification test's chance floor is 50% and no result means
anything.

**Seventeen photographs, ~16 distinct people**, from a wallpaper site. That puts
the identification floor at **1/16 = 6.25%** — a stronger bar than anything this
project has run.

---

**The flow is the decided one and nothing is swept.** Every dial was settled by
measurement on at least two axes; this run changes none of them:

    InstantID + OpenPose + the full criteria sheet, pose tags INCLUDED   F38
    cn_strength 0.8 · cfg 5                                             F25, F26
    hires pass at denoise 0.35                                          F39

**Flow `D` renders beside it**, unchanged, for two reasons and neither is that `D`
is the product. First, `D` is the **clean half of the identification test** — it
never touches the recognizer InstantID optimises against, so `A` is only readable
against it. Second, and specific to this set:

> **`D` is the contamination check.** These are real people and some may be
> recognisable to the base model. A memorised face would render *from the sheet
> alone*, so a subject where `D` scores unusually well is a contamination signal
> in the data rather than a guess about who is famous.

---

**Two limits of this set, recorded before the run rather than discovered after:**

- **Every photograph is professionally shot** — studio or well-lit outdoor, posed,
  retouched. That is closer to the synthetic sets than to a phone snapshot, so
  this tests *real faces* and still does not test the product's actual input. A
  phone-camera set is wanted and does not exist yet.
- **`male_full_height` may itself be AI-generated.** Sourced from an image search
  rather than the wallpaper site, and it has the marks — smooth skin, generic
  gradient, a much smaller source file than everything else. Kept deliberately and
  flagged here so a reader does not count it as evidence about real photographs.

**Two subjects will score badly on identity for reasons that are not the flow's:**
`ful_height_1` wears **sunglasses**, and the eyes are the strongest signal an
ArcFace recognizer has; and it is the **same person as `face_4`**, so an
identification "miss" that ranks the other one first is not really a miss. See
`pose_geometry.py` and `face_likeness.py` for how the pair is handled.

**A prediction, recorded first.** Nine of the seventeen sheets say `brown hair`
and fourteen say `standing`. These descriptions are **less distinctive than N29's
portfolio set**, where `D` scored 4/10 by being matched on demographics rather
than faces. **`D` should therefore score worse here than it did there** — and if
it does not, the reason is worth finding.

**Everything about these people is gitignored** — photographs, sheets, drafts and
renders (design.md D14).

    PYTHONPATH=. uv run python prototype/real_photo.py --dry-run
    PYTHONPATH=. uv run python prototype/real_photo.py --server http://127.0.0.1:8188
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
from prototype.sheet import photo_for

PHOTOS = Path("prototype/inputs/real")

# subject id -> its photograph's filename. Unlike the withdrawn set, whose names
# were camera-assigned and underivable, these are named for what they depict, so
# the id IS the stem and only the extension varies.
SUBJECTS = {
    "cowboy_shot_1": "cowboy_shot_1.jpeg",
    "cowboy_shot_2": "cowboy_shot_2.jpg",
    "cowboy_shot_3": "cowboy_shot_3.jpg",
    "cowboy_shot_4": "cowboy_shot_4.jpeg",
    "cowboy_shot_5": "cowboy_shot_5.jpeg",
    "face_1": "face_1.jpeg",
    "face_2": "face_2.jpeg",
    "face_3": "face_3.jpeg",
    "face_4": "face_4.jpeg",
    "face_5": "face_5.jpeg",
    "ful_height_1": "ful_height_1.jpeg",
    "full_height_2": "full_height_2.jpeg",
    "full_height_3": "full_height_3.jpeg",
    "full_height_4": "full_height_4.jpeg",
    "male_cowboy_shot_1": "male_cowboy_shot_1.jpg",
    "male_cowboy_shot_2": "male_cowboy_shot_2.jpg",
    "male_full_height": "male_full_height.jpg",
}

# `face_4` and `ful_height_1` are the same person. The identification test has no
# way to know that, so a render of one ranking the other's photograph first would
# be scored a miss when it is arguably a hit. Recorded here and handled in the
# scorer rather than by dropping a subject: the pair is the only
# same-person-across-photographs case this project has.
SAME_PERSON = (("face_4", "ful_height_1"),)

HIRES_DENOISE = 0.35  # F39

ARMS = {
    "1_a": ("A", "full"),
    "2_d": ("D", "full"),
}


def main() -> None:
    """Render both flows on the real photographs, at the settled dials."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--out", type=Path, default=render_dir("n30_real"))
    p.add_argument("--subjects", nargs="*", default=list(SUBJECTS))
    p.add_argument("--only", default=None, help="render one arm")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    base = json.loads(GRAPH.read_text())
    check_graph(base)
    client = None if args.dry_run else ComfyClient(args.server)

    for sid in args.subjects:
        photo = Path(photo_for(sid))
        sheet = sheet_path(sid)
        if not photo.exists():
            raise SystemExit(f"{photo} is missing")
        if not sheet.exists():
            raise SystemExit(f"{sheet} is missing")
        width, height = working_resolution(*image_dimensions(str(photo)))

        for arm, (flow, variant) in ARMS.items():
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
            add_hires(g, width, height, HIRES_DENOISE)
            check_hires(g)
            t = g[RESIZE]["inputs"]
            print(f"    hires -> {t['width']}x{t['height']} at denoise {HIRES_DENOISE}")

            dest.mkdir(parents=True, exist_ok=True)
            _render(client, g, dest / "0.png")
            (dest / "arm.json").write_text(
                json.dumps(
                    {
                        "arm": arm,
                        "subject": sid,
                        "flow": flow,
                        "prompt_variant": variant,
                        "hires_denoise": HIRES_DENOISE,
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
