"""The pipeline's command line: `python -m isekai <verb>`.

**The only surface.** v0.13 built this parser beside the old single-command one
and v0.14 deleted that one, discharging the suspension of the repository's own
rule: there is one render path, and this is its entry point. Four separate scripts
were rejected for the same reason one parser was chosen: it would multiply the
import guard by four and give argument parsing four places to drift.

**Seven verbs, and schema migration is not one of them.** Only schema version 1
exists, so an upgrade command would be a dispatch table with no entries and its
refusal would be unreachable -- nothing can write a version 2 artifact
(design.md D2).

    caption   (1) a photograph in; prose, the WD14 tags and the hosted tags out
    sheet     (2) the WD14 tag list in, a sheet of canonical tags out
    review    (3) the machine's sheet copied somewhere a human may edit it
    approve   (3) validate the edited sheet and rename it
    generate  (4) assemble every prompt locally, then render
    show          print a run's artifacts and what produced each one
    ui        (3) serve the review surface for a batch of inputs

**Five of them run a stage, one inspects a run and one serves a surface.** The
five that run a stage take `--flow` repeatably; `ui` takes exactly one, because
the surface is one schema's fields in one order; `show` takes none, because it
reports every flow the run already holds. `show` reads a run and decides
nothing, and `ui` is the second front end rather than a client of the first --
it calls `wiring` and the stage functions directly, exactly as this module does,
so neither surface is privileged and neither goes through the other
(design.md D1).

**`isekai/__main__.py` is a shim over this file.** `runpy` pins where the entry
point's *path* is; it does not pin where the parser lives, and a package's largest
interface surface has no business being the one module outside the filing scheme
(design.md D3). Everything the verb line does is here.

Stdlib only, and held to that by a subprocess guard that imports the entry point
with site-packages off the path.
"""

import argparse
import sys
import urllib.error
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, TypeVar

from isekai.boundary.comfy_types import (
    ComfyTransport,
    Image,
    Unreachable,
)
from isekai.boundary.wd14 import LocalTagger
from isekai.foundation.flow import Flow, Workflow, load_flow, tracked_flows
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import FRAME_NAME, RUNS_ROOT, Run, across, open_run
from isekai.interface.run_view import report
from isekai.interface.wiring import Wiring, wiring
from isekai.pipeline.caption import caption
from isekai.pipeline.generate import prepare, render
from isekai.pipeline.review import approve, review
from isekai.pipeline.sheet import sheet
from isekai.pipeline.tagging import caption_tags, caption_wd14
from isekai.shared.field_map import FieldMap
from isekai.shared.vocabulary import Vocabulary

# One line of prose per verb, used for both the subcommand list and its own help,
# so the two cannot disagree about what a stage does.
T = TypeVar("T")

VERBS: tuple[tuple[str, str], ...] = (
    ("caption", "read a photograph into prose, the WD14 tags and the hosted tags"),
    ("sheet", "fill a sheet of canonical tags from the WD14 tag list"),
    ("review", "copy a sheet somewhere a human may edit it"),
    ("approve", "validate an edited sheet and mark it approved"),
    ("generate", "assemble the prompts for a run, then render them"),
    ("show", "print a run's artifacts, versions and producers"),
    ("ui", "serve the review surface for a batch of inputs"),
)

# The review surface's loopback port. Declared here rather than in the package it
# starts, because the parser is the one authority for what a flag defaults to --
# and importing the surface at module scope is exactly what the `-S` guard
# forbids this file from doing.
DEFAULT_PORT = 8517


def _seed(value: str) -> int:
    """Parse a seed: an unsigned 64-bit integer, refused at parse time if it is not."""
    try:
        seed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer") from None
    if not 0 <= seed < 2**64:
        raise argparse.ArgumentTypeError(
            f"{seed} is outside the sampler's unsigned 64-bit range"
        )
    return seed


def _count(value: str) -> int:
    """Parse a render count: a positive integer. Every one of them costs money."""
    try:
        count = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer") from None
    if count < 1:
        raise argparse.ArgumentTypeError("a render count below 1 renders nothing")
    return count


