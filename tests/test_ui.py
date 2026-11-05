"""Prove bundle freshness, surface invariants and orderly shutdown.

The shutdown harness stops the app's own uvicorn server in-process, over the
suite's offline wiring. Endpoint contracts live in `tests/test_ui_api.py`.
"""

import asyncio
import importlib.util
import io
import os
import select
import signal
import subprocess
import sys
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from isekai.foundation.refusal import Refusal
from isekai.interface.ui import bundle, events

# Seconds a thread is waited for before the test fails; never part of a verdict.
WAIT = 20.0

# Every file in `ui/` that is neither `src/` nor an ignored root. `_is_fresh`
# watches them by exclusion rather than by name, so `tsconfig.json` -- which
# `vite` reads and which no allowlist here ever named -- is in this list.
_CONFIGS = ("vite.config.ts", "tsconfig.json", "package.json", "package-lock.json")

# --- the invariant that stands in for a structural guarantee ------------------


@pytest.mark.spec("ui:invariant:server-never-names-an-artifact")
def test_the_invariant_holds_no_module_of_the_surface_names_an_artifact() -> None:
    """A tripwire, and deliberately not a proof.

    `import artifact_name as name_it` walks straight past this, and a filename
    built by hand in an f-string is invisible to it. A check that overstated
    itself would be worse than none, so what it is worth is written down here
    rather than inferred from the fact that it exists.

    What it does buy is the one failure that matters: an approved artifact
    written around `approve()`'s `validate()` carries a tag outside the
    vocabulary into a prompt, and the first symptom is a render that looks wrong,
    minutes and money later. The same claim held by habit alone would go false
    with nothing to say so.
    """
    surface = Path(__file__).resolve().parent.parent / "isekai" / "interface" / "ui"
    forbidden = ("artifact_name(", "write_json(", "write(")

    named = {
        f"{path.name}: {name}"
        for path in sorted(surface.rglob("*.py"))
        for name in forbidden
        if name in path.read_text()
    }

    assert named == set(), (
        "the surface passes field values to pipeline functions, and they own the "
        "file's shape and its name"
    )


# --- the bundle: built when it is free, refused when it is not ----------------


@pytest.mark.spec("ui:bundle:a-missing-bundle-is-built")
def test_a_missing_bundle_is_built_before_the_surface_serves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "ui"
    (source / "node_modules").mkdir(parents=True)
    ran: list[list[str]] = []

    class _Build:
        """Stand in for `npm run build`, writing what vite would write."""

        returncode = 0

        def __init__(self, argv: list[str], **kwargs: object) -> None:
            ran.append(argv)
            (source / "dist" / "assets").mkdir(parents=True)
            (source / "dist" / "index.html").write_text("<!doctype html>")

        def communicate(self, timeout: float | None = None) -> tuple[str, str]:
            return "", ""

    monkeypatch.setattr(bundle.shutil, "which", lambda _: "/usr/local/bin/npm")
    monkeypatch.setattr(bundle.subprocess, "Popen", _Build)

    built = bundle.ensure_built(source)

    assert built == source / "dist"
    assert ran == [["npm", "run", "build"]]

    # A second start does not rebuild: the build is free, but it is not instant,
    # and the surface is opened many times a session.
    assert bundle.ensure_built(source) == built
    assert len(ran) == 1


@pytest.mark.spec("ui:bundle:missing-dependencies-refuse-by-name")
def test_absent_fetched_dependencies_refuse_and_name_the_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "ui"
    source.mkdir()
    monkeypatch.setattr(bundle.shutil, "which", lambda _: "/usr/local/bin/npm")

    with pytest.raises(Refusal) as refused:
        bundle.ensure_built(source)

    # A build is local and free and may run implicitly; fetching pulls arbitrary
    # third-party packages, so it is named rather than done.
    assert "npm install" in str(refused.value)
    assert not (source / "dist").exists()


@pytest.mark.spec("ui:bundle:missing-dependencies-refuse-by-name")
def test_an_absent_toolchain_refuses_naming_what_to_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "ui"
    (source / "node_modules").mkdir(parents=True)
    monkeypatch.setattr(bundle.shutil, "which", lambda _: None)

    with pytest.raises(Refusal) as refused:
        bundle.ensure_built(source)

    message = str(refused.value)
    # node is one of this repository's two system dependencies, beside Ollama,
    # and its refusal takes the shape both are under.
    assert "nodejs.org" in message
    assert "isekai ui" in message


