"""The pipeline's own entry point: its verbs, its refusals, and its import guard.

This is the only entry point, so the rule below has exactly one subject and the
guard that holds it lives here, beside the falsification that keeps it honest.

**The runtime is not stdlib-only, which makes the guard more load-bearing, not
less.** onnxruntime, numpy, Pillow, fastapi and uvicorn are declared dependencies,
because the local tagger runs on every `caption` and `uv sync` strips an extra it
is never told about. What the architecture actually rests on is this claim: **the
entry point imports no third-party package at module scope** (D20). `wd14.py`'s
three imports are function-local and `interface/ui/__init__.py` keeps FastAPI off
the graph the same way, which is why `isekai show` works on a checkout that has
provisioned nothing. With the packages installed by default, a module-scope import
resolves rather than failing, so this guard is what catches one appearing here;
`tests/test_wd14.py`'s source scan also catches one in `boundary/wd14.py`.
"""

import argparse
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from isekai.boundary import ollama
from isekai.foundation.artifacts import APPROVED_FILE, DRAFT_FILE, SHEET_FILE, read
from isekai.foundation.flow import MANIFEST_NAME, SIBLINGS, Flow, Schema, load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import Run, open_run
from isekai.interface.cli import VERBS, _flows_for, build_parser, dispatch, main
from isekai.interface.wiring import Wiring, reader_for, wiring_from
from isekai.pipeline.caption import FakeReader, OllamaReader
from isekai.pipeline.generate import prompt_artifact
from isekai.pipeline.review import approve, review
from isekai.pipeline.tagging import FakeTagger
from isekai.shared.vocabulary import Vocabulary, read_tags
from tests.conftest import CSV
from tests.fakes import READER, FakeComfyClient, stub_comfy
from tests.images import jpeg_bytes
from tests.stages import (
    FIELD_MAP,
    Always,
    fake_wd14,
    rendered_image,
    runs_flag,
    sheet,
    write_wd14,
)
from tests.transports import FakeTransport

ROOT = Path(__file__).resolve().parent.parent

EXPECTED_VERBS = (
    "import",
    "assign",
    "caption",
    "tag",
    "sheet",
    "review",
    "approve",
    "draft",
    "generate",
    "render",
    "show",
    "ui",
    "compare",
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
        field_map=lambda _: FIELD_MAP,
        runs_root=tmp_path / "runs",
        flows_dir=flows_dir or FLOWS_DIR,
        out=io.StringIO(),
        err=io.StringIO(),
    )


