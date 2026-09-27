"""The `compare` verb: one page of every run's photograph beside its renders.

The page is read by a person and handed over by an agent that must not read it,
so what is held here is its shape and that the verb prints the path alone.
"""

import io
import re
from pathlib import Path

import pytest

from isekai.foundation.flow import load_flow
from isekai.foundation.run import OUTPUTS, REVIEW, Run, artifact_name, open_run
from isekai.interface.cli import build_parser, dispatch
from isekai.interface.compare_view import PAGE_NAME
from isekai.interface.wiring import Wiring
from isekai.pipeline.caption import FakeReader
from isekai.shared.vocabulary import Vocabulary
from tests.images import jpeg_bytes
from tests.stages import FIELD_MAP, caption

SUMMON = "summon-anime-wai"
CONJURE = "conjure-anime-wai"


def _wiring(out: io.StringIO, err: io.StringIO) -> Wiring:
    """Return a wiring that reaches nothing: `compare` reads files alone."""

    def unreached() -> Vocabulary:
        raise AssertionError("compare read the vocabulary")

    return Wiring(
        reader=None,
        tagger=None,
        hosted_tagger=None,
        client=None,
        vocabulary=unreached,
        field_map=lambda _: FIELD_MAP,
        out=out,
        err=err,
    )


def _run(batch: Path, name: str, prose: str, height: int = 480) -> Run:
    """Open a run in `batch` and caption it under both flows.

    `height` tells two photographs apart: a run is keyed by the photograph's bytes.
    """
    photo = batch / "photos" / f"{name}.jpg"
    photo.parent.mkdir(parents=True, exist_ok=True)
    photo.write_bytes(jpeg_bytes(640, height))
    run = open_run(photo, batch / "runs")
    for flow in (SUMMON, CONJURE):
        caption(
            run,
            FakeReader(prose=f"{prose} for {flow}"),
            flow=flow,
            briefing_path=load_flow(flow).caption_briefing_path,
        )
    return run


def _approve(run: Run, flow: str, version: int) -> None:
    """Mark `version` approved by filename, which is all `compare` reads of it."""
    path = run.directory(flow, REVIEW) / artifact_name(version, "approved")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}\n")


def _render(run: Run, flow: str, version: int, *seeds: int) -> None:
    """Write placeholder renders under `version`'s outputs."""
    directory = run.directory(flow, OUTPUTS, f"{version:03d}")
    directory.mkdir(parents=True, exist_ok=True)
    for seed in seeds:
        (directory / f"{seed}.png").write_bytes(b"png")


def _compare(batch: Path) -> tuple[int, str, str]:
    """Run the verb the way the command line does; return its status, out and err."""
    out, err = io.StringIO(), io.StringIO()
    status = dispatch(
        build_parser().parse_args(["compare", str(batch)]), _wiring(out, err)
    )
    return status, out.getvalue(), err.getvalue()


def _section(body: str, run: Run) -> str:
    """Return the page's section for `run`."""
    return next(part for part in body.split("<section>") if run.id in part)


@pytest.mark.spec("cli:compare:the-page-links-photographs-to-renders")
def test_each_run_shows_its_photograph_and_each_flows_renders(tmp_path: Path) -> None:
    batch = tmp_path / "batch"
    ada = _run(batch, "ada", "Ada")
    bea = _run(batch, "bea", "Bea", height=481)
    for run in (ada, bea):
        _approve(run, SUMMON, 1)
        _render(run, SUMMON, 1, 11)
        _approve(run, CONJURE, 1)
        _render(run, CONJURE, 1, 21, 22)
    # A later approval supersedes the first: its renders are the ones shown.
    _approve(ada, SUMMON, 2)
    _render(ada, SUMMON, 2, 12)

    assert _compare(batch)[0] == 0

    body = (batch / PAGE_NAME).read_text()
    assert body.count("<section>") == 2
    for run in (ada, bea):
        assert f'src="runs/{run.id}/{run.photo.name}"' in _section(body, run)
        assert f"{CONJURE} &middot; seed 22" in _section(body, run)
    assert f"{SUMMON} &middot; seed 12" in _section(body, ada)
    assert f"{SUMMON} &middot; seed 11" not in _section(body, ada)
    assert f"{SUMMON} &middot; seed 11" in _section(body, bea)
    assert f'src="runs/{ada.id}/{CONJURE}/outputs/001/21.png"' in body
    assert f"Ada for {SUMMON}" in _section(body, ada)
    sources = re.findall(r'src="([^"]+)"', body)
    assert sources
    for source in sources:
        assert (batch / source).is_file(), source
    assert "data:" not in body


@pytest.mark.spec("cli:compare:a-run-without-a-render-is-marked")
def test_a_flow_with_no_render_says_so_and_the_page_is_written(tmp_path: Path) -> None:
    batch = tmp_path / "batch"
    run = _run(batch, "ada", "Ada")
    _approve(run, SUMMON, 1)
    _render(run, SUMMON, 1, 11)

    assert _compare(batch)[0] == 0

    body = (batch / PAGE_NAME).read_text()
    assert f"<figcaption>{CONJURE}</figcaption>" in body
    assert "no render yet" in body
    assert f"{SUMMON} &middot; seed 11" in body


@pytest.mark.spec("cli:compare:only-the-path-is-printed")
def test_the_verb_prints_the_pages_path_and_nothing_else(tmp_path: Path) -> None:
    batch = tmp_path / "batch"
    _run(batch, "ada", "Ada")

    assert _compare(batch) == (0, f"{batch / PAGE_NAME}\n", "")


@pytest.mark.spec("cli:compare:a-batch-without-runs-is-refused")
def test_a_directory_without_runs_is_refused_naming_it(tmp_path: Path) -> None:
    batch = tmp_path / "photos-only"
    batch.mkdir()

    status, out, err = _compare(batch)

    assert (status, out) == (1, "")
    assert err.startswith("refused: ")
    assert str(batch) in err
    assert list(batch.iterdir()) == []
