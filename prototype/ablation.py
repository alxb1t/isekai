#!/usr/bin/env python3
"""PROTOTYPE — N9: do the conditioning legs fight the booru tags, or carry them.

**The operator's hypothesis, 2026-09-08.** N8 showed that Danbooru vocabulary is a
far stronger lever than prose -- `00050`'s pose and `00003`'s gaze both came right
from tags alone -- and he asked whether InstantID and OpenPose are now *competing*
with the prompt rather than helping it.

The prediction, written before the render:

    if the legs FIGHT the tags   ->  dropping them IMPROVES adherence:
                                     pose, clothes and gaze land closer to the sheet
    if the legs CARRY            ->  dropping them loses the pose and the face,
                                     and the tags do not recover it

One of those happens, and the ablation says which.

**What `4_prompt_only` would mean if it wins.** The photograph is then never read
at render time -- only once, by a human, to write the sheet. `photo -> anime`
becomes `photo -> sheet -> anime`, which is a different product and a simpler one.
What it gives up is the one thing booru has no vocabulary for: **a particular
face.** Two people with identical tags get identical faces. That is the trade the
render is being asked about.

Arm `1_full` also does double duty: against `renders/n8_combined/` it is the same
dials and the same graph with only the **enriched sheets** changed, so it reads as
the operator's six prompt improvements measured alone.

    PYTHONPATH=. uv run python prototype/ablation.py --server http://127.0.0.1:8188
"""

import argparse
import copy
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
from prototype.paths import render_dir, sheet_path

OPENPOSE = "18"  # ControlNetApplyAdvanced, the DWPose leg
DWPOSE = "16"  # DWPreprocessor
POSE_LOADER = "17"


def drop_instantid(graph: dict) -> None:
    """Route the text conditioning past InstantID, and cut its model patch.

    Node 8 does two things at once -- it patches the MODEL and edits the
    conditioning -- so removing it means re-pointing *both*: the sampler back to
    the raw checkpoint, and whatever consumed its conditioning back to the text
    encoders. Deleting the node without doing both leaves a graph that still
    submits and quietly keeps half the adapter.
    """
    consumer = OPENPOSE if OPENPOSE in graph else SAMPLER
    graph[consumer]["inputs"]["positive"] = [POSITIVE, 0]
    graph[consumer]["inputs"]["negative"] = [NEGATIVE, 0]
    graph[SAMPLER]["inputs"]["model"] = ["1", 0]
    for node in (INSTANTID, "5", "6", "7"):
        graph.pop(node, None)


def drop_openpose(graph: dict) -> None:
    """Route the conditioning past the DWPose leg and drop its preprocessor."""
    source = graph[OPENPOSE]["inputs"]
    graph[SAMPLER]["inputs"]["positive"] = source["positive"]
    graph[SAMPLER]["inputs"]["negative"] = source["negative"]
    for node in (OPENPOSE, DWPOSE, POSE_LOADER):
        graph.pop(node, None)


def arms(graph: dict) -> dict[str, dict]:
    """Return arm name -> graph. Each is one leg removed, never a dial changed."""
    out = {"1_full": copy.deepcopy(graph)}

    g = copy.deepcopy(graph)
    drop_instantid(g)
    out["2_no_instantid"] = g

    g = copy.deepcopy(graph)
    drop_openpose(g)
    out["3_no_openpose"] = g

    # Both legs gone: nothing reads the photograph, so this render is reproducible
    # from the sheet alone. `LoadImage` and `ImageScale` stay only because the
    # latent's size is still derived from the photo's own header, and because
    # keeping them makes this arm one deletion from the others rather than a
    # different graph.
    g = copy.deepcopy(graph)
    drop_instantid(g)
    drop_openpose(g)
    out["4_prompt_only"] = g
    return out


def render(client: ComfyClient, graph: dict, photo: Path, dest: Path) -> None:
    """Submit one graph for one photo and save the image it returns.

    `pipeline.run` cannot drive these arms: its provenance record calls
    `find_node(class_type="ApplyInstantIDAdvanced")`, which is `find_node`'s
    exactly-one contract against a graph three of the four arms have deliberately
    removed that node from. Rather than weaken that contract for a prototype --
    the seam is load-bearing in the shipped path -- this does the two things `run`
    does that matter here, and `arm.json` beside the render carries the provenance
    `run.json` would have.
    """
    dest.mkdir(parents=True, exist_ok=True)
    graph = copy.deepcopy(graph)
    inject(graph, client.upload_image(str(photo)), str(photo))
    _render(client, graph, dest / "0.png")


def main() -> None:
    """Render every arm on every subject, at one seed and one set of dials."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--out", type=Path, default=render_dir("n9_ablation"))
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

        graph = copy.deepcopy(base)
        graph[POSITIVE]["inputs"]["text"] = prompt
        graph[NEGATIVE]["inputs"]["text"] = negative
        graph[LATENT]["inputs"].update(width=width, height=height)
        graph[INSTANTID]["inputs"]["cn_strength"] = CN_STRENGTH
        graph[SAMPLER]["inputs"]["cfg"] = CFG

        for name, patched in arms(graph).items():
            if args.only and name != args.only:
                continue
            dest = args.out / name / sid
            if (dest / "0.png").exists():
                print(f"skip {dest}")
                continue
            legs = [
                label
                for label, node in (("InstantID", INSTANTID), ("OpenPose", OPENPOSE))
                if node in patched
            ]
            print(f"\n=== {name} / {sid} ===  legs: {', '.join(legs) or 'none'}")
            if client is None:
                continue
            # The seed is written in rather than drawn, because `run`'s seed
            # machinery goes with `run`. One seed for every arm and subject, as
            # every ladder here has used.
            patched[SAMPLER]["inputs"]["seed"] = SEED
            render(client, patched, photo, dest)
            (dest / "arm.json").write_text(
                json.dumps(
                    {
                        "arm": name,
                        "subject": sid,
                        "seed": SEED,
                        "legs": legs,
                        "cn_strength": CN_STRENGTH,
                        "cfg": CFG,
                        "prompt": prompt,
                    },
                    indent=2,
                )
                + "\n"
            )


if __name__ == "__main__":
    main()
