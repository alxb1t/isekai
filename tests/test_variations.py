import random
from pathlib import Path

import pytest

from isekai.comfy_types import Workflow
from isekai.mutate import mutate
from isekai.pipeline import run
from isekai.workflow import inject_animagine
from tests.fakes import FakeComfyClient


@pytest.mark.spec("workflow-mutation:variations:mutator-varies-submission")
def test_run_mutates_the_submitted_workflow_when_a_mutator_is_given(
    animagine_i2i_workflow: Workflow, tmp_path: Path
) -> None:
    client = FakeComfyClient()
    run(
        client,
        animagine_i2i_workflow,
        inject_animagine,
        "photo.jpg",
        "anime",
        str(tmp_path / "out.png"),
        mutate=mutate,
        seed=7,
    )
    assert client.submitted_workflow is not None
    assert client.submitted_workflow["10"]["inputs"]["seed"] == random.Random(
        7
    ).getrandbits(64)


@pytest.mark.spec("workflow-mutation:variations:no-mutator-stays-deterministic")
def test_run_leaves_the_workflow_deterministic_without_a_mutator(
    animagine_i2i_workflow: Workflow, tmp_path: Path
) -> None:
    baked = animagine_i2i_workflow["10"]["inputs"]["seed"]
    client = FakeComfyClient()
    run(
        client,
        animagine_i2i_workflow,
        inject_animagine,
        "photo.jpg",
        "anime",
        str(tmp_path / "out.png"),
    )
    assert client.submitted_workflow is not None
    assert client.submitted_workflow["10"]["inputs"]["seed"] == baked


@pytest.mark.spec("workflow-mutation:reproducibility:seed-is-printed")
def test_run_prints_the_seed_as_the_reproducibility_contract(
    animagine_i2i_workflow: Workflow, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    client = FakeComfyClient()
    run(
        client,
        animagine_i2i_workflow,
        inject_animagine,
        "photo.jpg",
        "anime",
        str(tmp_path / "out.png"),
        mutate=mutate,
        seed=7,
    )
    assert "7" in capsys.readouterr().out


@pytest.mark.spec("workflow-mutation:variations:one-output-per-variation")
def test_run_writes_one_output_per_variation(
    animagine_i2i_workflow: Workflow, tmp_path: Path
) -> None:
    client = FakeComfyClient()
    run(
        client,
        animagine_i2i_workflow,
        inject_animagine,
        "photo.jpg",
        "anime",
        str(tmp_path / "out.png"),
        mutate=mutate,
        variations=3,
    )
    assert {p.name for p in tmp_path.iterdir()} == {
        "out_0.png",
        "out_1.png",
        "out_2.png",
    }


# --- Phase 2: apply_overrides integration ---


@pytest.mark.spec("workflow-mutation:base-relative:override-applied-before-jitter")
def test_run_applies_override_before_mutate_so_jitter_is_around_the_new_base(
    animagine_i2i_workflow: Workflow, tmp_path: Path
) -> None:
    client = FakeComfyClient()
    run(
        client,
        animagine_i2i_workflow,
        inject_animagine,
        "photo.jpg",
        "anime",
        str(tmp_path / "out.png"),
        mutate=mutate,
        seed=42,
        overrides={"denoise": 0.80},
    )
    assert client.submitted_workflow is not None
    assert 0.75 <= client.submitted_workflow["10"]["inputs"]["denoise"] <= 0.85


@pytest.mark.spec("workflow-mutation:reproducibility:override-plus-seed-reproduces")
def test_run_with_override_and_seed_is_reproducible(
    animagine_i2i_workflow: Workflow, tmp_path: Path
) -> None:
    import copy as _copy

    wf_a = _copy.deepcopy(animagine_i2i_workflow)
    wf_b = _copy.deepcopy(animagine_i2i_workflow)

    client_a = FakeComfyClient()
    run(
        client_a,
        wf_a,
        inject_animagine,
        "photo.jpg",
        "anime",
        str(tmp_path / "out_a.png"),
        mutate=mutate,
        seed=77,
        overrides={"denoise": 0.72, "cfg": 6.5},
    )

    client_b = FakeComfyClient()
    run(
        client_b,
        wf_b,
        inject_animagine,
        "photo.jpg",
        "anime",
        str(tmp_path / "out_b.png"),
        mutate=mutate,
        seed=77,
        overrides={"denoise": 0.72, "cfg": 6.5},
    )

    assert client_a.submitted_workflow == client_b.submitted_workflow


@pytest.mark.spec(
    "workflow-mutation:reproducibility:no-override-matches-previous-release"
)
def test_run_without_overrides_is_byte_identical_to_v04(
    animagine_i2i_workflow: Workflow, tmp_path: Path
) -> None:
    client = FakeComfyClient()
    run(
        client,
        animagine_i2i_workflow,
        inject_animagine,
        "photo.jpg",
        "anime",
        str(tmp_path / "out.png"),
        mutate=mutate,
        seed=99,
    )
    wf = client.submitted_workflow
    assert wf is not None
    assert wf["10"]["inputs"]["denoise"] == 0.6200075444574945
    assert wf["10"]["inputs"]["cfg"] == 4.6788023205866125
    assert wf["8"]["inputs"]["ip_weight"] == 0.8748431318500969
