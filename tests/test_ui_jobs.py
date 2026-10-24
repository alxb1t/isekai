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
from typing import Any, TextIO

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from isekai.boundary import gpu, ollama  # noqa: E402
from isekai.boundary.gpu import Seams, Volume  # noqa: E402
from isekai.foundation.flow import FLOWS_DIR, Schema, load_flow  # noqa: E402
from isekai.foundation.refusal import Refusal  # noqa: E402
from isekai.foundation.run import Run, approval_of, open_run  # noqa: E402
from isekai.interface.render import LOST_EXIT  # noqa: E402
from isekai.interface.ui import HOST, events, library  # noqa: E402
from isekai.interface.ui import app as app_module  # noqa: E402
from isekai.interface.ui.app import cell_event, create_app  # noqa: E402
from isekai.interface.ui.jobs import Jobs, Step, settle_s  # noqa: E402
from isekai.pipeline.generate import prepare  # noqa: E402
from isekai.pipeline.review import approve, review  # noqa: E402
from isekai.shared.vocabulary import Vocabulary  # noqa: E402
from tests.conftest import snapshot  # noqa: E402
from tests.fakes import FakeComfyClient  # noqa: E402
from tests.images import jpeg_bytes, photo_jpeg  # noqa: E402
from tests.stages import bare_wiring, render, sheet, write_wd14  # noqa: E402

FLOW = "summon-anime-wai"
CONTROL = "control-anime-wai"
OFFERED = (FLOW, "conjure-anime-wai")
PORT = 8766
WAIT = 20.0


def _batch(tmp_path: Path, *names: str) -> tuple[Path, list[Run]]:
    """Write a batch whose every source has a run assigned to `FLOW`."""
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
    """A command that runs `scripts[verb]` as the child, recording each verb asked."""

    def __init__(self, scripts: dict[str, str]) -> None:
        self.scripts = scripts
        self.asked: list[str] = []

    def __call__(
        self, verb: str, flow: str, runs: Path, ids: Sequence[str]
    ) -> list[str]:
        self.asked.append(verb)
        return [sys.executable, "-c", self.scripts.get(verb, "pass"), *ids]


def _line(state: str) -> str:
    """Return a script that prints a progress line for the run in `argv[1]`."""
    return (
        "import json, sys; print(json.dumps({'run': sys.argv[1], 'flow': "
        f"'{FLOW}', 'stage': 'tag', 'state': '{state}'}}), flush=True)"
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
    return [Step(FLOW, verb, (run.id,)) for verb in ("tag", "caption", "sheet")]


SLEEP = "import time; time.sleep(30)"


def _sleeping_render(limit: int, runs: Path, session: str) -> list[str]:
    """Return a render child that runs until it is interrupted."""
    return [sys.executable, "-c", SLEEP]


@pytest.mark.spec("ui:prepare:one-job-at-a-time")
def test_a_second_job_of_a_kind_is_refused_naming_the_one_that_runs(
    tmp_path: Path,
) -> None:
    folder, (run,) = _batch(tmp_path, "ada.jpg")
    volume, _ = _order(tmp_path / "acts")
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        command=_Script({"tag": SLEEP}),
        volume=volume,
        render=_sleeping_render,
    )
    jobs.prepare("b", folder, _steps(run), lambda line: None)
    jobs.render("b", folder, limit=1500, total=1, keep_open=False)

    try:
        with pytest.raises(Refusal, match="a job is running: Prepare on b"):
            jobs.prepare("other", folder, _steps(run), lambda line: None)
        with pytest.raises(Refusal, match="a job is running: Render on b"):
            jobs.render("other", folder, limit=1500, total=1, keep_open=False)
    finally:
        jobs.shutdown()


