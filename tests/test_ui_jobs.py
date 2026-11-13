"""Prepare as a job, and the event stream that tells the page of it.

Each child is a real process: a short Python script stands in for a verb, so Stop
and the slots are proved against a process that can be interrupted.
"""

import io
import json
import queue
import random
import subprocess
import sys
import threading
import time
import urllib.error
from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any, TextIO, cast

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from isekai.boundary import gpu, ollama  # noqa: E402
from isekai.boundary.gpu import GpunitExit, Say, Seams, Volume  # noqa: E402
from isekai.foundation.flow import FLOWS_DIR, Schema, load_flow  # noqa: E402
from isekai.foundation.refusal import Refusal  # noqa: E402
from isekai.foundation.run import Run, approval_of, open_run  # noqa: E402
from isekai.interface.cli import build_parser  # noqa: E402
from isekai.interface.render import LOST_EXIT, without_flags  # noqa: E402
from isekai.interface.ui import HOST, events, library  # noqa: E402
from isekai.interface.ui import app as app_module  # noqa: E402
from isekai.interface.ui.app import cell_event, create_app  # noqa: E402
from isekai.interface.ui.jobs import (  # noqa: E402
    Jobs,
    Step,
    cells_of,
    plan,
    prepare_command,
    render_command,
    settle_s,
)
from isekai.pipeline.generate import prepare  # noqa: E402
from isekai.pipeline.review import approve, review  # noqa: E402
from isekai.shared.vocabulary import Vocabulary  # noqa: E402
from tests.conftest import snapshot  # noqa: E402
from tests.fakes import FakeComfyClient  # noqa: E402
from tests.images import jpeg_bytes, photo_jpeg  # noqa: E402
from tests.record import recorded  # noqa: E402
from tests.stages import bare_wiring, render, sheet, write_wd14  # noqa: E402

FLOW = "summon-anime-wai"
CONTROL = "control-anime-wai"
OFFERED = (FLOW, "conjure-anime-wai")
PORT = 8766
WAIT = 20.0


def _collection(tmp_path: Path, *names: str) -> tuple[Path, list[Run]]:
    """Write a collection whose every source has a run assigned to `FLOW`."""
    folder = tmp_path / "lib" / "b"
    (folder / "sources").mkdir(parents=True)
    made = []
    for index, name in enumerate(names):
        source = folder / "sources" / name
        source.write_bytes(jpeg_bytes(600 + index, 800))
        run = open_run(source, folder / "runs")
        run.directory(FLOW).mkdir()
        made.append(run)
    return folder, made


class _Script:
    """A command that runs `script` as the child, recording the cells each asked.

    The child's arguments are each cell's run id once, in order.
    """

    def __init__(self, script: str) -> None:
        self.script = script
        self.asked: list[list[str]] = []

    def __call__(self, runs: Path, cells: Sequence[str]) -> list[str]:
        self.asked.append(list(cells))
        ids = dict.fromkeys(cell.rpartition("/")[0] for cell in cells)
        return [sys.executable, "-c", self.script, *ids]


def _as_is(line: dict[str, Any]) -> list[dict[str, Any]]:
    """Return `line` as the one cell event it makes, its stage as the line says."""
    return [dict(line)]


def _line(state: str) -> str:
    """Return a script printing `tag`'s progress line, naming no flow, for `argv[1]`."""
    return (
        "import json, sys; print(json.dumps({'run': sys.argv[1], "
        f"'stage': 'tag', 'state': '{state}'}}), flush=True)"
    )


def _until(found: "queue.Queue[events.Event]", kind: str) -> events.Event:
    """Return the next event of `kind` from a subscribed queue."""
    deadline = time.monotonic() + WAIT
    while time.monotonic() < deadline:
        event = found.get(timeout=WAIT)
        if event[0] == kind:
            return event
    raise AssertionError(f"no {kind} event")


def _steps(run: Run) -> list[Step]:
    """Return Prepare's steps for `run` in `FLOW`: the photograph's, then the sheet."""
    return [
        Step(None, "tag", (run.id,)),
        Step(None, "caption", (run.id,)),
        Step(FLOW, "sheet", (run.id,)),
    ]


SLEEP = "import time\nwhile True: time.sleep(0.05)"

# A render child that takes a while to tear its pod down once interrupted.
SLOW_TEARDOWN = (
    "import signal, sys, time\n"
    "def down(*_):\n"
    "    time.sleep(0.5)\n"
    "    open(sys.argv[1], 'a').write('torn down\\n')\n"
    "    sys.exit(130)\n"
    "signal.signal(signal.SIGINT, down)\n"
    "open(sys.argv[1], 'a').write('render\\n')\n"
    "while True: time.sleep(0.05)\n"
)


def _until_rendering(record: Path) -> None:
    """Return once a render child has written `render` to `record`."""
    deadline = time.monotonic() + WAIT
    while "render" not in (record.read_text() if record.exists() else ""):
        assert time.monotonic() < deadline, "the render child never started"
        time.sleep(0.01)


def _sleeping_render(limit: int, roots: Sequence[Path], session: str) -> list[str]:
    """Return a render child that runs until it is interrupted."""
    return [sys.executable, "-c", SLEEP]


@pytest.mark.spec("ui:prepare:one-job-at-a-time")
def test_a_second_job_of_a_kind_is_refused_naming_the_one_that_runs(
    tmp_path: Path,
) -> None:
    folder, (run,) = _collection(tmp_path, "ada.jpg")
    volume, _ = _order(tmp_path / "acts")
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        command=_Script(SLEEP),
        volume=volume,
        render=_sleeping_render,
    )
    jobs.prepare("b", folder, _steps(run), lambda line: [])
    jobs.render({"b": folder}, limit=1500, total=1, keep_open=False)

    try:
        with pytest.raises(Refusal, match="a job is running: Prepare on b"):
            jobs.prepare("other", folder, _steps(run), lambda line: [])
        with pytest.raises(Refusal, match="a job is running: Render on b"):
            jobs.render({"other": folder}, limit=1500, total=1, keep_open=False)
    finally:
        jobs.shutdown()


