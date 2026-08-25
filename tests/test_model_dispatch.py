import pytest

from isekai.models import get_model
from isekai.mutate import mutate
from isekai.workflow import inject_animagine, inject_qwen


@pytest.mark.spec("model-registry:name-resolution:qwen-resolves-to-its-workflow")
def test_dispatch_selects_the_qwen_workflow():
    assert get_model("qwen").workflow_path == "workflows/qwen-image-edit.json"


@pytest.mark.spec("model-registry:name-resolution:animagine-resolves-to-its-workflow")
def test_dispatch_selects_the_animagine_workflow():
    assert get_model("animagine").workflow_path == "workflows/animagine-instantid.json"


@pytest.mark.spec("model-registry:name-resolution:unknown-name-rejected")
def test_dispatch_exits_on_an_unknown_model():
    with pytest.raises(SystemExit):
        get_model("midjourney")


@pytest.mark.spec("model-registry:name-resolution:unknown-name-message-guides-the-user")
def test_dispatch_names_the_unknown_model_and_lists_the_valid_ones():
    with pytest.raises(SystemExit) as exit_info:
        get_model("midjourney")

    message = str(exit_info.value)

    assert "'midjourney'" in message
    # Guards the shell-style "${name}" typo: the f-string interpolates, so a
    # literal $ in the rendered message means the brace form leaked through.
    assert "$" not in message
    for known in ("qwen", "animagine", "animagine-i2i", "animagine-i2i-cn"):
        assert known in message


@pytest.mark.spec("model-registry:injector-pairing:qwen-uses-qwen-injector")
def test_dispatch_pairs_qwen_with_its_injection_adapter():
    assert get_model("qwen").inject is inject_qwen


@pytest.mark.spec("model-registry:injector-pairing:animagine-uses-animagine-injector")
def test_dispatch_pairs_animagine_with_its_injection_adapter():
    assert get_model("animagine").inject is inject_animagine


@pytest.mark.spec(
    "model-registry:name-resolution:animagine-i2i-resolves-to-its-workflow"
)
def test_dispatch_selects_the_animagine_i2i_workflow():
    assert get_model("animagine-i2i").workflow_path == "workflows/animagine-i2i.json"


@pytest.mark.spec("model-registry:injector-pairing:i2i-reuses-animagine-injector")
def test_dispatch_reuses_the_animagine_injector_for_img2img():
    assert get_model("animagine-i2i").inject is inject_animagine


@pytest.mark.spec("model-registry:mutation-pairing:i2i-carries-the-seam")
def test_dispatch_pairs_animagine_i2i_with_the_mutation_seam():
    assert get_model("animagine-i2i").mutate is mutate


@pytest.mark.spec("model-registry:mutation-pairing:earlier-models-have-no-mutator")
def test_dispatch_leaves_earlier_models_without_a_mutator():
    assert get_model("qwen").mutate is None
    assert get_model("animagine").mutate is None


@pytest.mark.spec(
    "model-registry:name-resolution:animagine-i2i-cn-resolves-to-its-workflow"
)
def test_dispatch_selects_the_animagine_i2i_cn_workflow():
    assert (
        get_model("animagine-i2i-cn").workflow_path == "workflows/animagine-i2i-cn.json"
    )


@pytest.mark.spec("model-registry:injector-pairing:cn-reuses-animagine-injector")
def test_dispatch_reuses_the_animagine_injector_for_the_cn_path():
    assert get_model("animagine-i2i-cn").inject is inject_animagine


@pytest.mark.spec("model-registry:mutation-pairing:cn-carries-the-seam")
def test_dispatch_pairs_animagine_i2i_cn_with_the_mutation_seam():
    assert get_model("animagine-i2i-cn").mutate is mutate
