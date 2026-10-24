"""`isekai render` on a fake session: what it rents, when, and how it lets go.

The session is gpunit's, faked by a context manager that records how its block
ended; `generate` is a stub recording each verb line, except where a render's
record is the point, which runs the real `generate` on a fake transport.
"""

import argparse
import dataclasses
import http.server
import io
import json
import threading
import tomllib
from collections.abc import Callable, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import gpunit
import pytest

from isekai.boundary import gpu
from isekai.boundary.comfy import ComfyClient, ComfyTransport, TransportFailure
from isekai.foundation.artifacts import (
    RENDER_FILE,
    SESSION_ID,
    SESSIONS,
    read,
    session_id,
)
from isekai.foundation.flow import Schema, load_flow
from isekai.foundation.run import REPOSITORY, Run, open_run
from isekai.interface import render
from isekai.interface.cli import _dispatch_argv, build_parser
from isekai.interface.wiring import Wiring
from isekai.pipeline.caption import FakeReader
from isekai.pipeline.generate import prepare
from isekai.pipeline.review import approve, review
from isekai.pipeline.tagging import FakeTagger
from isekai.shared.vocabulary import Vocabulary
from tests.fakes import FAKE_SYSTEM, SESSION_IMAGE, FakeComfyClient
from tests.images import jpeg_bytes
from tests.stages import (
    FIELD_MAP,
    Always,
    bare_wiring,
    caption,
    fake_wd14,
    reapprove,
    sheet,
)
from tests.stages import render as stage_render

FLOW = "summon-anime-wai"
LOCAL_PORT = 50123
STATS = {"system": dict(FAKE_SYSTEM), "devices": []}


@dataclass
class FakeSession:
    """What gpunit yields: the booted image and the forwarded port."""

    image: str = SESSION_IMAGE
    host: str = "203.0.113.7"
    local: int = LOCAL_PORT

    def port(self, remote: int) -> int:
        assert remote == render.PORT
        return self.local


@dataclass
class FakeOpen:
    """An `open_session` that records each session it opens and how it closed."""

    session: FakeSession = field(default_factory=FakeSession)
    opened: int = 0
    closed: int = 0
    ended: BaseException | None = None
    limits: list[int] = field(default_factory=list)

    def __call__(
        self,
        cwd: Path,
        environ: Mapping[str, str],
        say: Callable[[str], None],
        limit_s: int,
    ) -> AbstractContextManager[FakeSession]:
        self.limits.append(limit_s)
        return self._block()

    @contextmanager
    def _block(self) -> Iterator[FakeSession]:
        self.opened += 1
        try:
            yield self.session
        except BaseException as fault:
            self.ended = fault
            raise
        finally:
            self.closed += 1


@dataclass
class Calls:
    """A `generate` stub: each verb line, and the wiring it ran on."""

    answer: Callable[[list[str], Wiring], int] = lambda argv, wired: 0
    lines: list[list[str]] = field(default_factory=list)
    wirings: list[Wiring] = field(default_factory=list)

    def __call__(self, argv: list[str], wired: Wiring) -> int:
        self.lines.append(argv)
        self.wirings.append(wired)
        return self.answer(argv, wired)

    def rendered(self) -> list[list[str]]:
        return [line for line in self.lines if "--server" in line]


def batch(root: Path, *ids: str) -> Path:
    runs = root / "b" / "runs"
    for run_id in ids or ("r1",):
        (runs / run_id).mkdir(parents=True)
        (runs / run_id / "run.json").write_text("{}")
    return runs


def wired(runs: Path) -> Wiring:
    def unread() -> Vocabulary:
        raise AssertionError("a session reads no vocabulary")

    return Wiring(
        reader=None,
        tagger=None,
        hosted_tagger=None,
        client=None,
        vocabulary=unread,
        field_map=lambda _: FIELD_MAP,
        runs_root=runs,
        out=io.StringIO(),
        err=io.StringIO(),
    )


def session(
    runs: Path,
    *requests: str,
    generate: Callable[[list[str], Wiring], int] | None = None,
    opener: gpu.OpenSession | None = None,
    client: ComfyTransport | None = None,
    wiring: Wiring | None = None,
    given: str | None = None,
    **seams: Any,  # noqa: ANN401 -- `render.Seams`'s fields, by name
) -> int:
    defaults = render.Seams(
        open_session=opener or FakeOpen(),
        environ={},
        connect=lambda server: client or FakeComfyClient(),
        busy=lambda port: False,
        kill=lambda: None,
    )
    return render.run_session(
        argparse.Namespace(runs=runs, requests=list(requests), session=given),
        wiring or wired(runs),
        generate if generate is not None else Calls(),
        dataclasses.replace(defaults, **seams),
    )


