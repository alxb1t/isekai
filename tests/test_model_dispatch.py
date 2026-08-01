import pytest

from isekai.models import get_model
from isekai.mutate import mutate
from isekai.workflow import inject_animagine, inject_qwen


def test_dispatch_selects_the_qwen_workflow():
    assert get_model("qwen").workflow_path == "workflows/qwen-image-edit.json"


def test_dispatch_selects_the_animagine_workflow():
    assert get_model("animagine").workflow_path == "workflows/animagine-instantid.json"


def test_dispatch_exits_on_an_unknown_model():
    with pytest.raises(SystemExit):
        get_model("midjourney")


def test_dispatch_pairs_qwen_with_its_injection_adapter():
    assert get_model("qwen").inject is inject_qwen


def test_dispatch_pairs_animagine_with_its_injection_adapter():
    assert get_model("animagine").inject is inject_animagine


def test_dispatch_selects_the_animagine_i2i_workflow():
    assert get_model("animagine-i2i").workflow_path == "workflows/animagine-i2i.json"


def test_dispatch_reuses_the_animagine_injector_for_img2img():
    assert get_model("animagine-i2i").inject is inject_animagine


def test_dispatch_pairs_animagine_i2i_with_the_mutation_seam():
    assert get_model("animagine-i2i").mutate is mutate


def test_dispatch_leaves_earlier_models_without_a_mutator():
    assert get_model("qwen").mutate is None
    assert get_model("animagine").mutate is None
