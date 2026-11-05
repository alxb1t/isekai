"""`isekai migrate`: each run's per-flow description copied into `photo/`, once.

Every test runs the verb through `cli.main`, over a library of two collections
under `tmp_path`, with `ISEKAI_LIBRARY` and the default runs root pointed there.
"""

import argparse
import dataclasses
import io
import json
import os
from pathlib import Path

import pytest

import isekai.interface.cli as cli
from isekai.foundation.artifacts import write_json
from isekai.foundation.run import CAPTIONS, PHOTO, TAGS, WD14, Run, open_run
from isekai.interface.wiring import Wiring
from tests.conftest import snapshot
from tests.images import jpeg_bytes

FLOWS = ("control-anime-wai", "summon-anime-wai")


@dataclasses.dataclass
class Library:
    """A library of two collections, and what one `migrate` printed."""

    root: Path
    default: Path
    out: io.StringIO = dataclasses.field(default_factory=io.StringIO)
    err: io.StringIO = dataclasses.field(default_factory=io.StringIO)

    def runs(self, collection: str) -> Path:
        """Return a collection's runs root, making the collection."""
        (self.root / collection / "sources").mkdir(parents=True, exist_ok=True)
        return self.root / collection / "runs"

    def migrate(self, *argv: str) -> int:
        """Run `migrate` through `cli.main`, its lines kept for the test."""
        self.out, self.err = io.StringIO(), io.StringIO()
        return cli.main(["migrate", *argv])


