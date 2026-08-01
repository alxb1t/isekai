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