def _two_flows(tmp_path: Path) -> Path:
    """Return a scratch flows root tracking `summon-anime-wai` and a copy beside it."""
    source = load_flow("summon-anime-wai").path
    root = tmp_path / "two-flows"
    for name in ("summon-anime-wai", "other-v1"):
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
    model: str = "a-reader",
    name: str = "declared-v1",
) -> Flow:
    """Return a scratch flow whose manifest names the given model."""
    source = load_flow("summon-anime-wai").path
    directory = tmp_path / "declaring" / name
    directory.mkdir(parents=True)
    manifest = json.loads((source / MANIFEST_NAME).read_text())
    manifest["flow"] = name
    manifest["model"] = model
    (directory / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n")
    for sibling in SIBLINGS:
        (directory / sibling).write_bytes((source / sibling).read_bytes())
    return load_flow(name, tmp_path / "declaring")


def _two_models(tmp_path: Path) -> Path:
    """Return a flows root with two flows naming two different models.

    **Neither omits the key**, because omitting it is not expressible: with
    `model` required there is no default to fall back to, and the case the
    per-flow resolution still has real work in is two flows naming two *models*.
    """
    source = load_flow("summon-anime-wai").path
    root = tmp_path / "two-models"
    for name, model in (("flow-a", "a-reader"), ("flow-b", "b-reader")):
        directory = root / name
        directory.mkdir(parents=True)
        manifest = json.loads((source / MANIFEST_NAME).read_text())
        manifest["flow"] = name
        manifest["model"] = model
        (directory / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n")
        for sibling in SIBLINGS:
            (directory / sibling).write_bytes((source / sibling).read_bytes())
    return root


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
    # `compare` takes a collection directory, `render` its runs, `import` a
    # collection and its files, `draft` a flow and images; `ui` takes nothing.
    own = {
        "import": ["--collection", "collection", "photo.jpg"],
        "draft": ["--flow", "summon-anime-wai", "outputs/001/7.png"],
        "show": [],
        "ui": [],
        "compare": ["collection"],
        "render": ["runs", "summon-anime-wai=1"],
    }
    flag = own.get(verb, ["--flow", "summon-anime-wai"])

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
    # The whole entry point's module-scope graph, walked by the interpreter with
    # nowhere to resolve a wheel from. `onnxruntime` and `fastapi` are installed
    # in this environment, so only `-S` distinguishes a function-local import
    # from a module-scope one here.
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
    #
    # **It names a declared dependency for readability, not for reach.** Both
    # `pytest` and `onnxruntime` resolve from the same site-packages, so either
    # would go red the moment `-S` stopped removing it -- this is not a stronger
    # probe than an `import pytest`, only a clearer one about which wheels the
    # guards above exist to exclude.
    result = _stdlib_import("import onnxruntime")

    assert result.returncode != 0
    assert "No module named 'onnxruntime'" in result.stderr


@pytest.mark.spec_exempt("structural: the parser dispatches nothing yet")
def test_parsing_a_verb_succeeds() -> None:
    assert main(["show"]) == 0


# --- the flow selection --------------------------------------------------------

STAGE_VERBS = ("caption", "tag", "sheet", "review", "approve", "generate")


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

    assert "summon-anime-wai" in str(refused.value)


@pytest.mark.spec("cli:flow-selection:the-flag-is-repeatable")
def test_naming_two_flows_in_one_invocation_keeps_both() -> None:
    parsed = build_parser().parse_args(
        ["generate", "--flow", "summon-anime-wai", "--flow", "summon-anime-wai-2"]
    )

    assert parsed.flows == ["summon-anime-wai", "summon-anime-wai-2"]


@pytest.mark.spec("ui:library:the-verb-takes-no-arguments")
@pytest.mark.parametrize(
    "extra",
    [["--flow", "summon-anime-wai"], ["0d4b7e6fb2a8_ada"], ["--runs", "elsewhere"]],
    ids=["a-flow", "an-input", "a-runs-root"],
)
def test_the_serving_verb_refuses_a_flow_an_input_or_a_runs_root(
    extra: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exited:
        build_parser().parse_args(["ui", *extra])

    assert exited.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err
    assert build_parser().parse_args(["ui", "--port", "9000"]).port == 9000


@pytest.mark.spec("cli:flow-selection:the-flag-is-repeatable")
def test_no_named_flow_is_silently_dropped(tmp_path: Path) -> None:
    # With a single-string flag, a second `--flow` would overwrite the first and
    # the invocation would act on one of the two without saying so.
    wired = _wiring(tmp_path, flows_dir=_two_flows(tmp_path))
    parsed = build_parser().parse_args(
        ["review", "--flow", "summon-anime-wai", "--flow", "other-v1"]
    )

    assert list(_flows_for(parsed, wired)) == ["summon-anime-wai", "other-v1"]


@pytest.mark.spec("cli:flow-selection:every-stage-verb-accepts-it")
@pytest.mark.parametrize("verb", STAGE_VERBS)
def test_every_stage_verb_accepts_the_flag(verb: str) -> None:
    parsed = build_parser().parse_args([verb, "--flow", "summon-anime-wai"])

    assert parsed.flows == ["summon-anime-wai"]


@pytest.mark.spec("cli:flow-selection:every-stage-verb-accepts-it")
def test_the_inspection_verb_is_the_only_one_that_does_not_take_it() -> None:
    result = _module("show", "--flow", "summon-anime-wai")

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
    assert "summon-anime-wai" in message


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


# --- resolution: the flow names the model -------------------------------------


@pytest.mark.spec("caption:selection:an-unreachable-model-is-refused")
@pytest.mark.usefixtures("model_records")
def test_a_model_this_build_cannot_reach_refuses_naming_it_and_the_remedy(
    tmp_path: Path,
) -> None:
    """The refusal fires at the first call, not at resolution.

    There is no unknown-implementation case to refuse -- a one-entry registry
    has no key to miss. What a manifest can still get wrong is the **model**, and
    an alias that was never created is the failure that will actually happen. It
    is named where it is discovered: at the call, by `ollama.py`, with the one
    command that fixes it.
    """
    flow = _flow_declaring(tmp_path, model=READER)
    reader = reader_for(flow)
    assert isinstance(reader, OllamaReader)
    photo = tmp_path / "ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))

    with pytest.raises(Refusal) as refused:
        OllamaReader(
            model=flow.model,
            transport=FakeTransport(payload={"error": "not found"}, status=404),
        ).read(photo, "brief", tmp_path)

    message = str(refused.value)
    assert repr(READER) in message
    assert f"ollama create {READER}" in message


@pytest.mark.spec("caption:selection:the-flow-names-the-model")
def test_the_implementation_the_artifacts_record_is_the_one_the_adapter_names() -> None:
    """The duplication between the record and the adapter cannot drift.

    With one implementation there is no string to key a registry on, so no table
    has to equal `Reading.implementation`. The property such a table would protect
    is asserted directly: what a caption's producer records is what the adapter
    calls itself.
    """
    assert OllamaReader(model="r").implementation == "ollama"


@pytest.mark.spec("caption:selection:the-flow-names-the-model")
def test_a_flow_resolves_to_a_reader_running_the_model_its_manifest_names(
    tmp_path: Path,
) -> None:
    flow = _flow_declaring(tmp_path, model="a-reader")

    reader = reader_for(flow)

    assert isinstance(reader, OllamaReader) and reader.model == "a-reader"


@pytest.mark.spec("caption:reachability:the-check-fires-at-first-call")
def test_composing_a_wiring_contacts_no_host_and_looks_up_no_binary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing is constructed until a flow asks, so no check can fire here.

    Composing a wiring resolves nothing, so a machine with no Ollama running and
    no alias created still composes one. `shutil.which` and the transport both
    raise, and it still succeeds.
    """

    def unreachable(*args: object, **kwargs: object) -> object:
        raise AssertionError("something was reached at composition time")

    monkeypatch.setattr("shutil.which", unreachable)
    monkeypatch.setattr("urllib.request.urlopen", unreachable)
    stub_comfy(monkeypatch, unreachable)
    monkeypatch.setattr(ollama, "_verified_build", unreachable)

    wired = wiring_from(runs=tmp_path / "runs")

    assert wired.reader is not None


@pytest.mark.spec_exempt(
    "structural: ISEKAI_WIRING names the factory wiring_from calls"
)
def test_a_named_factory_builds_the_wiring_after_the_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ISEKAI_WIRING", "tests.e2e.wiring:fake")
    wired = wiring_from(runs=tmp_path / "runs")
    assert isinstance(wired.client, FakeComfyClient)
    assert wired.runs_root == tmp_path / "runs"
    with pytest.raises(Refusal, match="--runs"):
        wiring_from(runs=Path(__file__).resolve().parent.parent / "lib")


@pytest.mark.spec_exempt("structural: twin -- ISEKAI_WIRING without a factory refuses")
def test_a_named_wiring_without_a_factory_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ISEKAI_WIRING", "tests.e2e.wiring")
    with pytest.raises(Refusal, match="<module>:<factory>"):
        wiring_from(runs=tmp_path / "runs")
    monkeypatch.delenv("ISEKAI_WIRING")
    assert not isinstance(wiring_from(runs=tmp_path / "runs").client, FakeComfyClient)


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
        _cli_args("caption", str(photo), tmp_path, flow=["summon-anime-wai"]), wired
    )

    assert status == 1
    assert "composed without a reader" in err.getvalue()


@pytest.mark.spec("cli:resolution:one-command-two-models")
def test_one_command_over_two_flows_writes_two_artifacts_each_naming_its_own(
    tmp_path: Path,
) -> None:
    """The reason the resolution sits inside the loop, and it has work.

    Hoisted above it, one invocation naming two flows resolves a single reader
    and hands it to both -- so one of the two captions records a producer that did
    not produce it, with the whole gate green. With one arm, what it would get
    wrong is the **model**, which differs per flow and is what the artifact has
    to record.
    """
    wired = _wiring(tmp_path, flows_dir=_two_models(tmp_path))
    wired.reader = lambda flow: FakeReader(prose="A person.", models=(flow.model,))
    photo = tmp_path / "ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))

    status = dispatch(
        _cli_args("caption", str(photo), tmp_path, flow=["flow-a", "flow-b"]),
        wired,
    )

    assert status == 0
    named = {
        written.parent.parent.name: json.loads(written.read_text())["producer"][
            "models"
        ][0]
        for written in sorted((tmp_path / "runs").glob("*/*/captions/001.json"))
    }
    assert named == {"flow-a": "a-reader", "flow-b": "b-reader"}


def _caption_with_one_refusing(tmp_path: Path, refusing: str) -> tuple[int, Wiring]:
    """Caption one photograph over two flows, the reader refusing `refusing`'s."""
    wired = _wiring(tmp_path, flows_dir=_two_models(tmp_path))

    def reader(flow: Flow) -> FakeReader:
        if flow.id == refusing:
            raise Refusal(f"{flow.id}: its model is not running")
        return FakeReader(prose="A person.", models=(flow.model,))

    wired.reader = reader
    photo = tmp_path / "ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    status = dispatch(
        _cli_args("caption", str(photo), tmp_path, flow=["flow-a", "flow-b"]), wired
    )
    return status, wired


def _captioned(tmp_path: Path) -> list[str]:
    """Return the flows with a caption written, by name."""
    return sorted(
        path.parent.parent.name
        for path in (tmp_path / "runs").glob("*/*/captions/001.json")
    )


@pytest.mark.spec("cli:flow-selection:one-flows-refusal-leaves-the-others")
def test_one_flows_refusal_leaves_the_others(tmp_path: Path) -> None:
    status, wired = _caption_with_one_refusing(tmp_path, "flow-a")

    assert status == 1
    assert _captioned(tmp_path) == ["flow-b"]
    assert isinstance(wired.err, io.StringIO)
    assert "refused: flow-a: its model is not running" in wired.err.getvalue()


@pytest.mark.spec_exempt("twin: the named-first flow runs whatever the per-flow guard")
def test_a_refusal_after_the_first_flow_leaves_it_written(tmp_path: Path) -> None:
    status, _ = _caption_with_one_refusing(tmp_path, "flow-b")

    assert status == 1
    assert _captioned(tmp_path) == ["flow-a"]


@pytest.mark.spec("sheet:superseded:a-newer-tag-list-is-named")
def test_sheet_prints_a_superseded_list_as_a_warning(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    photo = tmp_path / "ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    run = open_run(photo, tmp_path / "runs")
    sheet(run, schema, vocabulary)
    write_wd14(run, version=2)
    wired = _wiring(tmp_path)

    status = dispatch(
        _cli_args("sheet", run.id, tmp_path, flow=["summon-anime-wai"]), wired
    )

    assert status == 0
    assert isinstance(wired.out, io.StringIO) and isinstance(wired.err, io.StringIO)
    assert wired.err.getvalue() == (
        f"warning: {run.id}/summon-anime-wai: sheet 001 was filled from "
        "wd14/001.json, and wd14/002.json is newer; run `python -m isekai sheet "
        f"--flow summon-anime-wai{runs_flag(run)} --new-version {run.id}`\n"
    )
    assert f"{run.id}: sheet is already complete" in wired.out.getvalue()


@pytest.mark.spec("review:copy-from:the-source-is-another-tracked-flow")
def test_a_flow_named_as_its_own_approval_source_is_refused_naming_it(
    tmp_path: Path,
) -> None:
    wired = _wiring(tmp_path)
    err = io.StringIO()
    wired.err = err
    parsed = build_parser().parse_args(
        ["approve", "--flow", "summon-anime-wai", "--from", "summon-anime-wai", "x"]
    )

    assert dispatch(parsed, wired) == 1

    assert err.getvalue().startswith("refused: summon-anime-wai: a flow is not")
    assert not (tmp_path / "runs").exists()


@pytest.mark.spec("cli:approve-cancel:each-run-on-its-own")
def test_approve_cancel_answers_each_run_on_its_own(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    runs = []
    for name in ("ada", "bo"):
        photo = tmp_path / f"{name}.jpg"
        photo.write_bytes(jpeg_bytes(640, 480 + len(runs)))
        run = open_run(photo, tmp_path / "runs")
        sheet(run, schema, vocabulary)
        review(run, "summon-anime-wai")
        approve(run, "summon-anime-wai", schema, vocabulary)
        runs.append(run)
    cancelled, rendered = runs
    prompt_artifact(rendered, load_flow("summon-anime-wai"), schema)
    wired = _wiring(tmp_path)
    err = io.StringIO()
    wired.err = err
    parsed = build_parser().parse_args(
        ["approve", "--flow", "summon-anime-wai", "--cancel", rendered.id, cancelled.id]
    )

    assert dispatch(parsed, wired) == 1

    review_of = cancelled.directory("summon-anime-wai", "review")
    assert sorted(path.name for path in review_of.iterdir()) == ["001.draft.json"]
    assert "summon-anime-wai/prompts/001.json came from it" in err.getvalue()
    assert (
        rendered.directory("summon-anime-wai", "review") / "001.approved.json"
    ).exists()


@pytest.mark.spec("cli:approve-cancel:not-beside-from")
def test_approve_cancel_beside_from_is_refused_before_any_run_is_read(
    tmp_path: Path,
) -> None:
    wired = _wiring(tmp_path)
    err = io.StringIO()
    wired.err = err
    photo = tmp_path / "ada.jpg"
    photo.write_bytes(jpeg_bytes(640, 480))
    parsed = build_parser().parse_args(
        [
            "approve",
            "--flow",
            "control-anime-wai",
            "--from",
            "summon-anime-wai",
            "--cancel",
            str(photo),
        ]
    )

    assert dispatch(parsed, wired) == 1

    assert err.getvalue().startswith("refused: --cancel takes an approval back")
    assert not (tmp_path / "runs").exists()


@pytest.mark.spec("review:copy-from:the-source-is-another-tracked-flow")
def test_an_untracked_approval_source_is_refused_naming_the_flows_there_are(
    tmp_path: Path,
) -> None:
    wired = _wiring(tmp_path)
    err = io.StringIO()
    wired.err = err
    # A photograph, so a run would be opened if the source were checked late.
    photo = tmp_path / "ada.jpg"
    photo.write_bytes(jpeg_bytes(640, 480))
    parsed = build_parser().parse_args(
        ["approve", "--flow", "summon-anime-wai", "--from", "summon-v9", str(photo)]
    )

    assert dispatch(parsed, wired) == 1

    assert not (tmp_path / "runs").exists()
    assert "summon-v9: not a flow this build tracks" in err.getvalue()


CONJURE = "conjure-anime-wai"


def _two_approvals(
    tmp_path: Path, name: str, schema: Schema, vocabulary: Vocabulary
) -> Run:
    """Open a run whose summon holds approvals one and two, and conjure a sheet."""
    photo = tmp_path / f"{name}.jpg"
    photo.write_bytes(jpeg_bytes(640, 480 + len(name)))
    run = open_run(photo, tmp_path / "runs")
    sheet(run, schema, vocabulary)
    sheet(run, load_flow(CONJURE).schema, vocabulary, flow=CONJURE)
    review(run, "summon-anime-wai")
    approve(run, "summon-anime-wai", schema, vocabulary)
    draft = review(run, "summon-anime-wai", new_version=True)
    assert draft is not None
    body = json.loads(draft.read_text())
    body["fields"]["hair_silhouette"] = ["very long hair"]
    draft.write_text(json.dumps(body))
    approve(run, "summon-anime-wai", schema, vocabulary)
    return run


@pytest.mark.spec("cli:draft:another-flow-is-drafted-from-the-image")
def test_draft_writes_another_flow_from_the_images_approval_and_seed(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = _two_approvals(tmp_path, "ada", schema, vocabulary)
    argv = ["draft", "--flow", CONJURE, str(rendered_image(run, 1, 7))]

    assert dispatch(build_parser().parse_args(argv), _wiring(tmp_path)) == 0

    draft = read(run.directory(CONJURE, "review") / "001.draft.json", DRAFT_FILE)
    first = read(
        run.directory("summon-anime-wai", "review") / "001.approved.json",
        APPROVED_FILE,
    )
    assert draft["fields"]["hair_silhouette"] == first["fields"]["hair_silhouette"]
    assert draft["producer"]["drafted_from"] == {
        "flow": "summon-anime-wai",
        "approval": 1,
    }
    assert draft["producer"]["image"] == {
        "flow": "summon-anime-wai",
        "version": 1,
        "seed": 7,
    }
    assert draft["renders"] == {"count": 1, "seeds": [7]}


@pytest.mark.spec("cli:review-from:a-target-with-no-sheet-is-filled-first")
def test_draft_assigns_a_target_with_no_sheet_and_fills_it_from_the_source(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    photo = tmp_path / "ada.jpg"
    photo.write_bytes(jpeg_bytes(640, 480))
    run = open_run(photo, tmp_path / "runs")
    sheet(run, schema, vocabulary)
    review(run, "summon-anime-wai")
    approve(run, "summon-anime-wai", schema, vocabulary)
    argv = ["draft", "--flow", CONJURE, str(rendered_image(run, 1, 7))]

    assert dispatch(build_parser().parse_args(argv), _wiring(tmp_path)) == 0

    filled = read(run.directory(CONJURE, "sheets") / "001.json", SHEET_FILE)
    assert filled["producer"]["tags_from"] == "summon-anime-wai"
    assert (run.directory(CONJURE, "review") / "001.draft.json").is_file()
    assert sorted(child.name for child in run.directory(CONJURE).iterdir()) == [
        "review",
        "sheets",
    ]
