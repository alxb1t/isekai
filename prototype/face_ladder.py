#!/usr/bin/env python3
"""PROTOTYPE — N6: one variable at a time, on the dials the photograph's exit orphaned.

F24 settled the architecture: `fromnoise-v1` meets the style bar by measurement and
the identity bar by the operator's eye. **Nothing in the graph has been swept.**
`ip_weight` 0.9, `cn_strength` 0.5 and the OpenPose leg 0.6 were every one of them
chosen for an img2img graph whose latent already carried the face, and none was
revisited when the photograph left it. From noise, InstantID is the *only* thing
carrying the face, so the dial that weights it is the most under-argued number in
the file.

Two arms are prompt arms rather than dial arms, and they close F24's two recorded
drifts: skin renders darker than the tag declares, and age renders younger on
every subject. Both are emphasis edits on the sheet's own field values -- the
tag is not replaced, it is weighted -- so the arm tests *whether the tag was
outvoted* rather than whether a different tag works better.

**One change each, never two**, and every arm measured against `1_control`, which
reproduces N3 exactly. Three subjects: a close-up where the face is largest, a
full-body where it is smallest, and the freckled subject whose drift was worst.

    PYTHONPATH=. uv run python prototype/face_ladder.py --server http://127.0.0.1:8188
"""

import argparse
import copy
import json
import re
from pathlib import Path

from isekai.comfy_client import ComfyClient
from isekai.pipeline import run
from isekai.workflow import image_dimensions, working_resolution
from prototype.fromnoise import (
    GRAPH,
    LATENT,
    NEGATIVE,
    PHOTOS,
    POSITIVE,
    SEED,
    check_graph,
    prompts_of,
)
from prototype.paths import sheet_path

INSTANTID = "8"  # ApplyInstantIDAdvanced
SAMPLER = "10"  # KSampler

# The close-up (face largest), the full body (face smallest, and the phenotype
# case), and the freckled subject whose age and skin drift were the worst of the
# six. Enough spread to tell a dial that helps from one that helps one framing.
SUBJECTS = ("00072", "00050", "00003")

_FIELD = re.compile(
    r"^\|\s*\d+ · (?P<name>[^|✓]+?)\s*✓?\s*\|\s*(?P<value>.+?)\s*\|$", re.M
)


def fields_of(sheet: Path) -> dict[str, str]:
    """Return the sheet's thirteen fields, keyed by name without its number.

    Read from the table rather than from the assembled prompt because an emphasis
    arm has to weight **one** field, and the assembled prompt is a flat string in
    which the boundary between two fields is not recoverable.
    """
    return {m["name"]: m["value"] for m in _FIELD.finditer(sheet.read_text())}


def emphasised(prompt: str, value: str, weight: float) -> str:
    """Return `prompt` with one field's text wrapped in ComfyUI's weight syntax.

    Fails loudly rather than silently returning the prompt unchanged: an arm that
    quietly did nothing would be recorded as evidence that the tag cannot be
    strengthened, which is the opposite of what it would have shown.
    """
    if value not in prompt:
        raise SystemExit(f"cannot emphasise {value!r}: not in the assembled prompt")
    return prompt.replace(value, f"({value}:{weight})", 1)


def arms(
    graph: dict, prompt: str, fields: dict[str, str]
) -> dict[str, tuple[dict, str]]:
    """Return arm name -> (patched graph, prompt). One change each, never two."""
    out: dict[str, tuple[dict, str]] = {"1_control": (copy.deepcopy(graph), prompt)}

    # The headline question. InstantID is now the only carrier of the face, and
    # 0.9 was chosen when it was one of four things carrying it.
    for name, weight in (("2_ip_1.2", 1.2), ("3_ip_1.5", 1.5)):
        g = copy.deepcopy(graph)
        g[INSTANTID]["inputs"]["ip_weight"] = weight
        out[name] = (g, prompt)

    # The adapter's other half: the keypoint ControlNet, which carries face
    # *geometry* where ip_weight carries face *identity*. Swept separately
    # because they are two mechanisms, not one dial with two names.
    g = copy.deepcopy(graph)
    g[INSTANTID]["inputs"]["cn_strength"] = 0.8
    out["4_cn_0.8"] = (g, prompt)

    # cfg went 5 -> 7 by argument, not by measurement: from noise the prompt
    # carries the criteria, so text adherence looked worth more. High cfg also
    # pushes toward the prompt and away from the adapter, so this arm is the
    # other side of arms 2 and 3 and has to be read beside them.
    g = copy.deepcopy(graph)
    g[SAMPLER]["inputs"]["cfg"] = 5
    out["5_cfg_5"] = (g, prompt)

    # F24's two drifts. Emphasis, not replacement.
    out["6_skin"] = (
        copy.deepcopy(graph),
        emphasised(prompt, fields["skin / ancestry"], 1.4),
    )
    out["7_age"] = (copy.deepcopy(graph), emphasised(prompt, fields["age band"], 1.4))
    return out


def main() -> None:
    """Render every arm on every subject, at one seed."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--out", type=Path, default=Path("prototype/renders/n6_face"))
    p.add_argument("--only", default=None, help="run one arm by name")
    p.add_argument("--pod-image", default=None)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    base = json.loads(GRAPH.read_text())
    check_graph(base)
    client = None if args.dry_run else ComfyClient(args.server)

    for sid in SUBJECTS:
        sheet = sheet_path(sid)
        photo = PHOTOS / f"synthetic_portrait_{sid}_.png"
        prompt, negative = prompts_of(sheet)
        width, height = working_resolution(*image_dimensions(str(photo)))

        graph = copy.deepcopy(base)
        graph[POSITIVE]["inputs"]["text"] = prompt
        graph[NEGATIVE]["inputs"]["text"] = negative
        graph[LATENT]["inputs"]["width"] = width
        graph[LATENT]["inputs"]["height"] = height

        for name, (patched, text) in arms(graph, prompt, fields_of(sheet)).items():
            if args.only and name != args.only:
                continue
            patched[POSITIVE]["inputs"]["text"] = text
            dest = args.out / name / sid
            if (dest / "0.png").exists():
                print(f"skip {dest}")
                continue
            print(f"\n=== {name} / {sid} ===")
            print(
                f"    ip {patched[INSTANTID]['inputs']['ip_weight']}"
                f"  cn {patched[INSTANTID]['inputs']['cn_strength']}"
                f"  cfg {patched[SAMPLER]['inputs']['cfg']}"
            )
            if text != prompt:
                print(f"    prompt: {text}")
            if client is None:  # --dry-run: everything above, nothing billed
                continue
            run(
                client,
                patched,
                str(photo),
                dest,
                variations=1,
                seed=SEED,
                fixed_dials=True,
                pod_image=args.pod_image,
            )
            (dest / "arm.json").write_text(
                json.dumps(
                    {
                        "arm": name,
                        "subject": sid,
                        "seed": SEED,
                        "ip_weight": patched[INSTANTID]["inputs"]["ip_weight"],
                        "cn_strength": patched[INSTANTID]["inputs"]["cn_strength"],
                        "cfg": patched[SAMPLER]["inputs"]["cfg"],
                        "prompt": text,
                    },
                    indent=2,
                )
                + "\n"
            )


if __name__ == "__main__":
    main()
