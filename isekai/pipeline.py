import sys
import time
from pathlib import Path
from urllib import error

from isekai.comfy_types import ComfyTransport, Workflow
from isekai.workflow import inject


def run(
    client: ComfyTransport,
    workflow: Workflow,
    input_path: str,
    prompt: str,
    output_path: str,
) -> None:
    """Orchestrate one conversion against an injected ComfyUI client."""
    image_name = client.upload_image(input_path)
    inject(workflow, image_name, prompt)

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