@pytest.mark.spec_exempt("structural: it proves the gate runs the API tests")
def test_the_gate_installs_the_web_framework_the_api_tests_need() -> None:
    # `tests/test_ui_api.py` opens with an `importorskip`, and four `ui`
    # scenarios are bound there and nowhere else. If FastAPI is absent from the
    # environment the gate syncs, that module skips and those four are proved by
    # a test that never runs. So the presence of the framework is itself
    # asserted, here, where its absence is a failure rather than a skip.
    assert importlib.util.find_spec("fastapi") is not None, (
        "FastAPI is absent, so tests/test_ui_api.py will skip and the four `ui` "
        "scenarios bound only there will be proved by nothing -- restore the "
        "`fastapi` pin in pyproject.toml's `dependencies`"
    )


# The manifest's own invariants -- that the server is declared, and declared
# once -- live in `tests/test_packaging.py`. They are not facts about the review
# surface, and split across two feature files they would carry two copies of one
# requirement-name parser.


# --- the bundle is rebuilt when the source moves under it ---------------------


@pytest.mark.spec_exempt("structural: when the on-demand build actually fires")
def test_a_bundle_older_than_its_source_is_rebuilt_rather_than_served(
    tmp_path: Path,
) -> None:
    # The defect this prevents: were `ensure_built` to return any non-empty
    # `dist/`, a bundle built from older source would go on being served while
    # the source sat rebuilt. Silent, and green -- `npm run typecheck` compiles
    # the source and the server reads the build.
    source = tmp_path / "ui"
    (source / "src").mkdir(parents=True)
    (source / "dist").mkdir()
    (source / "index.html").write_text("<!doctype html>")
    (source / "dist" / "index.html").write_text("built")
    component = source / "src" / "App.vue"
    component.write_text("old")
    os.utime(source / "dist" / "index.html", (2_000, 2_000))
    os.utime(component, (1_000, 1_000))
    os.utime(source / "index.html", (1_000, 1_000))

    assert bundle._is_fresh(source / "dist", source)

    # One source file edited after the build is the whole condition.
    os.utime(component, (3_000, 3_000))

    assert not bundle._is_fresh(source / "dist", source)


def _built_tree(tmp_path: Path) -> Path:
    """Return a `ui/` whose `dist/` is newer than every source beside it."""
    source = tmp_path / "ui"
    (source / "src").mkdir(parents=True)
    (source / "dist").mkdir()
    (source / "node_modules").mkdir()
    (source / "index.html").write_text("<!doctype html>")
    (source / "dist" / "index.html").write_text("built")
    (source / "src" / "App.vue").write_text("component")
    for name in _CONFIGS:
        (source / name).write_text("{}")
    for item in source.rglob("*"):
        os.utime(item, (1_000, 1_000))
    os.utime(source / "dist" / "index.html", (2_000, 2_000))
    return source


@pytest.mark.spec("ui:bundle:a-changed-build-input-makes-the-bundle-stale")
@pytest.mark.parametrize("name", _CONFIGS)
def test_a_build_config_edited_after_the_build_makes_the_bundle_stale(
    tmp_path: Path, name: str
) -> None:
    """The inputs outside `src/` that `_is_fresh` watches.

    A bumped dependency, an added vite plugin or a changed build script all
    change the emitted bundle and move nothing under `src/` -- so, unwatched,
    the operator would go on being served the previous build, silently, with a
    green gate. `tsconfig.json` is in this list because the watch is an
    exclusion rather than a list of build inputs: an allowlist naming the other
    three would miss it.
    """
    source = _built_tree(tmp_path)

    assert bundle._is_fresh(source / "dist", source)

    os.utime(source / name, (3_000, 3_000))

    assert not bundle._is_fresh(source / "dist", source)


@pytest.mark.spec("ui:bundle:a-fetched-tree-is-not-an-input")
def test_a_fetched_dependency_tree_is_not_source(tmp_path: Path) -> None:
    # The other half of the exclusion: `node_modules/` is fetched and `dist/` is
    # this function's own output, so neither may make the bundle look stale --
    # `npm install` alone would otherwise force a rebuild on every startup.
    source = _built_tree(tmp_path)
    (source / "node_modules" / "left-pad.js").write_text("module.exports = 1")
    os.utime(source / "node_modules" / "left-pad.js", (3_000, 3_000))

    assert bundle._is_fresh(source / "dist", source)


