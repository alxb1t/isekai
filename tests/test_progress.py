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
from isekai.shared.vocabulary import Vocabulary
from tests.images import jpeg_bytes
from tests.record import recorded
from tests.stages import bare_wiring, write_wd14

FLOW = "summon-anime-wai"


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


class _Flushes(io.StringIO):
    """A stdout that counts its flushes."""

    flushed = 0

    def flush(self) -> None:
        """Count the flush, then flush."""
        self.flushed += 1
        super().flush()


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
