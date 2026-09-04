"""Locate nodes in a ComfyUI graph, and wire the photo into one."""

import sys
from pathlib import Path

from isekai.comfy_types import Workflow

# The one graph, anchored to the repository rather than to the working
# directory: `convert.py` is run in place, and a CWD-relative path would make
# the product's only workflow unloadable from anywhere but the repo root. The
# suite loads the same constant, so the filename is spelled once.
PIPELINE_PATH = Path(__file__).parent.parent / "workflows" / "pipeline.json"


def find_nodes(workflow: Workflow, *, class_type: str) -> list[str]:
    """Return every node ID with this class_type, in the graph's own order."""
    return [
        nid for nid, node in workflow.items() if node.get("class_type") == class_type
    ]


def find_node(workflow: Workflow, *, class_type: str) -> str:
    """Return the single node ID with this class_type.

    Fail if the match is not exactly one node: an injection that edits the wrong
    node produces a silently wrong render rather than an error.
    """
    matches = find_nodes(workflow, class_type=class_type)

    if len(matches) != 1:
        sys.exit(
            f"find_node(class_type={class_type!r}): "
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
