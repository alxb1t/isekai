"""The pipeline's command line: `python -m isekai <verb>`.

**The only surface.** There is one render path, and this is its entry point.
Four separate scripts were rejected for the same reason one parser was chosen: it
would multiply the import guard by four and give argument parsing four places to
drift.

**`migrate` moves a layout, not a schema.** Every run file kind is at its first
version, so nothing upgrades one; `migrate` copies a run's per-flow description
into `photo/` (D17).

    import        clean photographs into a collection's sources/
    assign        give a source a flow's empty directory, or take an empty one away
    caption   (1) a photograph in, prose out
    tag       (1) a photograph in; the WD14 tags, then the hosted tags, out
    sheet     (2) the WD14 tag list in, a sheet of canonical tags out
    prepare   (1)(2) each photograph's tags, prose, then its cells' sheets, in turn
    review    (3) the machine's sheet copied somewhere a human may edit it
    approve   (3) validate the edited sheet and rename it
    draft     (3) a rendered image's approval copied into a flow's draft, its seed kept
    discard   (4) a render's image, its record and its thumbnails deleted
    generate  (4) assemble every prompt locally, then render
    render    (4) one whole render session on a rented GPU, torn down on every exit
    show          print a run's artifacts, what produced each, and its failures
    ui        (3) serve the review surface for the library's collections
    compare       write a page of every run's photograph beside its renders
    migrate       copy each run's per-flow description into photo/
    ink           cut a tattoo's photograph or image into a layer, free and local
    edit      (5) request an edit of a render from a composite, free and local

**`import` fills a collection, `assign` ticks a flow, `show` inspects a run, `ui`
serves a surface, `compare` writes a page, `migrate` copies a layout, and every
other verb runs a stage.** The stage verbs on a flow and `assign` take `--flow`
repeatably; `tag` and `caption` take no flow, since they describe the
photograph every flow reads (D17), `prepare` names each flow in a cell, and
`ui`, `show`, `compare` and `migrate` take none -- the surface serves every
flow it offers, and the others read every flow the runs already hold. `show`
reads a run and decides nothing, and `ui` is the second front end rather than a
client of the first -- it calls `wiring` and the stage functions directly,
exactly as this module does, so neither surface is privileged and neither goes
through the other.

**A verb is a row of `isekai/interface/verbs/`, declared once**: its name, summary,
arguments and run sit in the module of its family (D58). This file holds `ROWS`,
builds the parser from their arguments and dispatches to their runs. It keeps the
flow-stage verbs' per-item work, `assign`, `migrate`, and the runs of `render`
and `prepare`, which need what only this file holds.

**`isekai/__main__.py` is a shim over this file.** `runpy` pins where the entry
point's *path* is; it does not pin where the parser lives, and a package's largest
interface surface has no business being the one module outside the filing
scheme.

Stdlib only, and held to that by a subprocess guard that imports the entry point
with site-packages off the path.
"""

import argparse
import dataclasses
import shlex
import sys
from collections.abc import Callable, Mapping, Sequence
from functools import cache
from pathlib import Path
from typing import NoReturn, TypeVar

from isekai.boundary.wd14 import LocalTagger
from isekai.foundation.caption_config import load_caption_config
from isekai.foundation.flow import FLOWS_DIR, Flow, load_flow, tracked_flows
from isekai.foundation.migrate import migrate
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    FRAME_NAME,
    PHOTOGRAPH_VERBS,
    RUNS_ROOT,
    Run,
    across,
    assign,
    find_run,
)
from isekai.interface.drafting import (
    approve_across,
)
from isekai.interface.render import run_session
from isekai.interface.run_view import report
from isekai.interface.verbs import (
    APPROVE_ROW,
    ASSIGN_ROW,
    CAPTION_ROW,
    COMPARE_ROW,
    DISCARD_ROW,
    DRAFT_ROW,
    EDIT_ROW,
    GENERATE_ROW,
    IMPORT_ROW,
    INK_ROW,
    PREPARE_ROW,
    RENDER_ROW,
    REVIEW_ROW,
    SHEET_ROW,
    SHOW_ROW,
    TAG_ROW,
    UI_ROW,
    Reporter,
    Verb,
    generate_batch,
    once,
    require_tracked,
    run_for,
    run_or_photo,
    run_prepare,
    say,
)
from isekai.interface.wiring import Wiring, wiring
from isekai.pipeline.caption import caption
from isekai.pipeline.review import (
    approve,
    discard,
    review,
)
from isekai.pipeline.review import cancel as cancel_approval
from isekai.pipeline.sheet import sheet
from isekai.pipeline.tagging import tag_hosted, tag_wd14
from isekai.shared.field_map import FieldMap
from isekai.shared.vocabulary import Vocabulary