class _OneFlow(argparse.Action):
    """Accept `--flow` exactly once, refusing a repeat naming why.

    `action="append"` is what every stage verb uses, because flows batch: they
    render on one endpoint and a second boot costs what eight more renders
    would. A serving verb does not batch, so that reason does not reach it -- and
    argparse's own default for a plain option is to keep the last spelling
    silently, which would open a surface for a flow the operator did not mean.
    """

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        """Set the flow, or refuse because one was already named."""
        if getattr(namespace, self.dest, None) is not None:
            parser.error(
                "--flow may be given once here: the review surface serves one "
                "flow at a time, because two would be two field orders and two "
                "token budgets sharing one set of controls"
            )
        setattr(namespace, self.dest, values)


def build_parser() -> argparse.ArgumentParser:
    """Return the pipeline's parser, with one subparser per verb."""
    parser = argparse.ArgumentParser(
        prog="python -m isekai",
        description="The staged pipeline: photograph -> tags -> sheet -> render.",
    )
    verbs = parser.add_subparsers(dest="verb", metavar="verb", required=True)
    made = {
        name: verbs.add_parser(name, help=summary, description=summary)
        for name, summary in VERBS
    }

    for name in made:
        made[name].add_argument(
            "photos",
            nargs="*",
            help="photographs, or run identifiers for a run that already exists",
        )
        # The root every run lives under. It defaults to `.data/runs`, and it is a
        # flag because a version's acceptance run wants its own directory rather
        # than one pile every version adds to. A run holds a copy of the
        # photograph, so a run root is a directory of personal photographs by
        # construction -- which is why `wiring` refuses one that resolves INSIDE
        # this repository and outside `.data/`, where nothing ignores it and a
        # `git add` would publish it. A path outside the repository needs no
        # check at all: version control cannot reach it, whatever it is, and that
        # is what keeps a run on another disk expressible (design.md D7).
        made[name].add_argument(
            "--runs",
            type=Path,
            default=RUNS_ROOT,
            help=f"the directory runs live under (default {RUNS_ROOT.name}/)",
        )
    # Required, and repeatable, on every stage verb. A stage cannot act without
    # knowing which flow asked, because the flow is what supplies what it reads:
    # its briefing, its schema, its graph and its dials. "Every tracked flow" is
    # not a selection, it is the absence of one -- and at the last verb it spends
    # money, at the first it burns a paid model call.
    for name in ("caption", "sheet", "review", "approve", "generate"):
        made[name].add_argument(
            "--flow",
            action="append",
            dest="flows",
            required=True,
            metavar="FLOW",
            help="a flow to act on; repeatable, and required",
        )
    for name in ("caption", "sheet", "review"):
        made[name].add_argument(
            "--new-version",
            action="store_true",
            help="write the next numbered artifact instead of doing nothing",
        )

    # Exactly one, and required. The surface shows one schema's fields in one
    # fixed order, so a second flow would be a second page rather than a wider
    # one -- and the limit belongs at the command the operator typed rather than
    # at a screen that half-works.
    made["ui"].add_argument(
        "--flow",
        action=_OneFlow,
        dest="flow",
        required=True,
        metavar="FLOW",
        help="the flow to review; required, and given exactly once",
    )
    made["ui"].add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"the loopback port to serve on (default {DEFAULT_PORT})",
    )

    # Mutually exclusive at parse time, so asking for both is refused before any
    # work begins rather than discovered on a rented machine. One verb explores
    # and the other reproduces, and combining them has no meaning (design.md D13).
    render = made["generate"].add_mutually_exclusive_group()
    render.add_argument(
        "--count",
        type=_count,
        default=None,
        help="how many renders per photograph per flow (default 1, seeds drawn)",
    )
    render.add_argument(
        "--seed",
        type=_seed,
        action="append",
        dest="seeds",
        default=None,
        help="render exactly this seed; repeatable, and not combinable with --count",
    )
    # No default, deliberately. Assembly is free and rendering is not, so the
    # invocation that costs money is the one that names where to spend it --
    # `generate` without `--server` assembles every prompt and stops, which is
    # also how a malformed sheet is found before anything is rented.
    made["generate"].add_argument(
        "--server",
        default=None,
        help=(
            "the ComfyUI endpoint, reached through the tunnel; omit it to "
            "assemble every prompt and stop without rendering"
        ),
    )
    return parser


