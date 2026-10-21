"""`--progress json`: a stage verb's progress as JSON lines, its prose on stderr."""

import io
import json
from pathlib import Path

import pytest

from isekai.foundation.run import Run, open_run
from isekai.interface.cli import build_parser, dispatch
from isekai.shared.vocabulary import Vocabulary
from tests.images import jpeg_bytes
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
