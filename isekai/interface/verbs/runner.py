"""The flow stages' runner: the work one identifier gets, and `assign`'s."""

import argparse
import dataclasses
from collections.abc import Callable, Mapping, Sequence
from functools import cache
from typing import TypeVar

from isekai.boundary.wd14 import LocalTagger
from isekai.foundation.caption_config import load_caption_config
from isekai.foundation.flow import Flow
from isekai.foundation.library import render_running
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    PHOTOGRAPH_VERBS,
    Run,
    across,
    assign,
    find_run,
)
from isekai.interface.drafting import (
    approve_across,
)
from isekai.interface.run_view import report
from isekai.interface.verbs.common import (
    Reporter,
    once,
    run_for,
    run_or_photo,
    say,
)
from isekai.interface.wiring import Wiring
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


def _existing_run(identifier: str, wired: Wiring) -> Run | None:
    """Return the run an argument names, as `run_for` does, but never open one."""
    named = run_or_photo(identifier, wired)
    return named if isinstance(named, Run) else find_run(named, wired.runs_root)


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


@dataclasses.dataclass(frozen=True)
class _Item:
    """What one `_per_item` call shares among its builders and its runner."""

    args: argparse.Namespace
    wired: Wiring
    flows: Mapping[str, Flow]
    collected: list[str]
    reporter: Reporter
    new_version: bool
    vocabulary: Callable[[], Vocabulary]
    field_map: Callable[[], FieldMap]
    tagger: Callable[[], Callable[[], LocalTagger]]


def _item_of(
    args: argparse.Namespace,
    wired: Wiring,
    flows: Mapping[str, Flow],
    collected: list[str],
) -> _Item:
    """Return what one `_per_item` call shares, its reads memoised for the call.

    The vocabulary is resolved at most once for the same reason as the flows, and
    lazily for the old one: parsing the 308 KB tag list costs ~50 ms, and only
    two verbs need it at all.
    """
    opening: list[Callable[[], LocalTagger]] = []

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

    return _Item(
        args=args,
        wired=wired,
        flows=flows,
        collected=collected,
        reporter=Reporter(
            wired.out, wired.err, getattr(args, "progress", None) == "json"
        ),
        new_version=bool(getattr(args, "new_version", False)),
        vocabulary=vocabulary,
        field_map=field_map,
        tagger=tagger,
    )


_Step = Callable[[str], None]
_Builder = Callable[[Run, _Item], _Step]


def _caption_step(run: Run, item: _Item) -> _Step:
    """Return the step that captions the photograph, which names no flow."""

    def caption_photo(name: str) -> None:
        reader = _seam(item.wired.reader, "reader", "reads the photograph")()
        say(
            item.reporter,
            run,
            "caption",
            caption(
                run,
                reader,
                briefing_path=load_caption_config().briefing_path,
                new_version=item.new_version,
            ),
        )

    return caption_photo


def _tag_step(run: Run, item: _Item) -> _Step:
    """Return the step that tags the photograph, which names no flow."""

    def tag_photo(name: str) -> None:
        def hosted() -> None:
            tagger_for = _seam(
                item.wired.hosted_tagger, "hosted tagger", "tags the photograph"
            )
            written = tag_hosted(run, tagger_for(), new_version=item.new_version)
            say(item.reporter, run, "tags", written)

        # Each tagger's refusal is collected on its own, so neither costs
        # the other its list. WD14 first: it is the sheet's input and
        # reaches no network (D1).
        steps: tuple[Callable[[], None], ...] = (
            lambda: say(
                item.reporter,
                run,
                "wd14",
                tag_wd14(run, item.tagger(), new_version=item.new_version),
            ),
            hosted,
        )
        item.collected.extend(across(steps, lambda step: step()))

    return tag_photo


