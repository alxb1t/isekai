"""The render session's verb: `render`'s arguments and its row, with no run."""

import argparse
from pathlib import Path

from isekai.interface.verbs.common import Verb, _session_id, _Targets, session_limit


def render_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `render`'s arguments to `parser`."""
    parser.add_argument(
        "--progress",
        choices=["json"],
        default=None,
        help="print a JSON line per step of the session; prose goes to stderr",
    )
    parser.add_argument(
        "targets",
        nargs="+",
        action=_Targets,
        metavar="<runs>… [<flow>=<count|source> …]",
        help=(
            "each collection's runs/, rendered in one session in the order named; "
            "then, beside one runs/ alone, a flow and how many seeds it draws, or "
            "the flow whose seeds it takes. With no request, every approval short "
            "of its count renders what it lacks"
        ),
    )
    parser.add_argument(
        "--limit",
        type=session_limit,
        default=None,
        metavar="SECONDS",
        help=(
            "end the session after this many seconds, at most gpunit.toml's "
            "ceiling; without it, the limit is estimated from the work"
        ),
    )
    parser.add_argument(
        "--session",
        type=_session_id,
        default=None,
        metavar="ID",
        help=(
            "name the session's record <collection>/sessions/<ID>.json; without it, "
            "the session's start in UTC names it"
        ),
    )
    parser.add_argument(
        "--without",
        action="append",
        type=Path,
        default=None,
        metavar="<runs>/<run-id>/<flow>",
        help="take that run's flow out of what renders; repeatable, beside no request",
    )
    parser.set_defaults(photos=[])


RENDER_ROW = Verb(
    "render",
    "run a whole render session on a rented GPU, then tear it down",
    render_arguments,
)
