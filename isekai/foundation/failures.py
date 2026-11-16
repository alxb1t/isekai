"""The failure shape the stages share: its kind, its budgets and its records.

`Kind` and what each stage may spend, the attempts a directory records against an
artifact, `across` over a batch and `StageFailure`. `run.py` re-exports each name; a
module outside the foundation imports them from there. `StageFailure` is here and
not in `refusal.py`, which imports nothing, because the class needs `Kind`.

Stdlib only, and on `python -m isekai`'s import graph.
"""

import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeVar

from isekai.foundation.artifacts import ERROR_FILE, ErrorRecord, Failure, write
from isekai.foundation.names import ERROR
from isekai.foundation.refusal import Refusal
from isekai.foundation.rundir import Run

Kind = Literal["transient", "permanent"]

# What each stage may spend before it costs a person's attention instead. Reading
# and sorting are cheap and flaky, so they get three; assembling and rendering get
# one, because a render that has failed once should be looked at rather than paid
# for again.
#
# The two taggers are split on the same axis rather than sharing a number.
# `tags` is a hosted model over HTTP, so it is flaky in exactly the way `caption`
# is and gets its three. `wd14` is a local pass over a
# digest-verified graph, and what can still fail there is **this photograph's own
# bytes** -- a header no decoder can read. That is permanent by construction, so
# one attempt is the whole budget, exactly as `assemble` and `render` are one.
#
# The two file conditions that would fail identically for every input -- an
# absent model, bytes that disagree with the pin -- are deliberately **not**
# counted here. They are conditions about this build rather than about a
# photograph, so the tagger is opened before the stage's `try` and refuses the
# batch once instead of writing one error record per input for a single fix.
#
# **`sheet` is one for `wd14`'s reason.** It reached a hosted model once and had
# three; it is now a dictionary lookup over an artifact already on disk, so there
# is no transient failure left for a second attempt to catch -- which is exactly
# what `"wd14": 1` above already records for the other local producer. The stage
# records every failure as permanent, so a second attempt waits on a deletion.
#
# A missing entry here is not a missing feature, it is a crash: `BUDGETS[stage]`
# below is a bare lookup, and `across()` and `main()` both catch only `Refusal`
# -- so an unlisted stage name escapes as a raw traceback in a package where
# every failure is a named refusal.
BUDGETS: Mapping[str, int] = {
    "caption": 3,
    "wd14": 1,
    "tags": 3,
    "sheet": 1,
    "assemble": 1,
    "render": 1,
}

T = TypeVar("T")


# --- failures and budgets -----------------------------------------------------


@dataclass(frozen=True)
class Attempt:
    """One recorded failure against a known artifact: how it failed, and where.

    It carries no version: `attempts` is always asked about one, so storing it
    here would be the caller's own argument handed back.
    """

    attempt: int
    kind: Kind
    path: Path


def attempts(directory: Path, version: int) -> list[Attempt]:
    """Return the failures recorded against `version`, in attempt order.

    A listing. Counting attempts, and deciding whether the last one was permanent,
    are both retry decisions, which is why the kind and the ordinal are in the
    name rather than inside the file.
    """
    if not directory.is_dir():
        return []
    found: list[Attempt] = []
    for name in os.listdir(directory):
        named = failure_named(name)
        if named is not None and named[0] == version:
            found.append(Attempt(named[1], named[2], directory / name))
    return sorted(found, key=lambda recorded: recorded.attempt)


def failure_named(name: str) -> tuple[int, int, Kind] | None:
    """Return the version, attempt and kind a failure record's name carries.

    None when `name` is not a failure record.
    e.g. `"002.error.1.transient.json"` → `(2, 1, "transient")`
    """
    match = ERROR.match(name)
    if match is None:
        return None
    kind: Kind = "permanent" if match.group("kind") == "permanent" else "transient"
    return int(match.group("version")), int(match.group("attempt")), kind


