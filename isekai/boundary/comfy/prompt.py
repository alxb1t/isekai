"""Queue one graph on the endpoint, wait for it, and read what the endpoint ran on.

The render stage and the edit stage share these, so neither imports the other.
Stdlib only; the endpoint is behind `ComfyTransport`.
"""

import time
from typing import Any

from isekai.boundary.comfy.contract import ComfyTransport, TransportFailure, unread
from isekai.foundation.artifacts import Runtime
from isekai.foundation.flow import Workflow
from isekai.foundation.refusal import Refusal


def read_runtime(client: ComfyTransport) -> Runtime:
    """Return the versions the endpoint reports, and its first device's name.

    A report without them is an answer in a shape this build does not read, and
    `render` records it as permanent rather than claim a runtime it never read.
    A failed request keeps the transport's own kind.
    A report naming no device is read without one; the device decides nothing.
    """
    report = client.system_stats()
    try:
        system = report["system"]
        ran_on: Runtime = {
            "comfyui_version": str(system["comfyui_version"]),
            "python_version": str(system["python_version"]),
            "pytorch_version": str(system["pytorch_version"]),
        }
    except (KeyError, TypeError) as answer:
        raise unread(answer) from answer
    if (device := _first_device(report)) is not None:
        ran_on["device"] = device
    return ran_on


def _first_device(report: dict[str, Any]) -> str | None:
    """Return the name of the first device `report` lists, or None for no name."""
    devices = report.get("devices")
    if not isinstance(devices, list) or not devices:
        return None
    first = devices[0]
    name = first.get("name") if isinstance(first, dict) else None
    return name if isinstance(name, str) else None


def submit_and_wait(
    client: ComfyTransport, graph: Workflow, poll: float, deadline: float
) -> bytes:
    """Queue one graph, wait up to `deadline` seconds, and return the image's bytes."""
    prompt_id = client.submit(graph)
    end = time.monotonic() + deadline
    while prompt_id not in (history := _history(client, prompt_id)):
        if time.monotonic() >= end:
            raise TransportFailure(
                "transient",
                f"prompt {prompt_id} did not finish within {deadline:g} s; check "
                "the pod's ComfyUI log",
            )
        time.sleep(poll)
    record = history[prompt_id]
    outputs = record.get("outputs") if isinstance(record, dict) else None
    if not isinstance(outputs, dict):
        raise Refusal(
            "the endpoint's history for a graph it accepted carries no outputs; "
            "check the pod's ComfyUI log"
        )
    for output in outputs.values():
        images = output.get("images") if isinstance(output, dict) else None
        if isinstance(images, list) and images:
            return client.view(images[0])
    raise Refusal(
        "the endpoint returned no image for a graph it accepted; check the pod's "
        "ComfyUI log"
    )


def _history(client: ComfyTransport, prompt_id: str) -> dict[str, Any]:
    """Return the endpoint's history, refusing one that is not a JSON object.

    `in` on a list never matches, so without this a list would be polled until the
    deadline.
    """
    history: object = client.history(prompt_id)
    if not isinstance(history, dict):
        raise Refusal(
            "the endpoint's history is not a JSON object; check that `--server` "
            "names a ComfyUI"
        )
    return history
