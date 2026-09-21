"""The pipeline's own entry point: its verbs, its refusals, and its stdlib guard.

This is the only entry point: v0.14 deleted the single-command surface `convert.py`
carried, so the stdlib-only runtime rule now has exactly one subject and the guard
that holds it lives here, beside the falsification that keeps it honest.
"""

import argparse
import io
import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from isekai.foundation.flow import MANIFEST_NAME, SIBLINGS, Flow, load_flow
from isekai.foundation.refusal import Refusal
from isekai.interface.cli import VERBS, _flows_for, build_parser, dispatch, main
from isekai.interface.wiring import (
    DEFAULT_IMPLEMENTATION,
    READERS,
    Wiring,
    reader_for,
    wiring_from,
)
from isekai.pipeline.caption import ClaudeReader, FakeReader, OllamaReader
from isekai.pipeline.tagging import FakeTagger
from isekai.shared.vocabulary import Vocabulary, read_tags
from tests.conftest import CSV
from tests.images import jpeg_bytes
from tests.stages import FIELD_MAP, Always, fake_wd14

ROOT = Path(__file__).resolve().parent.parent

EXPECTED_VERBS = (
    "caption",
    "sheet",
    "review",
    "approve",
    "generate",
    "show",
    "ui",
)


def _module(*args: str) -> subprocess.CompletedProcess[str]:
    """Invoke `python -m isekai` the way an operator does, and capture everything."""
    return subprocess.run(
        [sys.executable, "-m", "isekai", *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def _wiring(tmp_path: Path, flows_dir: Path | None = None) -> Wiring:
    """Return an offline wiring, optionally pointed at a scratch flows root."""
    from isekai.foundation.flow import FLOWS_DIR

    return Wiring(
        reader=Always(FakeReader()),
        tagger=fake_wd14(),
        hosted_tagger=Always(FakeTagger()),
        client=None,
        vocabulary=lambda: Vocabulary("v", "r" * 40, "d" * 64, read_tags(CSV)),
        field_map=lambda: FIELD_MAP,
        runs_root=tmp_path / "runs",
        flows_dir=flows_dir or FLOWS_DIR,
        out=io.StringIO(),
        err=io.StringIO(),
    )


def _two_flows(tmp_path: Path) -> Path:
    """Return a scratch flows root tracking `summon-v1` and a copy beside it."""
    source = load_flow("summon-v1").path
    root = tmp_path / "two-flows"
    for name in ("summon-v1", "other-v1"):
        directory = root / name
        directory.mkdir(parents=True)
        manifest = json.loads((source / MANIFEST_NAME).read_text())
        manifest["flow"] = name
        (directory / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n")
        for sibling in SIBLINGS:
            (directory / sibling).write_bytes((source / sibling).read_bytes())
    return root


def _flow_declaring(
    tmp_path: Path,
    *,
    implementation: str = "ollama",
    reader: str = "a-reader",
    sorter: str = "a-sorter",
    name: str = "open-v1",
) -> Flow:
    """Return a scratch flow whose manifest declares a `hosted` block."""
    source = load_flow("summon-v1").path
    directory = tmp_path / "declaring" / name
    directory.mkdir(parents=True)
    manifest = json.loads((source / MANIFEST_NAME).read_text())
    manifest["flow"] = name
    manifest["hosted"] = {
        "implementation": implementation,
        "reader": reader,
        "sorter": sorter,
    }
    (directory / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n")
    for sibling in SIBLINGS:
        (directory / sibling).write_bytes((source / sibling).read_bytes())
    return load_flow(name, tmp_path / "declaring")


def _two_arms(tmp_path: Path) -> Path:
    """Return a flows root with one flow on each implementation.

    `open-v1` declares the open block; `summon-v1` declares none, which means the
    default. One command naming both is what the per-flow resolution exists for.
    """
    source = load_flow("summon-v1").path
    root = tmp_path / "two-arms"
    for name, hosted in (("summon-v1", None), ("open-v1", "ollama")):
        directory = root / name
        directory.mkdir(parents=True)
        manifest = json.loads((source / MANIFEST_NAME).read_text())
        manifest["flow"] = name
        if hosted is not None:
            manifest["hosted"] = {
                "implementation": hosted,
                "reader": "a-reader",
                "sorter": "a-sorter",
            }
        (directory / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n")
        for sibling in SIBLINGS:
            (directory / sibling).write_bytes((source / sibling).read_bytes())
    return root


def _arm_aware_reader() -> Callable[[Flow], FakeReader]:
    """Return a resolver that reports the implementation each flow declares.

    A double per arm rather than one for both: what is under test is that the
    resolution happens per flow, so a resolver that ignored the flow would make
    the assertion pass for the bug it exists to catch.
    """

    def resolve(flow: Flow) -> FakeReader:
        hosted = flow.hosted
        return FakeReader(
            prose="A person.",
            implementation=hosted.implementation if hosted else DEFAULT_IMPLEMENTATION,
        )

    return resolve


def _cli_args(
    verb: str, target: str, tmp_path: Path, *, flow: list[str]
) -> argparse.Namespace:
    """Return a parsed command line for one verb over one target."""
    flags = [item for name in flow for item in ("--flow", name)]
    return build_parser().parse_args([verb, *flags, target])


def _stdlib_import(statement: str) -> subprocess.CompletedProcess[str]:
    """Run one import under `-S`, with the repository on the path and nothing else.

    The mechanism is `-S`, chosen over an AST walk against `sys.stdlib_module_names`
    because it was verified to work here: inside this uv venv, `-S` leaves no
    site-packages on `sys.path` at all, so a third-party import anywhere in the
    graph raises rather than resolving. Spelled once, because the guards below and
    the falsification that keeps them honest must run under identical conditions --
    a falsification that differs from what it falsifies proves nothing.
    """
    return subprocess.run(
        [sys.executable, "-S", "-c", statement],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        cwd=ROOT,
    )


@pytest.mark.spec("cli:pipeline-surface:verbs-are-subcommands")
def test_the_verbs_are_the_ones_the_change_declares() -> None:
    assert tuple(name for name, _ in VERBS) == EXPECTED_VERBS


@pytest.mark.spec("cli:pipeline-surface:verbs-are-subcommands")
@pytest.mark.parametrize("verb", EXPECTED_VERBS)
def test_each_verb_is_reachable_as_a_subcommand(verb: str) -> None:
    flag = [] if verb == "show" else ["--flow", "summon-v1"]  # `ui` takes one too

    assert build_parser().parse_args([verb, *flag]).verb == verb


@pytest.mark.spec("cli:pipeline-surface:verbs-are-subcommands")
def test_the_help_lists_every_verb() -> None:
    result = _module("--help")

    assert result.returncode == 0, result.stderr
    for verb in EXPECTED_VERBS:
        assert verb in result.stdout


@pytest.mark.spec("cli:pipeline-surface:unknown-verb-is-refused")
def test_an_unknown_verb_is_refused_before_any_work_begins() -> None:
    result = _module("frobnicate")

    assert result.returncode != 0
    assert "invalid choice: 'frobnicate'" in result.stderr


@pytest.mark.spec("cli:pipeline-surface:unknown-verb-is-refused")
def test_the_refusal_lists_the_verbs_that_are_available() -> None:
    result = _module("frobnicate")

    for verb in EXPECTED_VERBS:
        assert verb in result.stderr


@pytest.mark.spec("cli:pipeline-surface:unknown-verb-is-refused")
def test_no_verb_at_all_is_refused_too() -> None:
    assert _module().returncode != 0


@pytest.mark.spec("cli:pipeline-surface:entry-point-is-stdlib-only")
def test_the_pipeline_entry_point_imports_with_site_packages_off_the_path() -> None:
    result = _stdlib_import("import isekai.__main__")

    assert result.returncode == 0, result.stderr


@pytest.mark.spec("cli:pipeline-surface:entry-point-is-stdlib-only")
def test_the_run_directory_module_imports_with_site_packages_off_the_path() -> None:
    result = _stdlib_import("import isekai.foundation.run")

    assert result.returncode == 0, result.stderr


@pytest.mark.spec_exempt(
    "structural: the two guards above prove nothing unless -S really refuses"
)
def test_the_stdlib_guard_would_actually_catch_a_third_party_import() -> None:
    # A check that cannot fail is not a check. If `-S` ever stopped removing
    # site-packages, the two guards above would pass for the wrong reason and an
    # accidental wheel in `python -m isekai`'s import graph would ship silently.
    # It moved here with the guard it falsifies: it used to sit beside the one
    # that held `convert.py`, and that guard died with its target.
    result = _stdlib_import("import pytest")

    assert result.returncode != 0
    assert "No module named 'pytest'" in result.stderr


@pytest.mark.spec_exempt("structural: the parser dispatches nothing yet")
def test_parsing_a_verb_succeeds() -> None:
    assert main(["show"]) == 0


# --- the flow selection --------------------------------------------------------

STAGE_VERBS = ("caption", "sheet", "review", "approve", "generate")


@pytest.mark.spec("cli:flow-selection:a-stage-verb-requires-a-flow")
@pytest.mark.parametrize("verb", STAGE_VERBS)
def test_a_stage_verb_without_a_flow_is_refused(verb: str) -> None:
    result = _module(verb, "ada.jpg")

    assert result.returncode != 0
    assert "--flow" in result.stderr


@pytest.mark.spec("cli:flow-selection:a-stage-verb-requires-a-flow")
def test_the_refusal_lists_the_flows_this_build_tracks(tmp_path: Path) -> None:
    wired = _wiring(tmp_path)

    with pytest.raises(Refusal) as refused:
        _flows_for(build_parser().parse_args(["review", "--flow", "nope"]), wired)

    assert "summon-v1" in str(refused.value)


@pytest.mark.spec("cli:flow-selection:the-flag-is-repeatable")
def test_naming_two_flows_in_one_invocation_keeps_both() -> None:
    parsed = build_parser().parse_args(
        ["generate", "--flow", "summon-v1", "--flow", "summon-v2"]
    )

    assert parsed.flows == ["summon-v1", "summon-v2"]


@pytest.mark.spec("cli:flow-selection:a-serving-verb-takes-one-flow")
def test_a_serving_verb_refuses_a_second_flow_rather_than_keeping_the_last(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # The stage verbs repeat the flag because flows batch onto one endpoint. A
    # serving verb does not batch: two flows would be two field orders and two
    # token budgets sharing one set of controls, so the limit is stated at the
    # command the operator typed rather than at a screen that half-works.
    with pytest.raises(SystemExit) as exited:
        build_parser().parse_args(["ui", "--flow", "summon-v1", "--flow", "conjure-v1"])

    assert exited.value.code == 2
    assert "one flow at a time" in capsys.readouterr().err


@pytest.mark.spec("cli:flow-selection:a-serving-verb-takes-one-flow")
def test_a_serving_verb_takes_the_one_flow_it_is_given() -> None:
    parsed = build_parser().parse_args(["ui", "--flow", "summon-v1"])

    assert parsed.flow == "summon-v1"
    # Not the stage verbs' list -- there is nothing here for `_flows_for` to read.
    assert not hasattr(parsed, "flows")


@pytest.mark.spec("cli:flow-selection:the-flag-is-repeatable")
def test_no_named_flow_is_silently_dropped(tmp_path: Path) -> None:
    # The old flag was a single string: a second `--flow` overwrote the first
    # and the invocation acted on one of the two without saying so.
    wired = _wiring(tmp_path, flows_dir=_two_flows(tmp_path))
    parsed = build_parser().parse_args(
        ["review", "--flow", "summon-v1", "--flow", "other-v1"]
    )

    assert list(_flows_for(parsed, wired)) == ["summon-v1", "other-v1"]


@pytest.mark.spec("cli:flow-selection:every-stage-verb-accepts-it")
@pytest.mark.parametrize("verb", STAGE_VERBS)
def test_every_stage_verb_accepts_the_flag(verb: str) -> None:
    parsed = build_parser().parse_args([verb, "--flow", "summon-v1"])

    assert parsed.flows == ["summon-v1"]


@pytest.mark.spec("cli:flow-selection:every-stage-verb-accepts-it")
def test_the_inspection_verb_is_the_only_one_that_does_not_take_it() -> None:
    result = _module("show", "--flow", "summon-v1")

    assert result.returncode != 0
    assert "--flow" in result.stderr


@pytest.mark.spec("cli:flow-selection:an-untracked-flow-is-refused")
def test_an_untracked_flow_is_refused_naming_it(tmp_path: Path) -> None:
    wired = _wiring(tmp_path)
    parsed = build_parser().parse_args(["generate", "--flow", "summon-v9"])

    with pytest.raises(Refusal) as refused:
        _flows_for(parsed, wired)

    message = str(refused.value)
    assert "summon-v9" in message
    assert "summon-v1" in message


@pytest.mark.spec("cli:flow-selection:an-untracked-flow-is-refused")
def test_an_untracked_flow_is_refused_before_any_run_is_opened(tmp_path: Path) -> None:
    # At `generate` the flow's first use is after a photograph has been uploaded,
    # so resolving the name at selection is what keeps the refusal free.
    err = io.StringIO()
    wired = _wiring(tmp_path)
    wired.err = err
    photo = tmp_path / "ada.jpg"
    photo.write_bytes(jpeg_bytes(640, 480))
    parsed = build_parser().parse_args(["generate", "--flow", "summon-v9", str(photo)])

    status = dispatch(parsed, wired)

    assert status == 1
    assert not (tmp_path / "runs").exists()
    assert "summon-v9" in err.getvalue()


# --- resolution: the flow picks the implementation ----------------------------


@pytest.mark.spec("caption:selection:unknown-implementation-is-refused")
def test_an_unknown_reader_implementation_refuses_naming_what_this_build_carries(
    tmp_path: Path,
) -> None:
    flow = _flow_declaring(tmp_path, implementation="vllm")

    with pytest.raises(Refusal) as refused:
        reader_for(flow)

    message = str(refused.value)
    assert "vllm" in message
    assert "claude-cli" in message and "ollama" in message


@pytest.mark.spec("caption:selection:the-flow-names-the-implementation")
def test_each_registrys_keys_are_the_strings_the_artifacts_record() -> None:
    """The duplication between the table and the adapter cannot drift.

    The registry's keys and `Reading.implementation` are the same strings in two
    places, and a run whose provenance disagreed with the manifest that asked for
    it would be silent. `Model`'s own docstring establishes this pattern for the
    digest it duplicates.

    **One registry rather than two**: the sheet's seam is gone, so `READERS` is
    what is left of this property on the reading side.
    """
    assert set(READERS) == {"claude-cli", "ollama"}
    assert ClaudeReader().implementation == "claude-cli"
    assert OllamaReader(model="r").implementation == "ollama"
    assert DEFAULT_IMPLEMENTATION in READERS


@pytest.mark.spec("caption:selection:the-flow-names-the-implementation")
def test_a_flow_declaring_no_block_resolves_to_the_default_implementation() -> None:
    flow = load_flow("summon-v1")

    assert flow.hosted is None
    assert isinstance(reader_for(flow), ClaudeReader)


@pytest.mark.spec("caption:selection:the-flow-names-the-implementation")
def test_a_flow_declaring_ollama_resolves_to_the_models_its_manifest_names(
    tmp_path: Path,
) -> None:
    flow = _flow_declaring(tmp_path, reader="a-reader", sorter="a-sorter")

    reader = reader_for(flow)

    assert isinstance(reader, OllamaReader) and reader.model == "a-reader"


@pytest.mark.spec("caption:reachability:the-check-fires-at-first-call")
def test_composing_a_wiring_contacts_no_host_and_looks_up_no_binary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing is constructed until a flow asks, so neither check can fire here.

    That is what lets a machine with one implementation available never touch the
    other. `shutil.which` and the transport both raise, and composing a wiring
    still succeeds because it resolves nothing.
    """

    def unreachable(*args: object, **kwargs: object) -> object:
        raise AssertionError("something was reached at composition time")

    monkeypatch.setattr("shutil.which", unreachable)
    monkeypatch.setattr("urllib.request.urlopen", unreachable)

    wired = wiring_from(runs=tmp_path / "runs")

    assert wired.reader is not None


@pytest.mark.spec("cli:resolution:uncomposed-seam-refuses-by-name")
def test_a_wiring_composed_without_a_reader_refuses_by_name(tmp_path: Path) -> None:
    """The ③-only front end's case: absent, not fabricated, and named when needed."""
    err = io.StringIO()
    wired = _wiring(tmp_path)
    wired.reader = None
    wired.err = err
    photo = tmp_path / "ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))

    status = dispatch(
        _cli_args("caption", str(photo), tmp_path, flow=["summon-v1"]), wired
    )

    assert status == 1
    assert "composed without a reader" in err.getvalue()


@pytest.mark.spec("cli:resolution:one-command-two-implementations")
def test_one_command_over_two_flows_writes_two_artifacts_each_naming_its_own(
    tmp_path: Path,
) -> None:
    """The reason the resolution moved inside the loop.

    Hoisted above it, one invocation naming flows on both arms resolved a single
    reader and handed it to both -- so one of the two captions recorded a producer
    that did not produce it, with the whole gate green.
    """
    wired = _wiring(tmp_path, flows_dir=_two_arms(tmp_path))
    wired.reader = _arm_aware_reader()
    photo = tmp_path / "ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))

    status = dispatch(
        _cli_args("caption", str(photo), tmp_path, flow=["summon-v1", "open-v1"]),
        wired,
    )

    assert status == 0
    named = {
        written.parent.parent.name: json.loads(written.read_text())["producer"][
            "implementation"
        ]
        for written in sorted((tmp_path / "runs").glob("*/*/captions/001.json"))
    }
    assert named == {"summon-v1": "claude-cli", "open-v1": "ollama"}
