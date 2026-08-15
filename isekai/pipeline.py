import copy
import random
import sys
import time
from pathlib import Path
from urllib import error

from isekai.comfy_types import ComfyTransport, Mutator, Overrides, Workflow
from isekai.models import Injector
from isekai.overrides import apply_overrides


def run(
    client: ComfyTransport,
    workflow: Workflow,
    inject: Injector,
    input_path: str,
    prompt: str,
    output_path: str,
    mutate: Mutator | None = None,
    seed: int | None = None,
    variations: int = 1,
    overrides: Overrides | None = None,
) -> None:
    """Orchestrate one or more conversions against an injected ComfyUI client."""
    image_name = client.upload_image(input_path)

    for i in range(variations):
        wf = copy.deepcopy(workflow)
        inject(wf, image_name, prompt)

        if overrides:
            apply_overrides(wf, **overrides)

        if mutate is not None:
            s = seed if (i == 0 and seed is not None) else random.getrandbits(64)
            mutate(wf, random.Random(s))
            print(f"variation {i}: seed {s}")

        out = output_path if variations == 1 else _numbered(output_path, i)
        _render(client, wf, out)


def _numbered(path: str, i: int) -> str:
    p = Path(path)
    return str(p.with_stem(f"{p.stem}_{i}"))


def _render(client: ComfyTransport, workflow: Workflow, output_path: str) -> None:
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

    Path(output_path).write_bytes(client.view(img))
    print(f"saved {output_path}")