@pytest.mark.spec("ui:prepare:a-job-follows-an-ended-one")
def test_a_job_of_a_kind_starts_once_the_one_before_it_has_ended(
    tmp_path: Path,
) -> None:
    folder, (run,) = _collection(tmp_path, "ada.jpg")
    record = tmp_path / "acts"
    volume, command = _order(record)
    script = _Script("pass")
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        command=script,
        volume=volume,
        render=command,
        now=lambda: "ended",
    )

    for _ in range(2):
        jobs.prepare("b", folder, _steps(run), lambda line: [])
        jobs.wait("prepare", WAIT)
    sessions = []
    for _ in range(2):
        jobs.render({"b": folder}, limit=1500, total=1, keep_open=False)
        jobs.wait("render", WAIT)
        sessions.append(((jobs.slot("render") or {})["session"])["id"])

    assert script.asked == [[f"{run.id}/{FLOW}"], [f"{run.id}/{FLOW}"]]
    acts = record.read_text().splitlines()
    assert [act for act in acts if act.startswith("render")] == [
        f"render 1500 {session}" for session in sessions
    ]


@pytest.mark.spec("ui:prepare:a-render-runs-beside-a-prepare")
def test_a_render_runs_beside_a_prepare_and_its_stop_leaves_the_prepare(
    tmp_path: Path,
) -> None:
    folder, (run,) = _collection(tmp_path, "ada.jpg")
    volume, _ = _order(tmp_path / "acts")
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        command=_Script(SLEEP),
        volume=volume,
        render=_sleeping_render,
    )
    jobs.prepare("b", folder, _steps(run), lambda line: [])

    try:
        jobs.render({"other": folder}, limit=1500, total=1, keep_open=False)
        assert jobs.running("prepare") and jobs.running("render")

        jobs.stop("render")
        jobs.wait("render", WAIT)

        assert (jobs.slot("render") or {})["state"] == "stopped"
        assert jobs.running("prepare")
    finally:
        jobs.shutdown()


@pytest.mark.spec("ui:prepare:stopping-the-surface-interrupts-both")
def test_stopping_the_surface_interrupts_both_and_closes_the_window_first(
    tmp_path: Path,
) -> None:
    folder, (run,) = _collection(tmp_path, "ada.jpg")
    record = tmp_path / "acts"
    volume, _ = _order(record)
    broadcast = events.Broadcast()
    found = broadcast.subscribe()
    prepared = _Script(_line("start") + "\nimport time\nwhile True: time.sleep(0.05)")
    jobs = Jobs(
        broadcast,
        lambda: None,
        command=prepared,
        volume=volume,
        render=lambda limit, roots, session: [
            sys.executable,
            "-c",
            SLOW_TEARDOWN,
            str(record),
        ],
        err=io.StringIO(),
    )
    jobs.prepare("b", folder, _steps(run), _as_is)
    _until(found, "cell")
    jobs.render({"b": folder}, limit=1500, total=1, keep_open=False)
    _until_rendering(record)

    jobs.shutdown(timeout=0.05)

    assert record.read_text().splitlines() == [
        "volume up --yes",
        "render",
        "torn down",
        "volume down",
    ]
    assert (jobs.slot("prepare") or {})["state"] == "stopped"
    assert prepared.asked == [[f"{run.id}/{FLOW}"]]


@pytest.mark.spec("ui:prepare:the-log-names-each-job")
def test_each_line_a_job_writes_to_the_collections_log_names_its_job(
    tmp_path: Path,
) -> None:
    folder, (run,) = _collection(tmp_path, "ada.jpg")

    def gpunit(argv: Sequence[str], say: Say) -> GpunitExit:
        say(f"gpunit {' '.join(argv)}")
        return GpunitExit(0)

    volume = Volume(run=gpunit, records=tmp_path / ".gpunit")
    # The last line ends with no newline, as a child cut short leaves it.
    said = "import sys; sys.stderr.write({!r})"
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        command=_Script(said.format("tag one\ntag two")),
        volume=volume,
        render=lambda limit, roots, session: [
            sys.executable,
            "-c",
            said.format("pod up\n"),
        ],
    )

    other = folder.parent / "c"
    other.mkdir()
    jobs.prepare("b", folder, _steps(run), lambda line: [])
    jobs.render({"b": folder, "c": other}, limit=1500, total=1, keep_open=False)
    jobs.wait("prepare", WAIT)
    jobs.wait("render", WAIT)

    rendered = [
        "[render] gpunit volume down",
        "[render] gpunit volume up --yes",
        "[render] pod up",
    ]
    assert sorted((folder / "log.txt").read_text().splitlines()) == [
        "[prepare] tag one",
        "[prepare] tag two",
        *rendered,
    ]
    # A render's prose reaches every collection it renders.
    assert sorted((other / "log.txt").read_text().splitlines()) == rendered
    assert (jobs.slot("render") or {})["collections"] == ["b", "c"]


@pytest.mark.spec("ui:prepare:refused-when-ollama-does-not-answer")
def test_prepare_is_refused_with_the_readers_message_and_starts_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[object] = []

    class Closed:
        def open(self, *args: object, **kwargs: object) -> None:
            opened.append(args)
            raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(ollama, "OPENER", Closed())
    folder, (run,) = _collection(tmp_path, "ada.jpg")
    script = _Script("pass")
    jobs = Jobs(events.Broadcast(), ollama.probe, command=script)

    with pytest.raises(Refusal) as refused:
        jobs.prepare("b", folder, _steps(run), lambda line: [])

    assert str(refused.value) == ollama.NOT_LISTENING
    assert len(opened) == 1
    assert script.asked == []
    assert jobs.slot("prepare") is None


