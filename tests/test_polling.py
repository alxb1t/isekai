from pathlib import Path

import pytest

from isekai.comfy_types import Workflow
from isekai.pipeline import run
from tests.fakes import FakeComfyClient


@pytest.mark.spec("comfy-transport:polling:polls-history-until-complete")
def test_run_polls_history_until_the_prompt_completes(
    workflow: Workflow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("time.sleep", lambda *_: None)
    client = FakeComfyClient(pending_polls=2)
    run_dir = tmp_path / "20260904T141530Z"

    run(client, workflow, "photo.jpg", run_dir, variations=1)

    assert client.history_calls == 3
    assert (run_dir / "0.png").read_bytes() == client.view_bytes


@pytest.mark.spec("comfy-transport:retrieval:downloads-image-named-in-history")
def test_run_downloads_the_image_named_in_the_history(
    workflow: Workflow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("time.sleep", lambda *_: None)
    client = FakeComfyClient(
        image={"filename": "anime_00001.png", "subfolder": "sub", "type": "output"}
    )
    run_dir = tmp_path / "20260904T141530Z"

    run(client, workflow, "photo.jpg", run_dir, variations=1)

    assert client.viewed == {
        "filename": "anime_00001.png",
        "subfolder": "sub",
        "type": "output",
    }
