import pytest

from isekai import cli
from isekai.mutate import mutate as mutate_fn
from isekai.workflow import inject_animagine


def _capturing_run(captured: dict):
    """A `run` double recording EVERY argument `main()` passes.

    Capturing all of them is the point. A double that merely declares
    `mutate=None, seed=None, variations=1` as defaults cannot distinguish
    "main() passed this" from "main() passed nothing", so deleting the
    plumbing in main() would leave the suite green.
    """

    def fake_run(*args, **kwargs):
        names = (
            "client",
            "workflow",
            "inject",
            "input_path",
            "prompt",
            "output_path",
        )
        captured.update(dict(zip(names, args)))
        captured.update(kwargs)

    return fake_run


@pytest.mark.spec("cli:model-selection:defaults-to-animagine-i2i")
def test_parse_args_defaults_to_the_animagine_i2i_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "--prompt", "anime"])
    assert cli.parse_args().model == "animagine-i2i"


@pytest.mark.spec("cli:model-selection:accepts-animagine")
def test_parse_args_accepts_the_animagine_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--model", "animagine"],
    )
    assert cli.parse_args().model == "animagine"


@pytest.mark.spec("cli:model-selection:rejects-unknown-model")
def test_parse_args_rejects_an_unknown_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--model", "midjourney"],
    )
    with pytest.raises(SystemExit):
        cli.parse_args()


@pytest.mark.spec("cli:dispatch:animagine-workflow-and-injector")
@pytest.mark.spec("cli:reproducibility:seed-defaults-to-unset")
@pytest.mark.spec("cli:reproducibility:variations-default-to-one")
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

    monkeypatch.setattr(cli, "run", _capturing_run(captured))

    cli.main()

    assert recorded["workflow_path"] == "workflows/animagine-instantid.json"
    assert captured["inject"] is inject_animagine
    assert captured["input_path"] == "face.jpg"
    # animagine carries no mutator, so main() must hand run() None explicitly.
    assert captured["mutate"] is None
    assert captured["seed"] is None
    assert captured["variations"] == 1


@pytest.mark.spec("cli:model-selection:accepts-animagine-i2i")
def test_parse_args_accepts_the_animagine_i2i_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--model", "animagine-i2i"],
    )
    assert cli.parse_args().model == "animagine-i2i"


@pytest.mark.spec("cli:dispatch:img2img-workflow-reuses-injector")
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

    monkeypatch.setattr(cli, "run", _capturing_run(captured))

    cli.main()

    assert recorded["workflow_path"] == "workflows/animagine-i2i.json"
    assert captured["inject"] is inject_animagine
    # The img2img model carries the mutation seam; dropping `mutate=model.mutate`
    # from main() would silently disable all jitter for every run.
    assert captured["mutate"] is mutate_fn


@pytest.mark.spec("cli:reproducibility:seed-defaults-to-unset")
def test_parse_args_defaults_seed_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "--prompt", "anime"])
    assert cli.parse_args().seed is None


@pytest.mark.spec("cli:reproducibility:accepts-a-seed")
def test_parse_args_accepts_a_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv", ["convert.py", "photo.jpg", "--prompt", "anime", "--seed", "42"]
    )
    assert cli.parse_args().seed == 42


@pytest.mark.spec("cli:reproducibility:variations-default-to-one")
def test_parse_args_defaults_variations_to_one(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "--prompt", "anime"])
    assert cli.parse_args().variations == 1


@pytest.mark.spec("cli:reproducibility:accepts-a-variation-count")
def test_parse_args_accepts_a_variation_count(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--variations", "3"],
    )
    assert cli.parse_args().variations == 3


@pytest.mark.spec("cli:model-selection:accepts-animagine-i2i-cn")
def test_cli_accepts_the_animagine_i2i_cn_model(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--model", "animagine-i2i-cn"],
    )
    assert cli.parse_args().model == "animagine-i2i-cn"


# --- Phase 2: --denoise / --cfg / --ip-weight flags ---


@pytest.mark.spec("cli:dial-defaults:denoise-defaults-to-unset")
def test_parse_args_defaults_denoise_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "--prompt", "anime"])
    assert cli.parse_args().denoise is None


@pytest.mark.spec("cli:dial-defaults:cfg-defaults-to-unset")
def test_parse_args_defaults_cfg_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "--prompt", "anime"])
    assert cli.parse_args().cfg is None


@pytest.mark.spec("cli:dial-defaults:ip-weight-defaults-to-unset")
def test_parse_args_defaults_ip_weight_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "--prompt", "anime"])
    assert cli.parse_args().ip_weight is None


@pytest.mark.spec("cli:dial-validation:accepts-denoise-in-range")
def test_parse_args_accepts_denoise_in_range(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--denoise", "0.7"],
    )
    assert cli.parse_args().denoise == pytest.approx(0.7)


@pytest.mark.spec("cli:dial-validation:accepts-cfg-in-range")
def test_parse_args_accepts_cfg_in_range(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--cfg", "7.5"],
    )
    assert cli.parse_args().cfg == pytest.approx(7.5)


@pytest.mark.spec("cli:dial-validation:accepts-ip-weight-in-range")
def test_parse_args_accepts_ip_weight_in_range(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--ip-weight", "0.85"],
    )
    assert cli.parse_args().ip_weight == pytest.approx(0.85)


@pytest.mark.spec("cli:dial-validation:rejects-denoise-above-one")
def test_parse_args_rejects_denoise_above_one(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--denoise", "1.1"],
    )
    with pytest.raises(SystemExit):
        cli.parse_args()


