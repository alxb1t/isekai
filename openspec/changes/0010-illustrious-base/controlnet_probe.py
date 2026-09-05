#!/usr/bin/env python3
"""Phase 5's ControlNet strength-to-zero comparison, at a fixed seed.

**Instrumentation for one phase, not a second path.** It exists because the
product CLI cannot express this comparison: `convert.py` has no per-ControlNet
flag, and `mutate` jitters every strength on every run, so "strength 0.0" is not
a thing the released path can submit. Rather than weaken the product to make a
measurement, the measurement gets its own harness, in this change's directory,
where it is archived with the change that needed it.

It asks one falsifiable question per ControlNet: **does the conditioning reach
the sampler at all?** Not whether the result is prettier -- that would need taste
this version is trying to spend as little of as possible. A component whose
render at 0.0 is indistinguishable from the baseline is a component that can be
deleted with evidence (design.md D7).

Everything except the ControlNet under test is held fixed: the same uploaded
photo, the same sampler seed, the same dials, and no mutation at all. So the one
difference between the baseline and each comparison render is the strength.

Run it from the repository root, against the tunnel:

    uv run python openspec/changes/0010-illustrious-base/controlnet_probe.py \
        outputs/original/darya_original.jpeg -o outputs/probe --seed 1

It writes one PNG per render plus a `probe.json` recording exactly what was
submitted, so the verdicts in `CHANGELOG.md` point at a reproducible artifact.
"""

import argparse
import copy
import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from isekai.comfy_client import ComfyClient  # noqa: E402
from isekai.comfy_types import ComfyTransport, Workflow  # noqa: E402
from isekai.workflow import PIPELINE_PATH, find_node, find_nodes, inject  # noqa: E402

# The strength a ControlNet is taken to when it is the one under test. Exactly
# zero, not a small number: the question is whether the conditioning arrives, and
# an almost-zero strength answers a different, weaker question.
ZERO = 0.0


def _controlnets(workflow: Workflow) -> dict[str, str]:
    """Return each ControlNet apply node's id, keyed by the model file it loads.

    Keyed by the file rather than by the node id so the record names `openpose`
    rather than `18`, and so a re-export of the graph in a different node order
    cannot silently retarget a verdict. A file sitting in its own directory is
    named by that directory: three of these weights are called
    `diffusion_pytorch_model.safetensors` and the stem alone would not say which.

    Only `ControlNetApplyAdvanced` nodes are listed. InstantID applies its own
    control net through a different node, and its `cn_strength` is the identity
    axis rather than one of the three this comparison is about.
    """
    names: dict[str, str] = {}
    for apply_id in sorted(
        find_nodes(workflow, class_type="ControlNetApplyAdvanced"), key=int
    ):
        loader_id = workflow[apply_id]["inputs"]["control_net"][0]
        path = Path(str(workflow[loader_id]["inputs"]["control_net_name"]))
        names[path.parent.name or path.stem] = apply_id
    return names


def _render(client: ComfyTransport, workflow: Workflow, destination: Path) -> None:
    """Submit one graph, wait for it, and write the image it produced."""
    prompt_id = client.submit(workflow)
    print(f"  queued {prompt_id} ...", flush=True)

    while True:
        history = client.history(prompt_id)
        if prompt_id in history:
            break
        time.sleep(1)

    outputs = history[prompt_id]["outputs"]
    for node_output in outputs.values():
        if "images" in node_output:
            destination.write_bytes(client.view(node_output["images"][0]))
            print(f"  saved {destination}", flush=True)
            return

    sys.exit(f"{destination.name}: no image in the workflow outputs")


def probe(
    client: ComfyTransport,
    workflow: Workflow,
    image_path: str,
    output_dir: Path,
    seed: int,
) -> dict[str, Any]:
    """Render the baseline and one zeroed render per ControlNet. Return the record."""
    image_name = client.upload_image(image_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    sampler_id = find_node(workflow, class_type="KSampler")
    applies = _controlnets(workflow)
    tuned = {
        name: workflow[apply_id]["inputs"]["strength"]
        for name, apply_id in applies.items()
    }
    print(f"tuned strengths: {tuned}")

    renders: list[dict[str, Any]] = []
    for label in ["baseline", *applies]:
        wf = copy.deepcopy(workflow)
        inject(wf, image_name, image_path)
        wf[sampler_id]["inputs"]["seed"] = seed
        if label != "baseline":
            wf[applies[label]]["inputs"]["strength"] = ZERO

        strengths = {
            name: wf[apply_id]["inputs"]["strength"]
            for name, apply_id in applies.items()
        }
        print(f"{label}: {strengths}", flush=True)
        _render(client, wf, output_dir / f"{label}.png")
        renders.append({"label": label, "zeroed": None, "strengths": strengths})
        if label != "baseline":
            renders[-1]["zeroed"] = label

    scale_id = find_node(workflow, class_type="ImageScale")
    example = copy.deepcopy(workflow)
    inject(example, image_name, image_path)
    record = {
        "photo": image_path,
        "seed": seed,
        "working_resolution": [
            example[scale_id]["inputs"]["width"],
            example[scale_id]["inputs"]["height"],
        ],
        "tuned_strengths": tuned,
        "renders": renders,
    }
    (output_dir / "probe.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def main() -> None:
    """Parse the flags and run the comparison."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", help="input photo (jpg/png)")
    parser.add_argument("-o", "--output", type=Path, default=Path("outputs/probe"))
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--seed", type=int, required=True, help="the fixed seed")
    args = parser.parse_args()

    workflow: Workflow = json.loads(PIPELINE_PATH.read_text())
    probe(ComfyClient(args.server), workflow, args.input, args.output, args.seed)


if __name__ == "__main__":
    main()
