"""The wiring the browser tests serve on: every seam a double, nothing reached.

`ISEKAI_WIRING=tests.e2e.wiring:fake` names `fake` to `wiring_from`, which calls it
after its run-root guard (D41). No GPU, no Ollama, no provisioned vocabulary.
"""

import io
import random
from pathlib import Path

from isekai.interface.wiring import Wiring
from isekai.pipeline.caption import FakeReader
from isekai.pipeline.tagging import FakeTagger
from tests.conftest import VOCABULARY
from tests.fakes import FakeComfyClient
from tests.stages import FIELD_MAP, Always, fake_wd14


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
    )