@pytest.mark.spec("cli:dial-validation:rejects-denoise-below-zero")
def test_parse_args_rejects_denoise_below_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--denoise", "-0.1"],
    )
    with pytest.raises(SystemExit):
        cli.parse_args()


@pytest.mark.spec("cli:dial-validation:rejects-cfg-above-thirty")
def test_parse_args_rejects_cfg_above_thirty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--cfg", "31.0"],
    )
    with pytest.raises(SystemExit):
        cli.parse_args()


@pytest.mark.spec("cli:dial-validation:rejects-cfg-below-zero")
def test_parse_args_rejects_cfg_below_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--cfg", "-1.0"],
    )
    with pytest.raises(SystemExit):
        cli.parse_args()


@pytest.mark.spec("cli:dial-validation:rejects-ip-weight-above-one")
def test_parse_args_rejects_ip_weight_above_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--ip-weight", "1.5"],
    )
    with pytest.raises(SystemExit):
        cli.parse_args()


@pytest.mark.spec("cli:dial-validation:rejects-ip-weight-below-zero")
def test_parse_args_rejects_ip_weight_below_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--ip-weight", "-0.5"],
    )
    with pytest.raises(SystemExit):
        cli.parse_args()


@pytest.mark.spec("cli:dial-plumbing:overrides-reach-the-run")
@pytest.mark.spec("cli:reproducibility:accepts-a-seed")
@pytest.mark.spec("cli:reproducibility:accepts-a-variation-count")
def test_main_passes_override_flags_to_pipeline_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "convert.py",
            "photo.jpg",
            "--prompt",
            "anime",
            "--denoise",
            "0.8",
            "--cfg",
            "6.0",
            "--ip-weight",
            "0.6",
            "--seed",
            "42",
            "--variations",
            "3",
        ],
    )

    class FakePath:
        def __init__(self, path) -> None:
            pass

        def read_text(self):
            return "{}"

    monkeypatch.setattr(cli, "Path", FakePath)
    monkeypatch.setattr(cli, "ComfyClient", lambda server: None)

    captured: dict = {}

    monkeypatch.setattr(cli, "run", _capturing_run(captured))

    cli.main()

    assert captured["overrides"] == {"denoise": 0.8, "cfg": 6.0, "ip_weight": 0.6}
    # --ip-weight, --seed and --variations previously parsed and validated but
    # were never observed reaching run().
    assert captured["seed"] == 42
    assert captured["variations"] == 3
    assert captured["mutate"] is mutate_fn


# --- Dial range boundaries --------------------------------------------------
# The accepted values above are strictly interior and the rejected ones strictly
# exterior, so nothing pinned the inclusive edges. Changing `lo <= v <= hi` to
# `lo < v < hi` would keep the suite green while rejecting --denoise 1.0, a value
# the help text and the spec both advertise as valid.


@pytest.mark.spec("cli:dial-validation:accepts-denoise-in-range")
def test_parse_args_accepts_denoise_at_both_inclusive_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for edge in ("0.0", "1.0"):
        monkeypatch.setattr(
            "sys.argv",
            ["convert.py", "photo.jpg", "--prompt", "anime", "--denoise", edge],
        )
        assert cli.parse_args().denoise == float(edge)


@pytest.mark.spec("cli:dial-validation:accepts-cfg-in-range")
def test_parse_args_accepts_cfg_at_both_inclusive_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for edge in ("0.0", "30.0"):
        monkeypatch.setattr(
            "sys.argv",
            ["convert.py", "photo.jpg", "--prompt", "anime", "--cfg", edge],
        )
        assert cli.parse_args().cfg == float(edge)


@pytest.mark.spec("cli:dial-validation:accepts-ip-weight-in-range")
def test_parse_args_accepts_ip_weight_at_both_inclusive_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for edge in ("0.0", "1.0"):
        monkeypatch.setattr(
            "sys.argv",
            ["convert.py", "photo.jpg", "--prompt", "anime", "--ip-weight", edge],
        )
        assert cli.parse_args().ip_weight == float(edge)


@pytest.mark.spec("cli:dial-validation:rejects-denoise-above-one")
def test_parse_args_says_which_range_a_rejected_denoise_violated(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    # The other rejection tests assert only that SystemExit is raised -- the same
    # shape that let a typo survive in get_model's message. Pin the text once.
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--prompt", "anime", "--denoise", "1.1"],
    )
    with pytest.raises(SystemExit):
        cli.parse_args()

    assert "must be in [0.0, 1.0], got 1.1" in capsys.readouterr().err


@pytest.mark.spec("cli:dial-plumbing:overrides-reach-the-run")
def test_main_passes_zero_valued_override_flags_to_pipeline_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Zero is a valid value for all three dials and the parser accepts it, but
    # every plumbing test above uses non-zero values. A truthiness guard
    # (`if args.denoise:`) instead of `is not None` would silently discard 0.0
    # and fall back to the workflow's baked value with no error.
    monkeypatch.setattr(
        "sys.argv",
        [
            "convert.py",
            "photo.jpg",
            "--prompt",
            "anime",
            "--denoise",
            "0.0",
            "--cfg",
            "0.0",
            "--ip-weight",
            "0.0",
        ],
    )

    class FakePath:
        def __init__(self, path) -> None:
            pass

        def read_text(self):
            return "{}"

    monkeypatch.setattr(cli, "Path", FakePath)
    monkeypatch.setattr(cli, "ComfyClient", lambda server: None)

    captured: dict = {}
    monkeypatch.setattr(cli, "run", _capturing_run(captured))

    cli.main()

    assert captured["overrides"] == {"denoise": 0.0, "cfg": 0.0, "ip_weight": 0.0}