def failures_alone(directory: Path) -> list[Path] | None:
    """Return the failure records `directory` holds when they are all it holds, sorted.

    None when it is no directory or holds anything else; an empty one gives [].
    e.g. outputs/002/ holding 002.error.1.permanent.json alone -> [that record]
    """
    if not directory.is_dir():
        return None
    held = sorted(directory.iterdir())
    if any(not path.is_file() or failure_named(path.name) is None for path in held):
        return None
    return held


def record_failure(
    directory: Path,
    version: int,
    kind: Kind,
    failure: Failure,
) -> Path:
    """Write an error record beside where `version`'s artifact would have gone.

    The failure does not consume the version number: a later successful attempt
    writes `version` itself, and the error records stay beside it. The attempt is
    the highest recorded plus one, so deleting an earlier record never makes the
    next one overwrite a later one.
    """
    recorded = attempts(directory, version)
    ordinal = recorded[-1].attempt + 1 if recorded else 1
    path = directory / f"{version:03d}.error.{ordinal}.{kind}.json"
    # By name, never the failure spread whole: its keys must not land among
    # ours. The seed sits between stage and detail, as `tests/golden/error.json`.
    record: ErrorRecord = {
        "schema": ERROR_FILE.schema,
        "version": version,
        "attempt": ordinal,
        "kind": kind,
        "stage": failure["stage"],
        **({"seed": failure["seed"]} if "seed" in failure else {}),
        "detail": failure["detail"],
    }
    write(path, ERROR_FILE, record)
    return path


def _spent(
    stage: str, recorded: Sequence[Attempt]
) -> Literal["permanent", "budget"] | None:
    """Return why `recorded` bars `stage` another attempt, or None if it does not.

    The one statement of the retry rule: a permanent record short-circuits the
    count, and otherwise the stage may try until it is at its budget.
    """
    if not recorded:
        return None
    if recorded[-1].kind == "permanent":
        return "permanent"
    return "budget" if len(recorded) >= BUDGETS[stage] else None


def exhausted(stage: str, directory: Path, version: int) -> bool:
    """Say whether `stage` may not attempt `version` again: permanent, or at budget."""
    return _spent(stage, attempts(directory, version)) is not None


def check_budget(stage: str, directory: Path, version: int, run: Run) -> None:
    """Refuse if `stage` may not attempt `version` again, naming why and where.

    A permanent failure short-circuits the count: it will fail the same way every
    time, so retrying it spends for nothing. A stage at its transient budget
    refuses too, because without one every resume retries every failure forever
    and at the rendering stage that costs money on every pass.
    e.g. `see photo/wd14/001.error.1.permanent.json`
    """
    recorded = attempts(directory, version)
    why = _spent(stage, recorded)
    if why is None:
        return
    where = recorded[-1].path.relative_to(run.path)
    if why == "permanent":
        raise Refusal(
            f"{run.id}: {stage} failed permanently -- see {where}; read the "
            "record, fix what it names, then delete it to let this stage attempt "
            "again"
        )
    budget = BUDGETS[stage]
    raise Refusal(
        f"{run.id}: {stage} has used its {budget} attempt"
        f"{'' if budget == 1 else 's'} -- see {where}; read the records, fix what "
        "they name, then delete them to let this stage attempt again"
    )


def across(items: Sequence[T], work: Callable[[T], None]) -> list[str]:
    """Run `work` over every item, collecting refusals instead of stopping at one.

    One photograph's failure must not cost the other nine their turn, and a
    failure reported when it happens scrolls off before the batch ends -- so every
    refusal is collected and returned for the caller to report together.
    """
    refused: list[str] = []
    for item in items:
        try:
            work(item)
        except Refusal as refusal:
            refused.append(str(refusal))
    return refused


class StageFailure(Exception):
    """A model call did not return what a stage can use, and the kind says what next."""

    def __init__(self, kind: Kind, detail: str) -> None:
        """Carry the kind and the detail an error record is written from."""
        super().__init__(detail)
        self.kind = kind
        self.detail = detail