T = TypeVar("T")

# What each of the photograph's verbs writes, for its refusal of `--flow`.
_WRITES: Mapping[str, str] = {"caption": "prose", "tag": "tags"}


class _Verb(argparse.ArgumentParser):
    """A verb's parser, whose refusal of a missing `--flow` lists the tracked flows."""

    def error(self, message: str) -> NoReturn:
        """Exit 2 with `message`, naming the tracked flows when it names `--flow`."""
        if "--flow" in message:
            flows = ", ".join(tracked_flows(FLOWS_DIR)) or "(none)"
            message += f"; the flows this build tracks are {flows}"
        super().error(message)


def build_parser() -> argparse.ArgumentParser:
    """Return the pipeline's parser, with one subparser per verb."""
    parser = argparse.ArgumentParser(
        prog="python -m isekai",
        description="The staged pipeline: photograph -> tags -> sheet -> render.",
    )
    verbs = parser.add_subparsers(
        dest="verb", metavar="verb", required=True, parser_class=_Verb
    )
    made = {
        name: verbs.add_parser(name, help=summary, description=summary)
        for name, summary in VERBS
    }

    for row in ROWS:
        row.arguments(made[row.name])
    return parser


def _migrate_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `migrate`'s arguments to `parser`: it takes no photograph."""
    parser.add_argument(
        "--runs",
        type=Path,
        default=None,
        help=(
            "walk this runs root alone; without it, .data/runs and every "
            "collection's runs/ in the library"
        ),
    )
    parser.set_defaults(photos=[])


def _migrate(args: argparse.Namespace, wired: Wiring) -> int:
    """Copy each run's per-flow description into `photo/`, printing a line per run.

    `--runs` walks that root alone; without it, `RUNS_ROOT` when it is a directory,
    then each collection's `runs/` (D40). The library is imported here for `run_ui`'s
    reason: it is off `python -m isekai`'s import graph.
    """
    if args.runs is not None:
        roots = [wired.runs_root]
    else:
        from isekai.interface.ui import collection_runs

        roots = [*([RUNS_ROOT] if RUNS_ROOT.is_dir() else []), *collection_runs()]
    refused = False
    for root in roots:
        named = sorted(path.name for path in root.iterdir()) if root.is_dir() else []
        for name in (name for name in named if (root / name / FRAME_NAME).is_file()):
            where = f"{root.parent.name}/{root.name}/{name}"
            try:
                print(f"{where}: {migrate(Run(name, root / name))}", file=wired.out)
            except Refusal as unmigrated:
                refused = True
                print(f"{where}: refused: {unmigrated}", file=wired.err)
    return 1 if refused else 0


def _existing_run(identifier: str, wired: Wiring) -> Run | None:
    """Return the run an argument names, as `run_for` does, but never open one."""
    named = run_or_photo(identifier, wired)
    return named if isinstance(named, Run) else find_run(named, wired.runs_root)


def _flows_for(args: argparse.Namespace, wired: Wiring) -> dict[str, Flow]:
    """Return the flows this invocation acts on, loaded, refusing an untracked one.

    Resolved once, at selection, so an untracked name or a broken manifest is
    caught before any run is opened -- rather than at the flow's first use, which
    on `generate` is after a photograph has been uploaded. The parser has already
    refused a stage verb on a flow naming none, and `show`, `tag` and `caption`
    name none by design, so an empty selection is one of them rather than a
    missing flag.
    """
    named: list[str] = list(getattr(args, "flows", None) or [])
    require_tracked(named, wired)
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
        row = next((row for row in ROWS if row.name == verb), None)
        if row is not None and row.run is not None:
            return row.run(args, wired)
        if verb in PHOTOGRAPH_VERBS and args.flows:
            raise Refusal(_named_a_flow(args, targets))
        flows = _flows_for(args, wired)
        if verb == "approve":
            if args.cancel and args.source is not None:
                raise Refusal(
                    "--cancel takes an approval back and --from copies one; drop "
                    f"`--from {args.source}` or `--cancel` from the command"
                )
            _refuse_bad_source(args.source, "from", flows, wired)
        if verb == "generate":
            _refuse_bad_source(args.seeds_from, "seeds-from", flows, wired)
    except Refusal as unselectable:
        print(f"refused: {unselectable}", file=wired.err)
        return 1
    if verb == "generate":
        refused = generate_batch(args, wired, targets, flows)
    else:
        # Refusals a verb collects without abandoning the photograph, reported
        # after `across`'s the way `generate_batch` reports `broken`.
        collected: list[str] = []
        work = _per_item(verb, args, wired, flows, collected)
        refused = across(targets, work) + collected
    for message in refused:
        print(f"refused: {message}", file=wired.err)
    return 1 if refused else 0


