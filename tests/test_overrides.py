import copy

import pytest

from isekai.comfy_types import Workflow
from isekai.overrides import apply_overrides


@pytest.mark.spec("workflow-mutation:overrides:sets-denoise")
def test_apply_overrides_sets_denoise_on_the_ksampler(
    animagine_i2i_workflow: Workflow,
) -> None:
    apply_overrides(animagine_i2i_workflow, denoise=0.80)
    assert animagine_i2i_workflow["10"]["inputs"]["denoise"] == 0.80


@pytest.mark.spec("workflow-mutation:overrides:sets-cfg")
def test_apply_overrides_sets_cfg_on_the_ksampler(
    animagine_i2i_workflow: Workflow,
) -> None:
    apply_overrides(animagine_i2i_workflow, cfg=7.0)
    assert animagine_i2i_workflow["10"]["inputs"]["cfg"] == 7.0


@pytest.mark.spec("workflow-mutation:overrides:sets-ip-weight")
def test_apply_overrides_sets_ip_weight_on_apply_instantid_advanced(
    animagine_i2i_workflow: Workflow,
) -> None:
    apply_overrides(animagine_i2i_workflow, ip_weight=0.75)
    assert animagine_i2i_workflow["8"]["inputs"]["ip_weight"] == 0.75


@pytest.mark.spec("workflow-mutation:overrides:unspecified-dial-untouched")
def test_apply_overrides_none_denoise_leaves_the_dial_unchanged(
    animagine_i2i_workflow: Workflow,
) -> None:
    before = animagine_i2i_workflow["10"]["inputs"]["denoise"]
    apply_overrides(animagine_i2i_workflow, denoise=None)
    assert animagine_i2i_workflow["10"]["inputs"]["denoise"] == before


@pytest.mark.spec("workflow-mutation:overrides:unspecified-dial-untouched")
def test_apply_overrides_none_cfg_leaves_the_dial_unchanged(
    animagine_i2i_workflow: Workflow,
) -> None:
    before = animagine_i2i_workflow["10"]["inputs"]["cfg"]
    apply_overrides(animagine_i2i_workflow, cfg=None)
    assert animagine_i2i_workflow["10"]["inputs"]["cfg"] == before


@pytest.mark.spec("workflow-mutation:overrides:unspecified-dial-untouched")
def test_apply_overrides_none_ip_weight_leaves_the_dial_unchanged(
    animagine_i2i_workflow: Workflow,
) -> None:
    before = animagine_i2i_workflow["8"]["inputs"]["ip_weight"]
    apply_overrides(animagine_i2i_workflow, ip_weight=None)
    assert animagine_i2i_workflow["8"]["inputs"]["ip_weight"] == before


@pytest.mark.spec("workflow-mutation:overrides:all-unspecified-is-a-no-op")
def test_apply_overrides_all_nones_leaves_the_workflow_unchanged(
    animagine_i2i_workflow: Workflow,
) -> None:
    before = copy.deepcopy(animagine_i2i_workflow)
    apply_overrides(animagine_i2i_workflow, denoise=None, cfg=None, ip_weight=None)
    assert animagine_i2i_workflow == before


@pytest.mark.spec("workflow-mutation:overrides:ip-weight-ignored-without-identity-node")
def test_apply_overrides_ip_weight_is_silently_ignored_when_no_instantid_node(
    qwen_workflow: Workflow,
) -> None:
    before = copy.deepcopy(qwen_workflow)
    apply_overrides(qwen_workflow, ip_weight=0.50)
    # No ApplyInstantIDAdvanced node — no exception and nothing else changed
    assert qwen_workflow == before


@pytest.mark.spec("workflow-mutation:overrides:mutates-in-place")
def test_apply_overrides_mutates_in_place(animagine_i2i_workflow: Workflow) -> None:
    original = animagine_i2i_workflow
    apply_overrides(animagine_i2i_workflow, denoise=0.90)
    assert original["10"]["inputs"]["denoise"] == 0.90


@pytest.mark.spec("workflow-mutation:overrides:sets-denoise")
def test_apply_overrides_sets_a_zero_denoise(animagine_i2i_workflow: Workflow) -> None:
    # Zero is a valid dial value and must survive: a truthiness guard
    # (`if denoise:`) instead of `is not None` would discard it silently and
    # render at the workflow's baked value instead.
    apply_overrides(animagine_i2i_workflow, denoise=0.0)
    assert animagine_i2i_workflow["10"]["inputs"]["denoise"] == 0.0


@pytest.mark.spec("workflow-mutation:overrides:sets-cfg")
def test_apply_overrides_sets_a_zero_cfg(animagine_i2i_workflow: Workflow) -> None:
    apply_overrides(animagine_i2i_workflow, cfg=0.0)
    assert animagine_i2i_workflow["10"]["inputs"]["cfg"] == 0.0


@pytest.mark.spec("workflow-mutation:overrides:sets-ip-weight")
def test_apply_overrides_sets_a_zero_ip_weight(
    animagine_i2i_workflow: Workflow,
) -> None:
    apply_overrides(animagine_i2i_workflow, ip_weight=0.0)
    assert animagine_i2i_workflow["8"]["inputs"]["ip_weight"] == 0.0


@pytest.mark.spec("workflow-mutation:overrides:linked-dial-is-overwritten")
def test_apply_overrides_replaces_a_dial_wired_to_another_node(
    qwen_workflow: Workflow,
) -> None:
    # qwen-image-edit.json drives cfg from a Switch node. Unlike jitter -- which
    # needs a numeric base and refuses -- an override IS the value the user asked
    # for, so it replaces the link rather than erroring.
    assert isinstance(qwen_workflow["102:3"]["inputs"]["cfg"], list)

    apply_overrides(qwen_workflow, cfg=7.0)

    assert qwen_workflow["102:3"]["inputs"]["cfg"] == 7.0
