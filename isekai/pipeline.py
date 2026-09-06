"""Drive a conversion end to end: upload, inject, override, mutate, render, save."""

import copy
import hashlib
import json
import random
import sys
import time
from pathlib import Path
from typing import Any
from urllib import error

from isekai.comfy_types import ComfyTransport, Overrides, Workflow
from isekai.mutate import draw_seed, mutate
from isekai.overrides import apply_overrides
from isekai.workflow import find_node, find_nodes, inject


def run(
    client: ComfyTransport,
    workflow: Workflow,
    input_path: str,
    output_dir: Path,
    variations: int,
    seed: int | None = None,
    overrides: Overrides | None = None,
    fixed_dials: bool = False,
    pod_image: str | None = None,
) -> None:
    """Orchestrate one or more conversions against an injected ComfyUI client.

    `client` and `workflow` stay parameters because something else is actually
    passed through them: `FakeComfyClient` is what makes the suite offline, and
    keeping the graph an argument is what keeps file I/O in the CLI. `inject` and
    `mutate` never had a second implementation, so they are imported (design.md
    D3).

    `output_dir` is this run's own directory, already resolved by the caller, and
    `variations` is required: the count is a spend decision, and its default and
    its ceiling belong together in the CLI that carries the flag.

    `pod_image` is the container image the ComfyUI on the other end of `client` is
    running, as the operator states it: nothing on the wire reports it, so it is
    passed in or it is not known. It is recorded verbatim and never guessed --
    `None` is written through as `null`, which is a run saying it does not know
    rather than a run claiming an image it was not produced on (design.md D14).

    `fixed_dials` holds the graph's committed dials still, and defaults to off so
    every existing invocation behaves exactly as it did. It is what a baseline
    means: the mutator moves six dials at once, so until this existed no two
    renders this repository had produced differed in one thing (design.md D3). A
    held run still draws its own sampler seed per variation -- otherwise it would
    be one render billed N times -- so its variations differ in exactly that.
    """
    image_name = client.upload_image(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Every variation's seed derives from this one source, so `--seed` is a
    # contract over the whole run rather than only its first render. Seeded with
    # None it draws from OS entropy, which is the unseeded behaviour.
    seeds = random.Random(seed)
    used: list[int] = []
    renders: list[dict[str, Any]] = []
    # Read off the graph rather than passed in: the base is what the run actually
    # loaded, and the resolution is what injection actually derived and wrote.
    # Both are constant across a run's variations -- same photo, same checkpoint --
    # so they are recorded once at the top rather than repeated per render.
    base_id = find_node(workflow, class_type="CheckpointLoaderSimple")
    base = workflow[base_id]["inputs"]["ckpt_name"]
    resolution: list[int] = []

    for i in range(variations):
        wf = copy.deepcopy(workflow)
        inject(wf, image_name, input_path)

        if overrides:
            apply_overrides(wf, **overrides)

        # Uniformly derived, variation 0 included: the run seed has exactly one
        # meaning -- the source every variation derives from -- rather than
        # doubling as the first render's sampler seed (design.md D5).
        s = seeds.getrandbits(64)
        used.append(s)
        # The same first draw either way, so a held run and a jittered run from
        # one run seed share their sampler seeds and differ in the jitter alone.
        if fixed_dials:
            draw_seed(wf, random.Random(s))
        else:
            mutate(wf, random.Random(s))
        print(f"variation {i}: seed {s}")

        if not resolution:
            scale_id = find_node(wf, class_type="ImageScale")
            resolution = [
                wf[scale_id]["inputs"]["width"],
                wf[scale_id]["inputs"]["height"],
            ]

        image = f"{i}.png"
        renders.append(_provenance_of(wf, image))
        _render(client, wf, output_dir / image)

    # Recorded so a later comparison can identify what produced these images: a
    # baseline nothing can identify is not a baseline. Keys are added and none
    # removed, so a manifest written by an earlier version stays readable.
    #
    # **The photograph is a digest, never pixels.** A digest of a face is not a
    # face, so the rule that derived faces are not committed is untouched -- and
    # the digest is what makes an uncommitted input checkable rather than merely
    # trusted.
    _write_manifest(
        output_dir,
        {
            "seed": seed,
            # From the seeds actually drawn rather than the count asked for: a
            # manifest claiming five renders beside four seeds would lie.
            "variations": len(used),
            "seeds": used,
            "overrides": dict(overrides) if overrides else {},
            "dials_mode": "held" if fixed_dials else "jittered",
            "photo_sha256": _digest_of_file(input_path),
            # The container image the render was produced on, spelled
            # `pod_image` because `renders[].image` already means a PNG
            # filename in this same file. `null` when the run was not told.
            "pod_image": pod_image,
            "base": base,
            "resolution": resolution,
            "renders": renders,
        },
    )


def _digest_of_file(path: str) -> str:
    """Return a file's SHA-256, read in chunks so a large photo does not go in RAM.

    Spelled here rather than imported from `isekai.provision`, which has one --
    that module is deliberately off `convert.py`'s import graph, and importing it
    for four lines would put it on. The runtime stays stdlib-only either way; what
    would change is the graph, and its narrowness is the property being kept.
    """
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _digest_of_graph(workflow: Workflow) -> str:
    """Return the SHA-256 of a graph as submitted.

    Key-sorted and separator-tight, so the digest is a property of the graph and
    not of how this file happened to serialise it. Two runs that submitted the
    same graph must agree, or the digest cannot be used to tell them apart.
    """
    return hashlib.sha256(
        json.dumps(workflow, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _provenance_of(workflow: Workflow, image: str) -> dict[str, Any]:
    """Record what one variation is about to be submitted with.

    Read off the graph rather than off the arguments that produced it: the dials
    that were *submitted* are the ones a later comparison needs, and reconstructing
    them from a seed and an override would re-derive the mutator to read it.

    Per variation rather than once for the run, because under jitter every
    variation carries its own -- a single record would be a lie about all but one.
    """
    sampler_id = find_node(workflow, class_type="KSampler")
    apply_id = find_node(workflow, class_type="ApplyInstantIDAdvanced")
    cn_ids = sorted(find_nodes(workflow, class_type="ControlNetApplyAdvanced"), key=int)
    return {
        "image": image,
        "sampler_seed": workflow[sampler_id]["inputs"]["seed"],
        "graph_sha256": _digest_of_graph(workflow),
        "dials": {
            "denoise": workflow[sampler_id]["inputs"]["denoise"],
            "cfg": workflow[sampler_id]["inputs"]["cfg"],
            "ip_weight": workflow[apply_id]["inputs"]["ip_weight"],
            "cn_strength": workflow[apply_id]["inputs"]["cn_strength"],
            # Keyed by node id, because the three are tuned differently and
            # "tile, pose, lineart" is an ordering nothing in the graph states.
            "controlnet_strength": {
                nid: workflow[nid]["inputs"]["strength"] for nid in cn_ids
            },
        },
    }


def _write_manifest(output_dir: Path, manifest: dict[str, Any]) -> None:
    """Write this run's manifest beside the images it produced.

    Takes the assembled record rather than nine positional arguments to
    reassemble it from: `run` already holds every field, and threading them
    through a signature only to rebuild the same dict on the other side made the
    call site a list of nine bare positionals whose order nothing checked.
    """
    (output_dir / "run.json").write_text(json.dumps(manifest, indent=2) + "\n")


def _render(client: ComfyTransport, workflow: Workflow, output_path: Path) -> None:
    try:
        prompt_id = client.submit(workflow)
    except error.HTTPError as e:
        sys.exit(f"ComfyUI rejected the workflow ({e.code}):\n{e.read().decode()}")

    print(f"queued {prompt_id} — waiting for the GPU...")

    while True:
        history = client.history(prompt_id)
        if prompt_id in history:
            break
        time.sleep(1)

    outputs = history[prompt_id]["outputs"]
    for node_output in outputs.values():
        if "images" in node_output:
            img = node_output["images"][0]
            break
    else:
        sys.exit("no image found in the workflow outputs")

    output_path.write_bytes(client.view(img))
    print(f"saved {output_path}")