def _sheet_step(run: Run, item: _Item) -> _Step:
    """Return the step that assembles one flow's sheet."""

    def sheet_flow(name: str) -> None:
        flow = item.flows[name]
        written, warnings = sheet(
            run,
            name,
            flow.schema,
            item.vocabulary(),
            item.field_map(),
            tagged=flow.tagger,
            flow_digest=flow.digest,
            new_version=item.new_version,
        )
        for warning in warnings:
            print(f"warning: {warning}", file=item.wired.err)
        say(item.reporter, run, "sheet", written)

    return sheet_flow


def _review_step(run: Run, item: _Item) -> _Step:
    """Return the step that opens one flow's draft, or discards it with `--discard`."""

    def review_flow(name: str) -> None:
        if item.args.discard:
            gone = discard(run, name)
            item.reporter.say(f"{run.id}: review discarded {name}/{gone.name}")
            return
        say(
            item.reporter,
            run,
            "review",
            review(run, name, new_version=item.new_version),
        )

    return review_flow


def _approve_step(run: Run, item: _Item) -> _Step:
    """Return the step that approves one flow's sheet, or cancels it with `--cancel`."""

    def approve_flow(name: str) -> None:
        if item.args.cancel:
            if render_running(run):
                raise Refusal(
                    f"{run.id}: A render session is running. Wait for it to end, "
                    "then cancel the approval again."
                )
            left, changed = cancel_approval(run, name)
            if not changed and left is not None:
                item.reporter.say(
                    f"{run.id}: approve has nothing to cancel in {name}; "
                    f"it is at its draft {left.name}"
                )
                return
            back = "a copy, deleted" if left is None else f"back to {left.name}"
            item.reporter.say(f"{run.id}: approve cancelled {name}, {back}")
            return
        flow = item.flows[name]
        written, warnings = (
            approve(
                run,
                name,
                flow.schema,
                item.vocabulary(),
                excluded=item.field_map().excluded,
                definition=flow,
            )
            if item.args.source is None
            else approve_across(
                run, flow, item.args.source, item.vocabulary, item.field_map
            )
        )
        for warning in warnings:
            print(f"warning: {warning}", file=item.wired.err)
        say(item.reporter, run, "approve", written)

    return approve_flow


_BUILDERS: Mapping[str, _Builder] = {
    "caption": _caption_step,
    "tag": _tag_step,
    "sheet": _sheet_step,
    "review": _review_step,
    "approve": _approve_step,
}


def _reported(item: _Item, run: Run, verb: str, name: str | None, step: _Step) -> None:
    """Run `step` between its `start` and its end; `None` names no flow."""
    item.reporter.item(run.id, name, verb, "start")
    before = len(item.collected)
    try:
        step("" if name is None else name)
    except Refusal as refused:
        item.reporter.item(run.id, name, verb, "refused", str(refused))
        raise
    # `tag` collects each tagger's refusal rather than raising it.
    if len(item.collected) > before:
        item.reporter.item(
            run.id, name, verb, "refused", "; ".join(item.collected[before:])
        )
    else:
        item.reporter.item(run.id, name, verb, "done")


def _run_item(verb: str, run: Run, item: _Item) -> None:
    """Run the step `verb` names: once for a photograph's verb, once per flow else."""
    build = _BUILDERS.get(verb)
    if build is None:
        raise Refusal(f"{verb!r} is not a stage this build runs")
    step = build(run, item)
    # The photograph is described once, for every flow (D17). Each flow's
    # refusal is collected on its own, so one flow's does not cost the input
    # its other flows.
    names: list[str | None] = [None] if verb in PHOTOGRAPH_VERBS else list(item.flows)
    item.collected.extend(
        across(names, lambda name: _reported(item, run, verb, name, step))
    )


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
    and its dials.
    """
    item = _item_of(args, wired, flows, collected)

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
                item.reporter.item(identifier, name, verb, "refused", str(unopened))
            raise
        if verb == "show":
            for line in report(run, wired.flows_dir):
                print(line, file=wired.out)
            return
        _run_item(verb, run, item)

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
