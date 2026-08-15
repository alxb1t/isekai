from isekai.comfy_types import Workflow
from isekai.workflow import find_node


def apply_overrides(
    workflow: Workflow,
    *,
    denoise: float | None = None,
    cfg: float | None = None,
    ip_weight: float | None = None,
) -> None:
    """Set user-chosen base values on the workflow by class_type. None = no-op."""
    if denoise is not None or cfg is not None:
        sampler_id = find_node(workflow, class_type="KSampler")
        if denoise is not None:
            workflow[sampler_id]["inputs"]["denoise"] = denoise
        if cfg is not None:
            workflow[sampler_id]["inputs"]["cfg"] = cfg

    if ip_weight is not None:
        # Silent no-op when no ApplyInstantIDAdvanced node (qwen, future non-InstantID paths)
        apply_ids = [
            nid
            for nid, node in workflow.items()
            if node.get("class_type") == "ApplyInstantIDAdvanced"
        ]
        if apply_ids:
            workflow[apply_ids[0]]["inputs"]["ip_weight"] = ip_weight
