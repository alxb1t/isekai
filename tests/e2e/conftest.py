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
from isekai.foundation.flow import load_flow, manifest_digest
from isekai.foundation.run import Run, approval_of, open_run
from isekai.pipeline.caption import FakeReader
from isekai.pipeline.generate import prepare
from isekai.pipeline.review import approve, review, revise, save_draft
from tests.e2e.wiring import VOCABULARY
from tests.fakes import FakeComfyClient
from tests.images import photo_jpeg
from tests.stages import caption, render, sheet

REPO = Path(__file__).resolve().parents[2]
FLOW = "summon-anime-wai"
CONJURE = "conjure-anime-wai"
FLAT = "summon-flat-anime-wai"
COLLECTION = "2026-10-19"

# A collection per approval test, each source a sheet with no draft, so every test
# owns the sheets it approves. Sizes differ so each source is its own run.
QUEUES: dict[str, tuple[tuple[str, tuple[int, int]], ...]] = {
    "queue-stays": (("cid", (700, 1000)), ("dot", (710, 1000))),
    "queue-fails": (("fay", (730, 1000)),),
    "queue-cancels": (("eve", (720, 1000)),),
}

# A collection per hub test, so every test owns the cells it ticks and prepares. Its
# sources are photographs with no run, except those `ASSIGNED` names.
FRESH: dict[str, tuple[str, ...]] = {
    "hub-tick": ("aside", "beside", "tick"),
    "hub-prepare": ("pick", "skip"),
}

# The fresh sources whose run is already assigned to `FLOW`, as a tick leaves it.
ASSIGNED: dict[str, tuple[str, ...]] = {"hub-prepare": ("pick",)}

# The collection a render test owns: one source approved for one image.
RENDER = "render"
# The collection the drawer's test renders: one source approved for one image.
DRAWN = "drawn"
# The collection the Renders view is read from: one source already rendered once.
SHOWN = "shown"
# The collection a revision is written in: one source rendered once at seed 7.
REVISED = "revised"
# The collection a discard is asked in and the pair is drawn from: one source
# rendered at seed 7, its render's revision drafted.
DISCARDED = "discarded"
# The collection Compare reads: one source with seed 7 rendered under v1 and under v2,
# which changes `clothes`, and flat summon's v1 rendered at seed 9.
COMPARED = "compared"
# The collection whose one approval is damaged: a source rendered at seed 7 under an
# approval holding a count no render takes.
DAMAGED = "damaged"

# The collection Draft from this drafts conjure in: one source whose summon approval
# changes `clothes`, rendered at seed 7, and no conjure sheet: the draft fills it.
CONJURED = "conjured"

# The collection the chooser opens on: one source with an unapproved sheet in each flow.
CHOSEN = "chosen"

# A first start may build the bundle, which `bundle.BUILD_TIMEOUT` bounds.
STARTUP = 300


@dataclass(frozen=True)
class Served:
    """The running app: its address, its collection and the runs it serves."""

    url: str
    collection: str
    draft: Run
    approved: Run
    queues: dict[str, tuple[Run, ...]]
    rendered: Run
    shown: Run
    revised: Run
    discarded: Run
    compared: Run
    conjured: Run
    chosen: Run
    prepare_release: Path

    def review(self, run: Run, collection: str | None = None) -> str:
        """Return the address of `run`'s review in `FLOW`, in `collection` or main."""
        return (
            f"{self.url}/c/{collection or self.collection}/review/{run.digest}/{FLOW}"
        )

    def hub_of(self, collection: str) -> str:
        """Return the address of `collection`'s hub."""
        return f"{self.url}/c/{collection}/hub"

    @property
    def hub(self) -> str:
        """Return the address of the main collection's hub."""
        return self.hub_of(self.collection)


def _run(folder: Path, name: str, size: tuple[int, int]) -> Run:
    """Return a run of a new source carrying a caption and a sheet for `FLOW`.

    Its photograph decodes, as a browser draws it; its size names its run.
    """
    photo = folder / "sources" / f"{name}.jpg"
    photo.write_bytes(photo_jpeg((40, 90, 60), size))
    run = open_run(photo, folder / "runs")
    caption(run, FakeReader(prose="Dark brown hair, brown eyes."))
    sheet(run, load_flow(FLOW).schema, VOCABULARY)
    return run


def _approved(folder: Path, name: str, size: tuple[int, int]) -> Run:
    """Return a run of a new source approved once and not yet rendered."""
    (folder / "sources").mkdir(parents=True)
    run = _run(folder, name, size)
    review(run, FLOW)
    approve(run, FLOW, load_flow(FLOW).schema, VOCABULARY)
    return run


def _rendered_at_seven(folder: Path, name: str, size: tuple[int, int]) -> Run:
    """Return a run of a new source approved once and rendered at seed 7."""
    run = _approved(folder, name, size)
    _render_at(run)
    return run


def _render_at(run: Run, seed: int = 7, flow: str = FLOW) -> None:
    """Render `run`'s newest approval in `flow` at seed 7, or `seed`, on the fake."""
    prepare(run, {flow: load_flow(flow)})
    image = photo_jpeg((90, 60, 30), (640, 800))
    render(
        run, load_flow(flow), FakeComfyClient(view_bytes=image), seeds=[seed], poll=0
    )


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
    """Serve a collection of one draft and one approved input of `FLOW`, then stop."""
    lib = tmp_path_factory.mktemp("e2e") / "isekai"
    folder = lib / COLLECTION
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

    rendered = _approved(lib / RENDER, "gia", (740, 1000))
    _approved(lib / DRAWN, "nia", (745, 1000))
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
    _render_at(compared)
    # A flat summon image, so Compare can pick another flow's.
    flat = load_flow(FLAT)
    sheet(
        compared, flat.schema, VOCABULARY, flow=FLAT, flow_digest=manifest_digest(FLAT)
    )
    review(compared, FLAT)
    approve(compared, FLAT, flat.schema, VOCABULARY)
    _render_at(compared, seed=9, flow=FLAT)
    damaged = _rendered_at_seven(lib / DAMAGED, "kim", (790, 1000))
    approval = approval_of(damaged, FLOW, 1)
    body = json.loads(approval.read_text())
    approval.write_text(json.dumps({**body, "renders": {"count": 0}}))
    (lib / CONJURED / "sources").mkdir(parents=True)
    conjured = _run(lib / CONJURED, "lu", (800, 1000))
    draft_of = review(conjured, FLOW)
    assert draft_of is not None
    fields = read(draft_of, DRAFT_FILE)["fields"]
    save_draft(conjured, FLOW, {**fields, "clothes": ["collared shirt"]})
    approve(conjured, FLOW, load_flow(FLOW).schema, VOCABULARY)
    _render_at(conjured)
    (lib / CHOSEN / "sources").mkdir(parents=True)
    chosen = _run(lib / CHOSEN, "mo", (810, 1000))
    sheet(chosen, load_flow(CONJURE).schema, VOCABULARY, flow=CONJURE)

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
            COLLECTION,
            draft,
            approved,
            queues,
            rendered,
            shown,
            revised,
            discarded,
            compared,
            conjured,
            chosen,
            lib / "hub-prepare" / ".prepare-release",
        )
    finally:
        server.terminate()
        server.wait(timeout=10)
