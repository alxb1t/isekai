import pytest

from isekai.comfy_types import Workflow
from isekai.workflow import find_node, inject_animagine


@pytest.mark.spec("workflow-injection:node-location:locates-by-class-type")
def test_find_node_locates_a_node_by_class_type() -> None:
    wf = {
        "7": {"class_type": "LoadImage", "_meta": {"title": "Load Image"}},
        "9": {"class_type": "KSampler", "_meta": {"title": "KSampler"}},
    }

    assert find_node(wf, class_type="LoadImage") == "7"


@pytest.mark.spec("workflow-injection:node-location:locates-by-title")
def test_find_node_locates_a_node_by_title() -> None:
    wf = {
        "7": {"class_type": "LoadImage", "_meta": {"title": "Load Image"}},
        "9": {"class_type": "KSampler", "_meta": {"title": "KSampler"}},
    }

    assert find_node(wf, title="KSampler") == "9"


@pytest.mark.spec("workflow-injection:node-location:exits-when-no-node-matches")
def test_find_node_exits_when_no_node_matches() -> None:
    wf = {"7": {"class_type": "LoadImage", "_meta": {"title": "Load Image"}}}

    with pytest.raises(SystemExit):
        find_node(wf, class_type="KSampler")


@pytest.mark.spec("workflow-injection:node-location:exits-when-ambiguous")
def test_find_node_exits_when_the_match_is_ambiguous() -> None:
    wf = {
        "1": {"class_type": "CLIPTextEncode", "_meta": {"title": "Positive"}},
        "2": {"class_type": "CLIPTextEncode", "_meta": {"title": "Negative"}},
    }

    with pytest.raises(SystemExit):
        find_node(wf, class_type="CLIPTextEncode")


@pytest.mark.spec("workflow-injection:node-location:single-load-image-in-real-workflow")
def test_find_node_locates_the_single_load_image_in_the_real_workflow(
    animagine_i2i_cn_workflow: Workflow,
) -> None:
    assert find_node(animagine_i2i_cn_workflow, class_type="LoadImage") == "2"


@pytest.mark.spec("workflow-injection:node-location:text-encoders-are-ambiguous")
def test_find_node_is_ambiguous_for_the_two_text_encoders(
    animagine_i2i_cn_workflow: Workflow,
) -> None:
    # The shipped graph carries a positive and a negative CLIPTextEncode, so a
    # class-type lookup cannot name either — which is why the positive string is
    # committed to the graph rather than reached by lookup.
    with pytest.raises(SystemExit):
        find_node(animagine_i2i_cn_workflow, class_type="CLIPTextEncode")


@pytest.mark.spec("workflow-injection:latent-init:img2img-inits-from-photo-below-one")
def test_graph_inits_the_latent_from_the_photo_at_denoise_below_one(
    animagine_i2i_cn_workflow: Workflow,
) -> None:
    # One LoadImage feeds VAEEncode, which seeds the KSampler latent at
    # denoise < 1 (from-photo, not from-noise).
    load_id = find_node(animagine_i2i_cn_workflow, class_type="LoadImage")
    vae_id = find_node(animagine_i2i_cn_workflow, class_type="VAEEncode")
    sampler_id = find_node(animagine_i2i_cn_workflow, class_type="KSampler")
    assert animagine_i2i_cn_workflow[vae_id]["inputs"]["pixels"][0] == load_id
    assert animagine_i2i_cn_workflow[sampler_id]["inputs"]["latent_image"][0] == vae_id
    assert animagine_i2i_cn_workflow[sampler_id]["inputs"]["denoise"] < 1


@pytest.mark.spec("workflow-injection:prompt-placement:traces-through-controlnet-chain")
def test_inject_traces_through_the_controlnet_chain_to_the_encoder(
    animagine_i2i_cn_workflow: Workflow,
) -> None:
    # CN apply nodes deepen the conditioning path
    # (KSampler.positive -> ControlNetApply(s) -> ApplyInstantID -> CLIPTextEncode),
    # so a fixed 2-hop trace no longer lands. The generalized walk must still
    # reach the real positive encoder.
    inject_animagine(
        animagine_i2i_cn_workflow, image_name="face.png", prompt="1girl, anime"
    )
    assert animagine_i2i_cn_workflow["3"]["inputs"]["text"] == "1girl, anime"
    assert animagine_i2i_cn_workflow["4"]["inputs"]["text"].startswith(
        "lowres, bad anatomy"
    )  # negative untouched


@pytest.mark.spec(
    "workflow-injection:photo-wiring:controlnet-single-loader-across-stack"
)
def test_inject_wires_the_single_load_image_across_the_stack(
    animagine_i2i_cn_workflow: Workflow,
) -> None:
    # One LoadImage fans out to VAEEncode + InstantID + all three CN preprocessors,
    # so find_node stays unique and the exactly-one-LoadImage rule holds.
    inject_animagine(
        animagine_i2i_cn_workflow, image_name="face.png", prompt="1girl, anime"
    )
    load_id = find_node(animagine_i2i_cn_workflow, class_type="LoadImage")
    assert animagine_i2i_cn_workflow[load_id]["inputs"]["image"] == "face.png"
