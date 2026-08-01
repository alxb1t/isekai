import random
from pathlib import Path

import pytest

from isekai.comfy_types import Workflow
from isekai.mutate import mutate
from isekai.pipeline import run
from isekai.workflow import inject_animagine
from tests.fakes import FakeComfyClient


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