def _dispatch_argv(argv: list[str], wired: Wiring) -> int:
    """Run one verb line on `wired`, as `render` runs `generate` for each flow.

    The line's own `--runs` is the runs root it is wired on: a session spans many.
    """
    args = build_parser().parse_args(argv)
    return dispatch(args, dataclasses.replace(wired, runs_root=args.runs))


def _render(args: argparse.Namespace, wired: Wiring) -> int:
    """Run `render`'s session, handing it `_dispatch_argv` to run each flow's line."""
    return run_session(args, wired, _dispatch_argv)


def _prepare(args: argparse.Namespace, wired: Wiring) -> int:
    """Run `prepare`, handing it `_per_item` for the work of each of its steps."""
    return run_prepare(args, wired, _per_item)


ROWS: tuple[Verb, ...] = (
    IMPORT_ROW,
    ASSIGN_ROW,
    CAPTION_ROW,
    TAG_ROW,
    SHEET_ROW,
    dataclasses.replace(PREPARE_ROW, run=_prepare),
    REVIEW_ROW,
    APPROVE_ROW,
    DRAFT_ROW,
    DISCARD_ROW,
    GENERATE_ROW,
    dataclasses.replace(RENDER_ROW, run=_render),
    SHOW_ROW,
    UI_ROW,
    COMPARE_ROW,
    Verb(
        "migrate",
        "copy each run's per-flow description into photo/",
        _migrate_arguments,
        _migrate,
    ),
    INK_ROW,
    EDIT_ROW,
)

# One line of prose per verb, used for both the subcommand list and its own help,
# so the two cannot disagree about what a stage does.
VERBS: tuple[tuple[str, str], ...] = tuple((row.name, row.summary) for row in ROWS)


def _refuse_bad_source(
    source: str | None, flag: str, flows: Mapping[str, Flow], wired: Wiring
) -> None:
    """Refuse a named source that is no tracked flow, or is one of `flows`.

    A flow is not its own source: the pair is compared only while they differ.
    """
    if source is None:
        return
    require_tracked([source], wired)
    if source in flows:
        raise Refusal(
            f"{source}: a flow is not its own source; drop `--{flag} {source}` or "
            f"`--flow {source}` from the command"
        )