@pytest.mark.spec("ui:prepare:stop-interrupts-the-job")
def test_stop_interrupts_the_stage_and_starts_no_later_one(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    folder, (run, done) = _collection(tmp_path, "ada.jpg", "bea.jpg")
    sheet(done, load_flow(FLOW).schema, vocabulary)
    before = snapshot(done.path)
    broadcast = events.Broadcast()
    found = broadcast.subscribe()
    script = _Script(_line("start") + "\nimport time\nwhile True: time.sleep(0.05)")
    jobs = Jobs(broadcast, lambda: None, command=script, now=lambda: STARTED)
    steps = plan({FLOW: [run.id, done.id]}, {FLOW: True})
    jobs.prepare("b", folder, steps, lambda line: [dict(line)])
    _until(found, "cell")

    jobs.stop("prepare")
    jobs.wait("prepare", WAIT)

    assert script.asked == [[f"{run.id}/{FLOW}", f"{done.id}/{FLOW}"]]
    assert jobs.slot("prepare") == {
        "kind": "prepare",
        "collection": "b",
        "state": "stopped",
        "flow": None,
        "stage": "tag",
        "message": None,
        "progress": {
            "started": STARTED,
            "stages": [
                {"stage": "tag", "done": 0, "of": 2},
                {"stage": "caption", "done": 0, "of": 2},
                {"stage": "sheet", "done": 0, "of": 2},
            ],
        },
    }
    assert snapshot(done.path) == before


@pytest.mark.spec("ui:prepare:a-silent-failure-ends-the-job")
def test_a_stage_that_fails_before_it_reports_ends_the_job_naming_the_log(
    tmp_path: Path,
) -> None:
    folder, (run,) = _collection(tmp_path, "ada.jpg")
    script = _Script("import sys; sys.exit('no module named onnxruntime')")
    jobs = Jobs(events.Broadcast(), lambda: None, command=script)

    jobs.prepare("b", folder, _steps(run), lambda line: [])
    jobs.wait("prepare", WAIT)

    assert script.asked == [[f"{run.id}/{FLOW}"]]
    slot = jobs.slot("prepare")
    assert slot is not None
    assert (slot["state"], slot["stage"]) == ("failed", None)
    assert "prepare ended before reporting" in slot["message"]
    assert "b/log.txt" in slot["message"]


@pytest.mark.spec("ui:events:a-connection-starts-with-a-snapshot")
def test_a_stream_opened_for_a_collection_starts_with_both_slots_and_its_hub(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    folder, (run,) = _collection(tmp_path, "ada.jpg")
    wired = bare_wiring(
        vocabulary=lambda: vocabulary,
        runs_root=folder / "runs",
        rng=random.Random(0),
        probe=lambda: None,
    )
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html>")

    def first_frame(url: str) -> dict[str, Any]:
        # Each stream is read on its own app: closing one ends its every stream.
        app = create_app(
            folder.parent,
            wired,
            flows=OFFERED,
            bundle=dist,
            wire=lambda runs: replace(wired, runs_root=runs),
            host=HOST,
            port=PORT,
        )
        broadcast: events.Broadcast = app.state.broadcast

        def close_once_open() -> None:
            deadline = time.monotonic() + WAIT
            while not broadcast._queues and time.monotonic() < deadline:
                time.sleep(0.01)
            broadcast.publish(events.CLOSE, {})

        threading.Thread(target=close_once_open, daemon=True).start()
        body = TestClient(app, base_url=f"http://{HOST}:{PORT}").get(url)
        assert body.status_code == 200
        assert body.headers["content-type"].startswith("text/event-stream")
        kind, data = body.text.split("\n")[:2]
        assert kind == "event: snapshot"
        return json.loads(data.removeprefix("data: "))

    first = first_frame("/events?collection=b")
    assert first["jobs"] == {"prepare": None, "render": None}
    assert first["hub"]["collection"] == "b"
    assert first["hub"]["sources"][0]["cells"][FLOW]["stage"] == "assigned"
    assert first["hub"]["sources"][0]["digest"] == run.digest

    # A collection or an import it cannot read is left out, and the stream still opens:
    # it is the page's only one, and a refused connect would end it for good.
    missing = first_frame("/events?collection=gone")
    assert (missing["jobs"]["prepare"], "hub" in missing) == (None, False)
    closed = first_frame("/events?collection=b&staging=0123")
    assert (closed["hub"]["collection"], "files" in closed) == ("b", False)


@pytest.mark.spec("ui:events:a-stages-report-reaches-the-stream")
def test_a_stage_reporting_an_item_done_sends_that_cells_new_stage(
    tmp_path: Path,
) -> None:
    folder, (run,) = _collection(tmp_path, "ada.jpg")
    tags = write_wd14(run)
    staged = tmp_path / "001.json"
    tags.rename(staged)
    copy = f"import shutil; shutil.copy({str(staged)!r}, {str(tags)!r}); " + _line(
        "done"
    )
    broadcast = events.Broadcast()
    grid = library.hub(folder, OFFERED, FLOWS_DIR)
    cell = cell_event(folder, grid, {FLOW: load_flow(FLOW)})
    stream = events.stream(
        broadcast, lambda: {"jobs": {}}, collection="b", heartbeat=WAIT
    )
    next(stream)
    jobs = Jobs(broadcast, lambda: None, command=_Script(copy))

    jobs.prepare("b", folder, _steps(run), cell)

    frames = []
    for frame in stream:
        frames.append(frame)
        if frame.startswith("event: cell"):
            break
    jobs.wait("prepare", WAIT)
    data = json.loads(frames[-1].split("\n")[1].removeprefix("data: "))
    assert (data["source"], data["flow"], data["state"]) == ("ada.jpg", FLOW, "done")
    assert data["cell"]["stage"] == "tagged"


@pytest.mark.spec_exempt(
    "structural: the cell and the job read the line the CLI prints"
)
def test_the_cell_and_the_job_read_the_sheet_line_the_cli_prints(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    folder, (run,) = _collection(tmp_path, "ada.jpg")
    sheet(run, schema, vocabulary)
    printed = cast("dict[str, Any]", recorded("wire"))["sheet"]
    script = (
        "import json, sys; "
        f"print(json.dumps({{**{printed!r}, 'run': sys.argv[1]}}), flush=True)"
    )
    broadcast = events.Broadcast()
    found = broadcast.subscribe()
    grid = library.hub(folder, OFFERED, FLOWS_DIR)
    cell = cell_event(folder, grid, {FLOW: load_flow(FLOW)})
    jobs = Jobs(broadcast, lambda: None, command=_Script(script))

    jobs.prepare("b", folder, [Step(FLOW, "sheet", (run.id,))], cell)
    jobs.wait("prepare", WAIT)

    published = _until(found, "cell")[1]
    assert (published["flow"], published["state"]) == (FLOW, "done")
    slot = jobs.slot("prepare")
    assert slot is not None
    assert slot["progress"]["stages"] == [{"stage": "sheet", "done": 1, "of": 1}]


STARTED = "2026-10-22T10:00:00Z"


def _reports(*lines: tuple[str, str | None, str, str, str]) -> str:
    """Return a script printing a line per `(run, flow, stage, state, reached)`.

    A `None` flow is a photograph's stage, and its line names no flow.
    """
    reports = [
        {
            "run": run_id,
            **({} if flow is None else {"flow": flow}),
            "stage": stage,
            "state": state,
            "cell": {"stage": reached},
        }
        for run_id, flow, stage, state, reached in lines
    ]
    return "import json; " + "; ".join(
        f"print(json.dumps({line!r}), flush=True)" for line in reports
    )


@pytest.mark.spec("ui:prepare:totals-count-cells-not-stages")
def test_prepare_totals_count_each_stages_cells_once(tmp_path: Path) -> None:
    folder, (run, refused) = _collection(tmp_path, "ada.jpg", "bea.jpg")
    other = OFFERED[1]
    script = _reports(
        (run.id, None, "tag", "done", "tagged"),
        (refused.id, None, "tag", "refused", "assigned"),
        (run.id, None, "tag", "done", "tagged"),
        (run.id, None, "caption", "done", "tagged"),
        (refused.id, None, "caption", "refused", "assigned"),
        # A tag line naming a flow is no photograph's, so it counts in none.
        (run.id, FLOW, "tag", "done", "tagged"),
        (refused.id, FLOW, "sheet", "refused", "sheet"),
        ("unknown", FLOW, "sheet", "done", "sheet"),
        (refused.id, other, "sheet", "done", "sheet"),
        (refused.id, FLOW, "sheet", "done", "tagged"),
        (run.id, FLOW, "sheet", "done", "sheet"),
        (run.id, FLOW, "sheet", "done", "sheet"),
        (run.id, other, "sheet", "done", "rendered"),
    )
    broadcast = events.Broadcast()
    found = broadcast.subscribe()
    jobs = Jobs(broadcast, lambda: None, command=_Script(script), now=lambda: STARTED)
    jobs.prepare(
        "b",
        folder,
        [
            *(Step(None, verb, (run.id, refused.id)) for verb in ("tag", "caption")),
            Step(FLOW, "sheet", (run.id, refused.id)),
            Step(other, "sheet", (run.id,)),
        ],
        _as_is,
    )
    jobs.wait("prepare", WAIT)
    slot = jobs.slot("prepare")
    assert slot is not None
    assert slot["progress"] == {
        "started": STARTED,
        "stages": [
            {"stage": "tag", "done": 1, "of": 2},
            {"stage": "caption", "done": 1, "of": 2},
            {"stage": "sheet", "done": 2, "of": 3},
        ],
    }
    updates = []
    while not found.empty():
        kind, data = found.get_nowait()
        if kind == "job":
            updates.append([one["done"] for one in data["progress"]["stages"]])
    assert [1, 0, 0] in updates and [1, 1, 1] in updates
    slot["progress"]["stages"][0]["done"] = 99
    copied = jobs.slot("prepare")
    assert copied is not None
    assert copied["progress"]["stages"][0]["done"] == 1


@pytest.mark.spec("ui:prepare:a-photograph-is-described-once")
@pytest.mark.spec("ui:prepare:each-photograph-in-turn")
def test_a_photograph_is_described_once(tmp_path: Path) -> None:
    other = OFFERED[1]
    tagged = {FLOW: True, other: True}

    steps = plan({FLOW: ["r1"], other: ["r1"]}, tagged)

    assert [step.verb for step in steps] == ["tag", "caption", "sheet", "sheet"]
    assert [step.runs for step in steps] == [("r1",)] * 4
    line = build_parser().parse_args(prepare_command(tmp_path, cells_of(steps))[3:])
    assert (line.verb, line.cells) == ("prepare", [f"r1/{FLOW}", f"r1/{other}"])
    assert cells_of(plan({FLOW: ["r1", "r2"], other: ["r2"]}, tagged)) == [
        f"r1/{FLOW}",
        f"r2/{FLOW}",
        f"r2/{other}",
    ]


@pytest.mark.spec("ui:events:a-reconnect-keeps-prepare-progress")
def test_reconnect_keeps_prepare_progress(
    tmp_path: Path, vocabulary: Vocabulary, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder, (run, later) = _collection(tmp_path, "ada.jpg", "bea.jpg")
    wired = bare_wiring(
        vocabulary=lambda: vocabulary,
        runs_root=folder / "runs",
        rng=random.Random(0),
        probe=lambda: None,
    )
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html>")
    made: list[Jobs] = []

    def make_jobs(
        broadcast: events.Broadcast,
        probe: Callable[[], None],
        *,
        volume: Volume,
        raise_volume: Callable[[], None],
        err: TextIO,
    ) -> Jobs:
        job = Jobs(broadcast, probe, volume=volume, raise_volume=raise_volume, err=err)
        made.append(job)
        return job

    monkeypatch.setattr(app_module, "Jobs", make_jobs)
    app = create_app(
        folder.parent,
        wired,
        flows=OFFERED,
        bundle=dist,
        wire=lambda runs: replace(wired, runs_root=runs),
        host=HOST,
        port=PORT,
    )
    jobs = made[0]
    broadcast: events.Broadcast = app.state.broadcast
    release = tmp_path / "release"
    first = {
        "run": run.id,
        "flow": FLOW,
        "stage": "sheet",
        "state": "done",
        "cell": {"stage": "sheet"},
    }
    script = (
        "import json, pathlib, time; "
        f"print(json.dumps({first!r}), flush=True); "
        f"release = pathlib.Path({str(release)!r}); deadline = time.monotonic() + 20; "
        "\nwhile not release.exists() and time.monotonic() < deadline:"
        "\n time.sleep(.01)"
    )
    monkeypatch.setattr(jobs, "_command", _Script(script))
    monkeypatch.setattr(jobs, "_now", lambda: STARTED)
    subscribe = broadcast.subscribe
    updates = subscribe()

    def finite_subscription() -> queue.Queue[events.Event]:
        found = subscribe()
        found.put((events.CLOSE, {}))
        return found

    monkeypatch.setattr(broadcast, "subscribe", finite_subscription)
    client = TestClient(app, base_url=f"http://{HOST}:{PORT}")
    try:
        initial = jobs.prepare(
            "b", folder, [Step(FLOW, "sheet", (run.id, later.id))], _as_is
        )
        assert initial["progress"]["started"] == STARTED
        monkeypatch.setattr(jobs, "_now", lambda: "2026-10-22T10:05:00Z")
        while _until(updates, "job")[1]["progress"]["stages"][0]["done"] != 1:
            pass
        for _ in range(2):
            body = client.get("/events?collection=b")
            first_frame = body.text.split("\n")[1].removeprefix("data: ")
            assert json.loads(first_frame)["jobs"]["prepare"]["progress"] == {
                "started": STARTED,
                "stages": [{"stage": "sheet", "done": 1, "of": 2}],
            }
        assert jobs.running("prepare")
    finally:
        broadcast.unsubscribe(updates)
        release.touch()
        jobs.shutdown()


# --- render ---------------------------------------------------------------------


def _order(
    record: Path,
) -> tuple[Volume, Callable[[int, Sequence[Path], str], list[str]]]:
    """Return a gpunit double and a render command, each appending its act to `record`.

    The render child is a real process, so the order is read from one file.
    """

    def run(argv: Sequence[str], say: Say) -> GpunitExit:
        with record.open("a") as acts:
            print(" ".join(argv), file=acts)
        return GpunitExit(LOST_EXIT if "up" in argv and "lost" in record.name else 0)

    def command(limit: int, roots: Sequence[Path], session: str) -> list[str]:
        script = (
            "import sys; open(sys.argv[1], 'a')"
            ".write(' '.join(['render', *sys.argv[2:]]) + '\\n')"
        )
        return [sys.executable, "-c", script, str(record), str(limit), session]

    return Volume(run=run, records=record.parent / ".gpunit"), command


def _failing_close(record: Path) -> Volume:
    """Return a gpunit double that opens the window and fails to close it."""

    def run(argv: Sequence[str], say: Say) -> GpunitExit:
        with record.open("a") as acts:
            print(" ".join(argv), file=acts)
        return GpunitExit(1 if "down" in argv else 0)

    return Volume(run=run, records=record.parent / ".gpunit")


# A render child that reports a step and an image, then fails.
STEPS = (
    "import json\n"
    "print(json.dumps({'step': 'pod', 'state': 'done'}), flush=True)\n"
    "print(json.dumps({'step': 'image', 'digest': 'd1', "
    "'flow': 'summon-anime-wai', 'version': 1, 'seed': '7'}), flush=True)\n"
    "raise SystemExit(1)\n"
)


@pytest.mark.spec("ui:render-job:a-failed-close-raises-the-volume-alert")
def test_a_failed_close_after_a_render_raises_the_volume_alert(
    tmp_path: Path,
) -> None:
    folder, _ = _collection(tmp_path, "ada.jpg")
    record = tmp_path / "acts"
    command = _order(record)[1]
    raised: list[bool] = []
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=_failing_close(record),
        render=command,
        raise_volume=lambda: raised.append(True),
        now=lambda: "ended",
    )

    jobs.render({"b": folder}, limit=1500, total=1, keep_open=False)
    jobs.wait("render", WAIT)

    slot = jobs.slot("render") or {}
    assert raised == [True]
    assert slot["session"]["steps"]["volume down"] == "failed"
    assert record.read_text().splitlines() == [
        "volume up --yes",
        f"render 1500 {slot['session']['id']}",
        "volume down",
    ]


@pytest.mark.spec("ui:render-job:the-verbs-lines-are-the-sessions-steps")
def test_the_verbs_step_and_image_lines_are_the_sessions_steps_and_images(
    tmp_path: Path,
) -> None:
    folder, _ = _collection(tmp_path, "ada.jpg")
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=_order(tmp_path / "acts")[0],
        render=lambda limit, roots, session: [sys.executable, "-c", STEPS],
        now=lambda: "ended",
    )

    jobs.render({"b": folder}, limit=1500, total=1, keep_open=False)
    jobs.wait("render", WAIT)

    slot = jobs.slot("render") or {}
    assert slot["state"] == "failed"
    assert slot["session"]["steps"]["pod"] == "done"
    assert slot["session"]["images"] == [
        {"digest": "d1", "flow": FLOW, "version": 1, "seed": "7"}
    ]
    assert slot["message"].startswith("render ended with exit 1;")
    assert "b/log.txt" in slot["message"]
    assert "before reporting" not in slot["message"]

    silent = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=_order(tmp_path / "silent-acts")[0],
        render=lambda limit, roots, session: [
            sys.executable,
            "-c",
            "raise SystemExit(1)",
        ],
        now=lambda: "ended",
    )
    silent.render({"b": folder}, limit=1500, total=1, keep_open=False)
    silent.wait("render", WAIT)

    assert (silent.slot("render") or {})[
        "message"
    ] == "render ended with exit 1 before reporting; read b/log.txt"


@pytest.mark.spec("ui:render-job:opens-renders-and-closes")
def test_a_render_job_opens_the_window_renders_at_the_limit_and_closes_it(
    tmp_path: Path,
) -> None:
    folder, _ = _collection(tmp_path, "ada.jpg")
    record = tmp_path / "acts"
    volume, command = _order(record)
    raised: list[bool] = []
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=volume,
        render=command,
        raise_volume=lambda: raised.append(True),
        now=lambda: "ended",
    )

    jobs.render({"b": folder}, limit=1500, total=1, keep_open=False)
    jobs.wait("render", WAIT)

    slot = jobs.slot("render") or {}
    # The verb's record is named by the slot's id, so the page reads that record.
    assert record.read_text().splitlines() == [
        "volume up --yes",
        f"render 1500 {slot['session']['id']}",
        "volume down",
    ]
    assert slot["state"] == "done"
    assert slot["session"]["ended"] == "ended"
    # The real line names every collection's runs root, as the verb reads them.
    roots = [folder / "runs", folder.parent / "c" / "runs"]
    line = render_command(1500, roots, slot["session"]["id"])
    parsed = build_parser().parse_args(line[3:])
    assert (parsed.runs, parsed.requests, parsed.limit) == (roots, [], 1500)
    assert raised == []


