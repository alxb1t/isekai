import csv
import json
import random
import subprocess
from pathlib import Path

import pytest

from isekai.labels import (
    CHOICES,
    SHEET_FIELDS,
    GitOrdering,
    Judgement,
    MalformedSheet,
    NotBlind,
    Pair,
    agreement,
    correlate,
    pairs_for,
    pairs_span_two_subjects,
    read_labels,
    scores_from_records,
    write_sheet,
)

# The four subjects that get labelled: five renders each, ten pairs each, forty
# judgements. The two refusal-path subjects are deliberately absent.
LABELLED = {
    "s1_control_blonde": [f"{i}.png" for i in range(5)],
    "s2_control_brunette": [f"{i}.png" for i in range(5)],
    "s3_multitone_balayage": [f"{i}.png" for i in range(5)],
    "s4_multitone_bob": [f"{i}.png" for i in range(5)],
}


class FakeOrdering:
    """Answers the priority question from a canned verdict, recording the ask."""

    def __init__(self, prior: bool) -> None:
        self.prior = prior
        self.asked: list[tuple[Path, list[Path]]] = []

    def labels_are_prior(self, labels: Path, scores: list[Path]) -> bool:
        self.asked.append((labels, scores))
        return self.prior


def _filled(path: Path, pairs: list[Pair], choices: list[str]) -> Path:
    """Write a sheet with the choices already filled in."""
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SHEET_FIELDS)
        writer.writeheader()
        for pair, choice in zip(pairs, choices):
            writer.writerow(
                {
                    "pair": pair.pair,
                    "subject": pair.subject,
                    "a": pair.a,
                    "b": pair.b,
                    "choice": choice,
                }
            )
    return path


# --- the sheet --------------------------------------------------------------


@pytest.mark.spec("evaluation:labels:sheet-carries-no-scores")
def test_the_sheet_contains_no_metric_value_for_any_render(tmp_path: Path) -> None:
    pairs = pairs_for(LABELLED, random.Random(7))
    sheet = tmp_path / "sheet.csv"
    write_sheet(pairs, sheet)
    text = sheet.read_text()

    # Every column the sheet has, named: there is nowhere a score could sit.
    assert list(csv.DictReader(sheet.open()).fieldnames or []) == list(SHEET_FIELDS)
    # And nothing that parses as a number appears anywhere in the body beyond the
    # render filenames and the pair identifiers.
    for row in csv.DictReader(sheet.open()):
        assert row["choice"] == ""
        for field in ("pair", "subject", "a", "b"):
            with pytest.raises(ValueError):
                float(row[field])
    assert "score" not in text.lower()
    assert "cosine" not in text.lower()


@pytest.mark.spec("evaluation:labels:sheet-carries-no-scores")
def test_the_pair_type_has_no_field_a_score_could_be_written_into() -> None:
    # Structural rather than incidental: a sheet that *could* carry a score is
    # one revision away from carrying one.
    assert set(Pair.__dataclass_fields__) == {"pair", "subject", "a", "b"}


@pytest.mark.spec("evaluation:labels:sheet-carries-no-scores")
def test_the_choice_column_is_empty_for_the_operator_to_fill(tmp_path: Path) -> None:
    pairs = pairs_for(LABELLED, random.Random(7))
    sheet = tmp_path / "sheet.csv"
    write_sheet(pairs, sheet)

    assert all(row["choice"] == "" for row in csv.DictReader(sheet.open()))


# --- within one subject -----------------------------------------------------


@pytest.mark.spec("evaluation:labels:pairs-are-within-one-subject")
def test_every_pair_draws_both_renders_from_the_same_subject() -> None:
    pairs = pairs_for(LABELLED, random.Random(7))

    assert pairs_span_two_subjects(pairs) == []
    for pair in pairs:
        assert pair.a.split("/")[0] == pair.subject
        assert pair.b.split("/")[0] == pair.subject


@pytest.mark.spec("evaluation:labels:pairs-are-within-one-subject")
def test_no_pair_asks_the_operator_to_compare_two_different_people() -> None:
    pairs = pairs_for(LABELLED, random.Random(7))

    assert all(pair.a.split("/")[0] == pair.b.split("/")[0] for pair in pairs)


@pytest.mark.spec("evaluation:labels:pairs-are-within-one-subject")
def test_a_pair_that_spans_two_subjects_is_reported() -> None:
    # The check must be able to fail, or it proves nothing about the ones above.
    smuggled = Pair(
        pair="p01",
        subject="s1_control_blonde",
        a="s1_control_blonde/0.png",
        b="s2_control_brunette/0.png",
    )

    assert pairs_span_two_subjects([smuggled]) == ["p01"]


@pytest.mark.spec("evaluation:labels:pairs-are-within-one-subject")
def test_four_subjects_of_five_renders_give_the_forty_judgements() -> None:
    pairs = pairs_for(LABELLED, random.Random(7))

    assert len(pairs) == 40
    for subject in LABELLED:
        assert sum(1 for p in pairs if p.subject == subject) == 10
    # Every unordered pair appears exactly once, in one orientation or the other.
    seen = {frozenset((p.a, p.b)) for p in pairs}
    assert len(seen) == 40