def _ui(args: argparse.Namespace, wired: Wiring, targets: Sequence[str]) -> int:
    """Serve the review surface for one flow, blocking until the operator stops it.

    **The import is inside this function, and it is load-bearing.**
    `tests/test_pipeline_cli.py` imports the entry point with `-S`, site-packages
    off the path, and walks this module's module-level imports: nothing there may
    need a wheel, and `isekai.interface.ui` reaches FastAPI. A top-level import
    here would put a web framework on `python -m isekai`'s import graph and turn
    that guard red for every verb, including the six that never serve anything.
    """
    from isekai.interface.ui import serve

    return serve(wired, str(args.flow), targets, port=int(args.port))


def _run_for(identifier: str, wired: Wiring) -> Run:
    """Return the run an argument names: a photograph to open, or a run to resume.

    A photograph is offered by path and an existing run by its id, and which one
    was meant is decided by what is on disk rather than by a flag.
    """
    directory = wired.runs_root / identifier
    if (directory / FRAME_NAME).is_file():
        return Run(identifier, directory)
    photo = Path(identifier)
    if not photo.is_file():
        raise Refusal(
            f"{identifier!r} is neither a photograph on disk nor a run under "
            f"{wired.runs_root.name}/; give the path to a JPEG or PNG, or the id "
            "`python -m isekai show` prints"
        )
    return open_run(photo, wired.runs_root)


def _flows_for(args: argparse.Namespace, wired: Wiring) -> dict[str, Flow]:
    """Return the flows this invocation acts on, loaded, refusing an untracked one.

    Resolved once, at selection, so an untracked name or a broken manifest is
    caught before any run is opened -- rather than at the flow's first use, which
    on `generate` is after a photograph has been uploaded. The parser has already
    refused a stage verb naming none, and `show` names none by design, so an empty
    selection is the inspection verb rather than a missing flag.
    """
    named: list[str] = list(getattr(args, "flows", None) or [])
    tracked = tracked_flows(wired.flows_dir)
    unknown = [name for name in named if name not in tracked]
    if unknown:
        raise Refusal(
            f"{', '.join(unknown)}: not a flow this build tracks; the flows it "
            f"carries are {', '.join(tracked) or '(none)'}"
        )
    # Deduplicated, order kept: naming a flow twice is a typo, not a request for
    # two renders of it.
    return {name: load_flow(name, wired.flows_dir) for name in dict.fromkeys(named)}


def dispatch(args: argparse.Namespace, wired: Wiring) -> int:
    """Run one verb over every identifier given, reporting every refusal together.

    **Batch is the general form here and per-item is the special case.** Assembly
    has to finish for the whole batch before any endpoint is acquired, so
    `generate` takes the targets itself; every other verb is per-item, and one
    photograph's failure does not cost the others their turn. Refusals are
    collected and printed at the end, and the exit status says whether any fired.
    """
    verb = str(args.verb)
    targets = list(args.photos)
    # Resolved before the first identifier is looked at, so an untracked flow or
    # a broken manifest refuses without opening a run -- and on `generate`,
    # without renting anything. The serving verb resolves its own single flow
    # inside `establish`, so it is answered before that.
    try:
        if verb == "ui":
            return _ui(args, wired, targets)
        flows = _flows_for(args, wired)
    except Refusal as unselectable:
        print(f"refused: {unselectable}", file=wired.err)
        return 1
    if verb == "generate":
        refused = _generate(args, wired, targets, flows)
    else:
        refused = across(targets, _per_item(verb, args, wired, flows))
    for message in refused:
        print(f"refused: {message}", file=wired.err)
    return 1 if refused else 0


def _seam(value: T | None, name: str, does: str) -> T:
    """Return a wiring seam the verb in hand cannot run without, or refuse.

    `reader` is optional on `Wiring` because a front end that serves stage (3)
    alone reaches no hosted model and would otherwise fabricate a double it never
    calls. The verbs that *do* call one say so here, in one
    place, rather than each inlining the same guard.
    """
    if value is None:
        raise Refusal(
            f"this wiring was composed without a {name}, and the verb {does} "
            f"through one"
        )
    return value