@pytest.mark.spec("ui:render-job:opens-renders-and-closes")
def test_bake_confirm_a_job_of_bakes_alone_plans_no_image(tmp_path: Path) -> None:
    folder, _ = _collection(tmp_path, "ada.jpg")
    record = tmp_path / "acts"
    volume, command = _order(record)
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=volume,
        render=command,
        now=lambda: "ended",
    )

    jobs.render({"b": folder}, limit=1500, total=0, keep_open=False)
    jobs.wait("render", WAIT)

    slot = jobs.slot("render") or {}
    assert slot["state"] == "done"
    assert (slot["session"]["of"], slot["session"]["images"]) == (0, [])
    assert record.read_text().splitlines() == [
        "volume up --yes",
        f"render 1500 {slot['session']['id']}",
        "volume down",
    ]


@pytest.mark.spec("ui:render-job:an-opening-that-raises-fails-its-step")
def test_a_window_opening_that_raises_fails_the_job_and_its_step(
    tmp_path: Path,
) -> None:
    folder, _ = _collection(tmp_path, "ada.jpg")
    rendered: list[int] = []

    def unstartable(argv: Sequence[str], say: Say) -> GpunitExit:
        raise OSError("gpunit is not installed")

    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=Volume(run=unstartable, records=tmp_path / ".gpunit"),
        render=lambda limit, roots, session: rendered.append(limit) or [],
    )

    jobs.render({"b": folder}, limit=1500, total=1, keep_open=False)
    jobs.wait("render", WAIT)

    slot = jobs.slot("render") or {}
    assert slot["state"] == "failed"
    assert slot["session"]["steps"]["volume up"] == "failed"
    assert rendered == []


