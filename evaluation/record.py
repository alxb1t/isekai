"""What both evaluators ask of a batch: its runs, and where its record goes.

The record sits beside the runs and never where git can reach. Both evaluators
refuse before they read anything, so a refusal costs no embedding and no tagging.
"""

from pathlib import Path

from isekai.foundation.refusal import Refusal
from isekai.foundation.run import FRAME_NAME, Run
from isekai.interface.wiring import trackable


def runs_in(directory: Path) -> list[Run]:
    """Return every run under `directory` that has a frame, in name order."""
    if not directory.is_dir():
        raise Refusal(
            f"{directory} is not a directory; give the batch's runs directory, the "
            "one `infra/render.sh` rendered into"
        )
    return [
        Run(frame.parent.name, frame.parent)
        for frame in sorted(directory.glob(f"*/{FRAME_NAME}"))
    ]


def destination(runs: Path, name: str) -> Path:
    """Return `<batch>/<name>`, refusing a place git can reach (D18).

    e.g. `.data/batch/runs`, `recall.json` -> `.data/batch/recall.json`
    """
    target = runs.parent / name
    if trackable(target.parent):
        raise Refusal(
            f"{target.resolve()} is inside this repository and outside .data/, "
            "the ignored data root, so the record would be one `git add` from "
            f"being published; move {runs.parent.resolve()} under .data/, "
            "then this command again with its new runs path"
        )
    return target
