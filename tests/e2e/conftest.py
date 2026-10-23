"""One app per session, over a fixture library, served on doubles.

The server is the real `python -m isekai ui` in its own process, so the page is
the built bundle and every request crosses the real guard. `ISEKAI_LIBRARY`
points it at a library under `tmp_path`, and `ISEKAI_WIRING` swaps the seams for
`tests/e2e/wiring.py`'s doubles (D41): no GPU, no Ollama.
"""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from isekai.foundation.artifacts import DRAFT_FILE, read
from isekai.foundation.flow import load_flow
from isekai.foundation.run import Run, approval_of, open_run
from isekai.pipeline.caption import FakeReader
from isekai.pipeline.generate import prepare
from isekai.pipeline.review import approve, review, revise, save_draft
from tests.e2e.wiring import VOCABULARY
from tests.fakes import FakeComfyClient
from tests.images import jpeg_bytes, photo_jpeg
from tests.stages import caption, render, sheet

REPO = Path(__file__).resolve().parents[2]
FLOW = "summon-anime-wai"
BATCH = "2026-10-19"

# A batch per approval test, each source a sheet with no draft, so every test
# owns the sheets it approves. Sizes differ so each source is its own run.
QUEUES: dict[str, tuple[tuple[str, tuple[int, int]], ...]] = {
    "queue-stays": (("cid", (700, 1000)), ("dot", (710, 1000))),
    "queue-fails": (("fay", (730, 1000)),),
}

# A batch per hub test, so every test owns the cells it ticks and prepares. Its
# sources are photographs with no run, except those `ASSIGNED` names.
FRESH: dict[str, tuple[str, ...]] = {
    "hub-tick": ("aside", "beside", "tick"),
    "hub-prepare": ("pick", "skip"),
}

# The fresh sources whose run is already assigned to `FLOW`, as a tick leaves it.
ASSIGNED: dict[str, tuple[str, ...]] = {"hub-prepare": ("pick",)}

# The batch a render test owns: one source approved for one image.
RENDER = "render"
# The batch the Renders view is read from: one source already rendered once.
SHOWN = "shown"
# The batch a revision is written in: one source rendered once at seed 7.
REVISED = "revised"
# The batch a discard is asked in: one source rendered at seed 7, its render's
# revision drafted.
DISCARDED = "discarded"
# The batch Compare reads: one source with seed 7 rendered under v1 and under v2,
# which changes `clothes`.
COMPARED = "compared"
# The batch whose one approval is damaged: a source rendered at seed 7 under an
# approval holding a count no render takes.
DAMAGED = "damaged"

# A first start may build the bundle, which `bundle.BUILD_TIMEOUT` bounds.
STARTUP = 300


@dataclass(frozen=True)
class Served:
    """The running app: its address, its batch and the runs it serves."""

    url: str
    batch: str
    draft: Run
    approved: Run
    queues: dict[str, tuple[Run, ...]]
    rendered: Run
    shown: Run
    revised: Run
    discarded: Run
    compared: Run
    prepare_release: Path

    def review(self, run: Run, batch: str | None = None) -> str:
        """Return the address of `run`'s review in `FLOW`, in `batch` or the main."""
        return f"{self.url}/b/{batch or self.batch}/review/{run.digest}/{FLOW}"

    def hub_of(self, batch: str) -> str:
        """Return the address of `batch`'s hub."""
        return f"{self.url}/b/{batch}/hub"

    @property
    def hub(self) -> str:
        """Return the address of the main batch's hub."""
        return self.hub_of(self.batch)


def _run(folder: Path, name: str, size: tuple[int, int]) -> Run:
    """Return a run of a new source carrying a caption and a sheet for `FLOW`."""
    photo = folder / "sources" / f"{name}.jpg"
    photo.write_bytes(jpeg_bytes(*size))
    run = open_run(photo, folder / "runs")
    caption(run, FakeReader(prose="Dark brown hair, brown eyes."))
    sheet(run, load_flow(FLOW).schema, VOCABULARY)
    return run


def _rendered_at_seven(folder: Path, name: str, size: tuple[int, int]) -> Run:
    """Return a run of a new source approved once and rendered at seed 7."""
    (folder / "sources").mkdir(parents=True)
    run = _run(folder, name, size)
    review(run, FLOW)
    approve(run, FLOW, load_flow(FLOW).schema, VOCABULARY)
    _render_seven(run)
    return run