@pytest.mark.spec("ui:render-job:a-lost-opening-renders-nothing")
def test_a_lost_window_opening_renders_nothing_and_raises_the_volume_alert(
    tmp_path: Path,
) -> None:
    folder, _ = _collection(tmp_path, "ada.jpg")
    record = tmp_path / "lost-acts"
    volume, command = _order(record)
    raised: list[bool] = []
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=volume,
        render=command,
        raise_volume=lambda: raised.append(True),
    )

    jobs.render({"b": folder}, limit=1500, total=1, keep_open=False)
    jobs.wait("render", WAIT)

    assert record.read_text().splitlines() == ["volume up --yes"]
    assert raised == [True]
    slot = jobs.slot("render") or {}
    assert slot["state"] == "failed"
    assert slot["session"]["steps"]["volume up"] == "lost"


@pytest.mark.spec("ui:render-job:a-refusal-names-its-kind-and-reason")
def test_a_refused_window_names_its_kind_and_reason(tmp_path: Path) -> None:
    folder, _ = _collection(tmp_path, "ada.jpg")
    refused = "refused: no card in 'gpus' meets vram_gb and max_hourly"
    rendered: list[int] = []

    def unfit(argv: Sequence[str], say: Say) -> GpunitExit:
        return GpunitExit(5, refused)

    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=Volume(run=unfit, records=tmp_path / ".gpunit"),
        render=lambda limit, roots, session: rendered.append(limit) or [],
    )

    jobs.render({"b": folder}, limit=1500, total=1, keep_open=False)
    jobs.wait("render", WAIT)

    slot = jobs.slot("render") or {}
    assert slot["state"] == "failed"
    assert slot["message"] == (
        f"no card fits max_hourly / vram_gb; gpunit {refused}; "
        "read b/log.txt for the cards it skipped"
    )
    assert rendered == []


