"""The blind pairwise labelling protocol, and the correlation it licenses.

**The operator's eye is the reference, and every metric in this project is the
thing being calibrated against it** (design.md D10). That is why the sheet
carries no scores: a rating invented while looking at a number is a rating of the
number.

Three properties, each enforced here rather than asked for politely:

- **Pairwise**, because "is A or B more like them?" is stable where a 1-5 rating
  drifts across a sitting.
- **Within-subject**, because "does subject 1's render preserve identity more
  than subject 4's" is a question with no meaning.
- **Blind, and provably so.** The sheet is emitted with no metric value on it and
  is committed **before any score for these renders exists**. Git ordering is what
  proves that, and `correlate` refuses labels it cannot show were prior.

The consequence is accepted rather than hidden: **a single holistic label cannot
attribute a disagreement to one axis.** If face and hair correlate differently
against the same label, that difference is itself a finding.

Stdlib only, like `isekai.evaluate`, so all of it is testable in CI with the
`[eval]` extra absent. The one impure thing -- asking git what was committed when
-- is behind the `Ordering` seam.
"""

import csv
import itertools
import json
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from random import Random
from typing import Protocol

# The sheet's columns. `choice` is the only one the operator fills in, and it is
# deliberately the last: a column order that puts the answer beside the question
# invites filling it in while still reading the question.
SHEET_FIELDS = ("pair", "subject", "a", "b", "choice")

# What a filled cell may say. `a` or `b` names the render judged more like the
# subject; `tie` is allowed because forcing a preference the operator does not
# have manufactures a signal rather than measuring one.
CHOICES = frozenset({"a", "b", "tie"})


class NotBlind(Exception):
    """The labels cannot be shown to predate the scores, so they cannot check them."""


class MalformedSheet(Exception):
    """The filled sheet is not something a correlation can be computed from."""


@dataclass(frozen=True)
class Pair:
    """One within-subject comparison, carrying no score by construction.

    There is no field here a metric could be written into. That is the point: a
    sheet that *could* carry a score is one revision away from carrying one.
    """

    pair: str
    subject: str
    a: str
    b: str


@dataclass(frozen=True)
class Judgement:
    """One filled row: the pair, and which side the operator chose."""

    pair: str
    subject: str
    a: str
    b: str
    choice: str


class Ordering(Protocol):
    """Answers whether the labels were committed before any score existed."""

    def labels_are_prior(self, labels: Path, scores: list[Path]) -> bool:
        """Return True only if `labels` was committed before every path in `scores`."""
        ...


class GitOrdering:
    """Asks git when each path first appeared, because git is what proves it.

    A timestamp inside the sheet would be written by whoever wrote the sheet, and
    a promise from the person being checked is not a check. A commit is a fact
    about a repository that the person filling in the sheet does not author alone.

    Any failure -- not a repository, a path git has never seen -- answers **False**
    rather than True. The whole point is that this may only ever license a
    correlation it can positively demonstrate.
    """

    def __init__(self, repo: Path | None = None) -> None:
        """Bind to a repository root; the current directory by default."""
        self.repo = repo

    def _first_commit_time(self, path: Path) -> int | None:
        """Return the unix time of the commit that first added `path`, or None."""
        try:
            out = subprocess.run(
                ["git", "log", "--diff-filter=A", "--format=%ct", "--", str(path)],
                capture_output=True,
                text=True,
                cwd=self.repo,
                check=True,
            ).stdout.split()
        except (subprocess.CalledProcessError, OSError):
            return None
        # `git log` is newest-first, so the *first* time this path was added is
        # the last line. A path added, deleted and re-added takes the earliest.
        return int(out[-1]) if out else None

    def labels_are_prior(self, labels: Path, scores: list[Path]) -> bool:
        """Return True only if the labels were committed before every score was."""
        when = self._first_commit_time(labels)
        if when is None:
            return False
        for score in scores:
            scored_at = self._first_commit_time(score)
            # An uncommitted score is fine: it cannot have been seen in a commit
            # the labels came after. A score committed at or before the labels is
            # not -- equal timestamps mean the same commit, which is exactly the
            # "committed together" case the separate-commit rule forbids.
            if scored_at is not None and scored_at <= when:
                return False
        return True


def pairs_for(renders: dict[str, list[str]], rng: Random) -> list[Pair]:
    """Build every within-subject pair, in a randomised order and with no scores.

    Each subject contributes every unordered pair of its own renders -- five
    renders give ten pairs, four subjects give the forty judgements design.md D10
    asks for. **No pair spans two subjects**, so the operator is never asked to
    compare two different people.

    The `rng` is injected, which is the whole reason this is testable, and it
    randomises two things rather than one: the order the pairs appear in, and
    which render of each pair is shown as `a`. Without the second, a systematic
    preference for the left-hand column would be indistinguishable from a
    preference for lower-numbered renders.
    """
    pairs: list[Pair] = []
    for subject in sorted(renders):
        # Rendered as `<subject>/<image>`, so a render's identifier is unique
        # across the whole sheet and "both sides came from one subject" is a
        # property of the identifier rather than of a column the caller supplied.
        images = sorted(f"{subject}/{image}" for image in renders[subject])
        for left, right in itertools.combinations(images, 2):
            if rng.random() < 0.5:
                left, right = right, left
            pairs.append(Pair(pair="", subject=subject, a=left, b=right))
    rng.shuffle(pairs)
    # Numbered after the shuffle, so the identifier says where a row sits on the
    # sheet and carries no trace of the order the pairs were generated in.
    return [
        Pair(pair=f"p{i:02d}", subject=p.subject, a=p.a, b=p.b)
        for i, p in enumerate(pairs, start=1)
    ]


