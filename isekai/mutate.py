from random import Random

from isekai.comfy_types import Workflow
from isekai.workflow import find_node


def mutate(workflow: Workflow, rng: Random) -> None:
    """Vary the workflow's dials in place using an injected RNG."""
    sampler_id = find_node(workflow, class_type="KSampler")
    workflow[sampler_id]["inputs"]["seed"] = rng.getrandbits(64)
    workflow[sampler_id]["inputs"]["denoise"] = rng.uniform(0.60, 0.70)
    workflow[sampler_id]["inputs"]["cfg"] = rng.uniform(4.5, 5.5)
    apply_id = find_node(workflow, class_type="ApplyInstantIDAdvanced")
    workflow[apply_id]["inputs"]["ip_weight"] = rng.uniform(0.85, 0.95)

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
        key=int,
    )
    for nid in cn_ids:
        base = workflow[nid]["inputs"]["strength"]
        workflow[nid]["inputs"]["strength"] = min(
            1.0, max(0.0, base + rng.uniform(-0.1, 0.1))
        )