@pytest.mark.spec("ui:render-job:a-refusal-names-its-kind-and-reason")
def test_a_refused_render_names_its_kind_and_reason(tmp_path: Path) -> None:
    folder, _ = _collection(tmp_path, "ada.jpg")
    volume, _ = _order(tmp_path / "acts")
    refused = "refused: no card in 'gpus' was placed"
    # The render child relays gpunit's lines to its stderr, as `isekai render` does.
    said = f"2026-11-03T09:14:02Z {refused}\nrefused: a line of isekai's own\n"
    script = f"import sys; sys.stderr.write({said!r}); sys.exit(4)"
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=volume,
        render=lambda limit, roots, session: [sys.executable, "-c", script],
    )

    jobs.render({"b": folder}, limit=1500, total=1, keep_open=False)
    jobs.wait("render", WAIT)

    slot = jobs.slot("render") or {}
    assert slot["state"] == "failed"
    assert slot["message"] == (
        f"no card in stock; gpunit {refused}; read b/log.txt for the cards it skipped"
    )


@pytest.mark.spec("ui:render-job:a-stopped-surface-closes-the-window")
def test_a_surface_stopped_mid_render_closes_the_window_after_the_teardown(
    tmp_path: Path,
) -> None:
    folder, _ = _collection(tmp_path, "ada.jpg")
    record = tmp_path / "acts"
    volume, _ = _order(record)
    err = io.StringIO()
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=volume,
        render=lambda limit, roots, session: [
            sys.executable,
            "-c",
            SLOW_TEARDOWN,
            str(record),
        ],
        err=err,
    )
    jobs.render({"b": folder}, limit=1500, total=1, keep_open=False)
    _until_rendering(record)

    # A wait shorter than the teardown: a render is waited for past it.
    jobs.shutdown(timeout=0.05)

    assert record.read_text().splitlines() == [
        "volume up --yes",
        "render",
        "torn down",
        "volume down",
    ]
    # Said as the wait begins, so a stop that takes minutes does not look hung.
    assert f"waiting up to {settle_s():.0f}s" in err.getvalue()
    assert "gpunit volume down" not in err.getvalue()
    assert "wait ran out" not in err.getvalue()


@pytest.mark.spec("ui:render-job:an-outlasted-stop-names-the-fix")
def test_a_stop_whose_wait_runs_out_names_the_command_that_closes_the_window(
    tmp_path: Path,
) -> None:
    folder, _ = _collection(tmp_path, "ada.jpg")
    record = tmp_path / "acts"
    volume, _ = _order(record)
    # A render child whose teardown outlasts the wait the server gives it.
    script = (
        "import signal, sys, time\n"
        "signal.signal(signal.SIGINT, lambda *_: (time.sleep(1), sys.exit(130)))\n"
        "open(sys.argv[1], 'a').write('render\\n')\n"
        "while True: time.sleep(0.05)\n"
    )
    err = io.StringIO()
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=volume,
        render=lambda limit, roots, session: [
            sys.executable,
            "-c",
            script,
            str(record),
        ],
        settle=lambda: 0.05,
        err=err,
    )
    jobs.render({"b": folder}, limit=1500, total=1, keep_open=False)
    _until_rendering(record)

    try:
        jobs.shutdown(timeout=0.05)

        assert "uv run --env-file .env gpunit volume down" in err.getvalue()
        assert "wait ran out" in err.getvalue()
    finally:
        jobs.wait("render", WAIT)


def _stop_with_window(tmp_path: Path, *, keep_open: bool) -> tuple[str, list[str]]:
    """Return terminal output and recorded teardown acts after a stopped render."""
    folder, _ = _collection(tmp_path, "ada.jpg")
    record = tmp_path / "acts"

    def volume(argv: Sequence[str], say: Say) -> GpunitExit:
        with record.open("a") as acts:
            print(" ".join(argv), file=acts)
        return GpunitExit(1 if "down" in argv else 0)

    script = (
        "import signal, sys, time\n"
        "def down(*_):\n"
        "    open(sys.argv[1], 'a').write('torn down\\n')\n"
        "    sys.exit(130)\n"
        "signal.signal(signal.SIGINT, down)\n"
        "open(sys.argv[1], 'a').write('render\\n')\n"
        "while True: time.sleep(0.05)\n"
    )
    err = io.StringIO()
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=Volume(run=volume, records=tmp_path / ".gpunit"),
        render=lambda limit, roots, session: [
            sys.executable,
            "-c",
            script,
            str(record),
        ],
        settle=lambda: 10,
        err=err,
    )
    jobs.render({"b": folder}, limit=1500, total=1, keep_open=keep_open)
    try:
        _until_rendering(record)
        jobs.shutdown(timeout=2)
        assert not jobs.running("render")
        thread = jobs._slots["render"].thread
        assert thread is not None and not thread.is_alive()
        return err.getvalue(), record.read_text().splitlines()
    finally:
        if jobs.running("render"):
            jobs.stop("render")
        jobs.wait("render", WAIT)


