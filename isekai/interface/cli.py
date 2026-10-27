"""The pipeline's command line: `python -m isekai <verb>`.

**The only surface.** There is one render path, and this is its entry point.
Four separate scripts were rejected for the same reason one parser was chosen: it
would multiply the import guard by four and give argument parsing four places to
drift.

**Schema migration is not a verb.** Every run file kind is at its first version,
so an upgrade command would be a dispatch table with no entries and its refusal
would be unreachable -- nothing writes a later one.

    import        clean photographs into a collection's sources/
    assign        give a source a flow's empty directory, or take an empty one away
    caption   (1) a photograph in, prose out
    tag       (1) a photograph in; the WD14 tags, then the hosted tags, out
    sheet     (2) the WD14 tag list in, a sheet of canonical tags out
    review    (3) the machine's sheet copied somewhere a human may edit it
    approve   (3) validate the edited sheet and rename it
    revise    (3) a rendered image's approval copied into a draft, its seed kept
    generate  (4) assemble every prompt locally, then render
    render    (4) one whole render session on a rented GPU, torn down on every exit
    show          print a run's artifacts, what produced each, and its failures
    ui        (3) serve the review surface for the library's collections
    compare       write a page of every run's photograph beside its renders

**`import` fills a collection, `assign` ticks a flow, `show` inspects a run, `ui`
serves a surface, `compare` writes a page, and every other verb runs a stage.**
The stage verbs and `assign` take `--flow` repeatably; `ui`, `show` and
`compare` take none -- the surface serves every flow it offers, and the others
report every flow the runs already hold. `show` reads a run and decides
nothing, and `ui` is the second front end rather than a client of the first --
it calls `wiring` and the stage functions directly, exactly as this module does,
so neither surface is privileged and neither goes through the other.

**`isekai/__main__.py` is a shim over this file.** `runpy` pins where the entry
point's *path* is; it does not pin where the parser lives, and a package's largest
interface surface has no business being the one module outside the filing
scheme. Everything the verb line does is here.

Stdlib only, and held to that by a subprocess guard that imports the entry point
with site-packages off the path.
"""

import argparse
import json
import shlex
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import TextIO, TypeVar

from isekai.boundary.comfy import TransportFailure
from isekai.boundary.wd14 import LocalTagger
from isekai.foundation.artifacts import DRAFT_FILE, SEED_RANGE, SESSION_ID
from isekai.foundation.artifacts import read as read_artifact
from isekai.foundation.flow import Flow, load_flow, tracked_flows
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    FRAME_NAME,
    RUNS_ROOT,
    Run,
    across,
    assign,
    find_run,
    open_run,
    rendered_at,
)
from isekai.interface.compare_view import write_page
from isekai.interface.drafting import draft_across
from isekai.interface.render import run_session
from isekai.interface.run_view import report
from isekai.interface.wiring import Wiring, trackable, wiring
from isekai.pipeline.caption import caption
from isekai.pipeline.generate import (
    STAGE_RENDER,
    Render,
    prepare,
    read_runtime,
    refuse_out_of_step,
    render,
    source_seeds,
)
from isekai.pipeline.importing import (
    SOURCES,
    Staged,
    cancel,
    commit,
    read,
    stage,
    upload_limit,
)
from isekai.pipeline.review import (
    Revision,
    approve,
    discard,
    drafted_from,
    refuse_revisions,
    review,
    revise,
)
from isekai.pipeline.review import cancel as cancel_approval
from isekai.pipeline.sheet import sheet
from isekai.pipeline.tagging import tag_hosted, tag_wd14
from isekai.shared.field_map import FieldMap
from isekai.shared.vocabulary import Vocabulary

# One line of prose per verb, used for both the subcommand list and its own help,
# so the two cannot disagree about what a stage does.
T = TypeVar("T")

