"""Locate nodes in a ComfyUI graph, and wire the photo into one."""

import sys

from isekai.comfy_types import Workflow


def find_node(
    workflow: Workflow, *, class_type: str | None = None, title: str | None = None
) -> str:
    """Return the single node ID matching class_type and/or title.

    Fail if the match is not exactly one node.
    """
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


def inject(workflow: Workflow, image_name: str) -> None:
    """Wire the uploaded photo into the pipeline graph.

    Mutates `workflow` in place. The positive prompt is committed to the graph,
    so the photo is the only thing injection wires.
    """
    load_id = find_node(workflow, class_type="LoadImage")
    workflow[load_id]["inputs"]["image"] = image_name