@pytest.mark.spec("ui:render-job:a-failed-close-at-stop-names-the-fix")
def test_failed_close_at_stop_names_the_fix(tmp_path: Path) -> None:
    terminal, acts = _stop_with_window(tmp_path, keep_open=False)
    assert acts == ["volume up --yes", "render", "torn down", "volume down"]
    assert "uv run --env-file .env gpunit volume down" in terminal
    assert "wait ran out" not in terminal
    assert "close failed" in terminal


@pytest.mark.spec("ui:render-job:a-kept-window-needs-no-close-remedy")
def test_kept_window_at_stop_needs_no_remedy(tmp_path: Path) -> None:
    terminal, acts = _stop_with_window(tmp_path, keep_open=True)
    assert acts == ["volume up --yes", "render", "torn down"]
    assert "waiting up to" in terminal
    assert "gpunit volume down" not in terminal
    assert "wait ran out" not in terminal


@pytest.mark.spec("ui:render-job:a-verb-that-cannot-start-fails-the-job")
def test_a_render_verb_that_cannot_start_fails_the_job_and_closes_the_window(
    tmp_path: Path,
) -> None:
    folder, _ = _collection(tmp_path, "ada.jpg")
    record = tmp_path / "acts"
    volume, _ = _order(record)
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=volume,
        render=lambda limit, roots, session: [str(tmp_path / "no-such-interpreter")],
    )

    jobs.render({"b": folder}, limit=1500, total=1, keep_open=False)
    jobs.wait("render", WAIT)

    assert record.read_text().splitlines() == ["volume up --yes", "volume down"]
    slot = jobs.slot("render") or {}
    assert slot["state"] == "failed"
    assert "b/log.txt" in slot["message"]


@pytest.mark.spec("ui:render-job:a-stopped-surface-closes-the-window")
def test_a_gpunit_verb_runs_in_its_own_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ran: list[tuple[list[str], dict[str, Any]]] = []
    real = subprocess.Popen

    def recorded(argv: list[str], **kwargs: Any) -> subprocess.Popen[str]:  # noqa: ANN401 -- Popen's
        ran.append((argv, kwargs))
        return real([sys.executable, "-c", "pass"], **kwargs)

    monkeypatch.setattr(gpu.subprocess, "Popen", recorded)

    assert Volume().down(lambda line: None).code == 0
    ((argv, kwargs),) = ran
    assert argv[1:] == ["-m", "gpunit", "volume", "down"]
    assert kwargs.get("start_new_session") is True


def _approved(
    folder: Path, name: str, flow: str, schema: Schema, vocabulary: Vocabulary
) -> Run:
    """Return a run of `name` under `folder` approved in `flow` for one image."""
    source = folder / "sources" / name
    source.write_bytes(jpeg_bytes(600 + len(name), 800))
    run = open_run(source, folder / "runs")
    sheet(run, schema, vocabulary, flow=flow)
    review(run, flow)
    approve(run, flow, schema, vocabulary)
    return run


def _quoting(
    tmp_path: Path, vocabulary: Vocabulary, environ: dict[str, str]
) -> tuple[Path, TestClient]:
    """Return a collection folder and a client whose session is handed `environ`."""
    folder = tmp_path / "lib" / "b"
    (folder / "sources").mkdir(parents=True)
    wired = bare_wiring(
        vocabulary=lambda: vocabulary,
        runs_root=folder / "runs",
        session=Seams(environ=environ),
    )
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html>")
    app = create_app(
        folder.parent,
        wired,
        flows=OFFERED,
        bundle=dist,
        wire=lambda runs: replace(wired, runs_root=runs),
        host=HOST,
        port=PORT,
    )
    return folder, TestClient(app, base_url=f"http://{HOST}:{PORT}")