def _named_a_flow(args: argparse.Namespace, targets: Sequence[str]) -> str:
    """Return the refusal of a photograph's verb named with `--flow`, and its command.

    The command repeats `--runs` and `--new-version` where given, and the
    identifiers; `--progress` is a job's, and is not repeated.
    e.g. `caption --flow f a.jpg` -> "`caption` takes no --flow: …; run
    `python -m isekai caption a.jpg`"
    """
    verb = str(args.verb)
    root = "" if args.runs == RUNS_ROOT else f" --runs {shlex.quote(str(args.runs))}"
    again = " --new-version" if args.new_version else ""
    photos = " ".join(shlex.quote(target) for target in targets) or "<photo>"
    return (
        f"`{verb}` takes no --flow: it writes the photograph's {_WRITES[verb]}, "
        f"which every flow reads; run `python -m isekai {verb}{root}{again} {photos}`"
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
    disk per identifier. `tag` and `caption` run once per photograph and name no
    flow, since every flow reads the one description (D17); every other stage
    runs per flow, because the flow is what supplies what it reads: its schema
    and its dials. The vocabulary is resolved at most once for the same reason and
    lazily for the old one: parsing the 308 KB tag list costs ~50 ms, and only
    two verbs need it at all.
    """
    new_version = bool(getattr(args, "new_version", False))
    opening: list[Callable[[], LocalTagger]] = []
    reporter = Reporter(wired.out, wired.err, getattr(args, "progress", None) == "json")

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

    def tagger() -> Callable[[], LocalTagger]:
        """Return a thunk that opens this invocation's local tagger, once.

        Lazy, because opening it hashes 467 MB and loads a graph: an invocation whose
        lists are all already written must not pay for that to write nothing,
        and a completed run must still resume on a machine that has since
        emptied `models/`. `vocabulary()` above is a thunk for exactly this
        reason and says so.
        """
        resolve = _seam(wired.tagger, "tagger", "scores the photograph")
        if not opening:
            # A refusal is kept too, so the 467 MB hash is not re-run to meet it.
            opening.append(once(resolve))
        return opening[0]

    def work(identifier: str) -> None:
        if verb == "assign":
            _assign(identifier, bool(args.remove), wired, list(flows), collected)
            return
        try:
            run = run_for(identifier, wired)
        except Refusal as unopened:
            names: list[str | None] = (
                [None] if verb in PHOTOGRAPH_VERBS else list(flows)
            )
            for name in names:
                reporter.item(identifier, name, verb, "refused", str(unopened))
            raise
        if verb == "show":
            for line in report(run, wired.flows_dir):
                print(line, file=wired.out)
            return
        step: Callable[[str], None] | None = None
        describe: Callable[[], None] | None = None
        if verb == "caption":

            def caption_photo() -> None:
                reader = _seam(wired.reader, "reader", "reads the photograph")()
                say(
                    reporter,
                    run,
                    "caption",
                    caption(
                        run,
                        reader,
                        briefing_path=load_caption_config().briefing_path,
                        new_version=new_version,
                    ),
                )

            describe = caption_photo
        elif verb == "tag":

            def tag_photo() -> None:
                def hosted() -> None:
                    tagger_for = _seam(
                        wired.hosted_tagger, "hosted tagger", "tags the photograph"
                    )
                    written = tag_hosted(run, tagger_for(), new_version=new_version)
                    say(reporter, run, "tags", written)

                # Each tagger's refusal is collected on its own, so neither costs
                # the other its list. WD14 first: it is the sheet's input and
                # reaches no network (D1).
                steps: tuple[Callable[[], None], ...] = (
                    lambda: say(
                        reporter,
                        run,
                        "wd14",
                        tag_wd14(run, tagger(), new_version=new_version),
                    ),
                    hosted,
                )
                collected.extend(across(steps, lambda step: step()))

            describe = tag_photo
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
                say(reporter, run, "sheet", written)

            step = sheet_flow
        elif verb == "review":

            def review_flow(name: str) -> None:
                if args.discard:
                    gone = discard(run, name)
                    reporter.say(f"{run.id}: review discarded {name}/{gone.name}")
                    return
                say(reporter, run, "review", review(run, name, new_version=new_version))

            step = review_flow
        elif verb == "approve":

            def approve_flow(name: str) -> None:
                if args.cancel:
                    left, changed = cancel_approval(run, name)
                    if not changed and left is not None:
                        reporter.say(
                            f"{run.id}: approve has nothing to cancel in {name}; "
                            f"it is at its draft {left.name}"
                        )
                        return
                    back = "a copy, deleted" if left is None else f"back to {left.name}"
                    reporter.say(f"{run.id}: approve cancelled {name}, {back}")
                    return
                written, warnings = (
                    approve(
                        run,
                        name,
                        flows[name].schema,
                        vocabulary(),
                        excluded=field_map().excluded,
                        definition=flows[name],
                    )
                    if args.source is None
                    else approve_across(
                        run, flows[name], args.source, vocabulary, field_map
                    )
                )
                for warning in warnings:
                    print(f"warning: {warning}", file=wired.err)
                say(reporter, run, "approve", written)

            step = approve_flow
        else:
            raise Refusal(f"{verb!r} is not a stage this build runs")

        def reported(name: str | None, each: Callable[[], None]) -> None:
            """Run `each` between its `start` and its end; `None` names no flow."""
            reporter.item(run.id, name, verb, "start")
            before = len(collected)
            try:
                each()
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

        if describe is not None:
            # The photograph is described once, for every flow (D17).
            collected.extend(across([describe], lambda one: reported(None, one)))
        elif step is not None:
            # Each flow's refusal is collected on its own, so one flow's does not
            # cost the input its other flows.
            per_flow = step
            collected.extend(
                across(list(flows), lambda name: reported(name, lambda: per_flow(name)))
            )

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
    run = _existing_run(identifier, wired) if remove else run_for(identifier, wired)
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


def main(argv: Sequence[str] | None = None) -> int:
    """Parse the pipeline's arguments and dispatch to the named stage."""
    args = build_parser().parse_args(argv)
    try:
        return dispatch(args, wiring(args))
    except Refusal as refused:
        print(f"refused: {refused}", file=sys.stderr)
        return 1
