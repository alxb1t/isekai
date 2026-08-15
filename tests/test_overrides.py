import copy

from isekai.overrides import apply_overrides


def test_apply_overrides_sets_denoise_on_the_ksampler(animagine_i2i_workflow):
    apply_overrides(animagine_i2i_workflow, denoise=0.80)
    assert animagine_i2i_workflow["10"]["inputs"]["denoise"] == 0.80


def test_apply_overrides_sets_cfg_on_the_ksampler(animagine_i2i_workflow):
    apply_overrides(animagine_i2i_workflow, cfg=7.0)
    assert animagine_i2i_workflow["10"]["inputs"]["cfg"] == 7.0


def test_apply_overrides_sets_ip_weight_on_apply_instantid_advanced(
    animagine_i2i_workflow,
):
    apply_overrides(animagine_i2i_workflow, ip_weight=0.75)
    assert animagine_i2i_workflow["8"]["inputs"]["ip_weight"] == 0.75


def test_apply_overrides_none_denoise_leaves_the_dial_unchanged(animagine_i2i_workflow):
    before = animagine_i2i_workflow["10"]["inputs"]["denoise"]
    apply_overrides(animagine_i2i_workflow, denoise=None)
    assert animagine_i2i_workflow["10"]["inputs"]["denoise"] == before


def test_apply_overrides_none_cfg_leaves_the_dial_unchanged(animagine_i2i_workflow):
    before = animagine_i2i_workflow["10"]["inputs"]["cfg"]
    apply_overrides(animagine_i2i_workflow, cfg=None)
    assert animagine_i2i_workflow["10"]["inputs"]["cfg"] == before


def test_apply_overrides_none_ip_weight_leaves_the_dial_unchanged(
    animagine_i2i_workflow,
):
    before = animagine_i2i_workflow["8"]["inputs"]["ip_weight"]
    apply_overrides(animagine_i2i_workflow, ip_weight=None)
    assert animagine_i2i_workflow["8"]["inputs"]["ip_weight"] == before


def test_apply_overrides_all_nones_leaves_the_workflow_unchanged(
    animagine_i2i_workflow,
):
    before = copy.deepcopy(animagine_i2i_workflow)
    apply_overrides(animagine_i2i_workflow, denoise=None, cfg=None, ip_weight=None)
    assert animagine_i2i_workflow == before


def test_apply_overrides_ip_weight_is_silently_ignored_when_no_instantid_node(
    qwen_workflow,
):
    before = copy.deepcopy(qwen_workflow)
    apply_overrides(qwen_workflow, ip_weight=0.50)
    # No ApplyInstantIDAdvanced node — no exception and nothing else changed
    assert qwen_workflow == before


def test_apply_overrides_mutates_in_place(animagine_i2i_workflow):
    original = animagine_i2i_workflow
    apply_overrides(animagine_i2i_workflow, denoise=0.90)
    assert original["10"]["inputs"]["denoise"] == 0.90