@pytest.mark.spec("ui:prepare:a-render-runs-beside-a-prepare")
def test_a_render_runs_beside_a_prepare_and_its_stop_leaves_the_prepare(
    tmp_path: Path,
) -> None:
    folder, (run,) = _batch(tmp_path, "ada.jpg")
    volume, _ = _order(tmp_path / "acts")
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        command=_Script({"tag": SLEEP}),
        volume=volume,
        render=_sleeping_render,
    )
    jobs.prepare("b", folder, _steps(run), lambda line: None)

    try:
        jobs.render("other", folder, limit=1500, total=1, keep_open=False)
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
    folder, (run,) = _batch(tmp_path, "ada.jpg")
    record = tmp_path / "acts"
    volume, _ = _order(record)
    # A render child that takes a while to tear its pod down once interrupted.
    script = (
        "import signal, sys, time\n"
        "def down(*_):\n"
        "    time.sleep(0.5)\n"
        "    open(sys.argv[1], 'a').write('torn down\\n')\n"
        "    sys.exit(130)\n"
        "signal.signal(signal.SIGINT, down)\n"
        "open(sys.argv[1], 'a').write('render\\n')\n"
        "time.sleep(30)\n"
    )
    broadcast = events.Broadcast()
    found = broadcast.subscribe()
    prepared = _Script({"tag": _line("start") + "; import time; time.sleep(30)"})
    jobs = Jobs(
        broadcast,
        lambda: None,
        command=prepared,
        volume=volume,
        render=lambda limit, runs, session: [sys.executable, "-c", script, str(record)],
        err=io.StringIO(),
    )
    jobs.prepare("b", folder, _steps(run), dict)
    _until(found, "cell")
    jobs.render("b", folder, limit=1500, total=1, keep_open=False)
    deadline = time.monotonic() + WAIT
    while "render" not in (record.read_text() if record.exists() else ""):
        assert time.monotonic() < deadline, "the render child never started"
        time.sleep(0.01)

    jobs.shutdown(timeout=0.05)

    assert record.read_text().splitlines() == [
        "volume up --yes",
        "render",
        "torn down",
        "volume down",
    ]
    assert (jobs.slot("prepare") or {})["state"] == "stopped"
    assert prepared.asked == ["tag"]


@pytest.mark.spec("ui:prepare:the-log-names-each-job")
def test_each_line_a_job_writes_to_the_batchs_log_names_its_job(
    tmp_path: Path,
) -> None:
    folder, (run,) = _batch(tmp_path, "ada.jpg")
    volume, _ = _order(tmp_path / "acts")
    # The last line ends with no newline, as a child cut short leaves it.
    said = "import sys; sys.stderr.write({!r})"
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        command=_Script({"tag": said.format("tag one\ntag two")}),
        volume=volume,
        render=lambda limit, runs, session: [
            sys.executable,
            "-c",
            said.format("pod up\n"),
        ],
    )

    jobs.prepare("b", folder, _steps(run), lambda line: None)
    jobs.render("b", folder, limit=1500, total=1, keep_open=False)
    jobs.wait("prepare", WAIT)
    jobs.wait("render", WAIT)

    assert sorted((folder / "log.txt").read_text().splitlines()) == [
        "[prepare] tag one",
        "[prepare] tag two",
        "[render] pod up",
    ]


@pytest.mark.spec("ui:prepare:refused-when-ollama-does-not-answer")
def test_prepare_is_refused_with_the_readers_message_and_starts_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Closed:
        def open(self, *args: object, **kwargs: object) -> None:
            raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(ollama, "OPENER", Closed())
    folder, (run,) = _batch(tmp_path, "ada.jpg")
    script = _Script({})
    jobs = Jobs(events.Broadcast(), ollama.probe, command=script)

    with pytest.raises(Refusal) as refused:
        jobs.prepare("b", folder, _steps(run), lambda line: None)

    assert str(refused.value) == ollama.NOT_LISTENING
    assert script.asked == []
    assert jobs.slot("prepare") is None


