"""The edits' verbs: `ink` and `edit`, with `--pending`'s run."""

import argparse
import shlex
from pathlib import Path

from isekai.boundary.comfy import read_runtime
from isekai.foundation.edit import load_edit, tracked_edits
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import RUNS_ROOT, Run, across
from isekai.interface.render import pending_edits
from isekai.interface.verbs.common import (
    Reporter,
    Verb,
    _depth,
    _seed,
    once,
    parse_cells,
)
from isekai.interface.wiring import Wiring
from isekai.pipeline.edit import OVERRIDES, image_of
from isekai.pipeline.edit import check as check_edit
from isekai.pipeline.edit import request as request_edit
from isekai.pipeline.edit import sample as sample_edit
from isekai.shared.ink import cut_ink


def run_ink(args: argparse.Namespace, wired: Wiring) -> int:
    """Write the ink layer of an image, printing its path."""
    cut_ink(args.image, args.out, args.outline, args.neutral, args.depth)
    print(f"ink wrote {args.out}", file=wired.out)
    return 0


def run_edit(args: argparse.Namespace, wired: Wiring) -> int:
    """Request an edit of a render, printing the files written and how to run it.

    Free and local: no endpoint is used and no session opens. An edit this build
    does not track is refused, naming the ones it does. With `--pending` it runs
    the pending edits of cells instead, `run_pending`'s form.
    """
    if args.pending is not None:
        if args.edit is not None or args.render is not None:
            raise Refusal(
                "--pending takes cells alone; drop the edit and the render from the "
                "command, or drop --pending to request an edit"
            )
        return run_pending(args, wired)
    if args.edit is None or args.render is None:
        raise Refusal(
            "a request names its edit and its render: "
            "`python -m isekai edit <edit> <render> --composite <png>`"
        )
    tracked = tracked_edits()
    if args.edit not in tracked:
        raise Refusal(
            f"{args.edit}: not an edit this build tracks; the edits it carries are "
            f"{', '.join(tracked) or '(none)'}"
        )
    asked = request_edit(
        load_edit(args.edit),
        args.render,
        args.composite,
        overrides={name: getattr(args, name) for name in OVERRIDES},
        seed=args.seed,
        rng=wired.rng,
    )
    runs = asked.record.parents[4]
    for path in (asked.composite, asked.record):
        print(f"edit wrote {path.relative_to(runs)}", file=wired.out)
    print(
        f"edit pending: run `python -m isekai render {shlex.quote(str(runs))}` "
        "to sample it on a rented GPU",
        file=wired.out,
    )
    return 0


def run_pending(args: argparse.Namespace, wired: Wiring) -> int:
    """Check every pending edit of the cells, then sample them when there is a client.

    Without a client each edit is derived and checked from its files and nothing is
    rented, so a stale request refuses before a pod is. With one the edits run in
    chain order, one refusal not costing the next its turn, and each prints a line.
    e.g. r1/f holding 42.edit-1.json with no image -> "r1: edited f/42.edit-1.png"
    """
    cells = parse_cells(args.pending, wired)
    reporter = Reporter(wired.out, wired.err, getattr(args, "progress", None) == "json")
    found: list[tuple[Run, str, Path]] = []
    for run_id, flow in cells:
        run = Run(run_id, wired.runs_root / run_id)
        found += [(run, flow, record) for record in pending_edits(run, flow)]
    waiting = {image_of(record) for _, _, record in found}
    refused = across(
        found, lambda one: check_edit(one[2], waiting=waiting - {image_of(one[2])})
    )
    client = wired.client
    if client is None or refused:
        for message in refused:
            print(f"refused: {message}", file=wired.err)
        if not refused:
            for run, flow, record in found:
                reporter.say(f"{run.id}: {flow}/{record.name} is ready to sample")
        return 1 if refused else 0
    ran_on = once(lambda: read_runtime(client))

    def sample_one(one: tuple[Run, str, Path]) -> None:
        run, flow, record = one
        image = sample_edit(client, record, runtime=ran_on)
        reporter.say(f"{run.id}: edited {flow}/{image.name}")
        reporter.item(
            run.id,
            flow,
            "edit",
            "done",
            digest=run.digest,
            version=int(image.parent.name),
            file=image.name,
        )

    for message in (failed := across(found, sample_one)):
        print(f"refused: {message}", file=wired.err)
    return 1 if failed else 0


def ink_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `ink`'s arguments to `parser`."""
    parser.add_argument("image", type=Path, help="the tattoo's photograph or image")
    parser.add_argument("out", type=Path, help="the PNG layer to write")
    parser.add_argument(
        "--outline",
        type=Path,
        default=None,
        metavar="MASK.png",
        help="white keeps the ink; the layer's alpha, for a photograph",
    )
    parser.add_argument(
        "--neutral",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="the ink as grey (default with an outline), or in colour",
    )
    parser.add_argument(
        "--depth",
        type=_depth,
        default=None,
        help="the power the layer's Multiply factor is raised to; a fill darkens "
        "(default 1.6 with an outline, 1.0 without)",
    )
    parser.set_defaults(photos=[], runs=RUNS_ROOT)


def edit_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `edit`'s arguments to `parser`."""
    # An edit's image is written beside its source, so a request's render path names
    # the run; `--pending` names cells, and the runs root they live under.
    parser.add_argument("edit", nargs="?", help="the edit to request, e.g. tattoo-wai")
    parser.add_argument(
        "render",
        nargs="?",
        type=Path,
        help="the render, <run>/<flow>/outputs/<NNN>/<seed>.png, or an edit's "
        "image <seed>.edit-<k>.png to chain from",
    )
    form = parser.add_mutually_exclusive_group(required=True)
    form.add_argument(
        "--composite",
        type=Path,
        metavar="COMPOSITE.png",
        help="the render with the tattoo multiplied on, at the render's size",
    )
    form.add_argument(
        "--pending",
        nargs="+",
        metavar="<run-id>/<flow>",
        help="sample every pending edit of these cells; with no --server, only "
        "derive and check them",
    )
    parser.add_argument(
        "--runs",
        type=Path,
        default=RUNS_ROOT,
        help=f"the directory --pending's runs live under (default {RUNS_ROOT.name}/)",
    )
    parser.add_argument(
        "--server",
        default=None,
        help="the ComfyUI endpoint --pending samples on, reached through the tunnel",
    )
    parser.add_argument(
        "--progress",
        choices=["json"],
        default=None,
        help="print a JSON line per sampled edit; prose goes to stderr",
    )
    for dial, meaning in (
        ("denoise", "how far the pass repaints under the mask"),
        ("strength", "how firmly the control holds the ink's lines"),
        ("lines", "how much of the ink is multiplied back after the pass"),
    ):
        parser.add_argument(
            f"--{dial}",
            type=float,
            default=None,
            help=f"{meaning}; for this edit only (default: the edit's own)",
        )
    parser.add_argument(
        "--seed",
        type=_seed,
        default=None,
        help="repeat this sampling seed (default: drawn)",
    )
    parser.set_defaults(photos=[])


INK_ROW = Verb(
    "ink",
    "cut a tattoo photograph or image into a layer to multiply over a render",
    ink_arguments,
    run_ink,
)
EDIT_ROW = Verb(
    "edit",
    "request an edit of a render from a composite of it, free and local",
    edit_arguments,
    run_edit,
)