@pytest.fixture
def library(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Library:
    """Return a library under `tmp_path`, the default runs root beside it."""
    made = Library(tmp_path / "library", tmp_path / "default" / "runs")
    made.root.mkdir()
    monkeypatch.setenv("ISEKAI_LIBRARY", str(made.root))
    monkeypatch.delenv("ISEKAI_WIRING", raising=False)
    monkeypatch.setattr(cli, "RUNS_ROOT", made.default)
    real = cli.wiring

    def captured(args: argparse.Namespace) -> Wiring:
        return dataclasses.replace(real(args), out=made.out, err=made.err)

    monkeypatch.setattr(cli, "wiring", lambda args: captured(args))
    return made


def _run(runs: Path, name: str, width: int = 800) -> Run:
    """Return a run of a photograph named `name`, opened under `runs`."""
    photo = runs.parent / f"{name}.jpg"
    photo.parent.mkdir(parents=True, exist_ok=True)
    photo.write_bytes(jpeg_bytes(width, 600))
    return open_run(photo, runs)


def _list(run: Run, flow: str, kind: str, number: int, *tags: str) -> Path:
    """Write `flow`'s list of `kind` numbered `number`, holding `tags`."""
    directory = run.directory(flow, kind)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{number:03d}.json"
    listed: list[object] = (
        [{"tag": tag, "confidence": 0.9} for tag in tags]
        if kind == WD14
        else list(tags)
    )
    write_json(
        path, {"schema": {"name": kind, "version": 1}, "producer": {}, "tags": listed}
    )
    return path


def _caption(run: Run, flow: str, prose: str, *, at: int) -> Path:
    """Write `flow`'s caption holding `prose`, its time `at` nanoseconds."""
    directory = run.directory(flow, CAPTIONS)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "001.json"
    write_json(
        path,
        {"schema": {"name": "caption", "version": 1}, "producer": {}, "prose": prose},
    )
    os.utime(path, ns=(at, at))
    return path


def _described(run: Run) -> None:
    """Give every flow of `run` the same lists and a caption of its own."""
    for index, flow in enumerate(FLOWS):
        _list(run, flow, WD14, 1, "1girl", "brown_hair")
        _list(run, flow, TAGS, 1, "smiling")
        _caption(run, flow, f"Read by {flow}.", at=10**18 + index)


@pytest.mark.spec("cli:migrate:a-second-run-changes-nothing")
def test_a_second_run_changes_nothing(library: Library) -> None:
    alpha = _run(library.runs("alpha"), "ada")
    beta = _run(library.runs("beta"), "bea", width=900)
    _described(alpha)
    _described(beta)
    assert library.migrate() == 0
    first = snapshot(library.root)

    assert library.migrate() == 0

    assert snapshot(library.root) == first
    assert library.out.getvalue().splitlines() == [
        f"{collection}/runs/{run.id}: already migrated"
        for collection, run in (("alpha", alpha), ("beta", beta))
    ]


@pytest.mark.spec("cli:migrate:the-old-files-stay")
def test_the_old_files_stay(library: Library) -> None:
    run = _run(library.runs("alpha"), "ada")
    _described(run)
    kept = {flow: snapshot(run.path / flow) for flow in FLOWS}

    assert library.migrate() == 0

    assert {flow: snapshot(run.path / flow) for flow in FLOWS} == kept
    for kind in (CAPTIONS, WD14, TAGS):
        assert (run.path / PHOTO / kind / "001.json").is_file(), kind
    assert (run.path / PHOTO / WD14 / "001.json").read_bytes() == (
        run.path / FLOWS[0] / WD14 / "001.json"
    ).read_bytes()
    assert library.out.getvalue() == (
        f"alpha/runs/{run.id}: migrated captions, wd14, tags\n"
    )


@pytest.mark.spec("cli:migrate:differing-lists-refuse-the-run")
@pytest.mark.spec("cli:refusals:refusal-names-the-remedy")
def test_differing_lists_refuse_the_run(library: Library) -> None:
    run = _run(library.runs("alpha"), "ada")
    _described(run)
    _list(run, FLOWS[1], WD14, 1, "1girl", "black_hair")

    assert library.migrate() == 1

    refused = library.err.getvalue()
    assert refused.startswith(f"alpha/runs/{run.id}: refused: {run.id}: its wd14")
    assert f"differ between {FLOWS[0]}, {FLOWS[1]}" in refused
    assert "`python -m isekai migrate --runs " in refused
    assert not (run.path / PHOTO).exists()

    # A hand-edited list with no `tags` refuses its run by name, and the walk goes on.
    damaged = _run(library.default, "cy", width=1000)
    _described(damaged)
    tagless = damaged.path / FLOWS[1] / WD14 / "001.json"
    tagless.write_text(json.dumps({"schema": {"name": WD14, "version": 1}}))
    walked = _run(library.runs("beta"), "bea", width=900)
    _list(walked, FLOWS[0], WD14, 1, "1girl")

    assert library.migrate() == 1

    assert (
        f"default/runs/{damaged.id}: refused: 001.json: records no `tags` list; "
        f"delete {FLOWS[1]}/{WD14}/, then run `python -m isekai migrate --runs "
    ) in library.err.getvalue()
    assert f"beta/runs/{walked.id}: migrated wd14" in library.out.getvalue()
    assert not (damaged.path / PHOTO).exists()


@pytest.mark.spec("cli:migrate:the-newest-caption-is-kept")
def test_the_newest_caption_is_kept(library: Library) -> None:
    run = _run(library.runs("alpha"), "ada")
    _caption(run, FLOWS[0], "The newer reading.", at=2 * 10**18)
    _caption(run, FLOWS[1], "The older reading.", at=10**18)

    assert library.migrate() == 0

    assert (run.path / PHOTO / CAPTIONS / "001.json").read_bytes() == (
        run.path / FLOWS[0] / CAPTIONS / "001.json"
    ).read_bytes()
    assert (
        json.loads((run.path / PHOTO / CAPTIONS / "001.json").read_text())["prose"]
        == "The newer reading."
    )


@pytest.mark.spec("cli:migrate:a-list-keeps-its-number")
def test_a_list_keeps_its_number(library: Library) -> None:
    run = _run(library.runs("alpha"), "ada")
    for flow in FLOWS:
        _list(run, flow, WD14, 1, "1girl")
        _list(run, flow, WD14, 2, "1girl", "smiling")

    assert library.migrate() == 0

    assert sorted(path.name for path in (run.path / PHOTO / WD14).iterdir()) == [
        "001.json",
        "002.json",
    ]
    assert (run.path / PHOTO / WD14 / "002.json").read_bytes() == (
        run.path / FLOWS[0] / WD14 / "002.json"
    ).read_bytes()


@pytest.mark.spec("cli:migrate:every-collection-is-walked")
def test_every_collection_is_walked(library: Library) -> None:
    alpha = _run(library.runs("alpha"), "ada")
    beta = _run(library.runs("beta"), "bea", width=900)
    default = _run(library.default, "cy", width=1000)
    for run in (alpha, beta, default):
        _list(run, FLOWS[0], WD14, 1, "1girl")

    assert library.migrate("--runs", str(library.runs("beta"))) == 0
    assert library.out.getvalue() == f"beta/runs/{beta.id}: migrated wd14\n"
    assert library.migrate() == 0

    assert library.out.getvalue().splitlines() == [
        f"default/runs/{default.id}: migrated wd14",
        f"alpha/runs/{alpha.id}: migrated wd14",
        f"beta/runs/{beta.id}: already migrated",
    ]


@pytest.mark.spec("cli:migrate:a-kind-is-copied-whole")
def test_a_kind_is_copied_whole(library: Library) -> None:
    run = _run(library.runs("alpha"), "ada")
    for number in (1, 2):
        _list(run, FLOWS[0], WD14, number, "1girl")
    stopped = run.path / PHOTO / ".wd14.partial"
    stopped.mkdir(parents=True)
    (stopped / "001.json").write_text("{half")

    assert library.migrate() == 0

    assert not stopped.exists()
    assert sorted(path.name for path in (run.path / PHOTO / WD14).iterdir()) == [
        "001.json",
        "002.json",
    ]
    assert (run.path / PHOTO / WD14 / "001.json").read_bytes() == (
        run.path / FLOWS[0] / WD14 / "001.json"
    ).read_bytes()
