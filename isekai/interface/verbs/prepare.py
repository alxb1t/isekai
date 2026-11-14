"""The `prepare` verb: its run, its arguments and its row, with no run bound."""

import argparse
import dataclasses
import shlex
from collections.abc import Callable, Mapping
from pathlib import Path

from isekai.foundation.flow import Flow, load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import RUNS_ROOT, across
from isekai.interface.verbs.common import (
    Reporter,
    Verb,
    once,
    parse_cells,
    progress_flag,
)
from isekai.interface.wiring import Wiring

PerItem = Callable[
    [str, argparse.Namespace, Wiring, Mapping[str, Flow], list[str]],
    Callable[[str], None],
]


def run_prepare(args: argparse.Namespace, wired: Wiring, per_item: PerItem) -> int:
    """Take each photograph through `tag`, `caption`, then its cells' sheets, in turn.

    Each step is the work `per_item` gives its verb, so its lines and refusals are
    that verb's; the one `tag` work opens the tagger once. A refusal costs only its
    own step (D1), and an unassigned cell's sheet refuses rather than making its
    directory again.
    e.g. r1/f r2/f r2/g -> r1: tag, caption, f; then r2: tag, caption, f, g
    """
    cells = parse_cells(args.cells, wired)
    vocabulary = once(wired.vocabulary)
    mapped = once(lambda: wired.field_map(vocabulary()))
    shared = dataclasses.replace(
        wired, vocabulary=vocabulary, field_map=lambda _: mapped()
    )
    flows = {
        name: load_flow(name, wired.flows_dir)
        for name in dict.fromkeys(flow for _, flow in cells)
    }
    collected: list[str] = []
    tag = per_item("tag", args, shared, {}, collected)
    describe = per_item("caption", args, shared, {}, collected)
    sheets = {
        name: per_item("sheet", args, shared, {name: flow}, collected)
        for name, flow in flows.items()
    }
    reporter = Reporter(wired.out, wired.err, args.progress == "json")
    runs = shlex.quote(str(wired.runs_root))

    def sheet_of(flow: str) -> Callable[[str], None]:
        def sheet_cell(run_id: str) -> None:
            if not (wired.runs_root / run_id / flow).is_dir():
                unassigned = (
                    f"{run_id}/{flow} is not assigned, so prepare makes no sheet for "
                    f"it; run `python -m isekai assign --flow {flow} --runs {runs} "
                    f"{run_id}` first"
                )
                reporter.item(run_id, flow, "sheet", "refused", unassigned)
                raise Refusal(unassigned)
            sheets[flow](run_id)

        return sheet_cell

    by_run: dict[str, list[str]] = {}
    for run_id, flow in cells:
        by_run.setdefault(run_id, []).append(flow)
    for run_id, named in by_run.items():
        steps = [
            *([tag] if any(flows[flow].tagger for flow in named) else []),
            describe,
            *(sheet_of(flow) for flow in named),
        ]
        collected.extend(across(steps, lambda step: step(run_id)))
    for message in collected:
        print(f"refused: {message}", file=wired.err)
    return 1 if collected else 0


def prepare_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `prepare`'s arguments to `parser`."""
    # A cell names its flow, so `prepare` takes no `--flow` and no photograph.
    parser.add_argument(
        "cells",
        nargs="+",
        metavar="<run-id>/<flow>",
        help="cells to prepare, each photograph in the order its first cell is named",
    )
    parser.add_argument(
        "--runs",
        type=Path,
        default=RUNS_ROOT,
        help=f"the directory runs live under (default {RUNS_ROOT.name}/)",
    )
    parser.set_defaults(photos=[])
    progress_flag(parser)


PREPARE_ROW = Verb("prepare", prepare_arguments)
