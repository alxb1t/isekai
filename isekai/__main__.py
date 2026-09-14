"""The pipeline's entry point: `python -m isekai <verb>`.

**A second surface, not an extension of the first.** `convert.py` is a shim over
`isekai.cli`, and that parser drives the render path this version promised not to
touch -- so the staged pipeline gets its own parser in its own module and the
existing single-command surface is unchanged (design.md D1). Four separate scripts
were rejected for the same reason one parser was chosen: it would multiply the
stdlib-only guard by four and give argument parsing four places to drift.

**Six verbs, and schema migration is not one of them.** Only schema version 1
exists, so an upgrade command would be a dispatch table with no entries and its
refusal would be unreachable -- nothing can write a version 2 artifact
(design.md D2).

    caption   (1) a photograph in, descriptive prose out
    sheet     (2) prose in, a sheet of canonical tags out
    review    (3) the machine's sheet copied somewhere a human may edit it
    approve   (3) validate the edited sheet and rename it
    generate  (4) assemble every prompt locally, then render
    show          print a run's artifacts and what produced each one

Stdlib only, and held to that by its own subprocess guard beside the one that
holds `convert.py`.
"""

import argparse
import sys
from collections.abc import Sequence

# One line of prose per verb, used for both the subcommand list and its own help,
# so the two cannot disagree about what a stage does.
VERBS: tuple[tuple[str, str], ...] = (
    ("caption", "read a photograph into descriptive prose"),
    ("sheet", "sort a caption into a sheet of canonical tags"),
    ("review", "copy a sheet somewhere a human may edit it"),
    ("approve", "validate an edited sheet and mark it approved"),
    ("generate", "assemble the prompts for a run, then render them"),
    ("show", "print a run's artifacts, versions and producers"),
)


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


def build_parser() -> argparse.ArgumentParser:
    """Return the pipeline's parser, with one subparser per verb."""
    parser = argparse.ArgumentParser(
        prog="python -m isekai",
        description="The staged pipeline: photograph -> prose -> sheet -> render.",
    )
    verbs = parser.add_subparsers(dest="verb", metavar="verb", required=True)
    made = {
        name: verbs.add_parser(name, help=summary, description=summary)
        for name, summary in VERBS
    }

    for name in ("caption", "sheet", "review", "approve", "generate", "show"):
        made[name].add_argument(
            "photos",
            nargs="*",
            help="photographs, or run identifiers for a run that already exists",
        )
    for name in ("review", "approve", "generate"):
        made[name].add_argument(
            "--flow",
            default=None,
            help="the flow to act on; every approved one by default",
        )
    for name in ("caption", "sheet", "review"):
        made[name].add_argument(
            "--new-version",
            action="store_true",
            help="write the next numbered artifact instead of doing nothing",
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
    made["generate"].add_argument(
        "--server",
        default="http://127.0.0.1:8188",
        help="the ComfyUI endpoint, reached through the tunnel",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse the pipeline's arguments and dispatch to the named stage."""
    build_parser().parse_args(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
