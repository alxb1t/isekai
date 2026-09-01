"""The mutation seam: jitter a graph's dials around their base, via an injected RNG."""

import sys
from random import Random

from isekai.comfy_types import Workflow
from isekai.workflow import find_node

_DENOISE_DELTA: float = 0.05
_CFG_DELTA: float = 0.5
_IP_WEIGHT_DELTA: float = 0.05


def _node_order(node_id: str) -> tuple:
    """Build a total order over node ids that survives every id format ComfyUI emits.

    Plain graphs number nodes "1", "2", ... but subgraph exports use "102:14",
    which `int` cannot parse. Each dot-separated part becomes a (kind, value)
    pair so numeric parts still sort numerically ("2" before "10") while any
    non-numeric part still compares without raising.
    """
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part) for part in node_id.split(":")
    )


def _base(workflow: Workflow, node_id: str, key: str) -> float:
    """Read a dial's current value, refusing one that is wired to another node.

    Jitter is base-relative, so it reads the dial before writing it. In ComfyUI
    API format an input may legally be a `[node_id, slot]` link instead of a
    scalar, and a graph like qwen-image-edit.json drives `cfg` that way. Reading
    it as a number would raise a bare TypeError out of the arithmetic; stop with
    a message naming the dial and the node driving it instead.
    """
    value = workflow[node_id]["inputs"][key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        # Only a [node_id, slot] link can be described as "wired"; anything else
        # (null, an object, a string) gets the generic wording. Reaching for
        # value[0] unconditionally would raise the very error this guard exists
        # to prevent.
        if isinstance(value, list) and value:
            detail = f"it is wired to node {value[0]!r}"
        else:
            detail = f"it is {value!r}"
        sys.exit(f"cannot jitter {key!r} on node {node_id}: {detail}, not a number")
    return value


def mutate(workflow: Workflow, rng: Random) -> None:
    """Vary the workflow's dials in place using an injected RNG."""
    sampler_id = find_node(workflow, class_type="KSampler")
    workflow[sampler_id]["inputs"]["seed"] = rng.getrandbits(64)

    base = _base(workflow, sampler_id, "denoise")
    workflow[sampler_id]["inputs"]["denoise"] = min(
        1.0, max(0.0, rng.uniform(base - _DENOISE_DELTA, base + _DENOISE_DELTA))
    )

    base = _base(workflow, sampler_id, "cfg")
    workflow[sampler_id]["inputs"]["cfg"] = min(
        30.0, max(0.0, rng.uniform(base - _CFG_DELTA, base + _CFG_DELTA))
    )

    apply_id = find_node(workflow, class_type="ApplyInstantIDAdvanced")
    base = _base(workflow, apply_id, "ip_weight")
    workflow[apply_id]["inputs"]["ip_weight"] = min(
        1.0, max(0.0, rng.uniform(base - _IP_WEIGHT_DELTA, base + _IP_WEIGHT_DELTA))
    )

    # Jitter each ControlNet strength ±0.1 around its tuned baseline, clamped to
    # [0, 1]. Base-relative because each CN has its own tuned value (tile/pose/
    # lineart). Runs last and draws nothing on graphs without CN apply nodes, so
    # animagine-i2i stays byte-for-byte unchanged (back-compat).
    cn_ids = sorted(
        (
            nid
            for nid, node in workflow.items()
            if node.get("class_type") == "ControlNetApplyAdvanced"
        ),
        key=_node_order,
    )
    for nid in cn_ids:
        base = _base(workflow, nid, "strength")
        workflow[nid]["inputs"]["strength"] = min(
            1.0, max(0.0, base + rng.uniform(-0.1, 0.1))
        )
