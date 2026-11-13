"""The record: each file of `tests/record/` is what a fresh pass derives.

A red test here means an output moved. `uv run python -m tests.record` writes the
files again, and the diff shows what moved.
"""

import argparse
import json
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest
from fastapi import FastAPI
from PIL import Image

from isekai.foundation.artifacts import EDIT_FILE, RENDER_FILE, read
from isekai.foundation.flow import graph_digest
from isekai.foundation.run import Run
from tests.record import (
    CALLS,
    CHILD_ROUTES,
    FILES,
    FIRST_FLOW,
    FLOWS,
    RECORD,
    REGENERATE,
    REPO_ROOT,
    SEED,
    Done,
    derive,
    differing,
    entry,
    normalised,
    offline,
    recorded,
    relative,
    served,
    shape,
    uncovered,
    walk,
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


def _argument(
    dest: str,
    flags: list[str],
    *,
    nargs: str | None = None,
    required: bool = False,
    default: object = None,
    choices: list[str] | None = None,
    type_: str | None = None,
    action: str = "_StoreAction",
) -> dict[str, object]:
    return {
        "dest": dest,
        "flags": flags,
        "nargs": nargs,
        "required": required,
        "default": default,
        "choices": choices,
        "type": type_,
        "metavar": None,
        "action": action,
    }


@pytest.mark.spec_exempt("structural: the walk reads each flag of a parser")
def test_the_walk_reads_each_flag_of_a_parser() -> None:
    parser = argparse.ArgumentParser()
    verb = parser.add_subparsers(dest="verb").add_parser("go", help="never recorded")
    verb.add_argument("name", nargs="*", help="never recorded")
    verb.add_argument("--look", choices=["flat", "vivid"], default="flat")
    verb.add_argument("--tag", action="append", dest="tags", required=True)
    verb.add_argument("--depth", type=float, default=1.5)
    either = verb.add_mutually_exclusive_group(required=True)
    either.add_argument("--left")
    either.add_argument("--right")

    walked = cast("dict[str, Any]", walk(parser))

    assert list(walked) == ["go"]
    assert walked["go"]["positionals"] == [_argument("name", [], nargs="*")]
    options = {each["dest"]: each for each in walked["go"]["options"]}
    assert set(options) == {"help", "look", "tags", "depth", "left", "right"}
    assert options["look"] == _argument(
        "look", ["--look"], default="flat", choices=["flat", "vivid"]
    )
    assert options["tags"] == _argument(
        "tags", ["--tag"], required=True, action="_AppendAction"
    )
    assert options["depth"] == _argument(
        "depth", ["--depth"], default=1.5, type_="float"
    )
    assert walked["go"]["groups"] == [{"required": True, "members": ["left", "right"]}]
    assert "never recorded" not in str(walked)


@pytest.mark.spec_exempt(
    "structural: a default inside the repository is recorded relative and one "
    "outside is refused"
)
def test_a_default_inside_the_repository_is_recorded_relative_and_outside_refused(
    tmp_path: Path,
) -> None:
    inside = REPO_ROOT / ".data" / "runs"
    assert relative(inside) == ".data/runs"
    assert relative("kept") == "kept"
    assert relative(None) is None
    with pytest.raises(ValueError, match="outside the repository"):
        relative(tmp_path / "runs")

    parser = argparse.ArgumentParser()
    verb = parser.add_subparsers(dest="verb").add_parser("go")
    verb.add_argument("--runs", type=Path, default=inside)
    held = cast("dict[str, Any]", walk(parser))
    assert held["go"]["options"][1]["default"] == ".data/runs"
    verb.add_argument("--elsewhere", type=Path, default=tmp_path)
    with pytest.raises(ValueError, match="outside the repository"):
        walk(parser)


@pytest.mark.spec_exempt("structural: a shape names keys and types and no value")
def test_a_shape_names_keys_and_types_and_no_value() -> None:
    body = {
        "name": "ada",
        "count": 3,
        "ratio": 0.5,
        "ready": True,
        "gone": None,
        "none": [],
        "rows": [{"id": "a", "seeds": ["1"]}, {"id": "b", "seeds": []}],
        "inner": {"saved": 1.5},
    }

    assert shape(body) == {
        "name": "str",
        "count": "int",
        "ratio": "float",
        "ready": "bool",
        "gone": "null",
        "none": [],
        "rows": [{"id": "str", "seeds": ["str"]}],
        "inner": {"saved": "float"},
    }
    assert "ada" not in str(shape(body))
    assert shape({}) == {}


@pytest.mark.spec_exempt(
    "structural: every route of the app is recorded or left to a child"
)
def test_every_route_of_the_app_is_recorded_or_left_to_a_child(done: Done) -> None:
    with served(done) as client:
        app = client.app
        assert isinstance(app, FastAPI)
        assert uncovered(app) == []
    assert not CHILD_ROUTES & {call.key for call in CALLS}


@pytest.mark.spec_exempt(
    "structural: twin of test_every_route_of_the_app_is_recorded_or_left_to_a_child"
)
def test_the_route_check_catches_a_route_no_call_covers() -> None:
    small = FastAPI()
    small.add_api_route("/api/library", lambda: {}, methods=["GET"])
    small.add_api_route("/events", lambda: {}, methods=["GET"])
    assert uncovered(small) == []

    small.add_api_route("/api/new", lambda: {}, methods=["GET"])
    small.add_api_route("/api/library", lambda: {}, methods=["DELETE"])
    assert uncovered(small) == ["DELETE /api/library", "GET /api/new"]


@pytest.mark.spec_exempt(
    "structural: no route answers a valid call with a server error"
)
def test_no_route_answers_a_valid_call_with_a_server_error(
    derived: dict[str, str],
) -> None:
    held = cast("dict[str, dict[str, Any]]", json.loads(derived["routes"]))
    assert held["GET /api/library"]["status"] == 200
    assert [route for route, said in held.items() if said["status"] >= 500] == []
