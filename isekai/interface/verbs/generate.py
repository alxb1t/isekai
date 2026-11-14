"""The `generate` verb: its batch, its arguments and its row, with no run."""

import argparse
from collections.abc import Mapping, Sequence

from isekai.boundary.comfy import read_runtime
from isekai.foundation.flow import Flow, load_flow
from isekai.foundation.run import Run, across
from isekai.interface.verbs.common import (
    Reporter,
    Verb,
    _seed,
    once,
    photographs,
    progress_flag,
    render_count,
    required_flow,
    run_for,
)
from isekai.interface.wiring import Wiring
from isekai.pipeline.generate import (
    STAGE_RENDER,
    Render,
    prepare,
    render,
    source_seeds,
)


def generate_batch(
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
    reporter = Reporter(wired.out, wired.err, getattr(args, "progress", None) == "json")
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
        run = run_for(identifier, wired)
        assembled, refusals = prepare(run, flows)
        broken.extend(refusals)
        if args.seeds_from is not None:
            borrowed[run.id] = source_seeds(
                run, args.seeds_from, source_suffix, list(flows)
            )[1]
        for flow, path in assembled.items():
            reporter.say(f"{run.id}: assembled {flow}/{path.name}")
            ready.append((run, flow))

    refused = across(list(targets), assemble_one) + broken
    client = wired.client
    if client is None:
        return refused
    # One report per session, read only when a render will run.
    ran_on = once(lambda: read_runtime(client))

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


def generate_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `generate`'s arguments to `parser`."""
    photographs(parser)
    required_flow(parser)
    progress_flag(parser)
    # Mutually exclusive at parse time, so asking for both is refused before any
    # work begins rather than discovered on a rented machine. One verb explores
    # and the other reproduces, and combining them has no meaning (D13).
    exclusive = parser.add_mutually_exclusive_group()
    exclusive.add_argument(
        "--count",
        type=render_count,
        default=None,
        help=(
            "how many renders per photograph per flow, seeds drawn (default: the "
            "approval's count, else 1)"
        ),
    )
    exclusive.add_argument(
        "--seed",
        type=_seed,
        action="append",
        dest="seeds",
        default=None,
        help="render exactly this seed; repeatable, and not combinable with --count",
    )
    exclusive.add_argument(
        "--seeds-from",
        dest="seeds_from",
        default=None,
        metavar="FLOW",
        help="render this flow's latest seeds for each run; not with the others",
    )
    # No default, deliberately. Assembly is free and rendering is not, so the
    # invocation that costs money is the one that names where to spend it --
    # `generate` without `--server` assembles every prompt and stops, which is
    # also how a malformed sheet is found before anything is rented.
    parser.add_argument(
        "--server",
        default=None,
        help=(
            "the ComfyUI endpoint, reached through the tunnel; omit it to "
            "assemble every prompt and stop without rendering"
        ),
    )


GENERATE_ROW = Verb(
    "generate", "assemble the prompts for a run, then render them", generate_arguments
)