@pytest.mark.spec("ui:render:the-dialog-lists-what-renders")
def test_the_quote_lists_each_flows_images_and_the_price(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    folder, client = _quoting(tmp_path, vocabulary, {"RUNPOD_API_KEY": "k"})
    ada = _approved(folder, "ada.jpg", FLOW, schema, vocabulary)
    _approved(folder, "beatrix.jpg", CONTROL, schema, vocabulary)
    drafted = open_run(folder / "sources" / "ada.jpg", folder / "runs")
    sheet(drafted, schema, vocabulary, flow=CONTROL)
    review(drafted, CONTROL)

    quote = client.post("/api/render/quote", json={"collections": ["b"]}).json()

    (row,) = quote["collections"]
    assert [(one["flow"], one["images"]) for one in row["flows"]] == [
        (CONTROL, 1),
        (FLOW, 1),
    ]
    assert row["flows"][1]["sources"][0]["name"] == "ada.jpg"
    assert "left_out" not in row
    assert row["flows"][1]["sources"][0]["run"] == ada.id
    assert quote["estimate"]["limit_s"] >= quote["estimate"]["seconds"]
    assert 0 < quote["price"]["about"] < quote["price"]["at_most"]
    assert quote["disabled"] is None


@pytest.mark.spec("ui:render:without-a-key-render-is-disabled")
def test_without_a_runpod_key_render_is_disabled_naming_the_fix(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    folder, client = _quoting(tmp_path, vocabulary, {})
    _approved(folder, "ada.jpg", FLOW, schema, vocabulary)

    quote = client.post("/api/render/quote", json={"collections": ["b"]}).json()
    started = client.post(
        "/api/render", json={"collections": ["b"], "keep_open": False}
    )

    assert "add RUNPOD_API_KEY to .env" in quote["disabled"]
    assert started.status_code == 409
    assert "RUNPOD_API_KEY" in started.json()["refusal"]


@pytest.mark.spec("ui:render:nothing-short-disables-render")
def test_with_every_count_rendered_render_is_disabled_naming_why(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    folder, client = _quoting(tmp_path, vocabulary, {"RUNPOD_API_KEY": "k"})
    run = _approved(folder, "ada.jpg", FLOW, schema, vocabulary)
    flow = load_flow(FLOW)
    prepare(run, {FLOW: flow})
    image = photo_jpeg((90, 60, 30), (640, 800))
    render(run, flow, FakeComfyClient(view_bytes=image), seeds=[7], poll=0)

    offer = client.get("/api/c/b/render").json()

    assert "already has its Count" in offer["disabled"]
    assert offer["images"] == 0


@pytest.mark.spec("ui:render:a-refused-count-is-shown")
def test_an_offer_whose_only_short_approval_is_damaged_carries_its_refusal(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    folder, client = _quoting(tmp_path, vocabulary, {"RUNPOD_API_KEY": "k"})
    run = _approved(folder, "ada.jpg", FLOW, schema, vocabulary)
    approval = approval_of(run, FLOW, 1)
    body = json.loads(approval.read_text())
    approval.write_text(json.dumps({**body, "renders": {"count": 0}}))

    offer = client.get("/api/c/b/render").json()

    assert offer["images"] == 0
    assert approval.name in offer["refused"]
    assert offer["disabled"] == offer["refused"]


@pytest.mark.spec("ui:render:a-grown-quote-is-refused")
def test_a_confirmation_shorter_than_the_quote_now_gives_is_refused(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    folder, client = _quoting(tmp_path, vocabulary, {"RUNPOD_API_KEY": "k"})
    _approved(folder, "ada.jpg", FLOW, schema, vocabulary)
    asked = {"collections": ["b"]}
    shown = client.post("/api/render/quote", json=asked).json()["estimate"]["limit_s"]

    started = client.post(
        "/api/render",
        json={**asked, "keep_open": False, "limit_s": shown - 1, "bakes": 0},
    )

    assert started.status_code == 409
    assert "the quote changed" in started.json()["refusal"]
    assert client.post("/api/render/quote", json=asked).json()["disabled"] is None

    # An approval made while the dialog is open adds an image the limit may not show.
    _approved(folder, "beatrix.jpg", FLOW, schema, vocabulary)
    grown = client.post(
        "/api/render",
        json={**asked, "keep_open": False, "limit_s": shown, "images": 1, "bakes": 0},
    )

    assert grown.status_code == 409
    assert "2 images, not 1" in grown.json()["refusal"]


@pytest.mark.spec("ui:damage:a-body-of-the-wrong-shape-is-refused-naming-what-it-lacks")
def test_a_confirmation_that_names_no_collections_limit_images_or_bakes_is_refused(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    folder, client = _quoting(tmp_path, vocabulary, {"RUNPOD_API_KEY": "k"})
    _approved(folder, "ada.jpg", FLOW, schema, vocabulary)
    asked = {"collections": ["b"]}
    shown = client.post("/api/render/quote", json=asked).json()["estimate"]["limit_s"]
    bodies = (
        ({"keep_open": False}, "names no collections"),
        (asked, "names no quoted limit"),
        ({**asked, "limit_s": shown}, "names no quoted images"),
        ({**asked, "limit_s": shown, "images": 1}, "names no quoted bakes"),
    )

    for body, text in bodies:
        started = client.post("/api/render", json=body)

        assert started.status_code == 409, text
        assert text in started.json()["refusal"]
    assert client.post("/api/render/quote", json=asked).json()["disabled"] is None


@pytest.mark.spec("ui:render:a-photograph-taken-out-leaves-the-quote")
def test_the_render_job_carries_each_photograph_taken_out(tmp_path: Path) -> None:
    folder, (ada,) = _collection(tmp_path, "ada.jpg")
    path = folder / "runs" / ada.id / FLOW
    record = tmp_path / "acts"
    volume, command = _order(record)
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=volume,
        render=command,
        now=lambda: "ended",
    )

    jobs.render({"b": folder}, limit=1500, total=1, keep_open=False, without=[path])
    jobs.wait("render", WAIT)

    session = (jobs.slot("render") or {})["session"]["id"]
    assert f"render 1500 {session} --without {path}" in record.read_text().splitlines()
    line = render_command(1500, [folder / "runs"], session)[3:]
    parsed = build_parser().parse_args([*line, *without_flags([path])])
    assert parsed.without == [path]


@pytest.mark.spec("ui:render:a-photograph-taken-out-leaves-the-quote")
def test_a_photograph_taken_out_leaves_the_quote_and_the_session(
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    folder, client = _quoting(tmp_path, vocabulary, {"RUNPOD_API_KEY": "k"})
    ada = _approved(folder, "ada.jpg", FLOW, schema, vocabulary)
    beatrix = _approved(folder, "beatrix.jpg", FLOW, schema, vocabulary)
    asked = {
        "collections": ["b"],
        "without": [{"collection": "b", "run": ada.id, "flow": FLOW}],
    }

    quote = client.post("/api/render/quote", json=asked).json()

    (row,) = quote["collections"]
    (flow,) = row["flows"]
    assert [(one["name"], one["run"]) for one in flow["sources"]] == [
        ("beatrix.jpg", beatrix.id)
    ]
    assert row["images"] == 1
    seen: dict[str, object] = {}

    def started(self: Jobs, collections: object, **kwargs: object) -> dict[str, Any]:
        seen.update(kwargs)
        return {}

    monkeypatch.setattr(Jobs, "render", started)
    limit = quote["estimate"]["limit_s"]
    confirmed = client.post(
        "/api/render",
        json={**asked, "keep_open": False, "limit_s": limit, "images": 1, "bakes": 0},
    )

    assert confirmed.status_code == 200
    assert seen["without"] == [folder / "runs" / ada.id / FLOW]


@pytest.mark.spec("ui:render:a-photograph-not-quoted-is-refused")
@pytest.mark.parametrize("run_id", ["nobody", "../b"], ids=["no-run", "outside"])
def test_a_photograph_no_quoted_run_holds_is_refused(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary, run_id: str
) -> None:
    folder, client = _quoting(tmp_path, vocabulary, {"RUNPOD_API_KEY": "k"})
    _approved(folder, "ada.jpg", FLOW, schema, vocabulary)
    asked = {
        "collections": ["b"],
        "without": [{"collection": "b", "run": run_id, "flow": FLOW}],
    }

    quote = client.post("/api/render/quote", json=asked)
    started = client.post(
        "/api/render",
        json={**asked, "keep_open": False, "limit_s": 1200, "images": 1, "bakes": 0},
    )

    for answered in (quote, started):
        assert answered.status_code == 409
        assert "close Render and open it again" in answered.json()["refusal"]
