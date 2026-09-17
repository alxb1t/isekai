"""The inspection command: what a person reads to answer "where is this run".

Every fact here comes out of a file, which is the opposite rule from the
completion tests -- control flow uses listings, and people get the whole record.
"""

from pathlib import Path

import pytest

from isekai.foundation.flow import Schema, load_flow
from isekai.foundation.run import Run, open_run
from isekai.interface.run_view import listings, rendered, report
from isekai.pipeline.caption import FakeReader, caption
from isekai.pipeline.generate import prepare, render
from isekai.pipeline.review import approve, review
from isekai.pipeline.sheet import FakeSorter, sheet
from isekai.shared.vocabulary import Vocabulary
from tests.fakes import FakeComfyClient
from tests.images import jpeg_bytes

FLOW = "summon-v1"


@pytest.fixture
def run(tmp_path: Path, schema: Schema, vocabulary: Vocabulary) -> Run:
    """Return a run carried to an approved sheet, with a second draft waiting."""
    photo = tmp_path / "ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    made = open_run(photo, tmp_path / "runs")
    caption(made, FakeReader(implementation="fake-reader", models=("m1", "m2")))
    sheet(made, FakeSorter(implementation="fake-sorter"), schema, vocabulary, [FLOW])
    review(made, FLOW)
    approve(made, FLOW, schema, vocabulary)
    review(made, FLOW, new_version=True)
    return made


@pytest.mark.spec("cli:show:active-version-is-marked")
def test_each_stage_lists_its_versions_and_marks_the_active_one(run: Run) -> None:
    by_name = {(item.stage, item.flow): item for item in listings(run)}

    assert by_name[("captions", None)].versions == [1]
    assert by_name[("captions", None)].active == 1
    assert by_name[("review", FLOW)].versions == [1, 2]
    # 002 is a draft; the active one is the highest *approved*, because that is
    # what a downstream stage may proceed from.
    assert by_name[("review", FLOW)].active == 1


@pytest.mark.spec("cli:show:active-version-is-marked")
def test_approval_is_shown_where_the_concept_applies(run: Run) -> None:
    by_name = {(item.stage, item.flow): item for item in listings(run)}

    assert by_name[("review", FLOW)].approved == [1]
    assert by_name[("sheets", FLOW)].approved == []


@pytest.mark.spec("cli:show:active-version-is-marked")
def test_the_report_marks_the_active_version_for_each_stage(run: Run) -> None:
    lines = list(report(run))

    assert any(line.strip().startswith("* 001 approved") for line in lines)
    assert any(line.strip().startswith("002") for line in lines)
    assert "* marks the active version for each stage" in lines[-1]


@pytest.mark.spec("cli:show:producers-are-reported")
def test_each_artifacts_producer_is_shown(run: Run) -> None:
    by_name = {(item.stage, item.flow): item for item in listings(run)}

    assert "fake-reader" in by_name[("captions", None)].producers[1]
    assert "m1+m2" in by_name[("captions", None)].producers[1]
    assert "unpinned" in by_name[("captions", None)].producers[1]
    assert "fake-sorter" in by_name[("sheets", FLOW)].producers[1]
    assert "unedited" in by_name[("review", FLOW)].producers[1]


@pytest.mark.spec("cli:show:producers-are-reported")
def test_artifacts_from_different_implementations_are_distinguishable(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    caption(run, FakeReader(implementation="other-reader"), new_version=True)

    captions = next(item for item in listings(run) if item.stage == "captions")

    assert "fake-reader" in captions.producers[1]
    assert "other-reader" in captions.producers[2]
    assert captions.producers[1] != captions.producers[2]


@pytest.mark.spec("cli:show:producers-are-reported")
def test_the_report_names_the_photograph_and_its_digest(run: Run) -> None:
    lines = list(report(run))

    assert lines[0] == run.id
    assert run.frame["photo"]["sha256"] in "\n".join(lines)
    assert "image/jpeg" in "\n".join(lines)


@pytest.mark.spec("cli:show:active-version-is-marked")
def test_a_stage_with_nothing_in_it_says_so(tmp_path: Path) -> None:
    photo = tmp_path / "bare.jpg"
    photo.write_bytes(jpeg_bytes(800, 600))
    bare = open_run(photo, tmp_path / "runs")

    lines = list(report(bare))

    assert any("captions" in line and "(none)" in line for line in lines)


@pytest.mark.spec("cli:show:producers-are-reported")
def test_renders_are_listed_under_the_sheet_version_they_came_from(
    run: Run, schema: Schema
) -> None:
    flow = load_flow(FLOW)
    prepare(run, {FLOW: flow}, schema)
    render(run, flow, FakeComfyClient(), seeds=[42], poll=0)

    assert rendered(run) == [(FLOW, 1, [42])]
    assert any("42.png" in line for line in report(run))