def _render_seven(run: Run) -> None:
    """Render `run`'s newest approval at seed 7, on the fake transport."""
    prepare(run, {FLOW: load_flow(FLOW)})
    image = photo_jpeg((90, 60, 30), (640, 800))
    render(run, load_flow(FLOW), FakeComfyClient(view_bytes=image), seeds=[7], poll=0)


def _free_port() -> int:
    """Return a loopback port nothing is listening on."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _wait(url: str, server: subprocess.Popen[bytes]) -> None:
    """Return once `url` answers, failing with the server's output if it stops."""
    deadline = time.monotonic() + STARTUP
    while time.monotonic() < deadline:
        if server.poll() is not None:
            output = server.stdout.read().decode() if server.stdout else ""
            pytest.fail(f"isekai ui exited {server.returncode}: {output}")
        try:
            with urllib.request.urlopen(url, timeout=1):
                return
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.2)
    pytest.fail(f"isekai ui did not answer {url} within {STARTUP} seconds")


@pytest.fixture(scope="session")
def served(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Served]:
    """Serve a batch of one draft and one approved input of `FLOW`, then stop."""
    lib = tmp_path_factory.mktemp("e2e") / "isekai"
    folder = lib / BATCH
    (folder / "sources").mkdir(parents=True)
    draft = _run(folder, "ada", (900, 1200))
    approved = _run(folder, "bea", (1200, 900))
    review(draft, FLOW)
    review(approved, FLOW)
    approve(approved, FLOW, load_flow(FLOW).schema, VOCABULARY)
    queues = {}
    for name, sources in QUEUES.items():
        (lib / name / "sources").mkdir(parents=True)
        queues[name] = tuple(_run(lib / name, one, size) for one, size in sources)
    for name, fresh in FRESH.items():
        (lib / name / "sources").mkdir(parents=True)
        for index, one in enumerate(fresh):
            body = photo_jpeg((90, 60, 30 + index), (640, 800 + index))
            photo = lib / name / "sources" / f"{one}.jpg"
            photo.write_bytes(body)
            if one in ASSIGNED.get(name, ()):
                open_run(photo, lib / name / "runs").directory(FLOW).mkdir()

    (lib / RENDER / "sources").mkdir(parents=True)
    rendered = _run(lib / RENDER, "gia", (740, 1000))
    review(rendered, FLOW)
    approve(rendered, FLOW, load_flow(FLOW).schema, VOCABULARY)
    shown = _rendered_at_seven(lib / SHOWN, "hal", (750, 1000))
    revised = _rendered_at_seven(lib / REVISED, "ida", (770, 1000))
    discarded = _rendered_at_seven(lib / DISCARDED, "ivy", (775, 1000))
    revise(discarded, FLOW, 1, 7)
    compared = _rendered_at_seven(lib / COMPARED, "jo", (780, 1000))
    again = review(compared, FLOW, new_version=True)
    assert again is not None
    fields = read(again, DRAFT_FILE)["fields"]
    save_draft(compared, FLOW, {**fields, "clothes": ["collared shirt"]})
    approve(compared, FLOW, load_flow(FLOW).schema, VOCABULARY)
    _render_seven(compared)
    damaged = _rendered_at_seven(lib / DAMAGED, "kim", (790, 1000))
    approval = approval_of(damaged, FLOW, 1)
    body = json.loads(approval.read_text())
    approval.write_text(json.dumps({**body, "renders": {"count": 0}}))

    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    server = subprocess.Popen(
        [sys.executable, "-m", "isekai", "ui", "--port", str(port)],
        cwd=REPO,
        env={
            **os.environ,
            "ISEKAI_LIBRARY": str(lib),
            "ISEKAI_WIRING": "tests.e2e.wiring:fake",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        _wait(f"{url}/api/library", server)
        yield Served(
            url,
            BATCH,
            draft,
            approved,
            queues,
            rendered,
            shown,
            revised,
            discarded,
            compared,
            lib / "hub-prepare" / ".prepare-release",
        )
    finally:
        server.terminate()
        server.wait(timeout=10)
