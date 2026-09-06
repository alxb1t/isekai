"""Apply the user's base dial values, before any mutation jitters around them."""

from isekai.comfy_types import Workflow
from isekai.workflow import find_node


def apply_overrides(
    workflow: Workflow,
    *,
    denoise: float | None = None,
    cfg: float | None = None,
    ip_weight: float | None = None,
    cn_strength: float | None = None,
) -> None:
    """Set user-chosen base values on the workflow by class_type. None = no-op."""
    if denoise is not None or cfg is not None:
        sampler_id = find_node(workflow, class_type="KSampler")
        if denoise is not None:
            workflow[sampler_id]["inputs"]["denoise"] = denoise
        if cfg is not None:
            workflow[sampler_id]["inputs"]["cfg"] = cfg

    # Both of the identity node's dials, found once. `cn_strength` is its
    # keypoint route, beside `ip_weight`'s embedding route -- and it is
    # deliberately NOT a `ControlNetApplyAdvanced` strength, which is a different
    # dial that happens to share a word. Setting it there would move pose and
    # structure while claiming to move identity.
    if ip_weight is not None or cn_strength is not None:
        apply_id = find_node(workflow, class_type="ApplyInstantIDAdvanced")
        if ip_weight is not None:
            workflow[apply_id]["inputs"]["ip_weight"] = ip_weight
        if cn_strength is not None:
            workflow[apply_id]["inputs"]["cn_strength"] = cn_strength
