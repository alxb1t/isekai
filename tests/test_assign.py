"""`isekai assign`: a flow's empty directory for each source, and nothing else."""

import io
from pathlib import Path

import pytest

from isekai.foundation.run import FRAME_NAME
from isekai.interface.cli import build_parser, dispatch
from isekai.interface.wiring import Wiring
from isekai.shared.vocabulary import Vocabulary
from tests.images import jpeg_bytes
from tests.stages import FIELD_MAP

FLOW = "summon-anime-wai"


def _unreached() -> Vocabulary:
    raise AssertionError("assign read the vocabulary")


def _wiring(runs: Path) -> Wiring:
    """Return a wiring with no model behind it: `assign` reaches none."""
    return Wiring(
        reader=None,
        tagger=None,
        hosted_tagger=None,
        client=None,
        vocabulary=_unreached,
        field_map=lambda _: FIELD_MAP,
        runs_root=runs,
        out=io.StringIO(),
        err=io.StringIO(),
    )


def _assign(runs: Path, *argv: str) -> tuple[int, Wiring]:
    wired = _wiring(runs)
    args = build_parser().parse_args(["assign", "--runs", str(runs), *argv])
    return dispatch(args, wired), wired


def _tree(root: Path) -> dict[str, bytes | None]:
    return {
        str(path.relative_to(root)): path.read_bytes() if path.is_file() else None
        for path in sorted(root.rglob("*"))
    }


@pytest.fixture
def photo(tmp_path: Path) -> Path:
    path = tmp_path / "sources" / "ada.jpg"
    path.parent.mkdir()
    path.write_bytes(jpeg_bytes(600, 800))
    return path


@pytest.mark.spec("cli:assign:assigning-creates-the-run-and-the-flow")
def test_assigning_creates_the_run_and_the_flows_empty_directory(
    tmp_path: Path, photo: Path
) -> None:
    runs = tmp_path / "runs"

    code, _ = _assign(runs, "--flow", FLOW, str(photo))

    assert code == 0
    (run,) = runs.iterdir()
    assert {path.name for path in run.iterdir()} == {FRAME_NAME, "photo.jpg", FLOW}
    assert list((run / FLOW).iterdir()) == []


@pytest.mark.spec("cli:assign:assigning-again-writes-nothing")
def test_assigning_an_assigned_flow_writes_nothing(tmp_path: Path, photo: Path) -> None:
    runs = tmp_path / "runs"
    _assign(runs, "--flow", FLOW, str(photo))
    before = _tree(runs)

    code, wired = _assign(runs, "--flow", FLOW, str(photo))

    assert code == 0
    assert _tree(runs) == before
    assert isinstance(wired.out, io.StringIO)
    assert f"{FLOW} is already assigned" in wired.out.getvalue()


@pytest.mark.spec("cli:assign:removing-an-empty-flow-deletes-it")
def test_removing_an_empty_assignment_deletes_its_directory(
    tmp_path: Path, photo: Path
) -> None:
    runs = tmp_path / "runs"
    _assign(runs, "--flow", FLOW, str(photo))

    code, _ = _assign(runs, "--flow", FLOW, "--remove", str(photo))

    (run,) = runs.iterdir()
    assert code == 0
    assert not (run / FLOW).exists()


@pytest.mark.spec("cli:assign:removing-a-prepared-flow-is-refused")
def test_removing_a_prepared_flow_is_refused_naming_the_run_and_the_flow(
    tmp_path: Path, photo: Path
) -> None:
    runs = tmp_path / "runs"
    _assign(runs, "--flow", FLOW, str(photo))
    (run,) = runs.iterdir()
    (run / FLOW / "wd14").mkdir()
    before = _tree(runs)

    code, wired = _assign(runs, "--flow", FLOW, "--remove", str(photo))

    assert code == 1
    assert isinstance(wired.err, io.StringIO)
    assert f"refused: {run.name}: {FLOW} holds work" in wired.err.getvalue()
    assert _tree(runs) == before
