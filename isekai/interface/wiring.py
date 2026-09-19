"""How the verbs reach the outside world, and the one refusal that bounds where.

The composition root, split out of `__main__.py` because it has a second consumer
that never sees an argv: the suite builds a `Wiring` directly, with no parser at
all, in three test modules. A parser is one way to fill this
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

from isekai.boundary.comfy_client import ComfyClient
from isekai.boundary.comfy_types import ComfyTransport
from isekai.foundation.flow import FLOWS_DIR
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import DATA_ROOT, RUNS_ROOT
from isekai.pipeline.caption import ClaudeReader, Reader
from isekai.pipeline.sheet import ClaudeSorter, Sorter
from isekai.shared.vocabulary import Vocabulary
from isekai.shared.vocabulary import load as load_vocabulary


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

    # `reader` and `sorter` follow `client`'s precedent and may be absent. A front
    # end that only serves stage ③ reaches no hosted model at all, and fabricating
    # a `ClaudeReader()` it never calls would be a lie in the code -- so the verbs
    # that do reach one say so at their own call site instead.
    reader: Reader | None
    sorter: Sorter | None
    client: ComfyTransport | None
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


def _identity(path: Path) -> tuple[int, int] | None:
    """Return what the filesystem calls this directory, or `None` if it has none.

    A directory that does not exist has no identity. That is the only reason this
    returns an option rather than a pair.
    """
    try:
        info = path.stat()
    except OSError:
        return None
    return (info.st_dev, info.st_ino)


def _is_within(resolved: Path, ancestor: Path) -> bool:
    """Decide whether `resolved` is that directory, or sits inside it.

    Decided by identity rather than by the text of the two paths. `Path.resolve()`
    follows symlinks and drops `..` segments, but it does **not** fold case -- so
    on a case-insensitive filesystem a differently-cased spelling of a directory
    inside the working tree resolves to a path that *compares* as a different path
    and *is* the same directory. A prefix test accepted it, which is the exact
    outcome the rule exists to refuse, reached by a typing mistake rather than by
    an adversary (design.md D10). `os.path.normcase` does not close this: it is a
    no-op on darwin.

    An ancestor that does not exist yet has no identity to compare against, so the
    textual test stands in for it. That is not a weakening of the rule: where a
    directory has never been created there is no second name for the filesystem to
    open as it.
    """
    target = _identity(ancestor)
    if target is None:
        return resolved.is_relative_to(ancestor)
    return any(
        _identity(candidate) == target for candidate in (resolved, *resolved.parents)
    )


def _check_run_root(runs: Path) -> None:
    """Refuse a run root inside the working tree that is not under `DATA_ROOT`.

    The rule bounds the working tree, not the filesystem. A run directory holds a
    copy of the photograph by construction, so inside the tree and outside the
    ignored root those photographs are trackable and one `git add` from being
    published; outside the repository they are not, whatever path they sit at
    (design.md D7).
    """
    resolved = runs.resolve()
    if _is_within(resolved, REPOSITORY) and not _is_within(resolved, DATA_ROOT):
        raise Refusal(
            f"--runs {resolved} is inside this repository and outside "
            f"{DATA_ROOT}, the one directory git ignores; a run holds a copy of "
            "the photograph, so that directory would be trackable and one `git "
            "add` from being published -- point it under .data/ or at a path "
            "outside the repository entirely"
        )


def wiring_from(*, runs: Path, server: str | None = None) -> Wiring:
    """Build the real wiring from values, with no `Namespace` anywhere in sight.

    The argv-free half, so that a front end which never parses a command line can
    still only reach a `Wiring` through `_check_run_root`. The UI server is that
    front end: building the dataclass directly, the way the suite does, would walk
    straight past the one guard that bounds where a copy of the photograph may be
    written -- and a server is exactly the thing that should not be able to
    (design.md D1).

    The vocabulary is read here rather than inside a stage, because reading a file
    is I/O and the stages are the part that must stay testable without any. A
    schema is not composed here at all: it sits inside the flow that uses it, so a
    loaded `Flow` already answers for its own.
    """
    _check_run_root(runs)
    return Wiring(
        reader=ClaudeReader(),
        sorter=ClaudeSorter(),
        client=ComfyClient(server) if server else None,
        vocabulary=load_vocabulary,
        runs_root=runs,
    )


def wiring(args: argparse.Namespace) -> Wiring:
    """Build the real wiring from a parsed command line.

    `getattr` rather than `args.server`: only `generate` declares the flag, so the
    attribute is genuinely absent on every other verb's namespace.
    """
    return wiring_from(runs=args.runs, server=getattr(args, "server", None))
