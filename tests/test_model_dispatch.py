import pytest

from isekai.models import get_model
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
