from pathlib import Path

import pytest

from isekai.comfy_types import Workflow
from isekai.pipeline import run
from isekai.workflow import inject_animagine
from tests.fakes import FakeComfyClient


@pytest.mark.spec("comfy-transport:polling:polls-history-until-complete")
def test_run_polls_history_until_the_prompt_completes(
    animagine_i2i_cn_workflow: Workflow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("time.sleep", lambda *_: None)
    client = FakeComfyClient(pending_polls=2)
    output = tmp_path / "out.png"

    run(
        client,
        animagine_i2i_cn_workflow,
        inject_animagine,
        "photo.jpg",
        "1girl, anime",
        str(output),
    )

    assert client.history_calls == 3
    assert output.read_bytes() == client.view_bytes


@pytest.mark.spec("comfy-transport:retrieval:downloads-image-named-in-history")
def test_run_downloads_the_image_named_in_the_history(
    animagine_i2i_cn_workflow: Workflow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("time.sleep", lambda *_: None)
    client = FakeComfyClient(
        image={"filename": "anime_00001.png", "subfolder": "sub", "type": "output"}
    )
    output = tmp_path / "out.png"

    run(
        client,
        animagine_i2i_cn_workflow,
        inject_animagine,
        "photo.jpg",
        "1girl, anime",
        str(output),
    )

    assert client.viewed == {
        "filename": "anime_00001.png",
        "subfolder": "sub",
        "type": "output",
    }
