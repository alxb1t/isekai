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

from isekai.boundary.comfy import ComfyClient, ComfyTransport
from isekai.boundary.wd14 import LocalTagger, open_session
from isekai.foundation.flow import FLOWS_DIR, Flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import DATA_ROOT, REPOSITORY, RUNS_ROOT
from isekai.pipeline.caption import OllamaReader, Reader
from isekai.pipeline.tagging import OllamaTagger, Tagger
from isekai.shared.field_map import FieldMap
from isekai.shared.field_map import load as load_field_map
from isekai.shared.vocabulary import (
    DEFAULT_MODELS_DIR,
    VOCABULARY_DEST,
    VOCABULARY_REMEDY,
    Vocabulary,
)
from isekai.shared.vocabulary import load as read_vocabulary


@dataclass
class Wiring:
    """Everything the verbs reach the outside world through, in one place.

    A parameter is a seam only if something else is actually passed through it,
    and something is passed through every one of these: the reader takes its
    offline double, the transport takes the fake the existing suite
    already drives `pipeline.run` with, and the roots take a temporary directory.
    That is what makes the resume assertion -- run everything twice, and nothing
    moved and nothing was called -- provable without a GPU or a network.
    """

    # `reader` follows `client`'s precedent and may be absent. A front
    # end that only serves stage ③ reaches no hosted model at all, and fabricating
    # an `OllamaReader()` it never calls would be a lie in the code -- so the
    # verbs that do reach one say so at their own call site instead.
    #
    # **Resolvers rather than values**, which is the shape `vocabulary` already
    # has one line below and for a related reason: the flow decides which
    # implementation runs, so a value composed here would have to be composed
    # before any flow was loaded. One invocation naming two flows on two
    # implementations would then resolve one reader and hand it to both, and the
    # provenance the artifacts record would be false for one of them.
    reader: Callable[[Flow], Reader] | None
    # The two tagging seams, and they are deliberately not one. `tagger` resolves
    # for **every** flow because the local tagger reads no manifest key at all;
    # `hosted_tagger` resolves on the one key the reader also reads, because which
    # model answers is a claim the flow makes about itself (design.md D3).
    #
    # Both are `| None` on the dataclass for `reader`'s reason: a front end that
    # serves stage (3) alone reaches neither, and fabricating a tagger it never
    # calls would open a 467 MB file to be thrown away.
    tagger: Callable[[Flow], LocalTagger] | None
    hosted_tagger: Callable[[Flow], Tagger] | None
    client: ComfyTransport | None
    # A thunk, not a value. Only `sheet` and `approve` read the vocabulary, and
    # parsing the 308 KB tag list costs ~50 ms -- but the real cost is that an
    # eager read made `python -m isekai show` impossible on a clone that had not
    # provisioned it. The doubles still inject one; they inject a lambda.
    vocabulary: Callable[[], Vocabulary]
    # Lazy for the same reason, and it **takes** the vocabulary rather than
    # finding its own: the table is only meaningful held against one, and every
    # caller already has the invocation's. A zero-argument thunk would re-verify
    # 308 KB against the manifest and re-parse 8,106 rows to answer a question
    # the caller's own vocabulary answers.
    field_map: Callable[[Vocabulary], FieldMap]
    runs_root: Path = RUNS_ROOT
    flows_dir: Path = FLOWS_DIR
    rng: random.Random = dataclasses.field(default_factory=random.Random)
    out: TextIO = sys.stdout
    err: TextIO = sys.stderr


# **What the seams resolve on is the model, not an implementation string.** There
# was a table here, keyed on the arm a manifest named, and the argument for it was
# that a two-branch conditional would hand an unrecognised name the default arm --
# a complete run on the wrong models, with the artifact's own provenance
# disagreeing with the manifest that asked for it. **That premise is gone**: there
# is no second arm to fall into and no default to fall back on, so a one-entry
# table would be a dispatch mechanism with nothing to dispatch (design.md D16, D17).
#
# What survives is the half of the argument that was never about having two: a
# manifest naming a model this build cannot reach still refuses by name, and it
# refuses at the first call rather than here -- `ollama.py` is what checks that a
# host is running and an alias created, and nothing is constructed until a flow
# asks.


