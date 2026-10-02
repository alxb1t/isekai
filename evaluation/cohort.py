"""The cohort, the two counts over it, and the record and table they make.

A cohort is `<directory>/<person>/<photograph>`: the directory is the ground truth
for who each photograph is of. Each render ranks every cohort photograph by
cosine; the counts are whether its own photograph is nearest, and whether, with
that one removed, the nearest is the same person. No cosine leaves this module.

Stdlib and `digest_of` alone, so the arithmetic is tested on vectors written by
hand and never needs the encoder.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

from isekai.boundary.provision import digest_of
from isekai.foundation.refusal import Refusal

Vector = Sequence[float]
Outcome = Literal["hit", "miss", "no face found", "not rendered"]


@dataclass(frozen=True)
class Photograph:
    """One cohort file: whose it is, where it is, and the digest a run is keyed by."""

    person: str
    path: Path
    sha256: str

    @property
    def name(self) -> str:
        """Return the photograph's path relative to the cohort, e.g. `p1/1.png`."""
        return f"{self.person}/{self.path.name}"


@dataclass(frozen=True)
class Cohort:
    """Every photograph of every person, in directory order."""

    directory: Path
    photographs: tuple[Photograph, ...]

    @property
    def people(self) -> list[str]:
        """Return the people, once each, in order."""
        return list(dict.fromkeys(p.person for p in self.photographs))

    def by_digest(self, sha256: str) -> Photograph | None:
        """Return the photograph whose bytes hash to `sha256`, or None."""
        return next((p for p in self.photographs if p.sha256 == sha256), None)


class Row(TypedDict):
    """One cohort photograph's outcome in one flow."""

    person: str
    photograph: str
    run: str | None
    seed: int | None
    outcome: Outcome
    nearest: str | None
    nearest_without_source: str | None
    photograph_hit: bool
    person_hit: bool
    also_rendered: list[int]


class Count(TypedDict):
    """Hits over the renders scored, beside the hits chance gives over them."""

    hits: int
    of: int
    chance: float


class FlowRecord(TypedDict):
    """One flow's rows and its two counts."""

    rows: list[Row]
    counts: dict[str, Count]


class Record(TypedDict):
    """One batch's evaluation: the cohort, the encoder, every flow, every stray run."""

    cohort: dict[str, object]
    encoder: dict[str, str]
    flows: dict[str, FlowRecord]
    outside_the_cohort: list[str]


def load_cohort(directory: Path) -> Cohort:
    """Return every file directly under each person's directory, with its digest.

    A dot-file is not a photograph, so a `.DS_Store` is passed over. Two files with
    one digest refuse, because a run keyed by those bytes would be both people's.
    """
    if not directory.is_dir():
        raise Refusal(
            f"{directory} is not a directory; give --cohort the directory holding "
            "one sub-directory per person"
        )
    photographs = tuple(
        Photograph(person.name, path, digest_of(path))
        for person in sorted(directory.iterdir())
        if person.is_dir() and not person.name.startswith(".")
        for path in sorted(person.iterdir())
        if path.is_file() and not path.name.startswith(".")
    )
    if len(photographs) < 2:
        raise Refusal(
            f"{directory} holds {len(photographs)} photographs, and ranking needs "
            "at least two; put each person's photographs in a sub-directory of it"
        )
    seen: dict[str, Photograph] = {}
    for photograph in photographs:
        if (twin := seen.setdefault(photograph.sha256, photograph)) is not photograph:
            raise Refusal(
                f"{twin.name} and {photograph.name} are the same bytes, so a run "
                "of them would belong to both; delete one from the cohort"
            )
    return Cohort(directory, photographs)


def _cosine(a: Vector, b: Vector) -> float:
    """Return the cosine between two vectors of one length."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    return dot / (math.hypot(*a) * math.hypot(*b))


def rank(render: Vector, gallery: Mapping[Photograph, Vector]) -> list[Photograph]:
    """Return the gallery's photographs, nearest the render first."""
    return sorted(gallery, key=lambda p: _cosine(render, gallery[p]), reverse=True)


def hits(ranked: Sequence[Photograph], source: Photograph) -> tuple[bool, bool]:
    """Return the photograph-level and the person-level hit for one ranking.

    The person-level hit skips the source, so a render that copied its
    photograph's pixels earns the first and not the second.
    """
    without = next(p for p in ranked if p != source)
    return ranked[0] == source, without.person == source.person


def chance(source: Photograph, cohort: Cohort) -> tuple[float, float]:
    """Return the hits chance gives one render: `1 / N` and `(K_P - 1) / (N - 1)`."""
    n = len(cohort.photographs)
    k = sum(p.person == source.person for p in cohort.photographs)
    return 1 / n, (k - 1) / (n - 1)


