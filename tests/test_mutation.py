import copy
import random

from isekai.mutate import mutate


def test_mutate_sets_the_ksampler_seed_from_the_rng(animagine_i2i_workflow):
    mutate(animagine_i2i_workflow, random.Random(0))
    assert animagine_i2i_workflow["10"]["inputs"]["seed"] == random.Random(
        0
    ).getrandbits(64)


def test_mutate_draws_a_64_bit_seed(animagine_i2i_workflow):
    mutate(animagine_i2i_workflow, random.Random(1))
    assert 0 <= animagine_i2i_workflow["10"]["inputs"]["seed"] < 2**64


def test_mutate_jitters_denoise_within_range(animagine_i2i_workflow):
    for i in range(100):
        wf = copy.deepcopy(animagine_i2i_workflow)
        mutate(wf, random.Random(i))
        assert 0.60 <= wf["10"]["inputs"]["denoise"] <= 0.70


def test_mutate_jitters_cfg_within_range(animagine_i2i_workflow):
    for i in range(100):
        wf = copy.deepcopy(animagine_i2i_workflow)
        mutate(wf, random.Random(i))
        assert 4.5 <= wf["10"]["inputs"]["cfg"] <= 5.5


def test_mutate_jitters_ip_weight_within_range(animagine_i2i_workflow):
    for i in range(100):
        wf = copy.deepcopy(animagine_i2i_workflow)
        mutate(wf, random.Random(i))
        assert 0.85 <= wf["8"]["inputs"]["ip_weight"] <= 0.95


def test_mutate_is_reproducible_for_the_same_seed(animagine_i2i_workflow):
    a = copy.deepcopy(animagine_i2i_workflow)
    b = copy.deepcopy(animagine_i2i_workflow)
    mutate(a, random.Random(42))
    mutate(b, random.Random(42))
    assert a == b


def test_mutate_differs_for_distinct_rng_states(animagine_i2i_workflow):
    a = copy.deepcopy(animagine_i2i_workflow)
    b = copy.deepcopy(animagine_i2i_workflow)
    mutate(a, random.Random(1))
    mutate(b, random.Random(2))
    assert a["10"]["inputs"]["seed"] != b["10"]["inputs"]["seed"]


def test_mutate_jitters_the_controlnet_strenghts(
    animagine_i2i_cn_workflow,
) -> None:
    before = {
        nid: n["inputs"]["strength"]
        for nid, n in animagine_i2i_cn_workflow.items()
        if n["class_type"] == "ControlNetApplyAdvanced"
    }
    assert before

    wf = copy.deepcopy(animagine_i2i_cn_workflow)
    mutate(wf, random.Random(3))
    after = {nid: wf[nid]["inputs"]["strength"] for nid in before}

    assert after != before
    for nid, base in before.items():
        assert max(0.0, base - 0.1) <= after[nid] <= min(1.0, base + 0.1)


def test_mutate_keeps_every_controlnet_strength_in_its_band(
    animagine_i2i_cn_workflow,
) -> None:
    bases = {
        nid: n["inputs"]["strength"]
        for nid, n in animagine_i2i_cn_workflow.items()
        if n["class_type"] == "ControlNetApplyAdvanced"
    }
    for i in range(100):
        wf = copy.deepcopy(animagine_i2i_cn_workflow)
        mutate(wf, random.Random(i))
        for nid, base in bases.items():
            s = wf[nid]["inputs"]["strength"]
            assert max(0.0, base - 0.1) <= s <= min(1.0, base + 0.1)


def test_mutate_in_reproducible_on_the_controlnet_path(
    animagine_i2i_cn_workflow,
) -> None:
    a = copy.deepcopy(animagine_i2i_cn_workflow)
    b = copy.deepcopy(animagine_i2i_cn_workflow)
    mutate(a, random.Random(7))
    mutate(b, random.Random(7))
    assert a == b


# --- Phase 1: base-relative jitter ---


def test_mutate_with_baked_defaults_reproduces_today_output(animagine_i2i_workflow):
    mutate(animagine_i2i_workflow, random.Random(99))
    assert animagine_i2i_workflow["10"]["inputs"]["seed"] == 7023646418445998953
    assert animagine_i2i_workflow["10"]["inputs"]["denoise"] == 0.6200075444574945
    assert animagine_i2i_workflow["10"]["inputs"]["cfg"] == 4.6788023205866125
    assert animagine_i2i_workflow["8"]["inputs"]["ip_weight"] == 0.8748431318500969


def test_mutate_jitters_denoise_around_its_current_base(animagine_i2i_workflow):
    animagine_i2i_workflow["10"]["inputs"]["denoise"] = 0.70
    for i in range(100):
        wf = copy.deepcopy(animagine_i2i_workflow)
        mutate(wf, random.Random(i))
        assert 0.65 <= wf["10"]["inputs"]["denoise"] <= 0.75


def test_mutate_jitters_cfg_around_its_current_base(animagine_i2i_workflow):
    animagine_i2i_workflow["10"]["inputs"]["cfg"] = 6.0
    for i in range(100):
        wf = copy.deepcopy(animagine_i2i_workflow)
        mutate(wf, random.Random(i))
        assert 5.5 <= wf["10"]["inputs"]["cfg"] <= 6.5


def test_mutate_jitters_ip_weight_around_its_current_base(animagine_i2i_workflow):
    animagine_i2i_workflow["8"]["inputs"]["ip_weight"] = 0.80
    for i in range(100):
        wf = copy.deepcopy(animagine_i2i_workflow)
        mutate(wf, random.Random(i))
        assert 0.75 <= wf["8"]["inputs"]["ip_weight"] <= 0.85
