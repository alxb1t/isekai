"""`--progress json`: a stage verb's progress as JSON lines, its prose on stderr."""

import ast
import io
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast, get_args

import pytest

from isekai.foundation.run import Run, open_run
from isekai.interface import progress
from isekai.interface.cli import build_parser, dispatch
from isekai.interface.progress import (
    ARGUMENT,
    CAPTION,
    DONE,
    EDIT,
    FLAG,
    FORMAT,
    IMAGE,
    LANDED,
    POD,
    PREPARE,
    REFUSED,
    RENDER,
    SHEET,
    START,
    TAG,
    TEARDOWN,
    ImageLine,
    ItemLine,
    ItemState,
    Stage,
    StepLine,
    StepName,
    StepState,
)
from isekai.interface.render import Records, Steps, _Images, progress_line
from isekai.interface.verbs import Reporter
from isekai.pipeline.generate import STAGE_RENDER
from isekai.shared.vocabulary import Vocabulary
from tests.images import jpeg_bytes
from tests.record import recorded
from tests.stages import bare_wiring, write_wd14

FLOW = "summon-anime-wai"
RUN = "0d4b7e6fb2a8_portrait"
DIGEST = "ab12"

ITEM_CASES: list[tuple[tuple[Any, ...], dict[str, str | int], str]] = [
    (
        (FLOW, "sheet", "start"),
        {},
        '{"run": "0d4b7e6fb2a8_portrait", "flow": "summon-anime-wai", '
        '"stage": "sheet", "state": "start"}',
    ),
    (
        (FLOW, "sheet", "done"),
        {},
        '{"run": "0d4b7e6fb2a8_portrait", "flow": "summon-anime-wai", '
        '"stage": "sheet", "state": "done"}',
    ),
    (
        (FLOW, "sheet", "refused", "no wd14 tags"),
        {},
        '{"run": "0d4b7e6fb2a8_portrait", "flow": "summon-anime-wai", '
        '"stage": "sheet", "state": "refused", "message": "no wd14 tags"}',
    ),
    (
        (None, "tag", "start"),
        {},
        '{"run": "0d4b7e6fb2a8_portrait", "stage": "tag", "state": "start"}',
    ),
    (
        (None, "caption", "refused", "no reader"),
        {},
        '{"run": "0d4b7e6fb2a8_portrait", "stage": "caption", '
        '"state": "refused", "message": "no reader"}',
    ),
]

WORK_CASES: list[tuple[tuple[Any, ...], dict[str, str | int], str]] = [
    (
        (FLOW, "render", "done"),
        {"digest": DIGEST, "version": 2, "seed": "42"},
        '{"run": "0d4b7e6fb2a8_portrait", "flow": "summon-anime-wai", '
        '"stage": "render", "state": "done", "digest": "ab12", "version": 2, '
        '"seed": "42"}',
    ),
    (
        (FLOW, "edit", "done"),
        {"digest": DIGEST, "version": 1, "file": "42.edit-1.png"},
        '{"run": "0d4b7e6fb2a8_portrait", "flow": "summon-anime-wai", '
        '"stage": "edit", "state": "done", "digest": "ab12", "version": 1, '
        '"file": "42.edit-1.png"}',
    ),
]

STEP_CASES: list[tuple[str, str, str]] = [
    ("pod", "starting", '{"step": "pod", "state": "starting"}'),
    ("pod", "ready", '{"step": "pod", "state": "ready"}'),
    ("pod", "lost", '{"step": "pod", "state": "lost"}'),
    ("pod", "refused", '{"step": "pod", "state": "refused"}'),
    ("teardown", "done", '{"step": "teardown", "state": "done"}'),
    ("teardown", "failed", '{"step": "teardown", "state": "failed"}'),
]

IMAGE_LINES = [
    '{"step": "image", "n": 1, "of": 2, "run": "0d4b7e6fb2a8_portrait", '
    '"digest": "ab12", "flow": "summon-anime-wai", "version": 2, "seed": "42", '
    '"state": "done"}',
    '{"step": "image", "n": 2, "of": 2, "run": "0d4b7e6fb2a8_portrait", '
    '"digest": "ab12", "flow": "summon-anime-wai", "version": 2, "seed": "42", '
    '"state": "done"}',
]