@pytest.mark.spec("evaluation:labels:pairs-are-within-one-subject")
def test_the_sheets_order_and_sides_are_randomised_by_the_injected_rng() -> None:
    one = pairs_for(LABELLED, random.Random(1))
    two = pairs_for(LABELLED, random.Random(2))
    same = pairs_for(LABELLED, random.Random(1))

    assert [p.a for p in one] == [p.a for p in same]
    assert [(p.subject, p.a, p.b) for p in one] != [(p.subject, p.a, p.b) for p in two]
    # Both orientations occur, so a left-column preference is not confounded with
    # a preference for lower-numbered renders.
    assert any(p.a > p.b for p in one) and any(p.a < p.b for p in one)


# --- the labels must be demonstrably prior ----------------------------------


@pytest.mark.spec("evaluation:labels:correlation-requires-prior-labels")
def test_a_correlation_against_labels_not_shown_prior_is_refused(
    tmp_path: Path,
) -> None:
    pairs = pairs_for(LABELLED, random.Random(7))
    sheet = _filled(tmp_path / "labels.csv", pairs, ["a"] * 40)
    ordering = FakeOrdering(prior=False)

    with pytest.raises(NotBlind) as refused:
        correlate(sheet, [tmp_path / "0.eval.json"], ordering)

    assert "committed before the scores" in str(refused.value)
    assert "git ordering" in str(refused.value).lower()


@pytest.mark.spec("evaluation:labels:correlation-requires-prior-labels")
def test_a_correlation_against_labels_shown_prior_is_allowed(tmp_path: Path) -> None:
    pairs = pairs_for(LABELLED, random.Random(7))
    sheet = _filled(tmp_path / "labels.csv", pairs, ["a"] * 40)
    ordering = FakeOrdering(prior=True)

    assert len(correlate(sheet, [tmp_path / "0.eval.json"], ordering)) == 40
    assert ordering.asked[0][0] == sheet


@pytest.mark.spec("evaluation:labels:correlation-requires-prior-labels")
def test_the_ordering_check_refuses_a_file_git_has_never_seen(
    tmp_path: Path,
) -> None:
    # The real check, not the fake: an uncommitted sheet cannot be shown to be
    # prior to anything, so it answers False rather than defaulting to True.
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    sheet = tmp_path / "labels.csv"
    sheet.write_text("pair,subject,a,b,choice\n")

    assert GitOrdering(tmp_path).labels_are_prior(sheet, []) is False


@pytest.mark.spec("evaluation:labels:correlation-requires-prior-labels")
def test_the_ordering_check_refuses_when_a_score_shares_the_labels_commit(
    tmp_path: Path,
) -> None:
    # Committed together is exactly the case the separate-commit rule forbids:
    # it cannot show the labels came first.
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "labels.csv").write_text("pair,subject,a,b,choice\n")
    (tmp_path / "0.eval.json").write_text("{}")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "both at once"], cwd=tmp_path, check=True)

    assert (
        GitOrdering(tmp_path).labels_are_prior(
            tmp_path / "labels.csv", [tmp_path / "0.eval.json"]
        )
        is False
    )


@pytest.mark.spec("evaluation:labels:correlation-requires-prior-labels")
def test_the_ordering_check_allows_labels_committed_in_an_earlier_commit(
    tmp_path: Path,
) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "labels.csv").write_text("pair,subject,a,b,choice\n")
    subprocess.run(["git", "add", "labels.csv"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "labels, alone", "--date", "2020-01-01T00:00:00"],
        cwd=tmp_path,
        check=True,
        env={"GIT_COMMITTER_DATE": "2020-01-01T00:00:00", "PATH": "/usr/bin:/bin"},
    )
    (tmp_path / "0.eval.json").write_text("{}")
    subprocess.run(["git", "add", "0.eval.json"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "scores, after"], cwd=tmp_path, check=True)

    assert (
        GitOrdering(tmp_path).labels_are_prior(
            tmp_path / "labels.csv", [tmp_path / "0.eval.json"]
        )
        is True
    )


# --- reading a filled sheet -------------------------------------------------


@pytest.mark.spec("evaluation:labels:correlation-requires-prior-labels")
def test_a_sheet_with_an_unfilled_row_is_refused_rather_than_dropped(
    tmp_path: Path,
) -> None:
    # A correlation over "the rows that happened to parse" reports a count that
    # does not match the sheet, and the count is what a reader discounts by.
    pairs = pairs_for(LABELLED, random.Random(7))
    sheet = _filled(tmp_path / "labels.csv", pairs, ["a"] * 39 + [""])

    with pytest.raises(MalformedSheet):
        read_labels(sheet)


