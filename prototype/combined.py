#!/usr/bin/env python3
"""PROTOTYPE — N8: the operator's two picks, together, with the sheets in booru tags.

N6 ran seven arms one change at a time and the operator chose two of them:
`cfg 5` and `cn_strength 0.8`. **They have never been rendered together** — every
N6 arm is one change from its control, so the combination is a render and not an
inference. At the same time the sheets moved from prose to Danbooru vocabulary and
gained a `gaze` field, because N6 showed the base fills in an untagged criterion
rather than leaving it alone (`notes/CRITERIA.md` §2).

**This run deliberately changes two things at once**, which every ladder in this
repository has refused to do. It is the operator's call and the reason is sound:
both changes are already argued, and the question here is *does the result hold on
six subjects*, not *which of the two did it*. The cost is stated rather than
hidden — **if the output disappoints, this run cannot say which half is at fault**,
and the separated version is `--arm dials` against `--arm tags`.

Six subjects, one seed, so it is comparable to `renders/n3_fromnoise/` render for
render.

    PYTHONPATH=. uv run python prototype/combined.py --server http://127.0.0.1:8188
"""

import argparse
import copy
import json
from pathlib import Path

from isekai.comfy_client import ComfyClient
from isekai.pipeline import run
from isekai.workflow import image_dimensions, working_resolution
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
from prototype.paths import sheet_path

CN_STRENGTH = 0.8  # N6 `4_cn_0.8` — held linework, best posterisation of any dial arm
CFG = 5  # N6 `5_cfg_5` — highest posterisation of all seven arms


def main() -> None:
    """Render the combined configuration on every subject, at one seed."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--out", type=Path, default=Path("prototype/renders/n8_combined"))
    p.add_argument("--subjects", nargs="*", default=list(SUGGESTED))
    p.add_argument("--pod-image", default=None)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    base = json.loads(GRAPH.read_text())
    check_graph(base)
    client = None if args.dry_run else ComfyClient(args.server)

    for sid in args.subjects:
        sheet = sheet_path(sid)
        photo = PHOTOS / f"synthetic_portrait_{sid}_.png"
        prompt, negative = prompts_of(sheet)
        width, height = working_resolution(*image_dimensions(str(photo)))

        graph = copy.deepcopy(base)
        graph[POSITIVE]["inputs"]["text"] = prompt
        graph[NEGATIVE]["inputs"]["text"] = negative
        graph[LATENT]["inputs"]["width"] = width
        graph[LATENT]["inputs"]["height"] = height
        graph[INSTANTID]["inputs"]["cn_strength"] = CN_STRENGTH
        graph[SAMPLER]["inputs"]["cfg"] = CFG

        dest = args.out / sid
        if (dest / "0.png").exists():
            print(f"skip {dest}")
            continue
        print(f"\n=== {sid} {'=' * (60 - len(sid))}")
        print(f"    {width}x{height}  cn {CN_STRENGTH}  cfg {CFG}")
        print(f"    + {prompt}")
        if client is None:
            continue
        run(
            client,
            graph,
            str(photo),
            dest,
            variations=1,
            seed=SEED,
            fixed_dials=True,
            pod_image=args.pod_image,
        )
        (dest / "run_notes.json").write_text(
            json.dumps(
                {
                    "subject": sid,
                    "seed": SEED,
                    "cn_strength": CN_STRENGTH,
                    "cfg": CFG,
                    "ip_weight": graph[INSTANTID]["inputs"]["ip_weight"],
                    "prompt": prompt,
                    "negative": negative,
                    "sheets": "booru vocabulary, gaze field added 2026-09-08",
                },
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    main()
