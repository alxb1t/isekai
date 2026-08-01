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
        mutate(animagine_i2i_workflow, random.Random(i))
        assert 0.60 <= animagine_i2i_workflow["10"]["inputs"]["denoise"] <= 0.70


def test_mutate_jitters_cfg_within_range(animagine_i2i_workflow):
    for i in range(100):
        mutate(animagine_i2i_workflow, random.Random(i))
        assert 4.5 <= animagine_i2i_workflow["10"]["inputs"]["cfg"] <= 5.5


def test_mutate_jitters_ip_weight_within_range(animagine_i2i_workflow):
    for i in range(100):
        mutate(animagine_i2i_workflow, random.Random(i))
        assert 0.85 <= animagine_i2i_workflow["8"]["inputs"]["ip_weight"] <= 0.95


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