def _run(tmp_path: Path, name: str, height: int) -> Run:
    photo = tmp_path / name
    photo.write_bytes(jpeg_bytes(600, height))
    return open_run(photo, tmp_path / "runs")


def _sheet(tmp_path: Path, vocabulary: Vocabulary, *argv: str) -> tuple[int, str, str]:
    """Run `sheet` over `argv`; return its exit code, stdout and stderr."""
    out, err = io.StringIO(), io.StringIO()
    wired = bare_wiring(
        vocabulary=lambda: vocabulary, runs_root=tmp_path / "runs", out=out, err=err
    )
    args = build_parser().parse_args(
        ["sheet", "--flow", FLOW, "--runs", str(tmp_path / "runs"), *argv]
    )
    return dispatch(args, wired), out.getvalue(), err.getvalue()


@pytest.mark.spec("cli:progress:each-item-reports-start-and-end")
def test_each_item_reports_its_start_and_its_end_as_json(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    run = _run(tmp_path, "ada.jpg", 800)
    write_wd14(run)

    code, out, err = _sheet(tmp_path, vocabulary, "--progress", "json", run.id)

    assert code == 0
    assert [json.loads(line) for line in out.splitlines()] == [
        {"run": run.id, "flow": FLOW, "stage": "sheet", "state": "start"},
        {"run": run.id, "flow": FLOW, "stage": "sheet", "state": "done"},
    ]
    assert f"{run.id}: sheet wrote 001.json" in err
    # A job reads the lines from a pipe as they happen, so each is flushed.
    piped = _Flushes()
    other = _run(tmp_path, "bea.jpg", 801)
    write_wd14(other)
    wired = bare_wiring(
        vocabulary=lambda: vocabulary, runs_root=tmp_path / "runs", out=piped
    )
    args = build_parser().parse_args(
        ["sheet", "--flow", FLOW, "--runs", str(tmp_path / "runs")]
        + ["--progress", "json", other.id]
    )

    assert dispatch(args, wired) == 0
    assert piped.flushed == len(piped.getvalue().splitlines())


@pytest.mark.spec("cli:progress:each-item-reports-start-and-end")
@pytest.mark.spec("cli:progress:a-refusal-is-a-line")
def test_a_sheets_lines_are_these_bytes(tmp_path: Path, vocabulary: Vocabulary) -> None:
    tagged = _run(tmp_path, "ada.jpg", 800)
    write_wd14(tagged)

    code, out, _ = _sheet(tmp_path, vocabulary, "--progress", "json", tagged.id)

    assert code == 0
    start, done, refused, *_ = (line for _, _, line in ITEM_CASES)
    assert out == f"{start.replace(RUN, tagged.id)}\n{done.replace(RUN, tagged.id)}\n"

    untagged = _run(tmp_path, "bea.jpg", 801)

    code, out, _ = _sheet(tmp_path, vocabulary, "--progress", "json", untagged.id)

    first, last = out.splitlines(keepends=True)
    prefix = refused.replace(RUN, untagged.id).partition('"message": "')[0]
    assert code == 1
    assert first == f"{start.replace(RUN, untagged.id)}\n"
    assert last.startswith(f'{prefix}"message": "')
    assert last.endswith('"}\n')


class _Flushes(io.StringIO):
    """A stdout that counts its flushes."""

    flushed = 0

    def flush(self) -> None:
        """Count the flush, then flush."""
        self.flushed += 1
        super().flush()


@pytest.mark.spec("cli:progress:a-photographs-line-names-no-flow")
@pytest.mark.spec("cli:progress:a-refusal-is-a-line")
def test_an_items_lines_are_these_bytes() -> None:
    out = _Flushes()
    reporter = Reporter(out, io.StringIO(), True)

    for arguments, more, _ in ITEM_CASES:
        reporter.item(RUN, *arguments, **more)

    assert out.getvalue() == "".join(f"{line}\n" for _, _, line in ITEM_CASES)
    assert out.flushed == len(out.getvalue().splitlines())


@pytest.mark.spec_exempt(
    "structural: a generate line and an edit line are these bytes, key order included"
)
def test_a_renders_and_an_edits_lines_are_these_bytes() -> None:
    out = _Flushes()
    reporter = Reporter(out, io.StringIO(), True)

    for arguments, more, _ in WORK_CASES:
        reporter.item(RUN, *arguments, **more)

    assert out.getvalue() == "".join(f"{line}\n" for _, _, line in WORK_CASES)
    assert out.flushed == len(out.getvalue().splitlines())


@pytest.mark.spec("cli:render-progress:each-image-of-the-total")
def test_a_sessions_step_and_image_lines_are_these_bytes() -> None:
    out = _Flushes()
    steps = Steps(out, True)
    render = json.loads(WORK_CASES[0][2])

    for step, state, _ in STEP_CASES:
        steps.step(step, state)
    for _ in IMAGE_LINES:
        steps.image(render, 2, None)

    expected = [line for _, _, line in STEP_CASES] + IMAGE_LINES
    assert out.getvalue() == "".join(f"{line}\n" for line in expected)
    assert out.flushed == len(expected)
    assert steps.flag == ("--progress", "json")
    unheard = _Flushes()
    quiet = Steps(unheard, False)
    quiet.step("pod", "ready")
    quiet.image(render, 2, None)
    assert unheard.getvalue() == ""
    assert quiet.flag == ()


@pytest.mark.spec_exempt("structural: what an emitter prints, the reader reads back")
def test_each_line_kind_is_read_back_as_what_built_it() -> None:
    lines = [line for _, _, line in ITEM_CASES + WORK_CASES]
    lines += [line for _, _, line in STEP_CASES] + IMAGE_LINES

    for line in lines:
        assert progress_line(line) == json.loads(line)
        assert json.dumps(progress_line(line)) == line

    for other in ("refused: no tags", "[1, 2]", ""):
        assert progress_line(other) is None


@pytest.mark.spec_exempt("structural: a render line is the session's image step")
def test_a_render_line_becomes_the_sessions_image_line() -> None:
    out = io.StringIO()
    images = _Images(Steps(out, True), 2, None)
    render = WORK_CASES[0][2]
    edit = WORK_CASES[1][2]
    refused_render = json.dumps({**json.loads(render), "state": "refused"})
    half = len(render) // 2

    images.write(render[:half])
    assert out.getvalue() == ""

    images.write(f"{render[half:]}\n")
    assert out.getvalue() == f"{IMAGE_LINES[0]}\n"

    held = out.getvalue()
    for line in [item for _, _, item in ITEM_CASES] + [edit, refused_render]:
        images.write(f"{line}\n")
    assert out.getvalue() == held

    images.write(f"{render}\n")
    assert out.getvalue() == f"{IMAGE_LINES[0]}\n{IMAGE_LINES[1]}\n"


@pytest.mark.spec_exempt(
    "structural: a quiet session with no record hands its child its own stream"
)
def test_a_quiet_session_hands_its_child_its_own_stream() -> None:
    out = io.StringIO()

    assert Steps(out, False).child() is out


class _Kept:
    """Stand in for the session's records: keep each image it is handed."""

    def __init__(self) -> None:
        self.images: list[Mapping[str, Any]] = []

    def step(self, step: str, state: str) -> None:
        pass

    def image(self, item: Mapping[str, Any], runs: Path) -> None:
        self.images.append(item)


@pytest.mark.spec_exempt(
    "structural: an image reaches the record only when both are given"
)
def test_a_session_records_an_image_only_with_a_record_and_its_runs() -> None:
    out = io.StringIO()
    render = json.loads(WORK_CASES[0][2])
    runs = Path("runs")

    Steps(out, True).image(render, 2, runs)

    assert out.getvalue() == f"{IMAGE_LINES[0]}\n"
    kept = _Kept()
    steps = Steps(io.StringIO(), True)
    steps.record = cast("Records", kept)

    steps.image(render, 2, None)
    assert kept.images == []

    steps.image(render, 2, runs)
    assert kept.images == [render]


class _Landed:
    """Stand in for `Steps`: keep each image item it is handed."""

    def __init__(self) -> None:
        self.items: list[Mapping[str, Any]] = []

    def image(self, item: Mapping[str, Any], total: int, runs: Path | None) -> None:
        self.items.append(item)


@pytest.mark.spec_exempt("structural: the session reads the lines the CLI prints")
def test_the_session_reads_the_lines_the_cli_prints() -> None:
    wire = cast("dict[str, dict[str, Any]]", recorded("wire"))
    assert progress_line(json.dumps(wire["sheet"])) == wire["sheet"]
    assert progress_line(json.dumps(wire["render"])) == wire["render"]
    landed = _Landed()
    images = _Images(cast("Steps", landed), 1, None)

    images.write(json.dumps(wire["sheet"]) + "\n")
    assert landed.items == []

    images.write(json.dumps(wire["render"]) + "\n")
    assert landed.items == [wire["render"]]


@pytest.mark.spec("cli:progress:a-refusal-is-a-line")
def test_a_refusal_is_a_line_and_the_other_items_still_report(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    untagged = _run(tmp_path, "ada.jpg", 800)
    tagged = _run(tmp_path, "bea.jpg", 801)
    write_wd14(tagged)

    code, out, _ = _sheet(
        tmp_path, vocabulary, "--progress", "json", untagged.id, tagged.id
    )

    lines = [json.loads(line) for line in out.splitlines()]
    assert code == 1
    (refused,) = [line for line in lines if line["state"] == "refused"]
    assert refused["run"] == untagged.id
    assert refused["message"]
    assert {"run": tagged.id, "flow": FLOW, "stage": "sheet", "state": "done"} in lines


@pytest.mark.spec("cli:progress:without-the-flag-nothing-changes")
def test_without_the_flag_stdout_holds_the_human_lines(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    run = _run(tmp_path, "ada.jpg", 800)
    write_wd14(run)

    code, out, _ = _sheet(tmp_path, vocabulary, run.id)

    assert code == 0
    assert out == f"{run.id}: sheet wrote 001.json\n"


@pytest.mark.spec_exempt("structural: the lines' module loads under -S")
def test_the_progress_module_imports_the_standard_library_alone() -> None:
    tree = ast.parse(Path(progress.__file__).read_text())
    modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(cast("str", node.module))

    assert modules
    for module in modules:
        assert module.split(".")[0] in sys.stdlib_module_names
        assert module.split(".")[0] != "isekai"


@pytest.mark.spec_exempt("structural: the declared names are the words printed")
def test_the_declared_names_are_the_words_the_lines_print() -> None:
    assert (FLAG, FORMAT, ARGUMENT) == ("--progress", "json", ("--progress", "json"))
    assert (TAG, CAPTION, SHEET, RENDER, EDIT) == (
        "tag",
        "caption",
        "sheet",
        "render",
        "edit",
    )
    assert PREPARE == ("tag", "caption", "sheet")
    assert (START, DONE, REFUSED) == ("start", "done", "refused")
    assert (POD, TEARDOWN, IMAGE) == ("pod", "teardown", "image")
    assert LANDED == ("digest", "flow", "version", "seed")
    assert RENDER == STAGE_RENDER
    assert Steps(io.StringIO(), True).flag == ARGUMENT
    assert Steps(io.StringIO(), False).flag == ()


@pytest.mark.spec_exempt("structural: each sample line is its declared shape")
def test_each_sample_line_is_the_shape_it_declares() -> None:
    declared = list(ItemLine.__annotations__)

    for _, _, line in ITEM_CASES + WORK_CASES:
        item = json.loads(line)
        remaining = iter(declared)
        assert all(key in remaining for key in item)
        assert {"run", "stage", "state"} <= item.keys()
        assert item["stage"] in get_args(Stage)
        assert item["state"] in get_args(ItemState)

    for _, _, line in STEP_CASES:
        step = json.loads(line)
        assert list(step) == list(StepLine.__annotations__)
        assert step["step"] in get_args(StepName)
        assert step["state"] in get_args(StepState)

    for line in IMAGE_LINES:
        assert list(json.loads(line)) == list(ImageLine.__annotations__)
