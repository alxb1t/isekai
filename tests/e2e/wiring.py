"""The wiring the browser tests serve on: every seam a double, nothing reached.

`ISEKAI_WIRING=tests.e2e.wiring:fake` names `fake` to `wiring_from`, which calls it
after its run-root guard (D41). No GPU, no Ollama, no provisioned vocabulary.
"""

import io
import random
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from isekai.boundary.gpu import Say, Seams, Volume
from isekai.interface.wiring import Wiring
from isekai.pipeline.caption import FakeReader, Reading
from isekai.pipeline.tagging import FakeTagger
from tests.conftest import VOCABULARY
from tests.fakes import SESSION_IMAGE, FakeComfyClient
from tests.images import photo_jpeg
from tests.stages import FIELD_MAP, NO_RECORDS, Always, fake_wd14


@dataclass(frozen=True)
class _Session:
    """What gpunit yields: the booted image, and a port nothing listens on."""

    image: str = SESSION_IMAGE

    def port(self, remote: int) -> int:
        return remote


@contextmanager
def _opened(
    cwd: Path, environ: Mapping[str, str], say: Callable[[str], None], limit_s: int
) -> Iterator[_Session]:
    """Open a session that rents nothing."""
    say(f"fake session, limit {limit_s}s")
    yield _Session()


def _gpunit(argv: Sequence[str], say: Say) -> int:
    """Answer every gpunit verb as done, saying its line."""
    say(f"fake gpunit {' '.join(argv)}")
    return 0


# A render on these rents nothing and answers at once with an image that decodes;
# the key is a stand-in, so Render is offered.
SESSION = Seams(
    open_session=_opened,
    environ={"RUNPOD_API_KEY": "e2e"},
    connect=lambda server: FakeComfyClient(
        view_bytes=photo_jpeg((90, 60, 30), (640, 800))
    ),
    busy=lambda port: False,
    kill=lambda: None,
)


class _HeldReader(FakeReader):
    def __init__(self, release: Path) -> None:
        super().__init__(prose="Dark brown hair, brown eyes.")
        self._release = release

    def read(self, photo: Path, briefing: str, workspace: Path) -> Reading:
        deadline = time.monotonic() + 30
        while not self._release.exists():
            if time.monotonic() >= deadline:
                raise AssertionError("Prepare reader was not released")
            time.sleep(0.02)
        return super().read(photo, briefing, workspace)


def fake(*, runs: Path) -> Wiring:
    """Return a wiring over `runs` whose every seam is an offline double."""
    reader = (
        _HeldReader(runs.parent / ".prepare-release")
        if runs.parent.name == "hub-prepare"
        else FakeReader(prose="Dark brown hair, brown eyes.")
    )
    return Wiring(
        reader=Always(reader),
        tagger=fake_wd14(),
        hosted_tagger=Always(FakeTagger()),
        client=FakeComfyClient(),
        vocabulary=lambda: VOCABULARY,
        field_map=lambda _: FIELD_MAP,
        runs_root=runs,
        rng=random.Random(0),
        err=io.StringIO(),
        probe=lambda: None,
        session=SESSION,
        volume=Volume(run=_gpunit, records=NO_RECORDS),
    )
