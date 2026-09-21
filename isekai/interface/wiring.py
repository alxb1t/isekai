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
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO, TypeVar

from isekai.boundary.comfy_client import ComfyClient
from isekai.boundary.comfy_types import ComfyTransport
from isekai.boundary.wd14 import LocalTagger, open_session
from isekai.foundation.flow import FLOWS_DIR, Flow, Hosted
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import DATA_ROOT, RUNS_ROOT
from isekai.pipeline.caption import ClaudeReader, OllamaReader, Reader
from isekai.pipeline.sheet import ClaudeSorter, OllamaSorter, Sorter
from isekai.pipeline.tagging import OllamaTagger, Tagger
from isekai.shared.vocabulary import Vocabulary
from isekai.shared.vocabulary import load as load_vocabulary

T = TypeVar("T")


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
    #
    # **Resolvers rather than values**, which is the shape `vocabulary` already
    # has one line below and for a related reason: the flow decides which
    # implementation runs, so a value composed here would have to be composed
    # before any flow was loaded. One invocation naming two flows on two
    # implementations would then resolve one reader and hand it to both, and the
    # provenance the artifacts record would be false for one of them.
    reader: Callable[[Flow], Reader] | None
    sorter: Callable[[Flow], Sorter] | None
    # The two tagging seams, and they are deliberately not one. `tagger` resolves
    # for **every** flow because the local tagger reads no manifest key at all;
    # `hosted_tagger` answers `None` where a flow declares no arm this build can
    # tag on, which is an absence rather than a failure (design.md D3, D20).
    #
    # Both are `| None` on the dataclass for `reader`'s reason: a front end that
    # serves stage (3) alone reaches neither, and fabricating a tagger it never
    # calls would open a 467 MB file to be thrown away.
    tagger: Callable[[Flow], LocalTagger] | None
    hosted_tagger: Callable[[Flow], Tagger | None] | None
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


# The implementation a flow that declares no `hosted` block runs: the behaviour of
# every flow written before that key existed, which is what keeps both incumbent
# manifests unedited and their digests still.
DEFAULT_IMPLEMENTATION = "claude-cli"


def _claude_reader(flow: Flow) -> Reader:
    """Return the CLI reader, which takes nothing from the manifest."""
    return ClaudeReader()


def _claude_sorter(flow: Flow) -> Sorter:
    """Return the CLI sorter, which takes nothing from the manifest."""
    return ClaudeSorter()


def _named_by(flow: Flow) -> Hosted:
    """Return the block that named this implementation, narrowing away its absence.

    `_resolve` reached a hosted builder by reading `flow.hosted.implementation`,
    so the block is present; this refuses rather than raising `AttributeError` if
    `DEFAULT_IMPLEMENTATION` ever names an arm that needs one.
    """
    if flow.hosted is None:
        raise Refusal(f"flow {flow.id} declares no `hosted` block to run")
    return flow.hosted


def _ollama_reader(flow: Flow) -> Reader:
    """Return the Ollama reader, named by the flow's own manifest."""
    return OllamaReader(model=_named_by(flow).reader)


def _ollama_sorter(flow: Flow) -> Sorter:
    """Return the Ollama sorter, named by the flow's own manifest."""
    return OllamaSorter(model=_named_by(flow).sorter)


def _no_tagger(flow: Flow) -> Tagger | None:
    """Return nothing: this arm has a reader and a sorter but no tagger.

    An entry rather than an omission, so an arm this build does not carry is
    still a refusal naming what it does carry. See `HOSTED_TAGGERS`.
    """
    return None


def _ollama_tagger(flow: Flow) -> Tagger:
    """Return the Ollama tagger, on the same alias the reader runs.

    One model answers both prompts, which is exactly why `TAG_PROMPT` is not
    chat-framed: two calls to the same alias must not arrive framed differently.
    The manifest carries no separate tagger name, and adding one would be
    re-pinning three frozen flow directories to say twice what they say once.
    """
    return OllamaTagger(model=_named_by(flow).reader)


# **A table rather than a two-branch conditional, and the argument is the
# refusal.** A conditional gives an unrecognised implementation the default one,
# producing a complete run on the wrong models with the artifact's own provenance
# disagreeing with the manifest that asked for it -- silent, and it corrupts any
# later comparison between the two arms. A table makes that a refusal by
# construction rather than by remembering to check.
#
# **The keys are the strings the artifacts record**, and a test holds the two
# equal so the duplication cannot drift (design.md D6).
READERS: Mapping[str, Callable[[Flow], Reader]] = {
    "claude-cli": _claude_reader,
    "ollama": _ollama_reader,
}

SORTERS: Mapping[str, Callable[[Flow], Sorter]] = {
    "claude-cli": _claude_sorter,
    "ollama": _ollama_sorter,
}

# **`claude-cli` is in the table and maps to nothing**, which is not the same as
# being absent from it. There is no Claude tagger and there should not be -- a
# second hosted model spending money on an advisory panel -- but *recording* that
# the arm has none costs nothing and keeps one resolution mechanism for all three
# seams. Left out of the table, an unrecognised arm (`"vllm"`, a typo) would
# resolve to silence, and D20 makes silence unreportable by design; in the table,
# `_resolve` names what this build carries, exactly as it does for the reader and
# the sorter.
HOSTED_TAGGERS: Mapping[str, Callable[[Flow], Tagger | None]] = {
    "claude-cli": _no_tagger,
    "ollama": _ollama_tagger,
}


def _resolve(flow: Flow, registry: Mapping[str, Callable[[Flow], T]], seam: str) -> T:
    """Return the implementation this flow asks for, or refuse naming what we have.

    Nothing is constructed until a flow asks. That is what lets a machine with one
    implementation available never touch the other -- the check that a host is
    running or a binary installed fires at the first call, not here.
    """
    declared = flow.hosted.implementation if flow.hosted else DEFAULT_IMPLEMENTATION
    build = registry.get(declared)
    if build is None:
        raise Refusal(
            f"flow {flow.id} declares the {seam} implementation {declared!r}, and "
            f"this build carries {', '.join(sorted(registry))}; correct the "
            f"manifest's `hosted`, or point at a flow this build can run"
        )
    return build(flow)


def reader_for(flow: Flow) -> Reader:
    """Return the reader `flow`'s manifest declares, constructing no other."""
    return _resolve(flow, READERS, "reader")


def sorter_for(flow: Flow) -> Sorter:
    """Return the sorter `flow`'s manifest declares, constructing no other."""
    return _resolve(flow, SORTERS, "sorter")


def hosted_tagger_for(flow: Flow) -> Tagger | None:
    """Return the hosted tagger `flow` declares, or `None` where it declares none.

    **Two absences, and only one of them is this function's to decide.** A flow
    with no `hosted` block has nothing to resolve and answers `None` here; an arm
    that *is* declared goes through `_resolve` like every other seam, and whether
    that arm has a tagger is the registry's answer rather than a missing key's.
    Both absences are silent downstream, because a missing tag artifact is an
    absent aid and never a blocked review (design.md D20).

    What `_resolve` still buys, and the reason this does not skip it: an arm this
    build has never heard of names what it does carry instead of resolving to
    nothing. Silence is the right answer for *"this arm has no tagger"* and the
    wrong one for *"nobody has heard of this arm"*, and only a table can tell
    them apart.
    """
    if flow.hosted is None:
        return None
    return _resolve(flow, HOSTED_TAGGERS, "hosted tagger")


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
        reader=reader_for,
        sorter=sorter_for,
        tagger=tagger_for,
        hosted_tagger=hosted_tagger_for,
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
