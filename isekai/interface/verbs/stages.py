"""The flow-stage verbs and `show`: their arguments and rows, with no run."""

import argparse

from isekai.interface.verbs.common import (
    Verb,
    hidden_flow,
    new_version_flag,
    photographs,
    progress_flag,
    required_flow,
)


def assign_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `assign`'s arguments to `parser`."""
    photographs(parser)
    required_flow(parser)
    parser.add_argument(
        "--remove",
        action="store_true",
        help="delete each flow's directory instead, refusing one that holds work",
    )


def caption_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `caption`'s arguments to `parser`."""
    photographs(parser)
    hidden_flow(parser)
    progress_flag(parser)
    new_version_flag(parser)


def tag_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `tag`'s arguments to `parser`."""
    photographs(parser)
    hidden_flow(parser)
    progress_flag(parser)
    new_version_flag(parser)


def sheet_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `sheet`'s arguments to `parser`."""
    photographs(parser)
    required_flow(parser)
    progress_flag(parser)
    new_version_flag(parser)


def review_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `review`'s arguments to `parser`."""
    photographs(parser)
    required_flow(parser)
    new_version_flag(parser)
    parser.add_argument(
        "--discard",
        action="store_true",
        help="delete each flow's waiting draft instead, refusing an approval",
    )


def approve_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `approve`'s arguments to `parser`."""
    photographs(parser)
    required_flow(parser)
    # A verb that reads another flow reads only the one the operator names.
    parser.add_argument(
        "--from",
        dest="source",
        default=None,
        metavar="FLOW",
        help="copy this flow's latest approval under each --flow instead of a draft",
    )
    parser.add_argument(
        "--cancel",
        action="store_true",
        help="turn each flow's newest approval back into its draft instead, "
        "deleting a copy and refusing one anything was made from",
    )


def show_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `show`'s arguments to `parser`."""
    photographs(parser)


ASSIGN_ROW = Verb(
    "assign",
    "give each source a flow's empty directory, or remove an empty one",
    assign_arguments,
)
CAPTION_ROW = Verb("caption", "read a photograph into prose", caption_arguments)
TAG_ROW = Verb(
    "tag", "score a photograph with WD14, then list the JoyCaption tags", tag_arguments
)
SHEET_ROW = Verb(
    "sheet", "fill a sheet of canonical tags from the WD14 tag list", sheet_arguments
)
REVIEW_ROW = Verb(
    "review", "copy a sheet somewhere a human may edit it", review_arguments
)
APPROVE_ROW = Verb(
    "approve", "validate an edited sheet and mark it approved", approve_arguments
)
SHOW_ROW = Verb(
    "show", "print a run's artifacts, versions, producers and failures", show_arguments
)
