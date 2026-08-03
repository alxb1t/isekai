import sys

from isekai.comfy_types import Workflow


def find_node(
    workflow: Workflow, *, class_type: str | None = None, title: str | None = None
) -> str:
    """Return the single node ID matching class_type and/or title. Fail if not exactly one."""
    matches = [
        nid
        for nid, node in workflow.items()
        if (class_type is None or node.get("class_type") == class_type)
        and (title is None or node.get("_meta", {}).get("title") == title)
    ]

    if len(matches) != 1:
        sys.exit(
            f"find_node(class_type={class_type!r}, title={title!r}): "
            f"expected exactly 1 match, found {len(matches)}"
        )

    return matches[0]


def inject_qwen(workflow: Workflow, image_name: str, prompt: str) -> None:
    """Wire the uploaded photo + prompt into the Qwen graph (mutates workflow in place)."""
    load_id = find_node(workflow, class_type="LoadImage")
    workflow[load_id]["inputs"]["image"] = image_name

    # The graph has two same-titled encoders; the positive one is whatever
    # KSampler.positive points at.
    sampler_id = find_node(workflow, class_type="KSampler")
    pos_id = workflow[sampler_id]["inputs"]["positive"][0]
    workflow[pos_id]["inputs"]["prompt"] = prompt


def inject_animagine(workflow: Workflow, image_name: str, prompt: str) -> None:
    """Wire the uploaded photo + prompt into an Animagine + InstantID graph (mutates in place).

    Handles any depth of conditioning chain: KSampler.positive may point at
    ApplyInstantID directly, or through a stack of ControlNetApply nodes. Walk
    .positive until the real positive CLIPTextEncode.
    """
    load_id = find_node(workflow, class_type="LoadImage")
    workflow[load_id]["inputs"]["image"] = image_name

    sampler_id = find_node(workflow, class_type="KSampler")
    node_id = workflow[sampler_id]["inputs"]["positive"][0]
    while workflow[node_id]["class_type"] != "CLIPTextEncode":
        node_id = workflow[node_id]["inputs"]["positive"][0]
    workflow[node_id]["inputs"]["text"] = prompt
