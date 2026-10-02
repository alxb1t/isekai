import json
import re
from pathlib import Path

import pytest

from evaluation.cohort import (
    Cohort,
    Photograph,
    Record,
    chance,
    hits,
    load_cohort,
    rank,
    record,
    scored,
    table,
    unscored,
)
from isekai.boundary.provision import digest_of
from isekai.foundation.refusal import Refusal

FIXTURE = Path(__file__).resolve().parent / "cohort"
ENCODER = {
    "detector": {"dest": "d.onnx", "sha256": "d" * 64},
    "encoder": {"dest": "e.onnx", "sha256": "e" * 64},
}


def _cohort(root: Path, people: dict[str, int]) -> Cohort:
    """Write `count` photographs per person under `root/cohort`, distinct bytes each."""
    for person, count in people.items():
        (root / "cohort" / person).mkdir(parents=True)
        for n in range(1, count + 1):
            (root / "cohort" / person / f"{n}.png").write_bytes(f"{person}{n}".encode())
    return load_cohort(root / "cohort")


def _named(cohort: Cohort, name: str) -> Photograph:
    """Return the cohort photograph called `name`, e.g. `p1/1.png`."""
    return next(p for p in cohort.photographs if p.name == name)


@pytest.mark.spec("evaluation:cohort:a-run-is-matched-by-digest")
def test_a_run_is_scored_as_the_photograph_whose_digest_its_frame_records(
    tmp_path: Path,
) -> None:
    cohort = _cohort(tmp_path, {"p1": 2, "p2": 1})
    frame_digest = digest_of(tmp_path / "cohort" / "p1" / "2.png")

    source = cohort.by_digest(frame_digest)
    assert source is not None
    ranked = rank(
        [1.0, 0.0],
        {p: [1.0, 0.0] if p == source else [0.0, 1.0] for p in cohort.photographs},
    )
    row = scored(source, "abc", 7, ranked)

    assert (row["person"], row["photograph"]) == ("p1", "p1/2.png")


@pytest.mark.spec("evaluation:cohort:a-run-outside-the-cohort-is-reported")
def test_a_run_outside_the_cohort_is_counted_and_the_others_are_scored(
    tmp_path: Path,
) -> None:
    cohort = _cohort(tmp_path, {"p1": 1, "p2": 1})
    p1, p2 = cohort.photographs
    assert cohort.by_digest("0" * 64) is None

    rec = record(cohort, {"f": [scored(p1, "r1", 1, [p1, p2])]}, 1, ENCODER)

    assert rec["outside_the_cohort"] == 1
    assert rec["flows"]["f"]["counts"]["photograph"] == {
        "hits": 1,
        "of": 1,
        "chance": 0.5,
    }
    assert "runs outside the cohort  1" in table(rec)


@pytest.mark.spec("evaluation:counts:photograph-level-hit")
def test_a_render_nearest_its_own_photograph_is_one_photograph_level_hit(
    tmp_path: Path,
) -> None:
    cohort = _cohort(tmp_path, {"p1": 2, "p2": 2})
    gallery = {
        _named(cohort, "p1/1.png"): [1.0, 0.0, 0.0],
        _named(cohort, "p1/2.png"): [0.8, 0.6, 0.0],
        _named(cohort, "p2/1.png"): [0.0, 1.0, 0.0],
        _named(cohort, "p2/2.png"): [0.0, 0.0, 1.0],
    }
    source = _named(cohort, "p1/1.png")

    ranked = rank([0.9, 0.1, 0.0], gallery)
    rec = record(cohort, {"f": [scored(source, "r", 1, ranked)]}, 0, ENCODER)

    assert ranked[0] == source
    assert rec["flows"]["f"]["counts"]["photograph"]["hits"] == 1


