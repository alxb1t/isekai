import inspect

import pytest

from isekai import cli
from isekai.comfy_types import Workflow
from isekai.workflow import find_node, inject


@pytest.mark.spec("workflow-injection:node-location:locates-by-class-type")
def test_find_node_locates_a_node_by_class_type() -> None:
    wf = {
        "7": {"class_type": "LoadImage", "_meta": {"title": "Load Image"}},
        "9": {"class_type": "KSampler", "_meta": {"title": "KSampler"}},
    }

    assert find_node(wf, class_type="LoadImage") == "7"


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
    workflow: Workflow,
) -> None:
    assert find_node(workflow, class_type="LoadImage") == "2"


@pytest.mark.spec("workflow-injection:node-location:text-encoders-are-ambiguous")
def test_find_node_is_ambiguous_for_the_two_text_encoders(
    workflow: Workflow,
) -> None:
    # The shipped graph carries a positive and a negative CLIPTextEncode, so a
    # class-type lookup cannot name either — which is why the positive string is
    # committed to the graph rather than reached by lookup.
    with pytest.raises(SystemExit):
        find_node(workflow, class_type="CLIPTextEncode")


@pytest.mark.spec("workflow-injection:latent-init:inits-from-photo-below-one")
def test_graph_inits_the_latent_from_the_photo_at_denoise_below_one(
    workflow: Workflow,
) -> None:
    # One LoadImage feeds VAEEncode, which seeds the KSampler latent at
    # denoise < 1 (from-photo, not from-noise).
    load_id = find_node(workflow, class_type="LoadImage")
    vae_id = find_node(workflow, class_type="VAEEncode")
    sampler_id = find_node(workflow, class_type="KSampler")
    assert workflow[vae_id]["inputs"]["pixels"][0] == load_id
    assert workflow[sampler_id]["inputs"]["latent_image"][0] == vae_id
    assert workflow[sampler_id]["inputs"]["denoise"] < 1


@pytest.mark.spec("workflow-injection:photo-wiring:single-loader-fans-out")
def test_inject_wires_the_single_load_image_across_the_stack(
    workflow: Workflow,
) -> None:
    # One LoadImage fans out to VAEEncode + InstantID + all three CN preprocessors,
    # so find_node stays unique and the exactly-one-LoadImage rule holds.
    inject(workflow, image_name="face.png")
    load_id = find_node(workflow, class_type="LoadImage")
    assert workflow[load_id]["inputs"]["image"] == "face.png"


# --- v0.8: the positive prompt is graph configuration -----------------------

# The committed positive string, pinned by equality rather than by a blacklist:
# "the string holds no subject text" has no mechanical form, and a test asserting
# `"arms crossed" not in text` is defeated silently by any rewrite. Equality
# makes every future prompt edit a deliberate test edit, which is what makes
# "not typeable" a property rather than a convention (design.md D7).
#
# The register tags -- `1girl, solo` -- are the Danbooru mode selector for this
# base, not subject text, and are OWNED BY v0.9, the version that changes the
# base and can probe a replacement against real renders. `1girl` fixing the
# gender of every input photo is a known, recorded defect of this version.
COMMITTED_POSITIVE = (
    "1girl, solo, anime screencap, detailed eyes, soft lighting, "
    "masterpiece, high score, great score"
)


@pytest.mark.spec("workflow-injection:committed-prompt:string-is-pinned")
def test_the_committed_positive_string_is_pinned(workflow: Workflow) -> None:
    assert workflow["3"]["inputs"]["text"] == COMMITTED_POSITIVE


@pytest.mark.spec("workflow-injection:committed-prompt:carries-no-pose-tag")
def test_the_committed_positive_carries_no_pose_tag() -> None:
    # Pose is the OpenPose ControlNet's axis. A pose tag in the prompt competes
    # with the mechanism that owns it, so it is removed on that argument alone --
    # no render is needed to justify it.
    assert "arms crossed" not in COMMITTED_POSITIVE


@pytest.mark.spec("workflow-injection:committed-prompt:not-settable-from-the-cli")
def test_no_command_line_path_sets_the_positive_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Two halves, both needed: no flag carries a prompt, AND injection takes no
    # prompt argument -- so there is no path by which typed text reaches the
    # encoder even if a flag were added back.
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "--prompt", "anime"])
    with pytest.raises(SystemExit):
        cli.parse_args()

    assert list(inspect.signature(inject).parameters) == ["workflow", "image_name"]


@pytest.mark.spec("workflow-injection:committed-prompt:negative-is-untouched")
def test_injection_leaves_the_negative_encoder_as_the_graph_committed_it(
    workflow: Workflow,
) -> None:
    before = workflow["4"]["inputs"]["text"]
    inject(workflow, image_name="face.png")
    assert workflow["4"]["inputs"]["text"] == before
    assert before.startswith("lowres, bad anatomy")
