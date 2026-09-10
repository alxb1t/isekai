#!/usr/bin/env python3
"""PROTOTYPE — N18: where the quality ladder goes, and both kept flows side by side.

Two questions in one session, and they do not interfere because they are on
different axes -- the prompt transform is identical across flows, and the flow is
identical across transforms.

**Question 1: does the quality ladder belong at the front?** `notes/ILLUSTRIOUS.md` §6b
found the two sources disagree. The Illustrious community guide puts quality tags
last, which is what we do; **WAI's own page says "always start your positive prompt
with"** them. For this checkpoint the publisher outranks the guide, and F32's
lesson was that publisher-sourced corrections win where plausible additions lose.

**Question 2: does `newest` help when it is placed correctly?** N16's `3_schema`
arm tested it *after* the ladder and bundled with a `general` rating tag, and lost.
WAI writes it as the ladder's fourth element at the front. **That arm did not test
what WAI recommends**, so this gives it a second, correctly-formed attempt --
separated from the position change rather than bundled with it, which is the
mistake being corrected.

    1_baseline   the sheet as written -- quality tags last          (flow A)
    2_front      the same three tags moved to the front             (flow A)
    3_wai        moved, plus `newest` -- WAI's exact string          (flow A)
    4_d_baseline the sheet as written                                (flow D)
    5_d_wai      WAI's exact string at the front                     (flow D)

`2_front` vs `1_baseline` is position alone. `3_wai` vs `2_front` is `newest`
alone. `4`/`5` are the operator's requested comparison of the two kept flows, and
carry the winning transform into the prompt-only flow where prompt effects are
undamped by conditioning legs.

**Only the three quality tags move.** `anime screencap`, `detailed eyes` and
`soft lighting` are content and style tags that happen to sit beside them in our
sheets; WAI's instruction is about the quality string, so moving those too would
test something nobody recommended.

    PYTHONPATH=. uv run python prototype/ladder_position.py --server http://127.0.0.1:8188
"""

import argparse
import copy
import json
from pathlib import Path

from isekai.comfy_client import ComfyClient
from isekai.workflow import image_dimensions, working_resolution
from prototype.ablation import drop_instantid, drop_openpose, render
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

QUALITY = ("masterpiece", "best quality", "amazing quality")
WAI_EXTRA = "newest"  # WAI's published string is QUALITY + this, in that order


def move_quality_to_front(prompt: str, *, extra: str | None = None) -> str:
    """Return `prompt` with the quality tags lifted to the front, in WAI's order.

    Fails loudly if a quality tag is missing: an arm that silently changed nothing
    would be recorded as evidence that position does not matter, which is the
    opposite of what it would have shown.
    """
    tags = [t.strip() for t in prompt.split(",") if t.strip()]
    missing = [q for q in QUALITY if q not in tags]
    if missing:
        raise SystemExit(f"quality tags missing from prompt: {missing}")
    rest = [t for t in tags if t not in QUALITY]
    head = [*QUALITY, extra] if extra else list(QUALITY)
    return ", ".join([*head, *rest])


def arms(prompt: str) -> dict[str, tuple[str, str]]:
    """Return arm name -> (prompt, flow). One change between adjacent arms."""
    front = move_quality_to_front(prompt)
    wai = move_quality_to_front(prompt, extra=WAI_EXTRA)
    return {
        "1_baseline": (prompt, "A"),
        "2_front": (front, "A"),
        "3_wai": (wai, "A"),
        "4_d_baseline": (prompt, "D"),
        "5_d_wai": (wai, "D"),
    }


def build(base: dict, flow: str) -> dict:
    """Return the graph for a flow: `A` keeps both legs, `D` keeps neither."""
    g = copy.deepcopy(base)
    if flow == "D":
        drop_instantid(g)
        drop_openpose(g)
    return g


def main() -> None:
    """Render every arm on every subject, at one seed."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--out", type=Path, default=render_dir("n18_position"))
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

        for name, (positive, flow) in arms(prompt).items():
            if args.only and name != args.only:
                continue
            dest = args.out / name / sid
            if (dest / "0.png").exists():
                print(f"skip {dest}")
                continue

            g = build(base, flow)
            g[POSITIVE]["inputs"]["text"] = positive
            g[NEGATIVE]["inputs"]["text"] = negative
            g[LATENT]["inputs"].update(width=width, height=height)
            g[SAMPLER]["inputs"].update(cfg=CFG, seed=SEED)
            if INSTANTID in g:
                g[INSTANTID]["inputs"]["cn_strength"] = CN_STRENGTH

            print(f"\n=== {name} / {sid} ===  flow {flow}")
            if positive != prompt:
                print(f"    {positive[:110]}...")
            if client is None:
                continue
            render(client, g, photo, dest)
            (dest / "arm.json").write_text(
                json.dumps(
                    {
                        "arm": name,
                        "flow": flow,
                        "subject": sid,
                        "seed": SEED,
                        "positive": positive,
                        "negative": negative,
                        "cfg": CFG,
                        "pod_image": args.pod_image,
                    },
                    indent=2,
                )
                + "\n"
            )


if __name__ == "__main__":
    main()