@pytest.mark.spec("ui:prepare:stop-interrupts-the-job")
def test_stop_interrupts_the_stage_and_starts_no_later_one(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    folder, (run, done) = _batch(tmp_path, "ada.jpg", "bea.jpg")
    sheet(done, load_flow(FLOW).schema, vocabulary)
    before = snapshot(done.path)
    broadcast = events.Broadcast()
    found = broadcast.subscribe()
    script = _Script({"tag": _line("start") + "; import time; time.sleep(30)"})
    jobs = Jobs(broadcast, lambda: None, command=script, now=lambda: STARTED)
    steps = [Step(FLOW, verb, (run.id, done.id)) for verb in ("tag", "caption")]
    jobs.prepare("b", folder, steps, lambda line: dict(line))
    _until(found, "cell")

    jobs.stop("prepare")
    jobs.wait("prepare", WAIT)

    assert script.asked == ["tag"]
    assert jobs.slot("prepare") == {
        "kind": "prepare",
        "batch": "b",
        "state": "stopped",
        "flow": FLOW,
        "stage": "tag",
        "message": None,
        "progress": {"started": STARTED, "of": 2, "done": 0},
    }
    assert snapshot(done.path) == before


@pytest.mark.spec("ui:prepare:a-silent-failure-ends-the-job")
def test_a_stage_that_fails_before_it_reports_ends_the_job_naming_the_log(
    tmp_path: Path,
) -> None:
    folder, (run,) = _batch(tmp_path, "ada.jpg")
    script = _Script({"tag": "import sys; sys.exit('no module named onnxruntime')"})
    jobs = Jobs(events.Broadcast(), lambda: None, command=script)

    jobs.prepare("b", folder, _steps(run), lambda line: None)
    jobs.wait("prepare", WAIT)

    assert script.asked == ["tag"]
    slot = jobs.slot("prepare")
    assert slot is not None
    assert (slot["state"], slot["stage"]) == ("failed", "tag")
    assert "b/log.txt" in slot["message"]


@pytest.mark.spec("ui:events:a-connection-starts-with-a-snapshot")
def test_a_stream_opened_for_a_batch_starts_with_both_slots_and_its_hub(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    folder, (run,) = _batch(tmp_path, "ada.jpg")
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
            broadcast.close()

        threading.Thread(target=close_once_open, daemon=True).start()
        body = TestClient(app, base_url=f"http://{HOST}:{PORT}").get(url)
        assert body.status_code == 200
        assert body.headers["content-type"].startswith("text/event-stream")
        kind, data = body.text.split("\n")[:2]
        assert kind == "event: snapshot"
        return json.loads(data.removeprefix("data: "))

    first = first_frame("/events?batch=b")
    assert first["jobs"] == {"prepare": None, "render": None}
    assert first["hub"]["batch"] == "b"
    assert first["hub"]["sources"][0]["cells"][FLOW]["stage"] == "assigned"
    assert first["hub"]["sources"][0]["digest"] == run.digest

    # A batch or an import it cannot read is left out, and the stream still opens:
    # it is the page's only one, and a refused connect would end it for good.
    missing = first_frame("/events?batch=gone")
    assert (missing["jobs"]["prepare"], "hub" in missing) == (None, False)
    closed = first_frame("/events?batch=b&staging=0123")
    assert (closed["hub"]["batch"], "files" in closed) == ("b", False)


@pytest.mark.spec("ui:events:a-stages-report-reaches-the-stream")
def test_a_stage_reporting_an_item_done_sends_that_cells_new_stage(
    tmp_path: Path,
) -> None:
    folder, (run,) = _batch(tmp_path, "ada.jpg")
    tags = write_wd14(run)
    staged = tmp_path / "001.json"
    tags.rename(staged)
    copy = f"import shutil; shutil.copy({str(staged)!r}, {str(tags)!r}); " + _line(
        "done"
    )
    broadcast = events.Broadcast()
    grid = library.hub(folder, OFFERED, FLOWS_DIR)
    cell = cell_event(folder, grid, {FLOW: load_flow(FLOW)})
    stream = events.stream(broadcast, lambda: {"job": None}, batch="b", heartbeat=WAIT)
    next(stream)
    jobs = Jobs(broadcast, lambda: None, command=_Script({"tag": copy}))

    jobs.prepare("b", folder, [Step(FLOW, "tag", (run.id,))], cell)

    frames = []
    for frame in stream:
        frames.append(frame)
        if frame.startswith("event: cell"):
            break
    jobs.wait("prepare", WAIT)
    data = json.loads(frames[-1].split("\n")[1].removeprefix("data: "))
    assert (data["source"], data["flow"], data["state"]) == ("ada.jpg", FLOW, "done")
    assert data["cell"]["stage"] == "tagged"


STARTED = "2026-10-22T10:00:00Z"


@pytest.mark.spec("ui:prepare:totals-count-cells-not-stages")
def test_prepare_totals_count_cells_once(tmp_path: Path) -> None:
    folder, (run, refused) = _batch(tmp_path, "ada.jpg", "bea.jpg")
    other = OFFERED[1]
    lines = [
        (run.id, FLOW, "tag", "done", "tagged"),
        (run.id, FLOW, "caption", "done", "sheet"),
        (refused.id, FLOW, "sheet", "refused", "sheet"),
        ("unknown", FLOW, "sheet", "done", "sheet"),
        (refused.id, other, "sheet", "done", "sheet"),
        (refused.id, FLOW, "sheet", "done", "tagged"),
        (run.id, FLOW, "sheet", "done", "sheet"),
        (run.id, FLOW, "sheet", "done", "sheet"),
        (run.id, other, "sheet", "done", "rendered"),
    ]
    reports = [
        {
            "run": run_id,
            "flow": flow,
            "stage": stage,
            "state": state,
            "cell": {"stage": reached},
        }
        for run_id, flow, stage, state, reached in lines
    ]
    script = "import json; " + "; ".join(
        f"print(json.dumps({line!r}), flush=True)" for line in reports
    )
    broadcast = events.Broadcast()
    found = broadcast.subscribe()
    jobs = Jobs(
        broadcast, lambda: None, command=_Script({"sheet": script}), now=lambda: STARTED
    )
    jobs.prepare(
        "b",
        folder,
        [Step(FLOW, "sheet", (run.id, refused.id)), Step(other, "sheet", (run.id,))],
        dict,
    )
    jobs.wait("prepare", WAIT)
    slot = jobs.slot("prepare")
    assert slot is not None
    assert slot["progress"] == {"started": STARTED, "of": 3, "done": 2}
    updates = []
    while not found.empty():
        kind, data = found.get_nowait()
        if kind == "job":
            updates.append(data["progress"]["done"])
    assert 1 in updates and 2 in updates
    slot["progress"]["done"] = 99
    copied = jobs.slot("prepare")
    assert copied is not None
    assert copied["progress"]["done"] == 2


@pytest.mark.spec("ui:events:a-reconnect-keeps-prepare-progress")
def test_reconnect_keeps_prepare_progress(
    tmp_path: Path, vocabulary: Vocabulary, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder, (run, later) = _batch(tmp_path, "ada.jpg", "bea.jpg")
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
    monkeypatch.setattr(jobs, "_command", _Script({"sheet": script}))
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
            "b", folder, [Step(FLOW, "sheet", (run.id, later.id))], dict
        )
        assert initial["progress"]["started"] == STARTED
        monkeypatch.setattr(jobs, "_now", lambda: "2026-10-22T10:05:00Z")
        while _until(updates, "job")[1]["progress"]["done"] != 1:
            pass
        for _ in range(2):
            body = client.get("/events?batch=b")
            first_frame = body.text.split("\n")[1].removeprefix("data: ")
            assert json.loads(first_frame)["jobs"]["prepare"]["progress"] == {
                "started": STARTED,
                "of": 2,
                "done": 1,
            }
        assert jobs.running("prepare")
    finally:
        broadcast.unsubscribe(updates)
        release.touch()
        jobs.shutdown()


# --- render ---------------------------------------------------------------------


def _order(record: Path) -> tuple[Volume, Callable[[int, Path, str], list[str]]]:
    """Return a gpunit double and a render command, each appending its act to `record`.

    The render child is a real process, so the order is read from one file.
    """

    def run(argv: Sequence[str], log: Path) -> int:
        with record.open("a") as acts:
            print(" ".join(argv), file=acts)
        return LOST_EXIT if "up" in argv and "lost" in record.name else 0

    def command(limit: int, runs: Path, session: str) -> list[str]:
        script = (
            "import sys; open(sys.argv[1], 'a')"
            ".write(f'render {sys.argv[2]} {sys.argv[3]}\\n')"
        )
        return [sys.executable, "-c", script, str(record), str(limit), session]

    return Volume(run=run, records=record.parent / ".gpunit"), command


@pytest.mark.spec("ui:render-job:opens-renders-and-closes")
def test_a_render_job_opens_the_window_renders_at_the_limit_and_closes_it(
    tmp_path: Path,
) -> None:
    folder, _ = _batch(tmp_path, "ada.jpg")
    record = tmp_path / "acts"
    volume, command = _order(record)
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=volume,
        render=command,
        now=lambda: "ended",
    )

    jobs.render("b", folder, limit=1500, total=1, keep_open=False)
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


@pytest.mark.spec("ui:render-job:an-opening-that-raises-fails-its-step")
def test_a_window_opening_that_raises_fails_the_job_and_its_step(
    tmp_path: Path,
) -> None:
    folder, _ = _batch(tmp_path, "ada.jpg")
    rendered: list[int] = []

    def unstartable(argv: Sequence[str], log: Path) -> int:
        raise OSError("gpunit is not installed")

    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=Volume(run=unstartable, records=tmp_path / ".gpunit"),
        render=lambda limit, runs, session: rendered.append(limit) or [],
    )

    jobs.render("b", folder, limit=1500, total=1, keep_open=False)
    jobs.wait("render", WAIT)

    slot = jobs.slot("render") or {}
    assert slot["state"] == "failed"
    assert slot["session"]["steps"]["volume up"] == "failed"
    assert rendered == []


