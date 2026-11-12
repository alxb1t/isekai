"""The record: each file of `tests/record/` is what a fresh pass derives.

A red test here means an output moved. `uv run python -m tests.record` writes the
files again, and the diff shows what moved.
"""

from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest
from PIL import Image

from isekai.foundation.artifacts import EDIT_FILE, RENDER_FILE, read
from isekai.foundation.flow import graph_digest
from isekai.foundation.run import Run
from tests.record import (
    FILES,
    FIRST_FLOW,
    FLOWS,
    RECORD,
    REGENERATE,
    SEED,
    Done,
    derive,
    differing,
    entry,
    normalised,
    offline,
    recorded,
)


@pytest.fixture(scope="module")
def done(tmp_path_factory: pytest.TempPathFactory) -> Done:
    """Run the pass once for the module."""
    return offline(tmp_path_factory.mktemp("record"))


@pytest.fixture(scope="module")
def derived(done: Done) -> dict[str, str]:
    """Return each record file's text, derived from the module's pass."""
    return derive(done)


def _group(run: Run, flow: str) -> Path:
    return run.path / flow / "outputs" / "001"


@pytest.mark.spec_exempt("structural: the pass renders every flow and the edit")
def test_the_pass_renders_every_flow_and_the_edit(done: Done) -> None:
    for flow in FLOWS:
        assert (_group(done.run, flow) / f"{SEED}.png").is_file(), flow
    assert (_group(done.run, FIRST_FLOW) / f"{SEED}.edit-1.png").is_file()


@pytest.mark.spec_exempt("structural: a record file is what the writer derives")
@pytest.mark.parametrize("name", sorted(FILES))
def test_each_record_file_is_what_the_writer_derives(
    name: str, done: Done, derived: dict[str, str]
) -> None:
    committed = RECORD / f"{name}.json"
    for spelling in (done.root, done.root.resolve(), Path.home()):
        assert str(spelling) not in derived[name], spelling
    assert committed.is_file() and committed.read_text() == derived[name], REGENERATE


@pytest.mark.spec_exempt(
    "structural: the record directory holds the files the writer names"
)
def test_the_record_directory_holds_the_files_the_writer_names(
    derived: dict[str, str],
) -> None:
    assert differing(RECORD, derived) == [], REGENERATE


@pytest.mark.spec_exempt(
    "structural: twin of test_the_record_directory_holds_the_files_the_writer_names"
)
def test_a_stale_record_file_is_caught(tmp_path: Path) -> None:
    derived = {"kept": "1\n", "stale": "2\n", "absent": "3\n"}
    (tmp_path / "kept.json").write_text("1\n")
    (tmp_path / "stale.json").write_text("0\n")
    (tmp_path / "extra.json").write_text("4\n")
    assert differing(tmp_path, derived) == ["absent", "extra", "stale"]


@pytest.mark.spec_exempt("structural: a duration and the root are normalised")
def test_a_duration_and_the_root_are_normalised(tmp_path: Path) -> None:
    held = tmp_path / "held"
    held.mkdir()
    link = tmp_path / "link"
    link.symlink_to(held)
    body = {
        "duration": 1.5,
        "kept": 7,
        "inner": [{"duration": 2, "path": f"{held.resolve()}/a.jpg"}],
        "given": f"{link}/b.jpg",
    }

    assert normalised(body, link) == {
        "duration": 0.0,
        "kept": 7,
        "inner": [{"duration": 0.0, "path": "<root>/a.jpg"}],
        "given": "<root>/b.jpg",
    }
    for refused in ("slow", True, None):
        with pytest.raises(AssertionError):
            normalised({"duration": refused}, link)


def _encoded(pixels: "np.ndarray", path: Path, level: int) -> Path:
    Image.fromarray(pixels).save(path, "PNG", compress_level=level)
    return path


@pytest.mark.spec_exempt(
    "structural: a png is recorded by its pixels and any other file by its bytes"
)
def test_a_png_is_recorded_by_its_pixels_and_any_other_file_by_its_bytes(
    tmp_path: Path,
) -> None:
    pixels = np.full((8, 8, 3), (10, 20, 30), dtype=np.uint8)
    plain = _encoded(pixels, tmp_path / "plain.png", 0)
    packed = _encoded(pixels, tmp_path / "packed.png", 9)
    moved = pixels.copy()
    moved[3, 4] = (11, 20, 30)

    assert plain.read_bytes() != packed.read_bytes()
    assert entry(plain, tmp_path) == entry(packed, tmp_path)
    assert entry(plain, tmp_path) != entry(
        _encoded(moved, tmp_path / "m.png", 0), tmp_path
    )

    (tmp_path / "a.jpg").write_bytes(b"one")
    (tmp_path / "b.jpg").write_bytes(b"two")
    assert entry(tmp_path / "a.jpg", tmp_path) != entry(tmp_path / "b.jpg", tmp_path)
    assert set(entry(tmp_path / "a.jpg", tmp_path)) == {"bytes"}
    (tmp_path / "c.json").write_text('{"duration": 3}')
    assert entry(tmp_path / "c.json", tmp_path) == {"json": {"duration": 0.0}}


@pytest.mark.spec_exempt(
    "structural: each recorded graph is the one its render record digests"
)
def test_each_recorded_graph_is_the_one_its_render_record_digests(done: Done) -> None:
    held = cast("dict[str, Any]", recorded("graphs"))
    for flow in FLOWS:
        record = _group(done.run, flow) / f"{SEED}.render.json"
        digest = read(record, RENDER_FILE)["graph_sha256"]
        assert graph_digest(held["flows"][flow]) == digest, flow
    edit = _group(done.run, FIRST_FLOW) / f"{SEED}.edit-1.json"
    assert graph_digest(held["edit"]) == read(edit, EDIT_FILE)["graph_sha256"]
