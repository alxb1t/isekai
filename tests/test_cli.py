import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from isekai import cli
from isekai.mutate import mutate as mutate_fn


def _capturing_run(captured: dict[str, Any]) -> Callable[..., None]:
    """Build a `run` double recording EVERY argument `main()` passes.

    Capturing all of them is the point. A double that merely declares
    `mutate=None, seed=None, variations=1` as defaults cannot distinguish
    "main() passed this" from "main() passed nothing", so deleting the
    plumbing in main() would leave the suite green.
    """

    def fake_run(*args: object, **kwargs: object) -> None:
        names = (
            "client",
            "workflow",
            "inject",
            "input_path",
            "output_dir",
        )
        captured.update(dict(zip(names, args)))
        captured.update(kwargs)

    return fake_run


def _stub_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stand in for the two things `main()` touches outside the process.

    `Path.read_text` is patched rather than `cli.Path` itself: `main()` also uses
    `Path` to resolve the run directory, and a stub class that cannot do `/`
    would fail there instead of standing in for the workflow file.
    """
    monkeypatch.setattr(cli.Path, "read_text", lambda self: "{}")
    monkeypatch.setattr(cli, "ComfyClient", lambda server: None)


@pytest.mark.spec("cli:reproducibility:seed-defaults-to-unset")
def test_parse_args_defaults_seed_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg"])
    assert cli.parse_args().seed is None


@pytest.mark.spec("cli:reproducibility:accepts-a-seed")
def test_parse_args_accepts_a_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "--seed", "42"])
    assert cli.parse_args().seed == 42


@pytest.mark.spec("cli:reproducibility:variations-default-to-five")
def test_parse_args_defaults_variations_to_five(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg"])
    assert cli.parse_args().variations == 5


@pytest.mark.spec("cli:reproducibility:accepts-a-variation-count")
def test_parse_args_accepts_a_variation_count(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--variations", "3"],
    )
    assert cli.parse_args().variations == 3


# --- Phase 2: --denoise / --cfg / --ip-weight flags ---


@pytest.mark.spec("cli:dial-defaults:denoise-defaults-to-unset")
def test_parse_args_defaults_denoise_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg"])
    assert cli.parse_args().denoise is None


@pytest.mark.spec("cli:dial-defaults:cfg-defaults-to-unset")
def test_parse_args_defaults_cfg_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg"])
    assert cli.parse_args().cfg is None


@pytest.mark.spec("cli:dial-defaults:ip-weight-defaults-to-unset")
def test_parse_args_defaults_ip_weight_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg"])
    assert cli.parse_args().ip_weight is None


@pytest.mark.spec("cli:dial-validation:accepts-denoise-in-range")
def test_parse_args_accepts_denoise_in_range(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--denoise", "0.7"],
    )
    assert cli.parse_args().denoise == pytest.approx(0.7)


@pytest.mark.spec("cli:dial-validation:accepts-cfg-in-range")
def test_parse_args_accepts_cfg_in_range(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--cfg", "7.5"],
    )
    assert cli.parse_args().cfg == pytest.approx(7.5)


@pytest.mark.spec("cli:dial-validation:accepts-ip-weight-in-range")
def test_parse_args_accepts_ip_weight_in_range(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--ip-weight", "0.85"],
    )
    assert cli.parse_args().ip_weight == pytest.approx(0.85)


@pytest.mark.spec("cli:dial-validation:rejects-denoise-above-one")
def test_parse_args_rejects_denoise_above_one(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--denoise", "1.1"],
    )
    with pytest.raises(SystemExit):
        cli.parse_args()


@pytest.mark.spec("cli:dial-validation:rejects-denoise-below-zero")
def test_parse_args_rejects_denoise_below_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--denoise", "-0.1"],
    )
    with pytest.raises(SystemExit):
        cli.parse_args()


@pytest.mark.spec("cli:dial-validation:rejects-cfg-above-thirty")
def test_parse_args_rejects_cfg_above_thirty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--cfg", "31.0"],
    )
    with pytest.raises(SystemExit):
        cli.parse_args()


@pytest.mark.spec("cli:dial-validation:rejects-cfg-below-zero")
def test_parse_args_rejects_cfg_below_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--cfg", "-1.0"],
    )
    with pytest.raises(SystemExit):
        cli.parse_args()


@pytest.mark.spec("cli:dial-validation:rejects-ip-weight-above-one")
def test_parse_args_rejects_ip_weight_above_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--ip-weight", "1.5"],
    )
    with pytest.raises(SystemExit):
        cli.parse_args()


@pytest.mark.spec("cli:dial-validation:rejects-ip-weight-below-zero")
def test_parse_args_rejects_ip_weight_below_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["convert.py", "photo.jpg", "--ip-weight", "-0.5"],
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

    _stub_environment(monkeypatch)

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
            ["convert.py", "photo.jpg", "--denoise", edge],
        )
        assert cli.parse_args().denoise == float(edge)


@pytest.mark.spec("cli:dial-validation:accepts-cfg-in-range")
def test_parse_args_accepts_cfg_at_both_inclusive_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for edge in ("0.0", "30.0"):
        monkeypatch.setattr(
            "sys.argv",
            ["convert.py", "photo.jpg", "--cfg", edge],
        )
        assert cli.parse_args().cfg == float(edge)


@pytest.mark.spec("cli:dial-validation:accepts-ip-weight-in-range")
def test_parse_args_accepts_ip_weight_at_both_inclusive_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for edge in ("0.0", "1.0"):
        monkeypatch.setattr(
            "sys.argv",
            ["convert.py", "photo.jpg", "--ip-weight", edge],
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
        ["convert.py", "photo.jpg", "--denoise", "1.1"],
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
            "--denoise",
            "0.0",
            "--cfg",
            "0.0",
            "--ip-weight",
            "0.0",
        ],
    )

    _stub_environment(monkeypatch)

    captured: dict = {}
    monkeypatch.setattr(cli, "run", _capturing_run(captured))

    cli.main()

    assert captured["overrides"] == {"denoise": 0.0, "cfg": 0.0, "ip_weight": 0.0}


@pytest.mark.spec("cli:reproducibility:variations-must-be-positive")
def test_parse_args_rejects_a_non_positive_variation_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # --variations 0 previously uploaded the photo, submitted nothing, wrote no
    # file and exited 0, leaving the user believing a render had happened.
    for bad in ("0", "-1"):
        monkeypatch.setattr(
            "sys.argv",
            ["convert.py", "photo.jpg", "--variations", bad],
        )
        with pytest.raises(SystemExit):
            cli.parse_args()


@pytest.mark.spec("cli:reproducibility:accepts-a-variation-count")
def test_main_allows_several_variations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "convert.py",
            "photo.jpg",
            "--variations",
            "3",
        ],
    )

    _stub_environment(monkeypatch)

    captured: dict = {}
    monkeypatch.setattr(cli, "run", _capturing_run(captured))

    cli.main()

    assert captured["variations"] == 3
    assert captured["mutate"] is mutate_fn


# --- v0.8: the output destination is a directory ----------------------------


@pytest.mark.spec("cli:output-destination:photo-is-the-only-required-argument")
def test_parse_args_needs_nothing_but_the_photo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # --prompt was required in v0.7. Everything else is defaulted or committed
    # to the graph, so the whole required surface is the photo.
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg"])
    assert cli.parse_args().input == "photo.jpg"


@pytest.mark.spec("cli:output-destination:defaults-to-an-outputs-directory")
def test_parse_args_defaults_the_output_to_the_outputs_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg"])
    assert cli.parse_args().output == "./outputs"


@pytest.mark.spec("cli:output-destination:defaults-to-an-outputs-directory")
def test_main_hands_the_run_a_directory_beneath_the_default_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg"])
    _stub_environment(monkeypatch)

    captured: dict = {}
    monkeypatch.setattr(cli, "run", _capturing_run(captured))

    cli.main()

    assert captured["output_dir"].parent == Path("./outputs")


@pytest.mark.spec("cli:output-destination:accepts-a-directory")
def test_main_carries_an_explicit_output_directory_into_the_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "-o", "/tmp/renders"])
    _stub_environment(monkeypatch)

    captured: dict = {}
    monkeypatch.setattr(cli, "run", _capturing_run(captured))

    cli.main()

    assert captured["output_dir"].parent == Path("/tmp/renders")


@pytest.mark.spec(
    "workflow-mutation:output-layout:destination-is-resolved-by-the-caller"
)
@pytest.mark.spec("workflow-mutation:output-layout:run-gets-its-own-directory")
def test_main_resolves_a_utc_instant_directory_for_the_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # `run` draws no clock of its own: main() resolves the instant and hands the
    # resolved path over, which is what keeps the suite deterministic.
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "-o", "out"])
    _stub_environment(monkeypatch)

    captured: dict = {}
    monkeypatch.setattr(cli, "run", _capturing_run(captured))

    cli.main()

    stamp = captured["output_dir"].name
    assert re.fullmatch(r"\d{8}T\d{6}Z", stamp), stamp
    # Parsing it back is what proves it is an instant rather than a fixed string.
    datetime.strptime(stamp, "%Y%m%dT%H%M%SZ")


@pytest.mark.spec("cli:output-destination:rejects-an-image-filename")
def test_parse_args_rejects_an_output_naming_an_image_file(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    # `-o out.png` was valid in v0.7 and would now silently create a DIRECTORY
    # called out.png. Refuse at parse time, before the photo is uploaded.
    for bad in ("out.png", "renders/out.JPG", "a.webp"):
        monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "-o", bad])
        with pytest.raises(SystemExit):
            cli.parse_args()

    assert "names a directory" in capsys.readouterr().err


@pytest.mark.spec("cli:reproducibility:variations-must-not-exceed-the-ceiling")
def test_parse_args_rejects_a_variation_count_above_the_ceiling(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    # Every variation is one billed GPU render, so an unbounded count bills a
    # mistyped digit at GPU rates.
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "--variations", "26"])
    with pytest.raises(SystemExit):
        cli.parse_args()

    assert "must be in [1, 25], got 26" in capsys.readouterr().err


@pytest.mark.spec("cli:reproducibility:accepts-a-variation-count")
def test_parse_args_accepts_the_ceiling_itself(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "--variations", "25"])
    assert cli.parse_args().variations == 25
