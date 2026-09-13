#!/usr/bin/env python3
"""PROTOTYPE -- N42: does the identity number measure a PERSON or a PHOTOGRAPH?

`face_likeness.py` answers *which of N photographs did this render come from*.
It is stylization-invariant and it is the method `notes/IDENTITY.md` exports --
but across four rounds it was only ever run on sets with **one photograph per
person**, so a hit could equally mean *"the render matches this person"* or
*"the render matches this photograph's framing, lighting and pose"*. The project
had exactly one same-person pair (`real_photo.py`'s `SAME_PERSON`), which is n=1.

N42's phone set is ten photographs of **four** people, so the question separates:

    if the number measures a PERSON      the OTHER photographs of the same person
                                         rank just below the correct one
    if it measures a PHOTOGRAPH          they rank no better than strangers

The test is the **mean rank of the same-person photographs**, excluding the
render's own source, against a permutation null. Flow `D` is the control: it
never reads the photograph, so it must show nothing.

    PYTHONPATH=. uv run python prototype/same_person.py
"""

import argparse
import json
import random
from pathlib import Path

GROUPS = Path("prototype/inputs/real/phone/groups.json")


def person_of(groups: dict[str, list[str]]) -> dict[str, str]:
    """Return subject id -> person id."""
    return {sid: person for person, sids in groups.items() for sid in sids}


def mean_rank(rows: list[dict], who: dict[str, str]) -> tuple[float, int, list]:
    """Return the mean rank of same-person photographs, and the per-render detail."""
    ranks: list[int] = []
    detail = []
    for row in rows:
        sid = row["subject"]
        ranking = row["ranking"]
        siblings = [s for s in ranking if who[s] == who[sid] and s != sid]
        if not siblings:
            continue
        got = [ranking.index(s) + 1 for s in siblings]
        ranks.extend(got)
        detail.append(
            {
                "subject": sid,
                "person": who[sid],
                "rank_of_own": ranking.index(sid) + 1,
                "siblings": dict(zip(siblings, got, strict=True)),
            }
        )
    return (sum(ranks) / len(ranks), len(ranks), detail)


def permutation_p(rows: list[dict], who: dict[str, str], observed: float,
                  rng: random.Random, trials: int = 100_000) -> float:
    """Fraction of shuffled rankings whose mean sibling rank is <= the observed one.

    The null shuffles each render's ranking independently, which preserves the
    group sizes and the number of siblings per render exactly -- so the only
    thing destroyed is the association between a photograph's rank and whose
    face it is.
    """
    better = 0
    for _ in range(trials):
        ranks: list[int] = []
        for row in rows:
            sid = row["subject"]
            shuffled = row["ranking"][:]
            rng.shuffle(shuffled)
            siblings = [s for s in shuffled if who[s] == who[sid] and s != sid]
            ranks.extend(shuffled.index(s) + 1 for s in siblings)
        if ranks and sum(ranks) / len(ranks) <= observed:
            better += 1
    return better / trials


def main() -> None:
    """Score both arms against the operator-confirmed grouping."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--groups", type=Path, default=GROUPS)
    p.add_argument("--seed", type=int, default=20260913)
    args = p.parse_args()

    groups = json.loads(args.groups.read_text())["groups"]
    who = person_of(groups)
    results = json.loads(args.results.read_text())
    rng = random.Random(args.seed)

    print(f"groups: {groups}")
    sizes = [len(v) for v in groups.values()]
    print(f"{len(groups)} people, {sum(sizes)} photographs, sizes {sizes}\n")

    for arm, data in results["arms"].items():
        rows = [r for r in data["rows"] if r.get("scored")]
        observed, n, detail = mean_rank(rows, who)
        p_value = permutation_p(rows, who, observed, rng)
        print(f"=== arm {arm} · flow {data['flow']} ===")
        print(f"  own photograph top-1 : {data['hits']}/{data['of']}")
        print(f"  sibling mean rank    : {observed:.2f}  over {n} sibling pairs")
        print(f"  permutation p        : {p_value:.4f}")
        print(
            "  verdict              : "
            + (
                "SAME PERSON RANKS ABOVE CHANCE -- the number tracks the person"
                if p_value < 0.05
                else "indistinguishable from chance -- no person-level signal"
            )
        )
        for d in detail:
            sibs = ", ".join(f"{k}#{v}" for k, v in d["siblings"].items())
            print(f"    {d['subject']:<12} own#{d['rank_of_own']}   siblings: {sibs}")
        print()


if __name__ == "__main__":
    main()