VERBS: tuple[tuple[str, str], ...] = (
    ("import", "clean photographs and add them to a collection's sources/"),
    ("assign", "give each source a flow's empty directory, or remove an empty one"),
    ("caption", "read a photograph into prose"),
    ("tag", "score a photograph with WD14, then list the JoyCaption tags"),
    ("sheet", "fill a sheet of canonical tags from the WD14 tag list"),
    ("review", "copy a sheet somewhere a human may edit it"),
    ("approve", "validate an edited sheet and mark it approved"),
    ("revise", "copy the approval a rendered image came from into a draft"),
    ("generate", "assemble the prompts for a run, then render them"),
    ("render", "run a whole render session on a rented GPU, then tear it down"),
    ("show", "print a run's artifacts, versions, producers and failures"),
    ("ui", "serve the app over the library of collections"),
    ("compare", "write a page of each run's photograph beside its renders"),
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
    if seed not in SEED_RANGE:
        raise argparse.ArgumentTypeError(
            f"{seed} is outside the sampler's unsigned 64-bit range"
        )
    return seed


def _positive(below_one: str) -> Callable[[str], int]:
    """Return a parser of a positive integer, refusing one below 1 with `below_one`."""

    def parse(value: str) -> int:
        try:
            whole = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{value!r} is not an integer") from None
        if whole < 1:
            raise argparse.ArgumentTypeError(below_one)
        return whole

    return parse


# A render count: every one of them costs money.
_count = _positive("a render count below 1 renders nothing")
_seconds = _positive("a session limit below 1s ends at once")


def _session_id(value: str) -> str:
    """Return `value` as a session's id, refusing one that is not a start in UTC.

    The id names a file, so nothing but the one shape reaches a path.
    e.g. "20261024T091200Z" -> "20261024T091200Z"
    """
    if SESSION_ID.fullmatch(value) is None:
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a start in UTC, e.g. 20261024T091200Z"
        )
    return value


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

    # `compare` takes a collection directory instead: its runs root is the collection's
    # `runs/`, so a second way to name it could only disagree. `render` takes
    # its runs root first, and every run under it. `ui` serves the library, and
    # `revise` takes images, whose paths name their runs.
    for name in (
        name
        for name in made
        if name not in ("compare", "import", "render", "revise", "ui")
    ):
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
        # is what keeps a run on another disk expressible (D18).
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
    for name in ("assign", "caption", "tag", "sheet", "review", "approve", "generate"):
        made[name].add_argument(
            "--flow",
            action="append",
            dest="flows",
            required=True,
            metavar="FLOW",
            help="a flow to act on; repeatable, and required",
        )
    made["assign"].add_argument(
        "--remove",
        action="store_true",
        help="delete each flow's directory instead, refusing one that holds work",
    )
    # A verb that reads another flow reads only the one the operator names.
    made["approve"].add_argument(
        "--from",
        dest="source",
        default=None,
        metavar="FLOW",
        help="copy this flow's latest approval under each --flow instead of a draft",
    )
    made["approve"].add_argument(
        "--cancel",
        action="store_true",
        help="turn each flow's newest approval back into its draft instead, "
        "deleting a copy and refusing one anything was made from",
    )
    # The job runner's channel: a line per item it can parse, the prose kept apart.
    for name in ("caption", "tag", "sheet", "generate"):
        made[name].add_argument(
            "--progress",
            choices=["json"],
            default=None,
            help="print a JSON line per item's start and end; prose goes to stderr",
        )
    made["render"].add_argument(
        "--progress",
        choices=["json"],
        default=None,
        help="print a JSON line per step of the session; prose goes to stderr",
    )
    for name in ("caption", "tag", "sheet", "review"):
        made[name].add_argument(
            "--new-version",
            action="store_true",
            help="write the next numbered artifact instead of doing nothing",
        )
    made["review"].add_argument(
        "--discard",
        action="store_true",
        help="delete each flow's waiting draft instead, refusing an approval",
    )
    made["review"].add_argument(
        "--from",
        dest="source",
        default=None,
        metavar="FLOW",
        help="draft each --flow from this flow's approval, its own fields from "
        "its sheet",
    )
    made["review"].add_argument(
        "--version",
        dest="approval",
        type=int,
        default=None,
        metavar="N",
        help="the approval --from drafts from (default its newest)",
    )

    made["revise"].add_argument(
        "images",
        nargs="+",
        type=Path,
        help="rendered images, each <run>/<flow>/outputs/<NNN>/<seed>.png",
    )
    made["revise"].set_defaults(photos=[], runs=RUNS_ROOT)

    # No flow, input or runs root: the app serves every collection of the library
    # `ISEKAI_LIBRARY` names, and its page selects one (D1).
    made["ui"].add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"the loopback port to serve on (default {DEFAULT_PORT})",
    )
    made["ui"].set_defaults(photos=[], runs=RUNS_ROOT)

    made["import"].add_argument(
        "--collection",
        type=Path,
        required=True,
        help=(
            "the collection directory; made when absent, else the files join its "
            "sources/"
        ),
    )
    made["import"].add_argument(
        "files", nargs="+", type=Path, help="the photographs to clean and add"
    )
    made["import"].set_defaults(photos=[], runs=RUNS_ROOT)

    made["compare"].add_argument(
        "collection",
        type=Path,
        help=(
            "the collection directory: the one holding runs/, where the page is written"
        ),
    )
    # Every namespace keeps one shape; `compare` reads its runs from the collection.
    made["compare"].set_defaults(photos=[], runs=RUNS_ROOT)

    made["render"].add_argument(
        "runs",
        type=Path,
        help="the collection's runs/; every run under it is rendered",
    )
    made["render"].add_argument(
        "requests",
        nargs="*",
        metavar="<flow>=<count|source>",
        help=(
            "a flow and how many seeds it draws, or the flow whose seeds it takes; "
            "with none, every approval short of its count renders what it lacks"
        ),
    )
    made["render"].add_argument(
        "--limit",
        type=_seconds,
        default=None,
        metavar="SECONDS",
        help=(
            "end the session after this many seconds, at most gpunit.toml's "
            "ceiling; without it, the limit is estimated from the work"
        ),
    )
    made["render"].add_argument(
        "--session",
        type=_session_id,
        default=None,
        metavar="ID",
        help=(
            "name the session's record <collection>/sessions/<ID>.json; without it, "
            "the session's start in UTC names it"
        ),
    )
    made["render"].set_defaults(photos=[])

    # Mutually exclusive at parse time, so asking for both is refused before any
    # work begins rather than discovered on a rented machine. One verb explores
    # and the other reproduces, and combining them has no meaning (D13).
    render = made["generate"].add_mutually_exclusive_group()
    render.add_argument(
        "--count",
        type=_count,
        default=None,
        help=(
            "how many renders per photograph per flow, seeds drawn (default: the "
            "approval's count, else 1)"
        ),
    )
    render.add_argument(
        "--seed",
        type=_seed,
        action="append",
        dest="seeds",
        default=None,
        help="render exactly this seed; repeatable, and not combinable with --count",
    )
    render.add_argument(
        "--seeds-from",
        dest="seeds_from",
        default=None,
        metavar="FLOW",
        help="render this flow's latest seeds for each run; not with the others",
    )
    # The free check for a source rendered by count earlier in the same session,
    # whose seeds do not exist until the pod is up: it renders nothing.
    render.add_argument(
        "--in-step-with",
        dest="in_step_with",
        default=None,
        metavar="FLOW",
        help=(
            "check that each copy of this flow's approval is of its latest, and "
            "render nothing; for a source that renders first in the same session"
        ),
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


def _ui(args: argparse.Namespace, wired: Wiring) -> int:
    """Serve the app over the library, blocking until the operator stops it.

    **The import is inside this function, and it is load-bearing.**
    `tests/test_pipeline_cli.py` imports the entry point with `-S`, site-packages
    off the path, and walks this module's module-level imports: nothing there may
    need a wheel, and `isekai.interface.ui` reaches FastAPI. A top-level import
    here would put a web framework on `python -m isekai`'s import graph and turn
    that guard red for every verb, including each one that never serves anything.
    """
    from isekai.interface.ui import serve

    return serve(wired, port=int(args.port))


def _import(args: argparse.Namespace, wired: Wiring) -> int:
    """Read each file into the collection's staging, commit what is clean, and report.

    No file that is not cleaned is imported: that choice is the page's, one file
    at a time.
    """
    collection = Path(args.collection).resolve()
    if trackable(collection.parent):
        raise Refusal(
            f"--collection {collection} is inside this repository and outside its "
            "ignored .data/ root; a collection holds copies of photographs, so it "
            "would be one `git add` from being published -- point --collection "
            "under .data/ or at a directory outside the repository"
        )
    staging = stage(collection.parent)
    limit = upload_limit()
    staged: list[Staged] = []
    try:
        refused = across(
            list(args.files), lambda file: staged.append(read(file, staging, limit))
        )
        for item in staged:
            print(_staged_line(item), file=wired.out)
        if any(item.state in ("ready", "converted") for item in staged):
            add = (collection / SOURCES).is_dir()
            done = commit(staging, collection.parent, collection.name, add=add)
            for name in done.skipped:
                print(f"{name}: skipped, a source holds its bytes", file=wired.out)
            if done.written:
                print(
                    f"{collection.name}: imported {', '.join(done.written)}",
                    file=wired.out,
                )
    except Refusal as uncommitted:
        refused.append(str(uncommitted))
    finally:
        cancel(staging)
    for message in refused:
        print(f"refused: {message}", file=wired.err)
    return 1 if refused else 0


def _staged_line(item: Staged) -> str:
    """Return one file's result. e.g. "a.jpg: not cleaned, carries XMP; left out"."""
    if item.state == "not cleaned":
        return f"{item.name}: not cleaned, carries {', '.join(item.carries)}; left out"
    if item.state == "skipped":
        return f"{item.name}: skipped, its bytes are already read"
    return f"{item.name}: {item.state}"


def _revise(images: Sequence[Path], wired: Wiring) -> int:
    """Write a revision for every image, or, when any is refused, none."""
    refused: list[str] = []
    located: list[tuple[Path, Revision]] = []
    for image in images:
        try:
            located.append((image, rendered_at(image)))
        except Refusal as unrendered:
            refused.append(f"{image}: {unrendered}")
    answers = refuse_revisions(located)
    refused += [
        f"{image}: {answer}"
        for (image, _), answer in zip(located, answers, strict=True)
        if answer is not None
    ]
    if not refused:
        for _, one in located:
            draft = revise(*one)
            print(f"revise wrote {draft.relative_to(draft.parents[3])}", file=wired.out)
    for message in refused:
        print(f"refused: {message}", file=wired.err)
    return 1 if refused else 0


def _run_for(identifier: str, wired: Wiring) -> Run:
    """Return the run an argument names: a photograph to open, or a run to resume."""
    named = _named(identifier, wired)
    return named if isinstance(named, Run) else open_run(named, wired.runs_root)


def _existing_run(identifier: str, wired: Wiring) -> Run | None:
    """Return the run an argument names, as `_run_for` does, but never open one."""
    named = _named(identifier, wired)
    return named if isinstance(named, Run) else find_run(named, wired.runs_root)


def _named(identifier: str, wired: Wiring) -> Run | Path:
    """Return the run an argument names by its id, or the photograph it names.

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
            f"{wired.runs_root}; give the path to a JPEG or PNG, or the name of "
            f"a run directory under {wired.runs_root}"
        )
    return photo


def _require_tracked(names: Sequence[str], wired: Wiring) -> None:
    """Refuse the names that are no tracked flow, naming the flows there are."""
    tracked = tracked_flows(wired.flows_dir)
    unknown = [name for name in names if name not in tracked]
    if unknown:
        raise Refusal(
            f"{', '.join(unknown)}: not a flow this build tracks; the flows it "
            f"carries are {', '.join(tracked) or '(none)'}"
        )


def _flows_for(args: argparse.Namespace, wired: Wiring) -> dict[str, Flow]:
    """Return the flows this invocation acts on, loaded, refusing an untracked one.

    Resolved once, at selection, so an untracked name or a broken manifest is
    caught before any run is opened -- rather than at the flow's first use, which
    on `generate` is after a photograph has been uploaded. The parser has already
    refused a stage verb naming none, and `show` names none by design, so an empty
    selection is the inspection verb rather than a missing flag.
    """
    named: list[str] = list(getattr(args, "flows", None) or [])
    _require_tracked(named, wired)
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
    # without renting anything. The serving verb takes no flow at all.
    try:
        if verb == "ui":
            return _ui(args, wired)
        if verb == "import":
            return _import(args, wired)
        if verb == "compare":
            print(write_page(args.collection, wired.flows_dir), file=wired.out)
            return 0
        if verb == "render":
            return run_session(args, wired, _dispatch_argv)
        if verb == "revise":
            return _revise(args.images, wired)
        flows = _flows_for(args, wired)
        if verb == "approve":
            if args.cancel and args.source is not None:
                raise Refusal(
                    "--cancel takes an approval back and --from copies one; drop "
                    f"`--from {args.source}` or `--cancel` from the command"
                )
        if verb == "review":
            _refuse_review_options(args)
        if verb in ("approve", "review"):
            _refuse_bad_source(args.source, "from", flows, wired)
        if verb == "generate":
            _refuse_bad_source(args.seeds_from, "seeds-from", flows, wired)
            _refuse_bad_source(args.in_step_with, "in-step-with", flows, wired)
            if args.in_step_with is not None and args.server is not None:
                raise Refusal(
                    "--in-step-with checks before the session and renders nothing; "
                    f"drop `--server {args.server}` from the command"
                )
        if verb == "tag":
            _require_tagged(flows, targets, args.runs)
    except Refusal as unselectable:
        print(f"refused: {unselectable}", file=wired.err)
        return 1
    if verb == "generate":
        refused = _generate(args, wired, targets, flows)
    else:
        # Refusals a verb collects without abandoning the photograph, reported
        # after `across`'s the way `_generate` reports `broken`.
        collected: list[str] = []
        work = _per_item(verb, args, wired, flows, collected)
        refused = across(targets, work) + collected
    for message in refused:
        print(f"refused: {message}", file=wired.err)
    return 1 if refused else 0


def _dispatch_argv(argv: list[str], wired: Wiring) -> int:
    """Run one verb line on `wired`, as `render` runs `generate` for each flow."""
    return dispatch(build_parser().parse_args(argv), wired)


def _refuse_bad_source(
    source: str | None, flag: str, flows: Mapping[str, Flow], wired: Wiring
) -> None:
    """Refuse a named source that is no tracked flow, or is one of `flows`.

    A flow is not its own source: the pair is compared only while they differ.
    """
    if source is None:
        return
    _require_tracked([source], wired)
    if source in flows:
        raise Refusal(
            f"{source}: a flow is not its own source; drop `--{flag} {source}` or "
            f"`--flow {source}` from the command"
        )


def _refuse_review_options(args: argparse.Namespace) -> None:
    """Refuse `--from` beside `--discard` or `--new-version`, or `--version` alone."""
    if args.source is None:
        if args.approval is not None:
            raise Refusal(
                f"--version names the approval --from drafts from; add `--from "
                f"FLOW` or drop `--version {args.approval}` from the command"
            )
        return
    for flag, given in (
        ("--discard", args.discard),
        ("--new-version", args.new_version),
    ):
        if given:
            raise Refusal(
                f"--from drafts from another flow and {flag} does not; drop "
                f"`--from {args.source}` or `{flag}` from the command"
            )


def _require_tagged(
    flows: Mapping[str, Flow], targets: Sequence[str], runs: Path
) -> None:
    """Refuse a `tag` invocation naming any flow that declares no tagger.

    Before any identifier, so no flow named with it is tagged: a skip would report
    success for a flow that wrote nothing (D31). With every flow untagged, "drop
    `--flow`" would leave argparse nothing to accept, so the refusal names `sheet`
    instead.
    """
    untagged = [name for name, flow in flows.items() if not flow.tagger]
    if untagged and len(untagged) == len(flows):
        root = "" if runs == RUNS_ROOT else f" --runs {shlex.quote(str(runs))}"
        photos = " ".join(shlex.quote(target) for target in targets) or "<photo>"
        raise Refusal(
            f"`tag` has nothing to do: {', '.join(untagged)} declare "
            f'`"tagger": false`; run `python -m isekai sheet --flow '
            f"{' --flow '.join(untagged)}{root} {photos}` next"
        )
    if untagged:
        raise Refusal(
            "; ".join(
                f'{name}\'s manifest declares `"tagger": false`, so `tag` has '
                f"nothing to do for it; drop `--flow {name}` from the command"
                for name in untagged
            )
        )


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


def _once(read: Callable[[], T]) -> Callable[[], T]:
    """Return `read`, answered at most once: its answer or its refusal is kept.

    A refusal is the build's or the endpoint's, not a photograph's, so meeting
    it again would redo the work to learn nothing. A transient
    transport failure is the exception: it is raised and not kept, since the
    endpoint may answer the next ask, and keeping it would refuse every later
    photograph in the session and spend each one's render budget.
    """
    outcome: list[T | Refusal] = []

    def reading() -> T:
        if not outcome:
            try:
                outcome.append(read())
            except TransportFailure as failed:
                if failed.kind == "transient":
                    raise
                outcome.append(failed)
            except Refusal as refused:
                outcome.append(refused)
        kept = outcome[0]
        if isinstance(kept, Refusal):
            raise kept
        return kept

    return reading


def _per_item(
    verb: str,
    args: argparse.Namespace,
    wired: Wiring,
    flows: Mapping[str, Flow],
    collected: list[str],
) -> Callable[[str], None]:
    """Return the work one identifier gets, with everything run-independent done.

    `collected` takes the refusals that must not abandon the rest of a
    photograph's work: one per flow, and `tag`'s one per tagger.

    The flows a verb acts on are a property of the invocation, not of the
    photograph, so they are resolved once by the caller rather than re-read from
    disk per identifier. Every stage but the inspection one is per flow, because
    the flow is what supplies what the stage reads: its briefing, its schema and
    its dials. The vocabulary is resolved at most once for the same reason and
    lazily for the old one: parsing the 308 KB tag list costs ~50 ms, and only
    two verbs need it at all.
    """
    new_version = bool(getattr(args, "new_version", False))
    opening: list[Callable[[], LocalTagger]] = []
    reporter = _Reporter(
        wired.out, wired.err, getattr(args, "progress", None) == "json"
    )

    @cache
    def vocabulary() -> Vocabulary:
        """Return this invocation's vocabulary, reading it at most once."""
        return wired.vocabulary()

    @cache
    def field_map() -> FieldMap:
        """Return this invocation's field map, reading it at most once.

        Memoised beside the vocabulary and for its reason: the table is held
        against the vocabulary at load, so reading it per photograph would
        re-run four whole-table checks for every input of an invocation. It is handed
        the memoised vocabulary rather than finding its own.
        """
        return wired.field_map(vocabulary())

    def tagger(flow: Flow) -> Callable[[], LocalTagger]:
        """Return a thunk that opens this invocation's local tagger, once.

        **A thunk rather than a value, and one slot rather than one per flow.**

        Lazy, because opening it hashes 467 MB and loads a graph: an invocation whose
        lists are all already written must not pay for that to write nothing,
        and a completed run must still resume on a machine that has since
        emptied `models/`. `vocabulary()` above is a thunk for exactly this
        reason and says so.

        One slot, because `wiring.tagger_for` takes a `Flow` and reads nothing
        from it -- no manifest key names the local tagger's model (D31).
        Keying the memo by flow would open the same graph once
        per flow named on one command line and hold every copy for the rest of
        the invocation. The parameter stays because the seam's shape is per flow
        and the day one of them selects a different tagger is the day this needs
        a key; giving it one before then buys two sessions and no behaviour.
        """
        resolve = _seam(wired.tagger, "tagger", "scores the photograph")
        if not opening:
            # A refusal is kept too, so the 467 MB hash is not re-run to meet it.
            opening.append(_once(lambda: resolve(flow)))
        return opening[0]

    def work(identifier: str) -> None:
        if verb == "assign":
            _assign(identifier, bool(args.remove), wired, list(flows), collected)
            return
        try:
            run = _run_for(identifier, wired)
        except Refusal as unopened:
            for name in flows:
                reporter.item(identifier, name, verb, "refused", str(unopened))
            raise
        if verb == "show":
            for line in report(run, wired.flows_dir):
                print(line, file=wired.out)
            return
        step: Callable[[str], None]
        if verb == "caption":

            def caption_flow(name: str) -> None:
                flow = flows[name]
                # **Resolved per flow, not once per invocation.** One command
                # naming two flows on two models would otherwise resolve one
                # reader and hand it to both, and the provenance one of the two
                # artifacts records would be false.
                reader = _seam(wired.reader, "reader", "reads the photograph")(flow)
                _say(
                    reporter,
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

            step = caption_flow
        elif verb == "tag":

            def tag_flow(name: str) -> None:
                flow = flows[name]

                def hosted() -> None:
                    tagger_for = _seam(
                        wired.hosted_tagger, "hosted tagger", "tags the photograph"
                    )
                    written = tag_hosted(
                        run, name, tagger_for(flow), new_version=new_version
                    )
                    _say(reporter, run, "tags", written)

                # Each tagger's refusal is collected on its own, so neither costs
                # the other its list. WD14 first: it is the sheet's input and
                # reaches no network (D1).
                steps: tuple[Callable[[], None], ...] = (
                    lambda: _say(
                        reporter,
                        run,
                        "wd14",
                        tag_wd14(run, name, tagger(flow), new_version=new_version),
                    ),
                    hosted,
                )
                collected.extend(across(steps, lambda step: step()))

            step = tag_flow
        elif verb == "sheet":

            def sheet_flow(name: str) -> None:
                flow = flows[name]
                written, warnings = sheet(
                    run,
                    name,
                    flow.schema,
                    vocabulary(),
                    field_map(),
                    tagged=flow.tagger,
                    flow_digest=flow.digest,
                    new_version=new_version,
                )
                for warning in warnings:
                    print(f"warning: {warning}", file=wired.err)
                _say(reporter, run, "sheet", written)

            step = sheet_flow
        elif verb == "review":

            def review_flow(name: str) -> None:
                if args.discard:
                    gone = discard(run, name)
                    reporter.say(f"{run.id}: review discarded {name}/{gone.name}")
                    return
                if args.source is not None:
                    drafted = draft_across(
                        run,
                        flows[name],
                        args.source,
                        args.approval,
                        vocabulary,
                        field_map,
                    )
                    origin = drafted_from(read_artifact(drafted, DRAFT_FILE))
                    approval = "" if origin is None else f" v{origin['approval']}"
                    reporter.say(
                        f"{run.id}: review drafted {name}/{drafted.name} from "
                        f"{args.source}{approval}"
                    )
                    return
                _say(
                    reporter, run, "review", review(run, name, new_version=new_version)
                )

            step = review_flow
        elif verb == "approve":

            def approve_flow(name: str) -> None:
                if args.cancel:
                    left = cancel_approval(run, name)
                    back = "a copy, deleted" if left is None else f"back to {left.name}"
                    reporter.say(f"{run.id}: approve cancelled {name}, {back}")
                    return
                written, warnings = approve(
                    run,
                    name,
                    flows[name].schema,
                    vocabulary(),
                    source=args.source,
                )
                for warning in warnings:
                    print(f"warning: {warning}", file=wired.err)
                _say(reporter, run, "approve", written)

            step = approve_flow
        else:
            raise Refusal(f"{verb!r} is not a stage this build runs")

        def reported(name: str) -> None:
            """Run `step` for one flow between its `start` and its end."""
            reporter.item(run.id, name, verb, "start")
            before = len(collected)
            try:
                step(name)
            except Refusal as refused:
                reporter.item(run.id, name, verb, "refused", str(refused))
                raise
            # `tag` collects each tagger's refusal rather than raising it.
            if len(collected) > before:
                reporter.item(
                    run.id, name, verb, "refused", "; ".join(collected[before:])
                )
            else:
                reporter.item(run.id, name, verb, "done")

        # Each flow's refusal is collected on its own, so one flow's does not cost
        # the input its other flows.
        collected.extend(across(list(flows), reported))

    return work


def _assign(
    identifier: str,
    remove: bool,
    wired: Wiring,
    flows: Sequence[str],
    collected: list[str],
) -> None:
    """Assign each flow to the run `identifier` names, or remove each empty one.

    Removing opens no run: a source with none has no flow to remove.
    """
    run = _existing_run(identifier, wired) if remove else _run_for(identifier, wired)
    if run is None:
        for name in flows:
            print(f"{identifier}: {name} is not assigned", file=wired.out)
        return
    collected.extend(
        across(list(flows), lambda name: _assign_one(run, name, remove, wired))
    )


def _assign_one(run: Run, flow: str, remove: bool, wired: Wiring) -> None:
    """Assign or remove one flow for `run`, and say which happened."""
    changed = assign(run, flow, remove=remove)
    if remove:
        done = f"removed {flow}" if changed else f"{flow} is not assigned"
    else:
        done = f"assigned {flow}" if changed else f"{flow} is already assigned"
    print(f"{run.id}: {done}", file=wired.out)


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
    reporter = _Reporter(
        wired.out, wired.err, getattr(args, "progress", None) == "json"
    )
    # The seeds each run takes from the source flow, when one is named.
    borrowed: dict[str, list[int]] = {}
    source_suffix = (
        load_flow(args.seeds_from, wired.flows_dir).output_suffix
        if args.seeds_from is not None
        else ""
    )
    # Collected alongside `across`'s, not raised: `prepare` already tried every
    # flow, so one run's broken sheet is a refusal to report at the end rather
    # than a reason its sibling flows go unrendered.
    broken: list[str] = []

    def assemble_one(identifier: str) -> None:
        run = _run_for(identifier, wired)
        assembled, refusals = prepare(run, flows)
        broken.extend(refusals)
        if args.seeds_from is not None:
            group, borrowed[run.id] = source_seeds(
                run, args.seeds_from, source_suffix, list(flows)
            )
            for flow in assembled:
                refuse_out_of_step(run, flow, args.seeds_from, group)
        if args.in_step_with is not None:
            for flow in assembled:
                refuse_out_of_step(run, flow, args.in_step_with)
        for flow, path in assembled.items():
            reporter.say(f"{run.id}: assembled {flow}/{path.name}")
            ready.append((run, flow))

    refused = across(list(targets), assemble_one) + broken
    client = wired.client
    if client is None or args.in_step_with is not None:
        return refused
    # One report per session, read only when a render will run.
    ran_on = _once(lambda: read_runtime(client))

    def render_one(pair: tuple[Run, str]) -> None:
        run, flow = pair

        def landed(made: Render) -> None:
            reporter.say(f"{run.id}: rendered {flow}/{made.image.name}")
            # The seed as a string: a 64-bit seed is past what a page's number holds.
            version = int(made.image.parent.name)
            reporter.item(
                run.id,
                flow,
                STAGE_RENDER,
                "done",
                digest=run.digest,
                version=version,
                seed=str(made.seed),
            )

        produced = render(
            run,
            flows[flow],
            client,
            image=wired.image,
            runtime=ran_on,
            count=args.count,
            seeds=borrowed.get(run.id, args.seeds),
            seeds_from=args.seeds_from,
            rng=wired.rng,
            on_image=landed,
        )
        if not produced:
            reporter.say(f"{run.id}: {flow} is already rendered")

    return refused + across(ready, render_one)


@dataclass(frozen=True)
class _Reporter:
    """Where a verb's lines go: prose to `out`, or with `progress` JSON to `out`.

    e.g. {"run": "0d4b…_ada", "flow": "summon-anime-wai", "stage": "sheet",
    "state": "done"}
    """

    out: TextIO
    err: TextIO
    progress: bool

    def say(self, line: str) -> None:
        """Print a line meant for a person: on stderr while JSON holds stdout."""
        print(line, file=self.err if self.progress else self.out)

    def item(
        self,
        run: str,
        flow: str,
        stage: str,
        state: str,
        message: str | None = None,
        **more: str | int,
    ) -> None:
        """Print one item's `start`, `done` or `refused` line, when asked for JSON.

        `more` adds what the item names beyond its run and flow, as a render its seed.
        """
        if not self.progress:
            return
        line: dict[str, str | int] = {
            "run": run,
            "flow": flow,
            "stage": stage,
            "state": state,
            **more,
        }
        if message is not None:
            line["message"] = message
        # Flushed: a job reads this from a pipe, line by line, as it happens.
        print(json.dumps(line), file=self.out, flush=True)


def _say(reporter: _Reporter, run: Run, verb: str, written: Path | None) -> None:
    """Report what a stage did, including that it was already complete."""
    if written is None:
        reporter.say(f"{run.id}: {verb} is already complete")
    else:
        reporter.say(f"{run.id}: {verb} wrote {written.name}")


def main(argv: Sequence[str] | None = None) -> int:
    """Parse the pipeline's arguments and dispatch to the named stage."""
    args = build_parser().parse_args(argv)
    try:
        return dispatch(args, wiring(args))
    except Refusal as refused:
        print(f"refused: {refused}", file=sys.stderr)
        return 1
