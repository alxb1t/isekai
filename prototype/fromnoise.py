#!/usr/bin/env python3
"""PROTOTYPE — N3: the from-noise flow, one render per criteria sheet.

Round 1 rejected both candidate flows. `notile-d045` is soft, and `SUMMARY.md`
argues the softness is architectural: `i2i` seeds the latent from the photograph
at `denoise < 1`, so the sampler reconciles a photographic latent with an anime
prior and returns an interpolation. This removes the photograph from the latent
and asks whether the softness goes with it.

What still conditions the render: **InstantID** for the face, **OpenPose** for the
skeleton, and a **hand-written prompt** assembled from the subject's criteria
sheet. Tile and lineart are dropped -- both condition on the photograph's
*appearance*, which is the thing being removed. The graph is
`prototype/styles/fromnoise-v1.json`; `notes/CRITERIA.md` §7 records the four edits.

The photograph is still loaded and still scaled, because InstantID and DWPose
both read it, and because `ImageScale` is what fixes the canvas pose PCK is
measured on. The one thing `inject` does not know about this graph is the empty
latent's size, so it is set here, from the same derivation, and asserted equal.

Two bars, both stated in `notes/CRITERIA.md` §4 before this was ever run: median
linework at or above the photograph's own, and 5 of 6 scored criteria surviving
with pose and hair silhouette mandatory.

    PYTHONPATH=. uv run python prototype/fromnoise.py --server http://127.0.0.1:8188
"""

import argparse
import json
import re
from pathlib import Path

from isekai.comfy_client import ComfyClient
from isekai.pipeline import run
from isekai.workflow import image_dimensions, working_resolution
from prototype.paths import render_dir, sheet_path

GRAPH = Path("prototype/styles/fromnoise-v1.json")
PHOTOS = Path("inputs/synthetic")

POSITIVE = "3"  # CLIPTextEncode, the positive
NEGATIVE = "4"  # CLIPTextEncode, the negative
LATENT = "9"  # EmptyLatentImage, where VAEEncode used to be
SCALE = "22"  # ImageScale, the working resolution

# The six of ten that carry the most between them: three framings, five hair
# silhouettes, three phenotypes, the freckles, the densest accessories, the
# age-band case, three hard poses -- and one small face. `sheets/README.md`
# argues the selection.
SUGGESTED = ("00003", "00014", "00033", "00050", "00059", "00072")

SEED = 20260908

_BLOCK = r"{}\s*\n(?:.*?\n)??\s*```\n(.+?)\n```"
_POSITIVE_RE = re.compile(
    _BLOCK.format("### The positive prompt, assembled"), re.DOTALL
)
_NEGATIVE_RE = re.compile(_BLOCK.format("### The negative prompt"), re.DOTALL)
# The ablation block: the same table with the pose field omitted. Its heading
# carries prose before the fence, so it needs its own pattern rather than
# `_BLOCK`.
_NO_POSE_RE = re.compile(
    r"### The positive prompt — pose tags dropped\n.*?```\n(.+?)\n```", re.DOTALL
)
POSITIVE_VARIANTS = ("full", "no_pose")


def prompts_of(sheet: Path, variant: str = "full") -> tuple[str, str]:
    """Return the positive and negative prompts a criteria sheet declares.

    `variant` picks which positive block: `full` is every field, `no_pose` is the
    same table with the pose field omitted -- **generated from one table** by
    `sheet.py build`, so a correction to the table reaches both and neither can
    drift from the other. A sheet written before the ablation block existed has
    only `full`, and asking it for `no_pose` names the sheet in the error rather
    than silently falling back to a prompt that answers a different question.

    Read out of the sheet rather than rebuilt from its table, because the sheet
    is the artifact the operator reviews and corrects -- a second assembly path
    here would mean the reviewed text and the rendered text could differ without
    anything saying so.

    **The negative is per sheet, and that is deliberate.** It is the shipped one
    for nine of the ten, which keeps them comparable to round 1's baselines; the
    tenth drops `nsfw` because its wardrobe fights the token, and the sheet says
    so beside the text. A single negative in this file would have made that
    change global and silent.
    """
    if variant not in POSITIVE_VARIANTS:
        raise SystemExit(f"unknown prompt variant {variant!r}")
    text = sheet.read_text()
    pattern = _POSITIVE_RE if variant == "full" else _NO_POSE_RE
    positive = pattern.search(text)
    negative = _NEGATIVE_RE.search(text)
    if positive is None:
        raise SystemExit(f"{sheet}: no `{variant}` positive prompt block")
    if negative is None:
        raise SystemExit(f"{sheet}: no negative prompt block")
    return positive.group(1).strip(), negative.group(1).strip()