@pytest.mark.spec("ui:render-job:a-lost-opening-renders-nothing")
def test_a_lost_window_opening_renders_nothing_and_raises_the_volume_alert(
    tmp_path: Path,
) -> None:
    folder, _ = _batch(tmp_path, "ada.jpg")
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

    jobs.render("b", folder, limit=1500, total=1, keep_open=False)
    jobs.wait("render", WAIT)

    assert record.read_text().splitlines() == ["volume up --yes"]
    assert raised == [True]
    slot = jobs.slot("render") or {}
    assert slot["state"] == "failed"
    assert slot["session"]["steps"]["volume up"] == "lost"


@pytest.mark.spec("ui:render-job:a-stopped-surface-closes-the-window")
def test_a_surface_stopped_mid_render_closes_the_window_after_the_teardown(
    tmp_path: Path,
) -> None:
    folder, _ = _batch(tmp_path, "ada.jpg")
    record = tmp_path / "acts"
    volume, _ = _order(record)
    # A render child that takes a while to tear its pod down once interrupted.
    script = (
        "import signal, sys, time\n"
        "def down(*_):\n"
        "    time.sleep(0.5)\n"
        "    open(sys.argv[1], 'a').write('torn down\\n')\n"
        "    sys.exit(130)\n"
        "signal.signal(signal.SIGINT, down)\n"
        "open(sys.argv[1], 'a').write('render\\n')\n"
        "time.sleep(30)\n"
    )
    err = io.StringIO()
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=volume,
        render=lambda limit, runs, session: [sys.executable, "-c", script, str(record)],
        err=err,
    )
    jobs.render("b", folder, limit=1500, total=1, keep_open=False)
    deadline = time.monotonic() + WAIT
    while "render" not in (record.read_text() if record.exists() else ""):
        assert time.monotonic() < deadline, "the render child never started"
        time.sleep(0.01)

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
    folder, _ = _batch(tmp_path, "ada.jpg")
    record = tmp_path / "acts"
    volume, _ = _order(record)
    # A render child whose teardown outlasts the wait the server gives it.
    script = (
        "import signal, sys, time\n"
        "signal.signal(signal.SIGINT, lambda *_: (time.sleep(1), sys.exit(130)))\n"
        "open(sys.argv[1], 'a').write('render\\n')\n"
        "time.sleep(30)\n"
    )
    err = io.StringIO()
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=volume,
        render=lambda limit, runs, session: [sys.executable, "-c", script, str(record)],
        settle=lambda: 0.05,
        err=err,
    )
    jobs.render("b", folder, limit=1500, total=1, keep_open=False)
    deadline = time.monotonic() + WAIT
    while "render" not in (record.read_text() if record.exists() else ""):
        assert time.monotonic() < deadline, "the render child never started"
        time.sleep(0.01)

    try:
        jobs.shutdown(timeout=0.05)

        assert "uv run --env-file .env gpunit volume down" in err.getvalue()
        assert "wait ran out" in err.getvalue()
    finally:
        jobs.wait("render", WAIT)