def scored(
    source: Photograph, run: str, seed: int, ranked: Sequence[Photograph]
) -> Row:
    """Return the row of a render whose face was found and ranked."""
    photograph_hit, person_hit = hits(ranked, source)
    without = next(p for p in ranked if p != source)
    return {
        "person": source.person,
        "photograph": source.name,
        "run": run,
        "seed": seed,
        "outcome": "hit" if photograph_hit and person_hit else "miss",
        "nearest": ranked[0].name,
        "nearest_without_source": without.name,
        "photograph_hit": photograph_hit,
        "person_hit": person_hit,
        "also_rendered": [],
    }


def unscored(
    source: Photograph, run: str | None, seed: int | None, outcome: Outcome
) -> Row:
    """Return the row of a photograph with no ranked render, naming why."""
    return {
        "person": source.person,
        "photograph": source.name,
        "run": run,
        "seed": seed,
        "outcome": outcome,
        "nearest": None,
        "nearest_without_source": None,
        "photograph_hit": False,
        "person_hit": False,
        "also_rendered": [],
    }


def record(
    cohort: Cohort,
    flows: Mapping[str, Sequence[Row]],
    outside: Sequence[str],
    encoder: Mapping[str, str],
) -> Record:
    """Return the batch's record: a row per cohort photograph per flow, and counts.

    A photograph a flow holds no row for is `not rendered`. A count is over the
    renders scored, and its chance is summed over the same renders.
    """
    by_name = {p.name: p for p in cohort.photographs}
    out: dict[str, FlowRecord] = {}
    for flow, given in sorted(flows.items()):
        have = {row["photograph"]: row for row in given}
        rows = [
            have.get(p.name) or unscored(p, None, None, "not rendered")
            for p in cohort.photographs
        ]
        ranked = [row for row in rows if row["outcome"] in ("hit", "miss")]
        odds = [chance(by_name[row["photograph"]], cohort) for row in ranked]
        out[flow] = {
            "rows": rows,
            "counts": {
                "photograph": {
                    "hits": sum(row["photograph_hit"] for row in ranked),
                    "of": len(ranked),
                    "chance": round(sum(photo for photo, _ in odds), 1),
                },
                "person": {
                    "hits": sum(row["person_hit"] for row in ranked),
                    "of": len(ranked),
                    "chance": round(sum(person for _, person in odds), 1),
                },
            },
        }
    return {
        "cohort": {
            "directory": cohort.directory.name,
            "people": cohort.people,
            "photographs": len(cohort.photographs),
        },
        "encoder": dict(encoder),
        "flows": out,
        "outside_the_cohort": sorted(outside),
    }


def _row_line(flow: str, row: Row) -> str:
    """Return one non-hit row as a line naming its photograph and outcome."""
    parts = [flow, row["photograph"], row["outcome"]]
    if row["run"] is not None:
        parts.append(f"run {row['run']} seed {row['seed']}")
    if row["outcome"] == "miss":
        parts.append(f"nearest {row['nearest']}")
        parts.append(f"nearest without source {row['nearest_without_source']}")
    return "  ".join(parts)


def table(rec: Record) -> str:
    """Return the table for a record: each flow's counts, chance, then every non-hit.

    e.g. `summon-anime-wai   15 / 18   14 / 18` above `chance   1.0 / 18   2.1 / 18`
    """
    head = ("", "photograph-level", "person-level")
    lines: list[tuple[str, str, str]] = []
    for flow, entry in rec["flows"].items():
        photo, person = entry["counts"]["photograph"], entry["counts"]["person"]
        lines.append(
            (
                flow,
                f"{photo['hits']} / {photo['of']}",
                f"{person['hits']} / {person['of']}",
            )
        )
        lines.append(
            (
                "chance",
                f"{photo['chance']:.1f} / {photo['of']}",
                f"{person['chance']:.1f} / {person['of']}",
            )
        )
    width = max(len(name) for name, _, _ in [head, *lines])
    text = [
        f"{name:<{width}}   {a:>16}   {b:>12}".rstrip() for name, a, b in [head, *lines]
    ]
    failures = [
        _row_line(flow, row)
        for flow, entry in rec["flows"].items()
        for row in entry["rows"]
        if row["outcome"] != "hit"
    ]
    also = [
        f"{flow}  {row['photograph']}  also rendered "
        + ", ".join(map(str, row["also_rendered"]))
        for flow, entry in rec["flows"].items()
        for row in entry["rows"]
        if row["also_rendered"]
    ]
    outside = [f"outside the cohort  {run}" for run in rec["outside_the_cohort"]]
    for block in (failures, also, outside):
        if block:
            text += ["", *block]
    return "\n".join(text) + "\n"
