import pytest

from isekai import cli
from isekai.workflow import inject_animagine


def test_parse_args_defaults_to_the_animagine_i2i_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "--prompt", "anime"])
    assert cli.parse_args().model == "animagine-i2i"


def test_parse_args_accepts_the_animagine_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--model", "animagine"],
    )
    assert cli.parse_args().model == "animagine"


def test_parse_args_rejects_an_unknown_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--model", "midjourney"],
    )
    with pytest.raises(SystemExit):
        cli.parse_args()


def test_main_dispatches_the_animagine_workflow_and_injector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "face.jpg", "--prompt", "anime", "--model", "animagine"],
    )

    recorded = {}

    class FakePath:
        def __init__(self, path) -> None:
            recorded["workflow_path"] = path

        def read_text(self):
            return "{}"

    monkeypatch.setattr(cli, "Path", FakePath)
    monkeypatch.setattr(cli, "ComfyClient", lambda server: None)

    captured = {}

    def fake_run(
        client,
        workflow,
        inject,
        input_path,
        prompt,
        output_path,
        mutate=None,
        seed=None,
        variations=1,
    ):
        captured["inject"] = inject
        captured["input_path"] = input_path

    monkeypatch.setattr(cli, "run", fake_run)

    cli.main()

    assert recorded["workflow_path"] == "workflows/animagine-instantid.json"
    assert captured["inject"] is inject_animagine
    assert captured["input_path"] == "face.jpg"


def test_parse_args_accepts_the_animagine_i2i_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--model", "animagine-i2i"],
    )
    assert cli.parse_args().model == "animagine-i2i"


def test_main_dispatches_the_animagine_i2i_workflow_and_reuses_the_injector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "face.jpg", "--prompt", "anime", "--model", "animagine-i2i"],
    )

    recorded = {}

    class FakePath:
        def __init__(self, path) -> None:
            recorded["workflow_path"] = path

        def read_text(self):
            return "{}"

    monkeypatch.setattr(cli, "Path", FakePath)
    monkeypatch.setattr(cli, "ComfyClient", lambda server: None)

    captured = {}

    def fake_run(
        client,
        workflow,
        inject,
        input_path,
        prompt,
        output_path,
        mutate=None,
        seed=None,
        variations=1,
    ):
        captured["inject"] = inject

    monkeypatch.setattr(cli, "run", fake_run)

    cli.main()

    assert recorded["workflow_path"] == "workflows/animagine-i2i.json"
    assert captured["inject"] is inject_animagine


def test_parse_args_defaults_seed_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "--prompt", "anime"])
    assert cli.parse_args().seed is None


def test_parse_args_accepts_a_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv", ["convert.py", "photo.jpg", "--prompt", "anime", "--seed", "42"]
    )
    assert cli.parse_args().seed == 42


def test_parse_args_defaults_variations_to_one(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "--prompt", "anime"])
    assert cli.parse_args().variations == 1


def test_parse_args_accepts_a_variation_count(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--variations", "3"],
    )
    assert cli.parse_args().variations == 3
