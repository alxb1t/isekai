"""One app per session, over a fixture library, served on doubles.

The server is the real `python -m isekai ui` in its own process, so the page is
the built bundle and every request crosses the real guard. `ISEKAI_LIBRARY`
points it at a library under `tmp_path`, and `ISEKAI_WIRING` swaps the seams for
`tests/e2e/wiring.py`'s doubles (D19): no GPU, no Ollama.
"""

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

from isekai.foundation.flow import load_flow
from isekai.foundation.run import Run, open_run
from isekai.pipeline.caption import FakeReader
from isekai.pipeline.review import approve, review
from tests.e2e.wiring import VOCABULARY
from tests.images import jpeg_bytes
from tests.stages import caption, sheet

REPO = Path(__file__).resolve().parents[2]
FLOW = "summon-anime-wai"
BATCH = "2026-10-19"

# A first start may build the bundle, which `bundle.BUILD_TIMEOUT` bounds.
STARTUP = 300


@dataclass(frozen=True)
class Served:
    """The running app: its address, its batch and the runs it serves."""

    url: str
    batch: str
    draft: Run
    approved: Run

    def review(self, run: Run) -> str:
        """Return the address of `run`'s review in `FLOW`."""
        return f"{self.url}/b/{self.batch}/review/{run.id[:12]}/{FLOW}"

    @property
    def hub(self) -> str:
        """Return the address of the batch's hub."""
        return f"{self.url}/b/{self.batch}/hub"


def _run(folder: Path, name: str, size: tuple[int, int]) -> Run:
    """Return a run of a new source carrying a caption and a sheet for `FLOW`."""
    photo = folder / "sources" / f"{name}.jpg"
    photo.write_bytes(jpeg_bytes(*size))
    run = open_run(photo, folder / "runs")
    caption(run, FakeReader(prose="Dark brown hair, brown eyes."))
    sheet(run, load_flow(FLOW).schema, VOCABULARY)
    return run


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
        yield Served(url, BATCH, draft, approved)
    finally:
        server.terminate()
        server.wait(timeout=10)
