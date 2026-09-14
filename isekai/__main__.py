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


def build_parser() -> argparse.ArgumentParser:
    """Return the pipeline's parser, with one subparser per verb."""
    parser = argparse.ArgumentParser(
        prog="python -m isekai",
        description="The staged pipeline: photograph -> prose -> sheet -> render.",
    )
    verbs = parser.add_subparsers(dest="verb", metavar="verb", required=True)
    for name, summary in VERBS:
        verbs.add_parser(name, help=summary, description=summary)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse the pipeline's arguments and dispatch to the named stage."""
    build_parser().parse_args(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