def _per_item(
    verb: str, args: argparse.Namespace, wired: Wiring, flows: Mapping[str, Flow]
) -> Callable[[str], None]:
    """Return the work one identifier gets, with everything run-independent done.

    The flows a verb acts on are a property of the invocation, not of the
    photograph, so they are resolved once by the caller rather than re-read from
    disk per identifier. Every stage but the inspection one is per flow, because
    the flow is what supplies what the stage reads: its briefing, its schema and
    its dials. The vocabulary is resolved at most once for the same reason and
    lazily for the old one: parsing the 308 KB tag list costs ~50 ms, and only
    two verbs need it at all.
    """
    new_version = bool(getattr(args, "new_version", False))
    opened: list[LocalTagger] = []

    @cache
    def vocabulary() -> Vocabulary:
        """Return this invocation's vocabulary, reading it at most once."""
        return wired.vocabulary()

    @cache
    def field_map() -> FieldMap:
        """Return this invocation's field map, reading it at most once.

        Memoised beside the vocabulary and for its reason: the table is held
        against the vocabulary at load, so reading it per photograph would
        re-run four whole-table checks for every input in a batch. It is handed
        the memoised vocabulary rather than finding its own.
        """
        return wired.field_map(vocabulary())

    def tagger(flow: Flow) -> Callable[[], LocalTagger]:
        """Return a thunk that opens this invocation's local tagger, once.

        **A thunk rather than a value, and one slot rather than one per flow.**

        Lazy, because opening it hashes 467 MB and loads a graph: a batch whose
        lists are all already written must not pay for that to write nothing,
        and a completed run must still resume on a machine that has since
        emptied `models/`. `vocabulary()` above is a thunk for exactly this
        reason and says so.

        One slot, because `wiring.tagger_for` takes a `Flow` and reads nothing
        from it -- the local tagger resolves through no manifest key at all
        (design.md D3). Keying the memo by flow would open the same graph once
        per flow named on one command line and hold every copy for the rest of
        the invocation. The parameter stays because the seam's shape is per flow
        and the day one of them selects a different tagger is the day this needs
        a key; giving it one before then buys two sessions and no behaviour.
        """
        resolve = _seam(wired.tagger, "tagger", "scores the photograph")

        def opening() -> LocalTagger:
            if not opened:
                opened.append(resolve(flow))
            return opened[0]

        return opening

    def work(identifier: str) -> None:
        run = _run_for(identifier, wired)
        if verb == "caption":
            for name, flow in flows.items():
                # **Resolved per flow, not once per invocation.** One command
                # naming two flows on two models would otherwise resolve one
                # reader and hand it to both, and the provenance one of the two
                # artifacts records would be false (design.md D6).
                reader = _seam(wired.reader, "reader", "reads the photograph")(flow)
                _say(
                    wired,
                    run,
                    "caption",
                    caption(
                        run,
                        name,
                        reader,
                        briefing_path=flow.caption_briefing_path,
                        new_version=new_version,
                    ),
                )
                # **The order decides what a refusal abandons.** `across()`
                # catches `Refusal` per *input* rather than per stage, so the
                # first refusal on a photograph abandons the rest of that
                # photograph's work. Prose first; the sheet reads the WD14 list,
                # so a prose refusal abandons that list too -- a known cost. WD14
                # second: local and deterministic, it fails only on a missing or
                # corrupt file, which is one operator fix and worth stopping on.
                # The hosted tagger last, because it is the tagger with a port, a
                # timeout and a retry budget -- so its refusal blocks nothing
                # that would have succeeded (design.md D7).
                _say(
                    wired,
                    run,
                    "wd14",
                    caption_wd14(run, name, tagger(flow), new_version=new_version),
                )
                hosted = _seam(
                    wired.hosted_tagger, "hosted tagger", "tags the photograph"
                )(flow)
                _say(
                    wired,
                    run,
                    "tags",
                    caption_tags(run, name, hosted, new_version=new_version),
                )
        elif verb == "sheet":
            for name, flow in flows.items():
                _say(
                    wired,
                    run,
                    "sheet",
                    sheet(
                        run,
                        name,
                        flow.schema,
                        vocabulary(),
                        field_map(),
                        new_version=new_version,
                    ),
                )
        elif verb == "review":
            for name in flows:
                _say(wired, run, "review", review(run, name, new_version=new_version))
        elif verb == "approve":
            for name, flow in flows.items():
                written, warnings = approve(run, name, flow.schema, vocabulary())
                for warning in warnings:
                    print(f"warning: {warning}", file=wired.err)
                _say(wired, run, "approve", written)
        elif verb == "show":
            for line in report(run, wired.flows_dir):
                print(line, file=wired.out)
        else:
            raise Refusal(f"{verb!r} is not a stage this build runs")

    return work