def reader_for(flow: Flow) -> Reader:
    """Return the reader running the model `flow`'s manifest names."""
    return OllamaReader(model=flow.model)


def hosted_tagger_for(flow: Flow) -> Tagger:
    """Return the hosted tagger, on the same alias the reader runs.

    **One model answers both prompts**, which is exactly why `TAG_PROMPT` is not
    chat-framed: two calls to the same alias must not arrive framed differently.
    The manifest carries no separate tagger name, and adding one would be a second
    key saying what `model` already says once.

    It is not optional any more. `model` is required, so there is no flow whose
    manifest leaves this unresolvable -- what can still go wrong is the alias not
    being created, and that is a refusal at the first call naming the one command
    that fixes it (design.md D25).
    """
    return OllamaTagger(model=flow.model)


def tagger_for(flow: Flow) -> LocalTagger:
    """Open the local tagger and read its label index, for any flow at all.

    **It takes a `Flow` and reads nothing from it**, which is the whole point
    rather than an oversight: the local tagger resolves through no manifest key,
    because it is a file this build pins, it costs nothing, it reaches no network,
    and there is no flow for which it would be wrong. Requiring a key would mean
    re-pinning every existing flow directory to state an opinion none of them has
    (design.md D3). The parameter stays so that both tagging seams have one shape
    and `cli.py` resolves them the same way.

    **Both digests are verified and 467 MB is opened here**, so nothing calls this
    until a flow asks -- and `cli.py` calls it once per flow per invocation rather
    than once per photograph, which is the difference between 0.89 s and 0.89 s
    times the batch (design.md D14).
    """
    return open_session()


# `REPOSITORY` is imported rather than re-derived, so the two halves of the check
# below cannot drift apart. The anchor is deliberate -- `python -m isekai` may be
# run from anywhere, and a CWD-relative answer would make the same run root legal
# or illegal depending on where the operator happened to be standing.


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


def load_vocabulary(models_dir: Path = DEFAULT_MODELS_DIR) -> Vocabulary:
    """Return the provisioned vocabulary, its bytes verified against the manifest.

    The digest check is the reason the pin is worth anything: the manifest is the
    only evidence the file on disk is the list the sheets were written against.
    `provision` is imported here rather than at module scope, so it stays off
    `python -m isekai`'s import graph. Why here: `0027` design D8.
    """
    from isekai.boundary.provision import (
        VOCABULARY_MANIFEST_PATH,
        load_manifest,
        resolve,
    )

    manifest = load_manifest(VOCABULARY_MANIFEST_PATH)
    try:
        path = resolve(VOCABULARY_DEST, models_dir, manifest)
    except FileNotFoundError as absent:
        # A `FileNotFoundError` is the one failure here that has a remedy this
        # build can perform, and a traceback names a path instead of naming it.
        raise Refusal(
            f"{VOCABULARY_DEST} is not provisioned under {models_dir}/, and no "
            f"sheet can be filled or approved without it; run `{VOCABULARY_REMEDY}` "
            "from the repository root to fetch and verify it against its pinned "
            "manifest"
        ) from absent
    entry = next(e for e in manifest["entries"] if e["dest"] == VOCABULARY_DEST)
    return read_vocabulary(path, entry)


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
        reader=reader_for,
        tagger=tagger_for,
        hosted_tagger=hosted_tagger_for,
        client=ComfyClient(server) if server else None,
        vocabulary=load_vocabulary,
        field_map=load_field_map,
        runs_root=runs,
    )


def wiring(args: argparse.Namespace) -> Wiring:
    """Build the real wiring from a parsed command line.

    `getattr` rather than `args.server`: only `generate` declares the flag, so the
    attribute is genuinely absent on every other verb's namespace.
    """
    return wiring_from(runs=args.runs, server=getattr(args, "server", None))