def write_sheet(pairs: list[Pair], path: Path) -> None:
    """Write the comparison sheet, with `choice` left empty for the operator."""
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SHEET_FIELDS)
        writer.writeheader()
        for pair in pairs:
            writer.writerow(
                {
                    "pair": pair.pair,
                    "subject": pair.subject,
                    "a": pair.a,
                    "b": pair.b,
                    "choice": "",
                }
            )


def read_labels(path: Path) -> list[Judgement]:
    """Read a filled sheet, refusing one that cannot be correlated.

    Refuses rather than dropping bad rows: a correlation computed over "the rows
    that happened to parse" reports a count that does not match the sheet, and
    the count is the thing a reader discounts the correlation by.
    """
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    judgements: list[Judgement] = []
    for row in rows:
        missing = [f for f in SHEET_FIELDS if f not in row]
        if missing:
            raise MalformedSheet(f"{path}: row {row} is missing {missing}")
        choice = (row["choice"] or "").strip().lower()
        if choice not in CHOICES:
            raise MalformedSheet(
                f"{path}: pair {row['pair']} has choice {row['choice']!r}; "
                f"expected one of {sorted(CHOICES)}"
            )
        if row["a"] == row["b"]:
            raise MalformedSheet(
                f"{path}: pair {row['pair']} compares a render to itself"
            )
        judgements.append(
            Judgement(
                pair=row["pair"],
                subject=row["subject"],
                a=row["a"],
                b=row["b"],
                choice=choice,
            )
        )
    return judgements


def pairs_span_two_subjects(pairs: list[Pair]) -> list[str]:
    """Return the identifiers of any pair whose two renders are not one subject's.

    A render is identified by its subject and its filename, so a pair spanning
    subjects is one whose sides came from different run directories. Reported
    rather than asserted, so the caller decides what to do about it.
    """
    return [
        p.pair
        for p in pairs
        if not (p.a.startswith(f"{p.subject}/") and p.b.startswith(f"{p.subject}/"))
    ]


def agreement(
    judgements: list[Judgement],
    # A `Mapping`, not a `dict`: `dict` is invariant in its value type, so a
    # caller holding `dict[str, float]` -- an axis that refused nothing -- could
    # not pass it to a parameter declared `dict[str, float | None]`.
    scores: Mapping[str, float | None],
    higher_is_closer: bool,
) -> tuple[float | None, int, int]:
    """Return how often one axis agreed with the operator, and over how many pairs.

    The count is returned beside the figure and never folded into it, because at
    forty judgements the count is what a reader discounts the number by
    (design.md D2).

    Ties are **excluded rather than scored**. A tie says the operator could not
    separate the two renders; an axis is neither right nor wrong about a question
    that was not asked, and counting a tie as half agreement would pull every axis
    toward 0.5 by an amount that depends on how decisive the operator felt.

    A pair either of whose renders the axis refused or could not measure is
    excluded too, and counted separately -- an axis is not penalised for
    abstaining, nor credited for it.

    Returns None when nothing was comparable, which is absence rather than a zero:
    the pose axis is saturated on this baseline and will land here.
    """
    agreed = 0
    used = 0
    skipped = 0
    for j in judgements:
        first, second = scores.get(j.a), scores.get(j.b)
        if j.choice == "tie" or first is None or second is None or first == second:
            skipped += 1
            continue
        used += 1
        better = j.a if (first > second) == higher_is_closer else j.b
        agreed += better == ({"a": j.a, "b": j.b}[j.choice])
    return (agreed / used if used else None), used, skipped


def correlate(
    labels: Path,
    score_paths: list[Path],
    ordering: Ordering,
) -> list[Judgement]:
    """Read the labels, but only once git shows they predate every score.

    This is the whole defence against the operator peeking, and it is a real one:
    the sheet is committed in its own commit before any score for these renders is
    computed, and a repository records that in a way the person filling in the
    sheet does not author alone.
    """
    if not ordering.labels_are_prior(labels, score_paths):
        raise NotBlind(
            f"{labels} cannot be shown to have been committed before the scores "
            f"in {[str(p) for p in score_paths]}. The labels are only a check on "
            "the metrics if they were recorded before the metrics existed, and "
            "git ordering is what proves that. Refusing to correlate."
        )
    return read_labels(labels)


def scores_from_records(records: list[dict], axis: str) -> dict[str, float | None]:
    """Pull one axis's value per render out of the scorer's own JSON records.

    A refused axis contributes None rather than being dropped, so `agreement`
    counts it as an abstention rather than never seeing the render at all.
    """
    out: dict[str, float | None] = {}
    for record in records:
        subject = record.get("subject", "")
        image = record.get("image") or Path(str(record.get("render", ""))).name
        value = None
        for entry in record.get("axes", []):
            if entry["name"] == axis and entry.get("refused") is None:
                value = entry.get("value")
        out[f"{subject}/{image}"] = value
    return out


def load_records(paths: list[Path]) -> list[dict]:
    """Read the scorer's per-render records."""
    return [json.loads(p.read_text()) for p in paths]
