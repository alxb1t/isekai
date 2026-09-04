"""The mutation seam: jitter a graph's dials around their base, via an injected RNG."""

from random import Random

from isekai.comfy_types import Workflow
from isekai.workflow import find_node, find_nodes

_DENOISE_DELTA: float = 0.05
_CFG_DELTA: float = 0.5
_IP_WEIGHT_DELTA: float = 0.05
_CN_STRENGTH_DELTA: float = 0.1


def _jitter(
    workflow: Workflow, node_id: str, key: str, delta: float, hi: float, rng: Random
) -> None:
    """Draw one dial uniformly within ±delta of its current value, clamped to [0, hi].

    Base-relative, so it reads the dial before writing it: each dial has its own
    tuned value and a shared constant would erase that tuning. One draw per call,
    which is what makes the RNG stream -- and therefore a seed -- canonical.
    """
    base = workflow[node_id]["inputs"][key]
    workflow[node_id]["inputs"][key] = min(
        hi, max(0.0, rng.uniform(base - delta, base + delta))
    )


def mutate(workflow: Workflow, rng: Random) -> None:
    """Vary the workflow's dials in place using an injected RNG."""
    sampler_id = find_node(workflow, class_type="KSampler")
    workflow[sampler_id]["inputs"]["seed"] = rng.getrandbits(64)

    _jitter(workflow, sampler_id, "denoise", _DENOISE_DELTA, 1.0, rng)
    _jitter(workflow, sampler_id, "cfg", _CFG_DELTA, 30.0, rng)

    apply_id = find_node(workflow, class_type="ApplyInstantIDAdvanced")
    _jitter(workflow, apply_id, "ip_weight", _IP_WEIGHT_DELTA, 1.0, rng)

    # Jitter each ControlNet strength around its own tuned baseline (tile/pose/
    # lineart are tuned differently). Runs last, so the dials drawn above keep a
    # fixed position in the RNG stream; sorted, so a re-export of the graph in a
    # different node order cannot change what a given seed renders.
    #
    # Deliberately NOT routed through _jitter: `base + uniform(-d, d)` and
    # `uniform(base - d, base + d)` are equal in exact arithmetic but differ in
    # the last ulp, and this draw is pinned by a golden. Unifying the spelling
    # would silently change what a given seed renders.
    cn_ids = sorted(find_nodes(workflow, class_type="ControlNetApplyAdvanced"), key=int)
    for nid in cn_ids:
        base = workflow[nid]["inputs"]["strength"]
        workflow[nid]["inputs"]["strength"] = min(
            1.0, max(0.0, base + rng.uniform(-_CN_STRENGTH_DELTA, _CN_STRENGTH_DELTA))
        )