def _stop_with_window(tmp_path: Path, *, keep_open: bool) -> tuple[str, list[str]]:
    """Return terminal output and recorded teardown acts after a stopped render."""
    folder, _ = _batch(tmp_path, "ada.jpg")
    record = tmp_path / "acts"

    def volume(argv: Sequence[str], log: Path) -> int:
        with record.open("a") as acts:
            print(" ".join(argv), file=acts)
        return 1 if "down" in argv else 0

    script = (
        "import signal, sys, time\n"
        "def down(*_):\n"
        "    open(sys.argv[1], 'a').write('torn down\\n')\n"
        "    sys.exit(130)\n"
        "signal.signal(signal.SIGINT, down)\n"
        "open(sys.argv[1], 'a').write('render\\n')\n"
        "time.sleep(30)\n"
    )
    err = io.StringIO()
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=Volume(run=volume, records=tmp_path / ".gpunit"),
        render=lambda limit, runs, session: [sys.executable, "-c", script, str(record)],
        settle=lambda: 2,
        err=err,
    )
    jobs.render("b", folder, limit=1500, total=1, keep_open=keep_open)
    try:
        deadline = time.monotonic() + WAIT
        while "render" not in (record.read_text() if record.exists() else ""):
            assert time.monotonic() < deadline, "render did not start"
            time.sleep(0.01)
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
    folder, _ = _batch(tmp_path, "ada.jpg")
    record = tmp_path / "acts"
    volume, _ = _order(record)
    jobs = Jobs(
        events.Broadcast(),
        lambda: None,
        volume=volume,
        render=lambda limit, runs, session: [str(tmp_path / "no-such-interpreter")],
    )

    jobs.render("b", folder, limit=1500, total=1, keep_open=False)
    jobs.wait("render", WAIT)

    assert record.read_text().splitlines() == ["volume up --yes", "volume down"]
    slot = jobs.slot("render") or {}
    assert slot["state"] == "failed"
    assert "b/log.txt" in slot["message"]