@pytest.mark.spec("evaluation:counts:person-level-excludes-the-source")
def test_the_person_level_hit_looks_past_the_render_s_own_photograph(
    tmp_path: Path,
) -> None:
    cohort = _cohort(tmp_path, {"p1": 2, "p2": 1})
    source, sibling, other = (
        _named(cohort, n) for n in ("p1/1.png", "p1/2.png", "p2/1.png")
    )
    # A render that copied its photograph: nearest its source, then the other person.
    copied = rank(
        [1.0, 0.0], {source: [1.0, 0.0], sibling: [0.0, 1.0], other: [0.9, 0.4]}
    )
    # A render of the person: its sibling is nearest once the source is set aside.
    alike = rank(
        [0.6, 0.8], {source: [1.0, 0.0], sibling: [0.6, 0.8], other: [0.0, 1.0]}
    )

    assert hits(copied, source) == (True, False)
    assert hits(alike, source) == (False, True)


@pytest.mark.spec("evaluation:counts:chance-is-reported")
def test_each_count_carries_its_denominator_and_the_hits_chance_gives(
    tmp_path: Path,
) -> None:
    cohort = _cohort(tmp_path, {"p1": 3, "p2": 1})
    p1, p2 = _named(cohort, "p1/1.png"), _named(cohort, "p2/1.png")
    rows = [
        scored(p1, "r1", 1, [p1, p2, *cohort.photographs[1:3]]),
        scored(p2, "r2", 1, [p2, *cohort.photographs[:3]]),
    ]

    counts = record(cohort, {"f": rows}, 0, ENCODER)["flows"]["f"]["counts"]

    assert chance(p1, cohort) == (1 / 4, 2 / 3)
    assert chance(p2, cohort) == (1 / 4, 0.0)
    assert counts["photograph"] == {"hits": 2, "of": 2, "chance": 0.5}
    assert counts["person"] == {"hits": 0, "of": 2, "chance": 0.7}


def _floats(value: object, path: str = "") -> list[str]:
    """Return the key path of every float under `value`."""
    if isinstance(value, float):
        return [path]
    if isinstance(value, dict):
        return [f for k, v in value.items() for f in _floats(v, f"{path}/{k}")]
    if isinstance(value, list):
        return [f for v in value for f in _floats(v, path)]
    return []


@pytest.mark.spec("evaluation:counts:no-average-no-percentage")
def test_neither_record_nor_table_carries_a_cosine_a_mean_or_a_percentage() -> None:
    rec: Record = json.loads((FIXTURE / "evaluation.json").read_text())
    written = json.dumps(rec) + table(rec)

    assert {path.rsplit("/", 1)[1] for path in _floats(rec)} == {"chance"}
    assert not re.search(r"%|cosine|mean|average", written, re.I)


@pytest.mark.spec("evaluation:table:one-row-per-flow")
def test_every_flow_has_its_own_counts_in_the_table(tmp_path: Path) -> None:
    cohort = _cohort(tmp_path, {"p1": 1, "p2": 1})
    p1, p2 = cohort.photographs
    flows = {
        "summon-anime-wai": [
            scored(p1, "r1", 1, [p1, p2]),
            scored(p2, "r2", 1, [p1, p2]),
        ],
        "control": [
            scored(p1, "r1", 2, [p2, p1]),
            unscored(p2, "r2", 2, "no face found"),
        ],
    }

    lines = table(record(cohort, flows, 0, ENCODER)).splitlines()

    assert re.fullmatch(r"control\s+0 / 1\s+0 / 1", lines[1])
    assert re.fullmatch(r"chance\s+0\.5 / 1\s+0\.0 / 1", lines[2])
    assert re.fullmatch(r"summon-anime-wai\s+1 / 2\s+0 / 2", lines[3])
    assert re.fullmatch(r"chance\s+1\.0 / 2\s+0\.0 / 2", lines[4])


@pytest.mark.spec("evaluation:table:the-table-re-derives-from-the-record")
def test_the_committed_table_re_derives_from_its_record() -> None:
    rec: Record = json.loads((FIXTURE / "evaluation.json").read_text())

    assert table(rec) == (FIXTURE / "evaluation.txt").read_text()


@pytest.mark.spec("evaluation:cohort:two-files-with-one-digest-are-refused")
def test_two_cohort_files_with_one_digest_refuse_naming_both(tmp_path: Path) -> None:
    for person in ("p1", "p2"):
        (tmp_path / person).mkdir()
        (tmp_path / person / "1.png").write_bytes(b"same")

    with pytest.raises(Refusal, match="p1/1.png and p2/1.png"):
        load_cohort(tmp_path)
