#!/usr/bin/env python3
"""PROTOTYPE — N16: the four prompt questions ILLUSTRIOUS.md raised, one at a time.

The research note turned up four changes the base's own training argues for, and
none of them had been tried. Bundling them was the operator's first proposal and
the risk is the one N8 already paid for: **two of these could cancel the other
two, and a disappointing render would not say which.** So each is an arm, and a
fifth arm stacks them all -- the render he actually asked to see, with the
attribution kept beside it.

    1_baseline    canonical sheets, skin tags corrected, `worst detail` gone
    2_negative    + the long Illustrious negative
    3_schema      + `rating` and a `year modifier` -- two trained caption slots
    4_underscore  every tag underscored
    5_all         every change stacked

**The baseline is not an arm.** The skin correction and the `worst detail`
removal are definitional -- `pale skin` means *bleached* per the Danbooru wiki,
and `worst detail` is on no ladder and in no vocabulary -- so they are fixes
carried by every arm rather than hypotheses under test.

**Why `rating` and `year modifier` are one arm and not two.** They are the two
slots our prompts leave empty in the paper's trained caption schema, and neither
has ever been filled here. Testing "does filling the schema help" first is worth
more than splitting a question that has never had a yes.

    PYTHONPATH=. uv run python prototype/prompt_arms.py --server http://127.0.0.1:8188
"""

import argparse
import copy
import json
import re
from pathlib import Path

from isekai.comfy_client import ComfyClient
from isekai.workflow import image_dimensions, working_resolution
from prototype.ablation import render
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
from prototype.paths import render_dir, sheet_path

# ILLUSTRIOUS.md §5. Built from the trained ladder's bottom two rungs
# (`worst quality`, `bad quality`) and two trained year modifiers (`old`,
# `oldest`), rather than from adjectives the model never learned.
LONG_NEGATIVE = (
    "lowres, worst quality, bad quality, bad anatomy, sketch, jpeg artifacts, "
    "signature, watermark, artist name, old, oldest, censor, nsfw"
)
# ILLUSTRIOUS.md §2. `general` is the rating every one of these sheets is;
# `newest` is the paper's most recent trained tier (~2023), chosen because modern
# anime illustration is flatter than older cel work and posterisation is the axis
# still short of the bar.
RATING = "general"
YEAR = "newest"

# Danbooru stores `long_hair`; our sheets are written with spaces. Only the
# multi-word tags change, and the quality ladder is left alone -- it is not
# Danbooru vocabulary and underscoring it would test two things at once.
LADDER_TAGS = {
    "anime screencap",
    "detailed eyes",
    "soft lighting",
    "masterpiece",
    "best quality",
    "amazing quality",
}


def underscored(prompt: str) -> str:
    """Return the prompt with every Danbooru tag in its stored spelling."""
    out = []
    for tag in (t.strip() for t in prompt.split(",")):
        out.append(tag if tag in LADDER_TAGS else tag.replace(" ", "_"))
    return ", ".join(out)


def with_schema(prompt: str) -> str:
    """Insert the rating after the count tags, and the year modifier at the end.

    Both go where the paper's caption schema puts them: `person count ||| ... |||
    rating ||| general tags ||| ... ||| year modifier`. Placing the year anywhere
    but last would be testing our ordering rather than the tag.
    """
    tags = [t.strip() for t in prompt.split(",")]
    # after `1girl, solo`, which is the schema's first slot
    tags.insert(2, RATING)
    return ", ".join([*tags, YEAR])


def arms(prompt: str, negative: str) -> dict[str, tuple[str, str]]:
    """Return arm name -> (positive, negative). One change each from the baseline."""
    return {
        "1_baseline": (prompt, negative),
        "2_negative": (prompt, LONG_NEGATIVE),
        "3_schema": (with_schema(prompt), negative),
        "4_underscore": (underscored(prompt), negative),
        "5_all": (underscored(with_schema(prompt)), LONG_NEGATIVE),
    }


def main() -> None:
    """Render every arm on every subject, at one seed and flow A's dials."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--out", type=Path, default=render_dir("n16_prompt"))
    p.add_argument("--subjects", nargs="*", default=list(SUGGESTED))
    p.add_argument("--only", default=None)
    p.add_argument("--pod-image", default=None)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    base = json.loads(GRAPH.read_text())
    check_graph(base)
    client = None if args.dry_run else ComfyClient(args.server)

    for sid in args.subjects:
        photo = PHOTOS / f"synthetic_portrait_{sid}_.png"
        prompt, negative = prompts_of(sheet_path(sid))
        width, height = working_resolution(*image_dimensions(str(photo)))

        for name, (positive, neg) in arms(prompt, negative).items():
            if args.only and name != args.only:
                continue
            dest = args.out / name / sid
            if (dest / "0.png").exists():
                print(f"skip {dest}")
                continue
            g = copy.deepcopy(base)
            g[POSITIVE]["inputs"]["text"] = positive
            g[NEGATIVE]["inputs"]["text"] = neg
            g[LATENT]["inputs"].update(width=width, height=height)
            g[INSTANTID]["inputs"]["cn_strength"] = CN_STRENGTH
            g[SAMPLER]["inputs"].update(cfg=CFG, seed=SEED)

            words = len(re.sub(r"[,_]", " ", positive).split())
            print(f"\n=== {name} / {sid} ===  ~{round(words * 1.35)} tokens")
            if name != "1_baseline":
                print(f"    + {positive}")
                if neg != negative:
                    print(f"    - {neg}")
            if client is None:
                continue
            render(client, g, photo, dest)
            (dest / "arm.json").write_text(
                json.dumps(
                    {
                        "arm": name,
                        "subject": sid,
                        "seed": SEED,
                        "positive": positive,
                        "negative": neg,
                        "cn_strength": CN_STRENGTH,
                        "cfg": CFG,
                        "pod_image": args.pod_image,
                    },
                    indent=2,
                )
                + "\n"
            )


if __name__ == "__main__":
    main()