@pytest.mark.spec("ui:bundle:an-unfinished-build-is-stopped-and-named")
def test_a_build_that_does_not_finish_is_stopped_and_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The ceiling is applied, and it and a Ctrl-C each stop the whole group.

    A real stand-in for `npm`, which starts a child the way `npm` starts `vite`:
    killing the parent alone would leave that child building unseen. The child
    alone holds the FIFO's write end, so the FIFO reads to its end once it is gone.
    """
    source = tmp_path / "ui"
    (source / "node_modules").mkdir(parents=True)
    child = tmp_path / "child.pid"
    held = tmp_path / "held"
    os.mkfifo(held)
    npm = tmp_path / "npm"
    script = (
        f"exec 3>{held}\nsleep 60 >/dev/null 2>&1 &\nexec 3>&-\n"
        f"echo $! > {child}\nwait\n"
    )
    npm.write_text(f"#!/bin/sh\n{script}")
    npm.chmod(0o755)
    monkeypatch.setattr(bundle, "BINARY", str(npm))
    monkeypatch.setattr(bundle, "BUILD_TIMEOUT", 3)
    communicate = subprocess.Popen.communicate

    def started(
        build: "subprocess.Popen[str]",
        input: str | None = None,
        timeout: float | None = None,
    ) -> tuple[str, str]:
        # The ceiling starts once the child is up, so a loaded machine cannot
        # spend it before the pid file is written.
        deadline = time.monotonic() + 30
        while not child.is_file() or not child.read_text().strip():
            assert time.monotonic() < deadline, "the stand-in never started its child"
            time.sleep(0.01)
        return communicate(build, input, timeout)

    reader = os.open(held, os.O_RDONLY | os.O_NONBLOCK)
    with monkeypatch.context() as patched, pytest.raises(Refusal) as refused:
        patched.setattr(subprocess.Popen, "communicate", started)
        bundle.ensure_built(source)

    assert "3 seconds" in str(refused.value)
    assert "by hand" in str(refused.value)
    assert _stops(reader)

    # A Ctrl-C while it builds stops the group too: in its own session, the
    # build never receives the terminal's SIGINT.
    child.unlink()
    reader = os.open(held, os.O_RDONLY | os.O_NONBLOCK)
    monkeypatch.setattr(bundle, "BUILD_TIMEOUT", 60)

    def interrupt(signum: int, frame: object) -> None:
        if not child.is_file() or not child.read_text().strip():
            signal.setitimer(signal.ITIMER_REAL, 0.05)
            return
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGALRM, interrupt)
    try:
        signal.setitimer(signal.ITIMER_REAL, 0.05)
        with pytest.raises(KeyboardInterrupt):
            bundle.ensure_built(source)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    assert _stops(reader)


def _stops(reader: int) -> bool:
    """Return whether every holder of the FIFO `reader` reads has let go, then close it.

    A process gone, or a zombie, holds no file, so the FIFO reads to its end.
    """
    try:
        while select.select([reader], [], [], WAIT)[0]:
            if not os.read(reader, 1):
                return True
        return False
    finally:
        os.close(reader)


@pytest.mark.spec_exempt("structural: when the on-demand build actually fires")
def test_an_absent_or_empty_bundle_is_still_not_fresh(tmp_path: Path) -> None:
    source = tmp_path / "ui"
    (source / "src").mkdir(parents=True)

    assert not bundle._is_fresh(source / "dist", source)

    (source / "dist").mkdir()

    assert not bundle._is_fresh(source / "dist", source)


@pytest.mark.spec("ui:events:stopping-ends-open-streams-quietly")
def test_closed_broadcast_ends_existing_and_late_streams() -> None:
    broadcast = events.Broadcast()
    stream = events.stream(broadcast, lambda: {}, heartbeat=30)
    assert next(stream).startswith("event: snapshot")
    ended = threading.Event()
    received: list[str | None] = []

    def consume() -> None:
        received.append(next(stream, None))
        ended.set()

    worker = threading.Thread(target=consume, daemon=True)
    worker.start()
    try:
        broadcast.close()
        broadcast.close()
        assert ended.wait(1)
        assert received == [None]
        late = events.stream(broadcast, lambda: {}, heartbeat=30)
        assert next(late, None) is None
        assert not broadcast._queues
    finally:
        broadcast.close()
        worker.join(1)


@pytest.mark.spec("ui:events:stopping-ends-open-streams-quietly")
def test_serve_returns_130_for_keyboard_interrupt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from isekai.interface import ui
    from isekai.interface.ui import app as app_module
    from isekai.interface.ui.billing import Billing
    from tests.e2e.wiring import fake

    root = tmp_path / "library"
    root.mkdir()
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html>")
    monkeypatch.setattr(ui.library, "root", lambda: root)
    monkeypatch.setattr(ui, "ensure_built", lambda: dist)
    monkeypatch.setattr(Billing, "watch", lambda self: None)

    def interrupted(*args: object, **kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(app_module, "run", interrupted)
    wired = fake(runs=root / "runs")
    assert ui.serve(wired, port=7717) == 130
    assert isinstance(wired.err, io.StringIO)
    assert wired.err.getvalue() == ""


@pytest.mark.spec("ui:events:stopping-ends-open-streams-quietly")
@pytest.mark.parametrize("streams", [0, 1, 3], ids=["idle", "open", "concurrent"])
def test_sigint_ends_streams_without_cancellation_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, streams: int
) -> None:
    import uvicorn
    from fastapi.testclient import TestClient

    from isekai.boundary.gpu import GpunitExit, Volume
    from isekai.foundation.run import open_run
    from isekai.interface.ui import HOST
    from isekai.interface.ui import app as app_module
    from isekai.interface.ui.jobs import Jobs, Step
    from tests.e2e.wiring import fake
    from tests.images import jpeg_bytes

    folder = tmp_path / "library" / "b"
    (folder / "sources").mkdir(parents=True)
    (folder / "sources" / "ada.jpg").write_bytes(jpeg_bytes(600, 800))
    run = open_run(folder / "sources" / "ada.jpg", folder / "runs")
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html>")
    err = io.StringIO()
    wired = replace(
        fake(runs=folder / "runs"),
        err=err,
        volume=Volume(
            run=lambda argv, say: GpunitExit(0), records=tmp_path / ".gpunit"
        ),
    )
    made: list[Jobs] = []

    def make_jobs(*args: Any, **kwargs: Any) -> Jobs:  # noqa: ANN401 -- Jobs' own
        made.append(Jobs(*args, **kwargs))
        return made[-1]

    monkeypatch.setattr(app_module, "Jobs", make_jobs)
    app = app_module.create_app(
        folder.parent,
        wired,
        flows=("summon-anime-wai",),
        bundle=dist,
        wire=lambda runs: replace(wired, runs_root=runs),
        host=HOST,
        port=7717,
    )
    (jobs,) = made
    sleep = [sys.executable, "-c", "import time; time.sleep(30)"]
    monkeypatch.setattr(jobs, "_command", lambda verb, flow, runs, ids: sleep)
    broadcast: events.Broadcast = app.state.broadcast
    server = app_module.Server(uvicorn.Config(app), broadcast)

    async def interrupt() -> None:
        server.handle_exit(signal.SIGINT, None)
        # The broadcast closes on the loop's next turn.
        await asyncio.sleep(0)

    with TestClient(app, base_url=f"http://{HOST}:7717"):
        jobs.prepare("b", folder, [Step("summon-anime-wai", "tag", (run.id,))], dict)
        assert jobs.running("prepare")
        opened = [
            events.stream(broadcast, dict, heartbeat=3600) for _ in range(streams)
        ]
        assert [next(one) for one in opened] == [
            "event: snapshot\ndata: {}\n\n"
        ] * streams
        # Each stream is read to its end; the job's own events may come first.
        workers = [
            threading.Thread(target=list, args=(one,), daemon=True) for one in opened
        ]
        for worker in workers:
            worker.start()
        asyncio.run(interrupt())
        for worker in workers:
            worker.join(WAIT)

        assert not [worker for worker in workers if worker.is_alive()]
        assert server.should_exit

    assert (jobs.slot("prepare") or {})["state"] == "stopped"
    assert "Traceback" not in err.getvalue()

    # The surface serves through the server that closes the streams; none binds.
    served: list[uvicorn.Server] = []
    monkeypatch.setattr(uvicorn.Server, "run", lambda self: served.append(self))
    app_module.run(app, host=HOST, port=7717)
    (serving,) = served
    assert isinstance(serving, app_module.Server)
    assert serving._broadcast is broadcast