def log(runs: Path) -> str:
    return (runs.parent / "log.txt").read_text()


@pytest.mark.spec("pod-image:session:every-exit-tears-down")
def test_a_flow_that_raises_closes_the_session(tmp_path: Path) -> None:
    runs = batch(tmp_path)
    opener = FakeOpen()

    def explode(argv: list[str], wired: Wiring) -> int:
        if "--server" in argv:
            raise RuntimeError("a flow raised")
        return 0

    with pytest.raises(RuntimeError, match="a flow raised"):
        session(runs, f"{FLOW}=1", generate=Calls(explode), opener=opener)

    assert (opener.opened, opener.closed) == (1, 1)
    assert isinstance(opener.ended, RuntimeError)


@pytest.mark.spec("pod-image:session:every-exit-tears-down")
def test_a_sigterm_inside_the_session_closes_it_and_exits_143(tmp_path: Path) -> None:
    runs = batch(tmp_path)
    opener = FakeOpen()

    def signalled(argv: list[str], wired: Wiring) -> int:
        if "--server" in argv:
            raise gpunit.Interrupted(15)
        return 0

    assert session(runs, f"{FLOW}=1", generate=Calls(signalled), opener=opener) == 143
    assert (opener.opened, opener.closed) == (1, 1)


@pytest.mark.spec("pod-image:session:every-exit-tears-down")
def test_nothing_is_rented_before_every_prompt_is_assembled(tmp_path: Path) -> None:
    runs = batch(tmp_path)
    opener = FakeOpen()
    calls = Calls(lambda argv, wired: 1)

    assert session(runs, f"{FLOW}=1", generate=calls, opener=opener) == 1
    assert opener.opened == 0
    assert calls.lines == [
        ["generate", "--flow", FLOW, "--runs", str(runs), "r1"],
    ]


@pytest.mark.spec("pod-image:session:the-endpoint-is-awaited")
def test_the_report_is_asked_through_the_forwarded_port_before_any_render(
    tmp_path: Path,
) -> None:
    runs = batch(tmp_path)
    client = FakeComfyClient()
    servers: list[str] = []
    asked_before: list[int] = []

    def connect(server: str) -> ComfyTransport:
        servers.append(server)
        return client

    def answer(argv: list[str], wired: Wiring) -> int:
        if "--server" in argv:
            asked_before.append(client.stats_calls)
        return 0

    calls = Calls(answer)

    assert session(runs, f"{FLOW}=1", generate=calls, connect=connect) == 0
    assert servers == [f"http://127.0.0.1:{LOCAL_PORT}"]
    assert asked_before == [1]
    assert calls.rendered() == [
        [
            "generate",
            "--progress",
            "json",
            "--flow",
            FLOW,
            "--count",
            "1",
            "--server",
            f"http://127.0.0.1:{LOCAL_PORT}",
            "--runs",
            str(runs),
            "r1",
        ]
    ]


@pytest.mark.spec("pod-image:session:the-endpoint-is-awaited")
def test_an_endpoint_silent_past_the_bound_refuses_and_closes_the_session(
    tmp_path: Path,
) -> None:
    runs = batch(tmp_path)
    opener = FakeOpen()
    silent = FakeComfyClient(
        report_failure=TransportFailure("transient", "connection refused")
    )
    calls = Calls()

    status = session(
        runs, f"{FLOW}=1", generate=calls, opener=opener, client=silent, wait_s=0
    )

    assert status == 1
    assert (opener.opened, opener.closed) == (1, 1)
    assert calls.rendered() == []
    assert (
        f"refused: http://127.0.0.1:{LOCAL_PORT}/system_stats did not answer within 0s"
    ) in log(runs)


@pytest.mark.spec("pod-image:session:the-endpoint-is-awaited")
def test_an_endpoint_that_answers_late_is_asked_again(tmp_path: Path) -> None:
    runs = batch(tmp_path)

    class Late(FakeComfyClient):
        def system_stats(self) -> dict[str, Any]:
            if self.stats_calls < 2:
                self.stats_calls += 1
                raise TransportFailure("transient", "connection refused")
            return super().system_stats()

    calls = Calls()
    late = Late()

    assert session(runs, f"{FLOW}=1", generate=calls, client=late, poll_s=0) == 0
    assert late.stats_calls == 3
    assert len(calls.rendered()) == 1


class _Stats(http.server.BaseHTTPRequestHandler):
    paths: list[str] = []

    def do_GET(self) -> None:  # noqa: N802 -- the handler's name is http.server's
        type(self).paths.append(self.path)
        body = json.dumps(STATS).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass


@pytest.mark.spec("pod-image:session:the-tunnel-is-reached-directly")
def test_the_report_reaches_the_loopback_with_a_proxy_exported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = batch(tmp_path)
    # Port 9 is discard: a request sent through this proxy never answers.
    for name in ("http_proxy", "HTTP_PROXY", "all_proxy", "ALL_PROXY"):
        monkeypatch.setenv(name, "http://127.0.0.1:9")
    monkeypatch.delenv("no_proxy", raising=False)
    monkeypatch.delenv("NO_PROXY", raising=False)
    _Stats.paths = []
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Stats)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        opener = FakeOpen(session=FakeSession(local=server.server_address[1]))
        status = session(
            runs,
            f"{FLOW}=1",
            opener=opener,
            connect=ComfyClient,
            wait_s=0,
        )
    finally:
        server.shutdown()
        server.server_close()

    assert status == 0
    assert _Stats.paths == ["/system_stats"]


@pytest.mark.spec("pod-image:session:the-watchdog-ends-with-its-session")
def test_the_watchdog_signals_nothing_once_its_session_has_ended(
    tmp_path: Path,
) -> None:
    runs = batch(tmp_path)
    fired = threading.Event()

    assert session(runs, f"{FLOW}=1", kill=fired.set, watchdog_s=0.05) == 0
    assert not fired.wait(0.15)
    assert "reached its" not in log(runs)


@pytest.mark.spec("pod-image:session:the-watchdog-ends-with-its-session")
def test_the_watchdog_signals_nothing_after_a_refused_session(tmp_path: Path) -> None:
    runs = batch(tmp_path)
    fired = threading.Event()
    silent = FakeComfyClient(
        report_failure=TransportFailure("transient", "connection refused")
    )

    status = session(
        runs, f"{FLOW}=1", client=silent, wait_s=0, kill=fired.set, watchdog_s=0.05
    )

    assert status == 1
    assert not fired.wait(0.15)


@pytest.mark.spec("pod-image:session:the-watchdog-ends-the-session")
def test_the_ceiling_writes_its_refusal_and_ends_the_session_with_143(
    tmp_path: Path,
) -> None:
    runs = batch(tmp_path)
    opener = FakeOpen()
    fired = threading.Event()

    def held(argv: list[str], wired: Wiring) -> int:
        if "--server" in argv:
            # What gpunit's handler does with the SIGTERM the watchdog sends.
            assert fired.wait(5)
            raise gpunit.Interrupted(15)
        return 0

    status = session(
        runs,
        f"{FLOW}=1",
        generate=Calls(held),
        opener=opener,
        kill=fired.set,
        watchdog_s=0.05,
    )

    assert status == 143
    assert (opener.opened, opener.closed) == (1, 1)
    assert f"refused: the session reached its {render.FLOOR_S}s limit" in log(runs)
    assert f"isekai render {runs} {FLOW}=1` renders only the rest" in log(runs)


