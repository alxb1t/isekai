"""The wiring the browser tests serve on: every seam a double, nothing reached.

`ISEKAI_WIRING=tests.e2e.wiring:fake` names `fake` to `wiring_from`, which calls it
after its run-root guard (D41). No GPU, no Ollama, no provisioned vocabulary.
"""

import io
import random
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from isekai.boundary.gpu import Seams, Volume
from isekai.interface.wiring import Wiring
from isekai.pipeline.caption import FakeReader
from isekai.pipeline.tagging import FakeTagger
from tests.conftest import VOCABULARY
from tests.fakes import SESSION_IMAGE, FakeComfyClient
from tests.stages import FIELD_MAP, Always, fake_wd14


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


def _gpunit(argv: Sequence[str], log: Path) -> int:
    """Answer every gpunit verb as done, writing its line to the log."""
    with log.open("a", encoding="utf-8") as appended:
        print(f"fake gpunit {' '.join(argv)}", file=appended)
    return 0


# A render on these rents nothing and answers at once.
SESSION = Seams(
    open_session=_opened,
    environ={},
    connect=lambda server: FakeComfyClient(),
    busy=lambda port: False,
    kill=lambda: None,
)


def fake(*, runs: Path) -> Wiring:
    """Return a wiring over `runs` whose every seam is an offline double."""
    return Wiring(
        reader=Always(FakeReader(prose="Dark brown hair, brown eyes.")),
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
        volume=Volume(run=_gpunit),
    )
