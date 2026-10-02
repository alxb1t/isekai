"""Where a batch's record goes: beside its runs, and never where git can reach.

Both evaluators write a record there and refuse before they read anything, so a
refusal costs no embedding and no tagging.
"""

from pathlib import Path

from isekai.foundation.refusal import Refusal
from isekai.interface.wiring import trackable


def destination(runs: Path, name: str) -> Path:
    """Return `<batch>/<name>`, refusing a place git can reach (D18).

    e.g. `.data/batch/runs`, `recall.json` -> `.data/batch/recall.json`
    """
    target = runs.parent / name
    if trackable(target.parent):
        raise Refusal(
            f"{target.resolve()} is inside this repository and outside .data/, "
            "the one directory git ignores, so the record would be one `git add` from "
            f"being published; move {runs.parent.resolve()} under .data/, "
            "then this command again with its new runs path"
        )
    return target
