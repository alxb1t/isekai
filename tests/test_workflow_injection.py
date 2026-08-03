import pytest

from isekai.comfy_types import Workflow
from isekai.workflow import find_node, inject_animagine, inject_qwen


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
    inject_qwen(qwen_workflow, image_name="uploaded.png", prompt="make it anime")
    load_id = find_node(qwen_workflow, class_type="LoadImage")
    assert qwen_workflow[load_id]["inputs"]["image"] == "uploaded.png"


def test_inject_sets_the_prompt_on_the_positive_encoder_only(
    qwen_workflow: Workflow,
) -> None:
    inject_qwen(qwen_workflow, image_name="uploaded.png", prompt="make it anime")
    assert qwen_workflow["102:76"]["inputs"]["prompt"] == "make it anime"  # positive
    assert qwen_workflow["102:77"]["inputs"]["prompt"] == ""  # negative untouched


def test_inject_animagine_points_load_image_at_the_reference_face(
    animagine_workflow: Workflow,
) -> None:
    inject_animagine(animagine_workflow, image_name="face.png", prompt="1girl, anime")
    load_id = find_node(animagine_workflow, class_type="LoadImage")
    assert animagine_workflow[load_id]["inputs"]["image"] == "face.png"


def test_inject_animagine_sets_the_prompt_on_the_positive_encoder_only(
    animagine_workflow: Workflow,
) -> None:
    inject_animagine(animagine_workflow, image_name="face.png", prompt="1girl, anime")
    assert animagine_workflow["3"]["inputs"]["text"] == "1girl, anime"  # positive
    assert animagine_workflow["4"]["inputs"]["text"].startswith(
        "lowres, bad anatomy"
    )  # negative untouched


def test_inject_animagine_wires_the_single_load_image_in_the_img2img_graph(
    animagine_i2i_workflow: Workflow,
) -> None:
    # One LoadImage fans out to BOTH VAEEncode and InstantID, so find_node stays unique:
    # convert.py's exactly-one-LoadImage invariant holds and inject_animagine is unchanged.
    inject_animagine(
        animagine_i2i_workflow, image_name="face.png", prompt="1girl, anime"
    )
    load_id = find_node(animagine_i2i_workflow, class_type="LoadImage")
    assert animagine_i2i_workflow[load_id]["inputs"]["image"] == "face.png"


def test_inject_animagine_sets_the_prompt_on_the_img2img_positive_encoder(
    animagine_i2i_workflow: Workflow,
) -> None:
    inject_animagine(
        animagine_i2i_workflow, image_name="face.png", prompt="1girl, anime"
    )
    assert animagine_i2i_workflow["3"]["inputs"]["text"] == "1girl, anime"
    assert animagine_i2i_workflow["4"]["inputs"]["text"].startswith(
        "lowres, bad anatomy"
    )  # negative untouched


def test_img2img_graph_inits_the_latent_from_the_photo_at_denoise_below_one(
    animagine_i2i_workflow: Workflow,
) -> None:
    # The topology delta vs v0.2: one LoadImage feeds VAEEncode, which seeds the
    # KSampler latent at denoise < 1 (from-photo, not from-noise).
    load_id = find_node(animagine_i2i_workflow, class_type="LoadImage")
    vae_id = find_node(animagine_i2i_workflow, class_type="VAEEncode")
    sampler_id = find_node(animagine_i2i_workflow, class_type="KSampler")
    assert animagine_i2i_workflow[vae_id]["inputs"]["pixels"][0] == load_id
    assert animagine_i2i_workflow[sampler_id]["inputs"]["latent_image"][0] == vae_id
    assert animagine_i2i_workflow[sampler_id]["inputs"]["denoise"] < 1


def test_inject_animagine_traces_through_the_controlnet_chain_to_the_encoder(
    animagine_i2i_cn_workflow: Workflow,
) -> None:
    # CN apply nodes deepen the conditioning path
    # (KSampler.positive -> ControlNetApply(s) -> ApplyInstantID -> CLIPTextEncode),
    # so the fixed 2-hop trace no longer lands. The generalized walk must still
    # reach the real positive encoder.
    inject_animagine(
        animagine_i2i_cn_workflow, image_name="face.png", prompt="1girl, anime"
    )
    assert animagine_i2i_cn_workflow["3"]["inputs"]["text"] == "1girl, anime"
    assert animagine_i2i_cn_workflow["4"]["inputs"]["text"].startswith(
        "lowres, bad anatomy"
    )  # negative untouched


def test_inject_animagine_cn_wires_the_single_load_image_across_the_stack(
    animagine_i2i_cn_workflow: Workflow,
) -> None:
    # One LoadImage fans out to VAEEncode + InstantID + all three CN preprocessors,
    # so find_node stays unique and convert.py's exactly-one-LoadImage rule holds.
    inject_animagine(
        animagine_i2i_cn_workflow, image_name="face.png", prompt="1girl, anime"
    )
    load_id = find_node(animagine_i2i_cn_workflow, class_type="LoadImage")
    assert animagine_i2i_cn_workflow[load_id]["inputs"]["image"] == "face.png"
