"""How the verbs reach the outside world, and the one refusal that bounds where.

The composition root, split out of `__main__.py` because it has a second consumer
that never sees an argv: the suite builds a `Wiring` directly, with no parser at
all, in fourteen tests (`tests/test_resume.py`). A parser is one way to fill this
dataclass; it is not the only one, and the module that owns the parser is not the
right home for something composed without it.

`_check_run_root` travels with `wiring()`, its only caller. It is the guard that
keeps a run directory -- which holds a copy of the photograph by construction --
from sitting inside the working tree and outside the one root git ignores.

Stdlib only, and on `python -m isekai`'s import graph.
"""

import argparse
import dataclasses
import random
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from isekai.caption import ClaudeReader, Reader
from isekai.comfy_client import ComfyClient
from isekai.comfy_types import ComfyTransport
from isekai.flow import FLOWS_DIR, Schema
from isekai.refusal import Refusal
from isekai.run import DATA_ROOT, RUNS_ROOT
from isekai.sheet import ClaudeSorter, Sorter, load_schema
from isekai.vocabulary import Vocabulary
from isekai.vocabulary import load as load_vocabulary


@dataclass
class Wiring:
    """Everything the verbs reach the outside world through, in one place.

    A parameter is a seam only if something else is actually passed through it,
    and something is passed through every one of these: the reader and the sorter
    take their offline doubles, the transport takes the fake the existing suite
    already drives `pipeline.run` with, and the roots take a temporary directory.
    That is what makes the resume assertion -- run everything twice, and nothing
    moved and nothing was called -- provable without a GPU or a network.
    """

    reader: Reader
    sorter: Sorter
    client: ComfyTransport | None
    schema: Schema
    # A thunk, not a value. Only `sheet` and `approve` read the vocabulary, and
    # parsing the 308 KB tag list costs ~50 ms -- but the real cost is that an
    # eager read made `python -m isekai show` impossible on a clone that had not
    # provisioned it. The doubles still inject one; they inject a lambda.
    vocabulary: Callable[[], Vocabulary]
    runs_root: Path = RUNS_ROOT
    flows_dir: Path = FLOWS_DIR
    rng: random.Random = dataclasses.field(default_factory=random.Random)
    out: TextIO = sys.stdout
    err: TextIO = sys.stderr


# Derived from `DATA_ROOT` rather than recomputed, so the two halves of the check
# below cannot drift apart: both the repository and the ignored root are then
# anchored to one `__file__`. That anchor is deliberate -- `python -m isekai` may
# be run from anywhere, and a CWD-relative answer would make the same run root
# legal or illegal depending on where the operator happened to be standing.
REPOSITORY = DATA_ROOT.parent


def _check_run_root(runs: Path) -> None:
    """Refuse a run root inside the working tree that is not under `DATA_ROOT`.

    The rule bounds the working tree, not the filesystem. A run directory holds a
    copy of the photograph by construction, so inside the tree and outside the
    ignored root those photographs are trackable and one `git add` from being
    published; outside the repository they are not, whatever path they sit at
    (design.md D7).
    """
    resolved = runs.resolve()
    if resolved.is_relative_to(REPOSITORY) and not resolved.is_relative_to(DATA_ROOT):
        raise Refusal(
            f"--runs {resolved} is inside this repository and outside "
            f"{DATA_ROOT}, the one directory git ignores; a run holds a copy of "
            "the photograph, so that directory would be trackable and one `git "
            "add` from being published -- point it under .data/ or at a path "
            "outside the repository entirely"
        )


def wiring(args: argparse.Namespace) -> Wiring:
    """Build the real wiring: the hosted reader and sorter, and the HTTP transport.

    The vocabulary and the schema are read here rather than inside a stage,
    because reading a file is I/O and the stages are the part that must stay
    testable without any.
    """
    server = getattr(args, "server", None)
    _check_run_root(args.runs)
    return Wiring(
        reader=ClaudeReader(),
        sorter=ClaudeSorter(),
        client=ComfyClient(server) if server else None,
        schema=load_schema(),
        vocabulary=load_vocabulary,
        runs_root=args.runs,
    )