def check_graph(graph: dict) -> None:
    """Fail before the pod is billed if the four edits are not what is on disk.

    A from-noise graph is one wrong link away from being an img2img graph that
    merely ignores its latent, and the difference is invisible in the render's
    filename. Checked here rather than trusted, because the cost of finding out
    afterwards is a session.
    """
    if graph[LATENT]["class_type"] != "EmptyLatentImage":
        raise SystemExit(f"node {LATENT} is not the empty latent")
    if any(n["class_type"] == "VAEEncode" for n in graph.values()):
        raise SystemExit("a VAEEncode survives: the photograph is still in the latent")
    if graph["10"]["inputs"]["denoise"] != 1.0:
        raise SystemExit("denoise is not 1.0")
    if graph["10"]["inputs"]["latent_image"] != [LATENT, 0]:
        raise SystemExit("the sampler does not read the empty latent")
    legs = [k for k, n in graph.items() if n["class_type"] == "ControlNetApplyAdvanced"]
    if legs != ["18"]:
        raise SystemExit(f"expected OpenPose alone, found legs {legs}")
    # Both conditioners still read the scaled photograph -- that is the whole of
    # what survives of it, and a from-noise graph that dropped them too would be
    # text-to-image with extra steps.
    if graph["8"]["inputs"]["image"] != [SCALE, 0]:
        raise SystemExit("InstantID does not read the scaled photograph")
    if graph["16"]["inputs"]["image"] != [SCALE, 0]:
        raise SystemExit("DWPose does not read the scaled photograph")


def main() -> None:
    """Render one from-noise image per criteria sheet, on one server."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--out", type=Path, default=render_dir("n3_fromnoise"))
    p.add_argument(
        "--subjects",
        nargs="*",
        default=list(SUGGESTED),
        help="sheet ids to render; defaults to the suggested five",
    )
    p.add_argument("--pod-image", default=None)
    args = p.parse_args()

    client = ComfyClient(args.server)
    check_graph(json.loads(GRAPH.read_text()))

    for sid in args.subjects:
        sheet = sheet_path(sid)
        photo = PHOTOS / f"synthetic_portrait_{sid}_.png"
        if not sheet.exists() or not photo.exists():
            raise SystemExit(f"{sid}: sheet or photo missing")

        graph = json.loads(GRAPH.read_text())
        prompt, negative = prompts_of(sheet)
        graph[POSITIVE]["inputs"]["text"] = prompt
        graph[NEGATIVE]["inputs"]["text"] = negative

        # `inject` writes ImageScale from the photo's header; the empty latent has
        # to agree with it or the render and the photograph are not one canvas,
        # and pose PCK is measured across two grids that never matched.
        width, height = working_resolution(*image_dimensions(str(photo)))
        graph[LATENT]["inputs"]["width"] = width
        graph[LATENT]["inputs"]["height"] = height

        print(f"\n=== {sid} {'=' * (60 - len(sid))}")
        print(f"    {width}x{height}")
        print(f"    + {prompt}")
        print(f"    - {negative}")

        run(
            client,
            graph,
            str(photo),
            args.out / sid,
            variations=1,
            seed=SEED,
            fixed_dials=True,  # the prompt is the only thing that differs
            pod_image=args.pod_image,
        )

        (args.out / sid / "sheet.json").write_text(
            json.dumps(
                {
                    "subject": sid,
                    "photo": str(photo),
                    "sheet": str(sheet),
                    "prompt": prompt,
                    "negative": negative,
                    "seed": SEED,
                    "canvas": [width, height],
                    "graph": str(GRAPH),
                },
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    main()
