import pytest

from isekai.comfy_types import Workflow
from isekai.workflow import find_node, inject


def test_find_node_locates_a_node_by_class_type():
    wf = {
        "7": {"class_type": "LoadImage", "_meta": {"title": "Load Image"}},
        "9": {"class_type": "KSampler", "_meta": {"title": "KSampler"}},
    }

    assert find_node(wf, class_type="LoadImage") == "7"


def test_find_node_locates_a_node_by_title():
    wf = {
        "7": {"class_type": "LoadImage", "_meta": {"title": "Load Image"}},
        "9": {"class_type": "KSampler", "_meta": {"title": "KSampler"}},
    }

    assert find_node(wf, title="KSampler") == "9"


def test_find_node_exits_when_no_node_matches():
    wf = {"7": {"class_type": "LoadImage", "_meta": {"title": "Load Image"}}}

    with pytest.raises(SystemExit):
        find_node(wf, class_type="KSampler")


def test_find_node_exits_when_the_match_is_ambiguous():
    wf = {
        "1": {"class_type": "CLIPTextEncode", "_meta": {"title": "Positive"}},
        "2": {"class_type": "CLIPTextEncode", "_meta": {"title": "Negative"}},
    }

    with pytest.raises(SystemExit):
        find_node(wf, class_type="CLIPTextEncode")


def test_find_node_locates_the_single_load_image_in_the_real_workflow(qwen_workflow):
    assert find_node(qwen_workflow, class_type="LoadImage") == "78"


def test_find_node_is_ambiguous_for_the_two_qwen_text_encoders(qwen_workflow):
    # The exported graph has two TextEncodeQwenImageEdit nodes (positive + negative)
    # sharing a title — exactly why convert.py traces KSampler.positive instead of
    # searching for the encoder by class_type/title.
    with pytest.raises(SystemExit):
        find_node(qwen_workflow, class_type="TextEncodeQwenImageEdit")


def test_inject_points_load_image_at_the_uploaded_file(qwen_workflow: Workflow) -> None:
    inject(qwen_workflow, image_name="uploaded.png", prompt="make it anime")
    load_id = find_node(qwen_workflow, class_type="LoadImage")
    assert qwen_workflow[load_id]["inputs"]["image"] == "uploaded.png"


def test_inject_sets_the_prompt_on_the_positive_encoder_only(
    qwen_workflow: Workflow,
) -> None:
    inject(qwen_workflow, image_name="uploaded.png", prompt="make it anime")
    assert qwen_workflow["102:76"]["inputs"]["prompt"] == "make it anime"  # positive
    assert qwen_workflow["102:77"]["inputs"]["prompt"] == ""  # negative untouched
