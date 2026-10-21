"""Prepare as a job, and the event stream that tells the page of it.

Each child is a real process: a short Python script stands in for a verb, so Stop
and the one slot are proved against a process that can be interrupted.
"""

import json
import queue
import random
import sys
import threading
import time
import urllib.error
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from isekai.boundary import ollama  # noqa: E402
from isekai.foundation.flow import FLOWS_DIR, load_flow  # noqa: E402
from isekai.foundation.refusal import Refusal  # noqa: E402
from isekai.foundation.run import Run, open_run  # noqa: E402
from isekai.interface.ui import HOST, events, library  # noqa: E402
from isekai.interface.ui.app import cell_event, create_app  # noqa: E402
from isekai.interface.ui.jobs import Jobs, Step  # noqa: E402
from isekai.shared.vocabulary import Vocabulary  # noqa: E402
from tests.conftest import snapshot  # noqa: E402
from tests.images import jpeg_bytes  # noqa: E402
from tests.stages import bare_wiring, write_wd14  # noqa: E402

FLOW = "summon-anime-wai"
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


@pytest.mark.spec("ui:prepare:one-job-at-a-time")
def test_a_second_job_is_refused_naming_the_one_that_runs(tmp_path: Path) -> None:
    folder, (run,) = _batch(tmp_path, "ada.jpg")
    jobs = Jobs(events.Broadcast(), lambda: None, command=_Script({"tag": SLEEP}))
    jobs.prepare("b", folder, _steps(run), lambda line: None)

    try:
        with pytest.raises(Refusal, match="a job is running: Prepare on b"):
            jobs.prepare("other", folder, _steps(run), lambda line: None)
    finally:
        jobs.stop()
        jobs.wait(WAIT)


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
    assert jobs.slot() is None


@pytest.mark.spec("ui:prepare:stop-interrupts-the-job")
def test_stop_interrupts_the_stage_and_starts_no_later_one(tmp_path: Path) -> None:
    folder, (run, done) = _batch(tmp_path, "ada.jpg", "bea.jpg")
    write_wd14(done)
    before = snapshot(done.path)
    broadcast = events.Broadcast()
    found = broadcast.subscribe()
    script = _Script({"tag": _line("start") + "; import time; time.sleep(30)"})
    jobs = Jobs(broadcast, lambda: None, command=script)
    jobs.prepare("b", folder, _steps(run), lambda line: dict(line))
    _until(found, "cell")

    jobs.stop()
    jobs.wait(WAIT)

    assert script.asked == ["tag"]
    assert jobs.slot() == {
        "kind": "prepare",
        "batch": "b",
        "state": "stopped",
        "flow": FLOW,
        "stage": "tag",
    }
    assert snapshot(done.path) == before


@pytest.mark.spec("ui:events:a-connection-starts-with-a-snapshot")
def test_a_stream_opened_for_a_batch_starts_with_the_slot_and_its_hub(
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
    body = TestClient(app, base_url=f"http://{HOST}:{PORT}").get("/events?batch=b")

    assert body.headers["content-type"].startswith("text/event-stream")
    kind, data = body.text.split("\n")[:2]
    assert kind == "event: snapshot"
    first = json.loads(data.removeprefix("data: "))
    assert first["job"] is None
    assert first["hub"]["batch"] == "b"
    assert first["hub"]["sources"][0]["cells"][FLOW]["stage"] == "assigned"
    assert first["hub"]["sources"][0]["digest"] == run.digest


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
    jobs.wait(WAIT)
    data = json.loads(frames[-1].split("\n")[1].removeprefix("data: "))
    assert (data["source"], data["flow"], data["state"]) == ("ada.jpg", FLOW, "done")
    assert data["cell"]["stage"] == "tagged"