@pytest.mark.spec("evaluation:labels:correlation-requires-prior-labels")
def test_every_allowed_choice_reads_back(tmp_path: Path) -> None:
    pairs = pairs_for(LABELLED, random.Random(7))[:3]
    sheet = _filled(tmp_path / "labels.csv", pairs, ["a", "B", " tie "])

    assert [j.choice for j in read_labels(sheet)] == ["a", "b", "tie"]
    assert CHOICES == {"a", "b", "tie"}


# --- agreement, per axis, with its count ------------------------------------


@pytest.mark.spec("evaluation:labels:correlation-is-per-axis")
def test_agreement_is_reported_with_the_count_behind_it() -> None:
    judgements = [
        Judgement("p01", "s1", "s1/0.png", "s1/1.png", "a"),
        Judgement("p02", "s1", "s1/2.png", "s1/3.png", "b"),
    ]
    scores = {"s1/0.png": 0.9, "s1/1.png": 0.1, "s1/2.png": 0.1, "s1/3.png": 0.9}

    value, used, skipped = agreement(judgements, scores, higher_is_closer=True)
    assert (value, used, skipped) == (1.0, 2, 0)


@pytest.mark.spec("evaluation:labels:correlation-is-per-axis")
def test_a_lower_is_closer_axis_agrees_in_the_other_direction() -> None:
    judgements = [Judgement("p01", "s1", "s1/0.png", "s1/1.png", "a")]
    scores = {"s1/0.png": 1.0, "s1/1.png": 9.0}

    assert agreement(judgements, scores, higher_is_closer=False)[0] == 1.0
    assert agreement(judgements, scores, higher_is_closer=True)[0] == 0.0


@pytest.mark.spec("evaluation:labels:correlation-is-per-axis")
def test_ties_are_excluded_rather_than_scored_as_half() -> None:
    # Counting a tie as half agreement pulls every axis toward 0.5 by an amount
    # that depends on how decisive the operator felt, which is not a property of
    # the axis.
    judgements = [
        Judgement("p01", "s1", "s1/0.png", "s1/1.png", "tie"),
        Judgement("p02", "s1", "s1/2.png", "s1/3.png", "a"),
    ]
    scores = {"s1/0.png": 0.9, "s1/1.png": 0.1, "s1/2.png": 0.9, "s1/3.png": 0.1}

    assert agreement(judgements, scores, higher_is_closer=True) == (1.0, 1, 1)


@pytest.mark.spec("evaluation:labels:correlation-is-per-axis")
def test_a_refused_axis_abstains_rather_than_being_penalised() -> None:
    judgements = [Judgement("p01", "s1", "s1/0.png", "s1/1.png", "a")]

    assert agreement(judgements, {"s1/0.png": None, "s1/1.png": 0.5}, True) == (
        None,
        0,
        1,
    )


@pytest.mark.spec("evaluation:labels:correlation-is-per-axis")
def test_a_saturated_axis_reports_absence_rather_than_a_number() -> None:
    # The pose axis on this baseline: every render scores identically, so every
    # pair is a tie in the metric and there is nothing to agree or disagree with.
    judgements = [
        Judgement("p01", "s1", "s1/0.png", "s1/1.png", "a"),
        Judgement("p02", "s1", "s1/2.png", "s1/3.png", "b"),
    ]
    scores = dict.fromkeys(["s1/0.png", "s1/1.png", "s1/2.png", "s1/3.png"], 1.0)

    assert agreement(judgements, scores, higher_is_closer=True) == (None, 0, 2)


@pytest.mark.spec("evaluation:labels:correlation-is-per-axis")
def test_scores_are_pulled_per_axis_from_the_scorers_own_records() -> None:
    records = [
        {
            "subject": "s1",
            "image": "0.png",
            "axes": [
                {"name": "face_styleid", "value": 0.8, "refused": None},
                {"name": "hair_colour_delta_e", "value": 3.2, "refused": None},
            ],
        },
        {
            "subject": "s1",
            "image": "1.png",
            "axes": [
                {"name": "face_styleid", "value": None, "refused": "the guard"},
                {"name": "hair_colour_delta_e", "value": 5.0, "refused": None},
            ],
        },
    ]

    assert scores_from_records(records, "face_styleid") == {
        "s1/0.png": 0.8,
        "s1/1.png": None,
    }
    assert scores_from_records(records, "hair_colour_delta_e") == {
        "s1/0.png": 3.2,
        "s1/1.png": 5.0,
    }


@pytest.mark.spec("evaluation:labels:correlation-is-per-axis")
def test_axes_are_never_rolled_up_into_one_agreement(tmp_path: Path) -> None:
    # `agreement` takes one axis's scores and returns one figure. There is no
    # signature here that could average two axes together (design.md D2).
    records = json.loads(
        json.dumps(
            [
                {
                    "subject": "s1",
                    "image": "0.png",
                    "axes": [
                        {"name": "face_styleid", "value": 0.8, "refused": None},
                        {"name": "pose_pck", "value": 1.0, "refused": None},
                    ],
                }
            ]
        )
    )

    assert set(scores_from_records(records, "face_styleid")) == {"s1/0.png"}
    assert set(scores_from_records(records, "pose_pck")) == {"s1/0.png"}
