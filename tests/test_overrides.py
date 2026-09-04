import copy

import pytest

from isekai.comfy_types import Workflow
from isekai.overrides import apply_overrides


@pytest.mark.spec("workflow-mutation:overrides:sets-denoise")
def test_apply_overrides_sets_denoise_on_the_ksampler(
    workflow: Workflow,
) -> None:
    apply_overrides(workflow, denoise=0.80)
    assert workflow["10"]["inputs"]["denoise"] == 0.80


@pytest.mark.spec("workflow-mutation:overrides:sets-cfg")
def test_apply_overrides_sets_cfg_on_the_ksampler(
    workflow: Workflow,
) -> None:
    apply_overrides(workflow, cfg=7.0)
    assert workflow["10"]["inputs"]["cfg"] == 7.0


@pytest.mark.spec("workflow-mutation:overrides:sets-ip-weight")
def test_apply_overrides_sets_ip_weight_on_apply_instantid_advanced(
    workflow: Workflow,
) -> None:
    apply_overrides(workflow, ip_weight=0.75)
    assert workflow["8"]["inputs"]["ip_weight"] == 0.75


@pytest.mark.spec("workflow-mutation:overrides:unspecified-dial-untouched")
def test_apply_overrides_none_denoise_leaves_the_dial_unchanged(
    workflow: Workflow,
) -> None:
    before = workflow["10"]["inputs"]["denoise"]
    apply_overrides(workflow, denoise=None)
    assert workflow["10"]["inputs"]["denoise"] == before


@pytest.mark.spec("workflow-mutation:overrides:unspecified-dial-untouched")
def test_apply_overrides_none_cfg_leaves_the_dial_unchanged(
    workflow: Workflow,
) -> None:
    before = workflow["10"]["inputs"]["cfg"]
    apply_overrides(workflow, cfg=None)
    assert workflow["10"]["inputs"]["cfg"] == before


@pytest.mark.spec("workflow-mutation:overrides:unspecified-dial-untouched")
def test_apply_overrides_none_ip_weight_leaves_the_dial_unchanged(
    workflow: Workflow,
) -> None:
    before = workflow["8"]["inputs"]["ip_weight"]
    apply_overrides(workflow, ip_weight=None)
    assert workflow["8"]["inputs"]["ip_weight"] == before


@pytest.mark.spec("workflow-mutation:overrides:all-unspecified-is-a-no-op")
def test_apply_overrides_all_nones_leaves_the_workflow_unchanged(
    workflow: Workflow,
) -> None:
    before = copy.deepcopy(workflow)
    apply_overrides(workflow, denoise=None, cfg=None, ip_weight=None)
    assert workflow == before


@pytest.mark.spec("workflow-mutation:overrides:mutates-in-place")
def test_apply_overrides_mutates_in_place(workflow: Workflow) -> None:
    original = workflow
    apply_overrides(workflow, denoise=0.90)
    assert original["10"]["inputs"]["denoise"] == 0.90


@pytest.mark.spec("workflow-mutation:overrides:sets-denoise")
def test_apply_overrides_sets_a_zero_denoise(
    workflow: Workflow,
) -> None:
    # Zero is a valid dial value and must survive: a truthiness guard
    # (`if denoise:`) instead of `is not None` would discard it silently and
    # render at the workflow's baked value instead.
    apply_overrides(workflow, denoise=0.0)
    assert workflow["10"]["inputs"]["denoise"] == 0.0


@pytest.mark.spec("workflow-mutation:overrides:sets-cfg")
def test_apply_overrides_sets_a_zero_cfg(workflow: Workflow) -> None:
    apply_overrides(workflow, cfg=0.0)
    assert workflow["10"]["inputs"]["cfg"] == 0.0


@pytest.mark.spec("workflow-mutation:overrides:sets-ip-weight")
def test_apply_overrides_sets_a_zero_ip_weight(
    workflow: Workflow,
) -> None:
    apply_overrides(workflow, ip_weight=0.0)
    assert workflow["8"]["inputs"]["ip_weight"] == 0.0
