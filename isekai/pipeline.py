"""Drive a conversion end to end: upload, inject, override, mutate, render, save."""

import copy
import json
import random
import sys
import time
from pathlib import Path
from urllib import error

from isekai.comfy_types import ComfyTransport, Overrides, Workflow
from isekai.mutate import draw_seed, mutate
from isekai.overrides import apply_overrides
from isekai.workflow import inject


def run(
    client: ComfyTransport,
    workflow: Workflow,
    input_path: str,
    output_dir: Path,
    variations: int,
    seed: int | None = None,
    overrides: Overrides | None = None,
    fixed_dials: bool = False,
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

        _render(client, wf, output_dir / f"{i}.png")

    _write_manifest(output_dir, seed, used, overrides)


def _write_manifest(
    output_dir: Path,
    seed: int | None,
    used: list[int],
    overrides: Overrides | None,
) -> None:
    """Record what produced this run, beside the images it produced.

    With the per-variation seeds printed and nowhere else, reproducing render 3
    next week means still having the terminal. The manifest moves that from a
    property of the operator's scrollback to a property of the artifact.
    """
    manifest = {
        "seed": seed,
        # Derived from the seeds actually drawn rather than from the count asked
        # for: a manifest claiming five renders beside four seeds would lie.
        "variations": len(used),
        "seeds": used,
        "overrides": dict(overrides) if overrides else {},
    }
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
