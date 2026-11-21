"""`--progress json`: a stage verb's progress as JSON lines, its prose on stderr."""

import io
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import pytest

from isekai.foundation.run import Run, open_run
from isekai.interface.cli import build_parser, dispatch
from isekai.interface.render import Steps, _Images, progress_line
from isekai.interface.verbs import Reporter
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