@pytest.mark.spec("pod-image:session:the-watchdog-ends-the-session")
def test_the_watchdog_is_armed_at_the_pods_own_limit_before_the_session_opens(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = batch(tmp_path)
    opener = FakeOpen()
    armed: list[tuple[float, int]] = []

    class Timer(threading.Timer):
        def start(self) -> None:
            # The interval, and how many sessions were open when it started.
            armed.append((self.interval, opener.opened))
            super().start()

    monkeypatch.setattr(render.threading, "Timer", Timer)

    assert session(runs, f"{FLOW}=1", opener=opener) == 0
    assert armed == [(opener.limits[0], 0)]


@pytest.mark.spec("pod-image:boot:no-override")
def test_the_session_is_opened_on_the_repositorys_gpunit_toml_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = batch(tmp_path)
    opened: list[tuple[object, dict[str, object]]] = []

    @contextmanager
    def recorded(spec: object, **kwargs: object) -> Iterator[FakeSession]:
        opened.append((spec, kwargs))
        yield FakeSession()

    monkeypatch.setattr(gpunit, "session", recorded)
    calls = Calls()
    environ = {"ISEKAI_IMAGE": "ghcr.io/a/b:latest", "GPUNIT_IMAGE": "x"}

    assert (
        session(
            runs,
            f"{FLOW}=1",
            generate=calls,
            opener=gpu.open_session,
            given="20261024T091200Z",
        )
        == 0
    )
    status = session(
        runs,
        f"{FLOW}=1",
        generate=calls,
        opener=gpu.open_session,
        environ=environ,
        given="20261024T091201Z",
    )

    assert status == 0
    toml = gpunit.load_spec(REPOSITORY / "gpunit.toml")
    limited = dataclasses.replace(toml, ceiling_s=render.FLOOR_S)
    assert [spec for spec, _ in opened] == [limited] * 2
    assert {key for _, kwargs in opened for key in kwargs} == {"environ", "cwd", "say"}
    assert {wired.image for wired in calls.wirings if wired.client} == {SESSION_IMAGE}
    with pytest.raises(SystemExit):
        build_parser().parse_args(["render", str(runs), f"{FLOW}=1", "--image", "x"])


def approved(root: Path, schema: Schema, vocabulary: Vocabulary, name: str) -> Run:
    photo = root / f"{name}.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900 + 8 * len(name)))
    made = open_run(photo, root / "b" / "runs")
    caption(made, FakeReader(prose="Brown hair, brown eyes."))
    sheet(made, schema, vocabulary)
    review(made, FLOW)
    approve(made, FLOW, schema, vocabulary)
    return made


@pytest.mark.spec("pod-image:boot:the-booted-image-is-recorded")
def test_each_render_records_the_image_the_session_names(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    runs = [approved(tmp_path, schema, vocabulary, name) for name in ("ada", "bea")]
    root = tmp_path / "b" / "runs"
    wiring = Wiring(
        reader=Always(FakeReader(prose="unused")),
        tagger=fake_wd14(),
        hosted_tagger=Always(FakeTagger()),
        client=None,
        vocabulary=lambda: vocabulary,
        field_map=lambda _: FIELD_MAP,
        runs_root=root,
        out=io.StringIO(),
        err=io.StringIO(),
    )

    status = session(root, f"{FLOW}=1", generate=_dispatch_argv, wiring=wiring)

    assert status == 0, log(root)
    for run in runs:
        (sidecar,) = (run.path / FLOW / "outputs" / "001").glob("*.render.json")
        record = read(sidecar, RENDER_FILE)
        assert record.get("image") == SESSION_IMAGE
        assert record.get("pinned") is True


def real(root: Path, vocabulary: Vocabulary) -> Wiring:
    """Return a wiring the real `generate` runs on, over `root`."""
    return bare_wiring(
        reader=Always(FakeReader(prose="unused")),
        tagger=fake_wd14(),
        hosted_tagger=Always(FakeTagger()),
        vocabulary=lambda: vocabulary,
        runs_root=root,
    )


def counted(
    root: Path, schema: Schema, vocabulary: Vocabulary, name: str, made: int
) -> Run:
    """Return a run approved for two images of `FLOW`, `made` of them rendered."""
    run = approved(root, schema, vocabulary, name)
    reapprove(run, schema, vocabulary, {"count": 2, "seeds": []})
    flow = load_flow(FLOW)
    prepare(run, {FLOW: flow})
    if made:
        seeds = list(range(1, made + 1))
        stage_render(run, flow, FakeComfyClient(), seeds=seeds, poll=0)
    return run


def images(run: Run) -> int:
    """Return how many images `run`'s newest approval of `FLOW` holds."""
    return len(list((run.path / FLOW / "outputs" / "002").glob("*.png")))


@pytest.mark.spec("cli:render-short:what-is-short-is-rendered")
def test_with_no_request_only_what_is_short_is_rendered(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    lacking = counted(tmp_path, schema, vocabulary, "ada", 1)
    full = counted(tmp_path, schema, vocabulary, "beatrix", 2)
    root = tmp_path / "b" / "runs"

    status = session(root, generate=_dispatch_argv, wiring=real(root, vocabulary))

    assert status == 0, log(root)
    assert images(lacking) == 2
    assert images(full) == 2
    assert f"{lacking.id}: rendered" in log(root)
    assert f"{full.id}: rendered" not in log(root)


@pytest.mark.spec("cli:render-short:a-run-without-the-flow-is-skipped")
def test_with_no_request_a_run_without_the_flow_is_skipped(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    held = approved(tmp_path, schema, vocabulary, "ada")
    photo = tmp_path / "bea.jpg"
    photo.write_bytes(jpeg_bytes(1200, 932))
    bare = open_run(photo, tmp_path / "b" / "runs")
    root = tmp_path / "b" / "runs"
    calls = Calls()

    assert session(root, generate=calls) == 0, log(root)
    assert calls.rendered() == [
        ["generate", "--progress", "json", "--flow", FLOW]
        + ["--server", f"http://127.0.0.1:{LOCAL_PORT}"]
        + ["--runs", str(root), held.id]
    ]
    assert bare.id not in log(root)


@pytest.mark.spec("cli:render-short:an-unapproved-flow-is-left-out")
def test_with_no_request_an_unapproved_flow_is_left_out_and_named(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    lacking = counted(tmp_path, schema, vocabulary, "ada", 1)
    photo = tmp_path / "bea.jpg"
    photo.write_bytes(jpeg_bytes(1200, 932))
    started = open_run(photo, tmp_path / "b" / "runs")
    caption(started, FakeReader(prose="Brown hair, brown eyes."))
    sheet(started, schema, vocabulary)
    review(started, FLOW)
    root = tmp_path / "b" / "runs"

    status = session(root, generate=_dispatch_argv, wiring=real(root, vocabulary))

    assert status == 0, log(root)
    assert images(lacking) == 2
    assert not (started.path / FLOW / "outputs").exists()
    assert f"left out: {started.id}: {FLOW} is a draft" in log(root)


@pytest.mark.spec(
    "image-generation:seeds-from:a-copy-behind-a-source-rendering-first-is-refused-first"
)
def test_a_dependent_behind_its_source_in_one_session_refuses_before_the_pod(
    tmp_path: Path,
) -> None:
    runs = batch(tmp_path)
    opener = FakeOpen()
    calls = Calls(lambda argv, wired: 1 if "--in-step-with" in argv else 0)

    status = session(
        runs,
        "summon-anime-wai=1",
        "control-anime-wai=summon-anime-wai",
        generate=calls,
        opener=opener,
    )

    assert status == 1
    assert opener.opened == 0
    assert calls.lines[-1] == [
        "generate",
        "--flow",
        "control-anime-wai",
        "--in-step-with",
        "summon-anime-wai",
        "--runs",
        str(runs),
        "r1",
    ]


@pytest.mark.spec_exempt("structural: a session's line names its source after it")
def test_a_dependent_before_its_source_is_refused_naming_both(tmp_path: Path) -> None:
    runs = batch(tmp_path)
    opener = FakeOpen()

    status = session(
        runs,
        "control-anime-wai=summon-anime-wai",
        "summon-anime-wai=1",
        opener=opener,
    )

    assert status == 1
    assert opener.opened == 0
    assert (
        "refused: 'control-anime-wai=summon-anime-wai' comes before its source "
        "'summon-anime-wai=1'; put the source first"
    ) in log(runs)


@pytest.mark.spec_exempt("structural: the verb's argument shape")
def test_a_request_of_another_shape_is_refused_into_the_log(tmp_path: Path) -> None:
    runs = batch(tmp_path)

    assert session(runs, "summon-anime-wai=0") == 1
    assert (
        "refused: 'summon-anime-wai=0' is not <flow>=<count> or <flow>=<source>"
    ) in log(runs)


@pytest.mark.spec_exempt("structural: a busy port is refused before the session")
def test_a_port_that_already_answers_is_refused_before_the_session(
    tmp_path: Path,
) -> None:
    runs = batch(tmp_path)
    opener = FakeOpen()

    assert session(runs, f"{FLOW}=1", opener=opener, busy=lambda port: True) == 1
    assert opener.opened == 0
    assert f"refused: 127.0.0.1:{render.PORT} already answers" in log(runs)


@pytest.mark.spec_exempt("structural: gpunit's outcomes become the verb's exit")
def test_a_lost_create_exits_3_and_a_failed_teardown_names_gpunit_down(
    tmp_path: Path,
) -> None:
    runs = batch(tmp_path)

    def raising(fault: BaseException) -> FakeOpen:
        class Raising(FakeOpen):
            @contextmanager
            def _block(self) -> Iterator[FakeSession]:
                raise fault
                yield FakeSession()

        return Raising()

    # gpunit reads no .env, and the key lives only there: each remedy loads it.
    assert (
        session(
            runs, f"{FLOW}=1", opener=raising(gpunit.Lost()), given="20261024T091200Z"
        )
        == 3
    )
    assert "`uv run --env-file .env gpunit status` shows" in log(runs)
    assert "`uv run --env-file .env gpunit down` deletes it" in log(runs)
    failed = gpunit.TeardownFailed("the teardown failed")
    assert (
        session(runs, f"{FLOW}=1", opener=raising(failed), given="20261024T091201Z")
        == 1
    )
    assert "run `uv run --env-file .env gpunit down`" in log(runs)


@pytest.mark.spec_exempt("structural: gpunit's outcomes become the verb's exit")
def test_a_refusal_naming_a_bare_gpunit_command_ends_on_one_that_loads_the_key(
    tmp_path: Path,
) -> None:
    def refusing(text: str) -> gpu.OpenSession:
        @contextmanager
        def block(
            cwd: Path,
            environ: Mapping[str, str],
            say: Callable[[str], None],
            limit_s: int,
        ) -> Iterator[FakeSession]:
            # What gpunit's `log.refuse` does through the sink it was handed.
            say(f"2026-10-10T12:00:00Z refused: {text}")
            raise gpunit.Refused(text)
            yield FakeSession()

        return block

    listed = "a gpunit-isekai pod already exists: abc (RUNNING); run gpunit down"
    runs = batch(tmp_path / "listed")
    assert session(runs, f"{FLOW}=1", opener=refusing(listed)) == 1
    lines = log(runs).splitlines()
    assert lines[-1].endswith("run `uv run --env-file .env gpunit down`")
    # A note, not a second refusal: one failure prints one `refused:` line.
    assert sum("refused:" in line for line in lines) == 1

    # The window's refusals name a bare `gpunit volume up` or `volume down`.
    window = {
        "no window volume is up; run gpunit volume up": "volume up",
        "the volume ends at 2026-10-10T13:00:00Z; shorten the ceiling or run gpunit "
        "volume up": "volume up",
        "volume abc passed its ceiling at 2026-10-10T13:00:00Z and is kept; "
        "run gpunit volume down": "volume down",
    }
    for index, (text, verb) in enumerate(window.items()):
        runs = batch(tmp_path / f"window{index}")
        assert session(runs, f"{FLOW}=1", opener=refusing(text)) == 1
        lines = log(runs).splitlines()
        assert lines[-1].endswith(f"run `uv run --env-file .env gpunit {verb}`")
        assert sum("refused:" in line for line in lines) == 1

    other = "no card in 'gpus' meets vram_gb and max_hourly"
    runs = batch(tmp_path / "other")
    assert session(runs, f"{FLOW}=1", opener=refusing(other)) == 1
    assert "gpunit" not in log(runs).splitlines()[-1]
    assert "--env-file" not in log(runs)


@pytest.mark.spec("cli:render-progress:each-image-of-the-total")
def test_a_session_reports_each_image_of_the_total_as_json(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    made = counted(tmp_path, schema, vocabulary, "ada", 0)
    root = tmp_path / "b" / "runs"
    wiring = real(root, vocabulary)
    asked = argparse.Namespace(runs=root, requests=[], progress="json")
    seams = render.Seams(
        open_session=FakeOpen(),
        environ={},
        connect=lambda server: FakeComfyClient(),
        busy=lambda port: False,
        kill=lambda: None,
    )

    status = render.run_session(asked, wiring, _dispatch_argv, seams)

    assert status == 0, log(root)
    assert isinstance(wiring.out, io.StringIO)
    lines = [json.loads(line) for line in wiring.out.getvalue().splitlines()]
    images = [line for line in lines if line["step"] == "image"]
    assert [(line["n"], line["of"]) for line in images] == [(1, 2), (2, 2)]
    assert {(line["run"], line["flow"]) for line in images} == {(made.id, FLOW)}
    seeds = {path.stem for path in (made.path / FLOW / "outputs" / "002").glob("*.png")}
    assert {(line["version"], line["seed"]) for line in images} == {
        (2, seed) for seed in seeds
    }
    assert lines[-1] == {"step": "teardown", "state": "done"}
    # The prose is the caller's to log, so the session writes no line of it twice.
    assert isinstance(wiring.err, io.StringIO)
    assert f"{made.id}: rendered" in wiring.err.getvalue()
    assert not (root.parent / "log.txt").exists()


@pytest.mark.spec("cli:render-progress:a-refused-session-reports-its-teardown")
def test_a_session_whose_endpoint_never_answers_reports_its_teardown(
    tmp_path: Path,
) -> None:
    runs = batch(tmp_path)
    wiring = wired(runs)
    silent = FakeComfyClient(
        report_failure=TransportFailure("transient", "connection refused")
    )
    seams = render.Seams(
        open_session=FakeOpen(),
        environ={},
        connect=lambda server: silent,
        busy=lambda port: False,
        kill=lambda: None,
        wait_s=0,
    )
    asked = argparse.Namespace(runs=runs, requests=[f"{FLOW}=1"], progress="json")

    status = render.run_session(asked, wiring, Calls(), seams)

    assert status == 1
    assert isinstance(wiring.out, io.StringIO)
    lines = [json.loads(line) for line in wiring.out.getvalue().splitlines()]
    assert lines[-1] == {"step": "teardown", "state": "done"}


def records(runs: Path) -> list[dict[str, Any]]:
    """Return the batch's session records, by name."""
    folder = runs.parent / SESSIONS
    return [json.loads(path.read_text()) for path in sorted(folder.glob("*.json"))]


def landing(*seeds: str, seen: list[dict[str, Any]]) -> Calls:
    """Return a `generate` stub landing each seed, noting the record after each."""

    def land(argv: list[str], wired: Wiring) -> int:
        if "--server" not in argv:
            return 0
        runs = Path(argv[argv.index("--runs") + 1])
        for seed in seeds:
            line: dict[str, object] = {"run": "r1", "flow": FLOW, "digest": "d1"}
            line |= {"stage": "render", "state": "done", "version": 1, "seed": seed}
            print(json.dumps(line), file=wired.out)
            seen.extend(records(runs))
        return 0

    return Calls(land)


@pytest.mark.spec("cli:render-session:a-session-writes-its-record")
def test_a_session_writes_its_record_of_each_image_and_no_price(
    tmp_path: Path,
) -> None:
    runs = batch(tmp_path)

    assert session(runs, f"{FLOW}=2", generate=landing("7", "8", seen=[])) == 0

    (record,) = records(runs)
    assert record["schema"] == {"name": "session", "version": 1}
    assert record["images"] == [
        {"digest": "d1", "flow": FLOW, "version": 1, "seed": seed}
        for seed in ("7", "8")
    ]
    assert (record["outcome"], record["message"]) == ("done", None)
    assert record["asked"] == {FLOW: 2}
    assert record["steps"] == {"pod": "ready", "teardown": "done"}
    assert record["ended"] is not None
    assert set(record) == {
        "schema", "id", "started", "ended", "limit", "asked", "steps", "images",
        "outcome", "message",
    }  # fmt: skip


@pytest.mark.spec("cli:render-session:the-record-follows-each-image")
def test_the_record_reads_running_with_the_first_image_before_the_second(
    tmp_path: Path,
) -> None:
    runs = batch(tmp_path)
    seen: list[dict[str, Any]] = []

    assert session(runs, f"{FLOW}=2", generate=landing("7", "8", seen=seen)) == 0

    first = seen[0]
    assert first["outcome"] == "running"
    assert [image["seed"] for image in first["images"]] == ["7"]
    assert first["ended"] is None


@pytest.mark.spec("cli:render-session:the-given-id-names-the-record")
def test_the_given_id_names_the_record_and_another_shape_is_refused(
    tmp_path: Path,
) -> None:
    runs = batch(tmp_path)
    given = "20261024T091200Z"

    assert session(runs, f"{FLOW}=1", given=given) == 0

    named = runs.parent / SESSIONS / f"{given}.json"
    assert json.loads(named.read_text())["id"] == given
    # The id the start writes is one the flag reads.
    assert SESSION_ID.fullmatch(session_id(datetime.now(UTC)))
    # The id names a file, so no other shape reaches a path.
    with pytest.raises(SystemExit):
        build_parser().parse_args(["render", str(runs), "--session", "../x"])


@pytest.mark.spec("cli:render-session:a-refusal-before-renting-writes-none")
def test_a_session_refused_before_renting_writes_no_record(tmp_path: Path) -> None:
    runs = batch(tmp_path)

    assert session(runs, f"{FLOW}=1", busy=lambda port: True) == 1

    assert not (runs.parent / SESSIONS).exists()


TIMING = render.Timing(
    boot_s=600, per_image_s=60, teardown_s=120, limit_factor=1.5, volume_rate=0.005
)


@pytest.mark.spec("cli:render-limit:the-estimate-comes-from-durations")
def test_the_estimate_takes_the_median_of_recorded_durations(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    made = approved(tmp_path, schema, vocabulary, "ada")
    flow = load_flow(FLOW)
    prepare(made, {FLOW: flow})
    ticks = iter([0.0, 80.0, 0.0, 90.0, 0.0, 400.0])
    stage_render(made, flow, FakeComfyClient(), seeds=[1, 2, 3], clock=ticks.__next__)
    recorded = {FLOW: render.recent(made.path.parent, [made.id], FLOW)}

    got = render.estimate({FLOW: 4}, recorded, TIMING, 3 * 60 * 60)

    assert sorted(recorded[FLOW]) == [80.0, 90.0, 400.0]
    assert got.seconds == 600 + 4 * 90 + 120
    assert got.limit_s == (600 + 4 * 90 + 120) * 1.5


@pytest.mark.spec("cli:render-limit:the-configured-figure-without-records")
def test_with_no_recorded_duration_the_configured_time_per_image_is_used() -> None:
    got = render.estimate({FLOW: 10}, {FLOW: []}, TIMING, 3 * 60 * 60)

    assert got.seconds == 600 + 10 * 60 + 120
    assert got.limit_s == (600 + 10 * 60 + 120) * 1.5


@pytest.mark.spec("cli:render-limit:a-short-session-takes-the-floor")
def test_a_short_sessions_limit_is_the_hold_plus_five_minutes(tmp_path: Path) -> None:
    runs = batch(tmp_path)
    opener = FakeOpen()

    got = render.estimate({FLOW: 1}, {}, render.load_timing(), 3 * 60 * 60)

    assert got.seconds * 1.5 < render.HOLD_SECONDS + 300
    assert got.limit_s == render.HOLD_SECONDS + 300
    assert session(runs, f"{FLOW}=1", opener=opener) == 0
    assert opener.limits == [render.HOLD_SECONDS + 300]
    assert f"session limit {render.HOLD_SECONDS + 300}s" in log(runs)


@pytest.mark.spec("cli:render-limit:above-the-ceiling-is-refused")
def test_a_limit_above_gpunit_tomls_ceiling_is_refused_before_renting(
    tmp_path: Path,
) -> None:
    runs = batch(tmp_path)
    opener = FakeOpen()
    calls = Calls()
    ceiling = gpunit.load_spec(REPOSITORY / "gpunit.toml").ceiling_s
    over = argparse.Namespace(runs=runs, requests=[f"{FLOW}=1"], limit=ceiling + 1)

    status = render.run_session(
        over,
        wired(runs),
        calls,
        dataclasses.replace(render.Seams(), open_session=opener),
    )

    assert status == 1
    assert (opener.opened, calls.lines) == (0, [])
    assert f"above gpunit.toml's ceiling of {ceiling}s" in log(runs)


@pytest.mark.spec_exempt("structural: one port, declared in gpunit.toml and here")
def test_the_port_the_verb_reads_is_the_one_gpunit_toml_forwards() -> None:
    spec = tomllib.loads((REPOSITORY / "gpunit.toml").read_text())
    assert spec["ports"] == [render.PORT]


@pytest.mark.spec_exempt("structural: one ceiling, declared in gpunit.toml and here")
def test_the_limit_never_passes_gpunit_tomls_ceiling() -> None:
    spec = gpunit.load_spec(REPOSITORY / "gpunit.toml")
    timing = render.load_timing()

    whole_day = render.estimate({FLOW: 24 * 60}, {}, timing, spec.ceiling_s)

    assert gpu.bounds(REPOSITORY).ceiling_s == spec.ceiling_s
    assert whole_day.limit_s == spec.ceiling_s


@pytest.mark.spec_exempt("structural: the .env reader gpunit's environ is built from")
def test_the_env_file_is_read_as_key_value_lines(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text(
        "# a comment\n\nRUNPOD_API_KEY=\"k1\"\nOTHER='two words'\nBARE=v\nnoise\n"
    )

    assert gpu.read_env(env) == {
        "RUNPOD_API_KEY": "k1",
        "OTHER": "two words",
        "BARE": "v",
    }
    assert gpu.read_env(tmp_path / "absent") == {}


@pytest.mark.spec("cli:render-session:an-owned-id-is-refused")
def test_an_owned_session_id_refuses_before_renting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = batch(tmp_path)
    given = "20261024T091200Z"
    assert session(runs, f"{FLOW}=1", given=given) == 0
    path = runs.parent / SESSIONS / f"{given}.json"
    previous = path.read_bytes()
    for chosen in (given, None):
        monkeypatch.setattr(render, "session_id", lambda moment: given)
        opener = FakeOpen()
        assert session(runs, f"{FLOW}=1", given=chosen, opener=opener) == 1
        assert opener.opened == 0
        assert path.read_bytes() == previous


@pytest.mark.spec("cli:render-session:concurrent-starts-reserve-one-record")
def test_concurrent_starts_reserve_one_whole_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from concurrent.futures import ThreadPoolExecutor

    from isekai.foundation.refusal import Refusal

    barrier = threading.Barrier(2)

    def start() -> bool:
        record = render.Record(tmp_path, "20261024T091200Z", 1200, {FLOW: 1})
        barrier.wait(timeout=5)
        try:
            record.open()
        except Refusal:
            return False
        return True

    with ThreadPoolExecutor(max_workers=2) as workers:
        outcomes = list(workers.map(lambda _: start(), range(2)))
    assert sorted(outcomes) == [False, True]
    record = json.loads((tmp_path / "20261024T091200Z.json").read_text())
    assert record["outcome"] == "running"
    assert record["asked"] == {FLOW: 1}

    # Even a writer outside the lifetime-lock protocol cannot be replaced in the
    # gap before publication. The complete record that won stays byte-for-byte.
    from isekai.foundation import atomic_write

    original = atomic_write.os.link
    occupied = tmp_path / "20261024T091201Z.json"
    previous = (tmp_path / "20261024T091200Z.json").read_bytes()

    def raced(source: str, destination: Path) -> None:
        destination.write_bytes(previous)
        original(source, destination)

    monkeypatch.setattr(atomic_write.os, "link", raced)
    with pytest.raises(Refusal, match="already exists"):
        render.Record(tmp_path, "20261024T091201Z", 1200, {FLOW: 2}).open()
    assert occupied.read_bytes() == previous
    assert list(tmp_path.glob("*.partial")) == []