@pytest.mark.spec("ui:render-job:a-stopped-surface-closes-the-window")
def test_a_gpunit_verb_runs_in_its_own_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ran: list[tuple[list[str], dict[str, object]]] = []

    def recorded(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        ran.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(gpu.subprocess, "run", recorded)

    assert Volume().down(tmp_path / "log.txt") == 0
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
    """Return a batch folder and a client whose session is handed `environ`."""
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
def test_the_quote_lists_each_flows_images_what_is_left_out_and_the_price(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    folder, client = _quoting(tmp_path, vocabulary, {"RUNPOD_API_KEY": "k"})
    _approved(folder, "ada.jpg", FLOW, schema, vocabulary)
    _approved(folder, "beatrix.jpg", CONTROL, schema, vocabulary)
    drafted = open_run(folder / "sources" / "ada.jpg", folder / "runs")
    sheet(drafted, schema, vocabulary, flow=CONTROL)
    review(drafted, CONTROL)

    quote = client.post("/api/b/b/render/quote").json()

    assert [(one["flow"], one["images"]) for one in quote["flows"]] == [
        (CONTROL, 1),
        (FLOW, 1),
    ]
    assert quote["flows"][1]["sources"][0]["name"] == "ada.jpg"
    assert quote["left_out"] == [
        {
            "name": "ada.jpg",
            "digest": drafted.digest,
            "version": None,
            "flow": CONTROL,
            "reason": "a draft",
        }
    ]
    assert quote["estimate"]["limit_s"] >= quote["estimate"]["seconds"]
    assert 0 < quote["price"]["about"] < quote["price"]["at_most"]
    assert quote["disabled"] is None


@pytest.mark.spec("ui:render:without-a-key-render-is-disabled")
def test_without_a_runpod_key_render_is_disabled_naming_the_fix(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    folder, client = _quoting(tmp_path, vocabulary, {})
    _approved(folder, "ada.jpg", FLOW, schema, vocabulary)

    quote = client.post("/api/b/b/render/quote").json()
    started = client.post("/api/b/b/render", json={"keep_open": False})

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

    offer = client.get("/api/b/b/render").json()

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

    offer = client.get("/api/b/b/render").json()

    assert offer["images"] == 0
    assert approval.name in offer["refused"]
    assert offer["disabled"] == offer["refused"]


@pytest.mark.spec("ui:render:a-grown-quote-is-refused")
def test_a_confirmation_shorter_than_the_quote_now_gives_is_refused(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    folder, client = _quoting(tmp_path, vocabulary, {"RUNPOD_API_KEY": "k"})
    _approved(folder, "ada.jpg", FLOW, schema, vocabulary)
    shown = client.post("/api/b/b/render/quote").json()["estimate"]["limit_s"]

    started = client.post(
        "/api/b/b/render", json={"keep_open": False, "limit_s": shown - 1}
    )

    assert started.status_code == 409
    assert "the quote changed" in started.json()["refusal"]
    assert client.post("/api/b/b/render/quote").json()["disabled"] is None

    # An approval made while the dialog is open adds an image the limit may not show.
    _approved(folder, "beatrix.jpg", FLOW, schema, vocabulary)
    grown = client.post(
        "/api/b/b/render", json={"keep_open": False, "limit_s": shown, "images": 1}
    )

    assert grown.status_code == 409
    assert "2 images, not 1" in grown.json()["refusal"]