def _generate(
    args: argparse.Namespace,
    wired: Wiring,
    targets: Sequence[str],
    flows: Mapping[str, Flow],
) -> list[str]:
    """Assemble every prompt in the batch, and only then reach for the endpoint.

    **The whole batch, before anything is acquired.** Assembly is free and
    rendering is not, so a malformed sheet should cost nothing rather than a boot
    and several minutes of waiting -- and doing the batch first is what turns that
    from a per-item saving into a guarantee. Interleaving them would rent a
    machine and then discover the third sheet was broken.
    """
    ready: list[tuple[Run, str]] = []
    # Collected alongside `across`'s, not raised: `prepare` already tried every
    # flow, so one run's broken sheet is a refusal to report at the end rather
    # than a reason its sibling flows go unrendered.
    broken: list[str] = []

    def assemble_one(identifier: str) -> None:
        run = _run_for(identifier, wired)
        assembled, refusals = prepare(run, flows)
        broken.extend(refusals)
        for flow, path in assembled.items():
            print(f"{run.id}: assembled {flow}/{path.name}", file=wired.out)
            ready.append((run, flow))

    refused = across(list(targets), assemble_one) + broken
    if wired.client is None:
        return refused

    client = _Reporting(wired.client)

    def render_one(pair: tuple[Run, str]) -> None:
        run, flow = pair
        produced = render(
            run,
            flows[flow],
            client,
            count=args.count,
            seeds=args.seeds,
            rng=wired.rng,
        )
        for made in produced:
            print(f"{run.id}: rendered {flow}/{made.image.name}", file=wired.out)
        if not produced:
            print(f"{run.id}: {flow} is already rendered", file=wired.out)

    return refused + across(ready, render_one)


@dataclass(frozen=True)
class _Reporting:
    """The transport, with every network error turned into a named refusal."""

    inner: ComfyTransport

    def upload_image(self, path: str) -> str:
        """Upload a photograph, refusing legibly if the endpoint is unreachable."""
        with _reported():
            return self.inner.upload_image(path)

    def submit(self, workflow: Workflow) -> str:
        """Queue a graph, refusing legibly if the endpoint is unreachable."""
        with _reported():
            return self.inner.submit(workflow)

    def history(self, prompt_id: str) -> dict[str, Any]:
        """Poll a queued graph, refusing legibly if the endpoint is unreachable."""
        with _reported():
            return self.inner.history(prompt_id)

    def view(self, image: Image) -> bytes:
        """Download one render, refusing legibly if the endpoint is unreachable."""
        with _reported():
            return self.inner.view(image)


@contextmanager
def _reported() -> Iterator[None]:
    """Turn a transport-level network error into a `Refusal` naming the remedy.

    `Unreachable` rather than a bare `Refusal`, because nothing that reaches
    here says anything about the graph: the pod went away, the tunnel closed, or
    it was never opened. Every caller that only reports a refusal is unaffected;
    the one that writes an error record records this as transient (v0.13 R7).
    """
    try:
        yield
    except (urllib.error.URLError, OSError) as unreachable:
        raise Unreachable(
            f"the rendering endpoint could not be reached ({unreachable}); "
            "bring a pod up with `bash infra/up.sh`, open the tunnel, and pass "
            "its address with `--server` -- or drop `--server` to assemble the "
            "prompts and stop"
        ) from unreachable


def _say(wired: Wiring, run: Run, verb: str, written: Path | None) -> None:
    """Report what a stage did, including that it was already complete."""
    if written is None:
        print(f"{run.id}: {verb} is already complete", file=wired.out)
    else:
        print(f"{run.id}: {verb} wrote {written.name}", file=wired.out)


def main(argv: Sequence[str] | None = None) -> int:
    """Parse the pipeline's arguments and dispatch to the named stage."""
    args = build_parser().parse_args(argv)
    try:
        return dispatch(args, wiring(args))
    except Refusal as refused:
        print(f"refused: {refused}", file=sys.stderr)
        return 1
