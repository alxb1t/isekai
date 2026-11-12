"""A bake's placement record: its names, request, chain, listing and discard.

Each image is built here from flat colour, so what the request must read is known
before it runs.
"""

import io
import json
import random
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

import isekai.pipeline.edit as edit_module
from isekai.foundation.artifacts import (
    EDIT_FILE,
    PLACEMENT_FILE,
    VERSIONS,
    PlacementRecord,
    PlacementValues,
    read,
)
from isekai.foundation.edit import load_edit
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    FRAME_NAME,
    edit_files,
    edit_numbers,
    is_edit_file,
    next_edit,
    placement_file,
)
from isekai.pipeline.edit import Requested, discard_edit, request_placed
from isekai.pipeline.generate import discard_render, rendered_seeds

FLOW = "summon-anime-wai"
EDIT = load_edit("tattoo-wai")
SKIN = (200, 150, 120)
SIDE = 400
# The square a tattoo covers, as rows and columns.
INKED = slice(80, 120)
RENDER_SEED = 42


def _group(tmp_path: Path) -> Path:
    """Return an outputs group inside a run that has a frame."""
    run = tmp_path / "runs" / "0123456789ab_a"
    group = run / FLOW / "outputs" / "001"
    group.mkdir(parents=True)
    (run / FRAME_NAME).write_text("{}\n")
    return group


def _png(pixels: "np.ndarray") -> bytes:
    """Return `pixels` encoded as a PNG."""
    body = io.BytesIO()
    Image.fromarray(pixels).save(body, "PNG")
    return body.getvalue()


def _render(factor: float = 1.0) -> "np.ndarray":
    """Return a flat render, its tattoo's square multiplied by `factor`."""
    pixels = np.full((SIDE, SIDE, 3), SKIN, dtype=np.uint8)
    square = pixels[INKED, INKED].astype(np.float32) * factor
    pixels[INKED, INKED] = (square + 0.5).astype(np.uint8)
    return pixels


def _scene(tmp_path: Path) -> tuple[Path, Path]:
    """Return a group and the path of a render in it."""
    group = _group(tmp_path)
    image = group / f"{RENDER_SEED}.png"
    image.write_bytes(_png(_render()))
    return group, image


def _values() -> PlacementValues:
    """Return the placement a bake of a two-stage tattoo holds."""
    return {
        "tattoo": "swallow",
        "kind": "image",
        "cut_from": None,
        "mode": "two-stage",
        "outline": {
            "points": [[0.0, 0.0], [40.0, 0.0], [40.0, 40.0]],
            "white": 1.0,
            "neutral": False,
            "depth": 1.0,
        },
        "stage1": [[[1.0, 2.0], [3.0, 4.0]]],
        "pairs": [[[5.0, 6.0], [7.0, 8.0]]],
        "limb": None,
        "exclusions": [],
    }


def _place(source: Path, composite: bytes, *, seed: int = 5) -> Requested:
    """Request the placed edit of `source` from `composite`, the dials as they are."""
    return request_placed(
        EDIT,
        source,
        composite,
        _values(),
        overrides={},
        seed=seed,
        rng=random.Random(1),
    )


def _listing(group: Path) -> list[str]:
    """Return the names a group holds."""
    return sorted(path.name for path in group.iterdir())


@pytest.mark.spec_exempt(
    "structural: the placement kind is declared once, at its first version"
)
def test_placement_names_the_kind_is_declared_and_versioned() -> None:
    assert PLACEMENT_FILE.schema == {"name": "placement", "version": 1}
    assert VERSIONS["placement"] == 1


@pytest.mark.spec_exempt(
    "structural: a placement is named for its edit's seed and number"
)
def test_placement_names_the_file_shares_its_edits_stem(tmp_path: Path) -> None:
    group = tmp_path / "outputs" / "001"

    assert placement_file(group, 42, 2) == group / "42.edit-2.placement.json"
    assert edit_files(group, 42, 2)[1] == group / "42.edit-2.json"


@pytest.mark.spec_exempt(
    "structural: a placement is a file an edit writes, and holds its number"
)
def test_placement_names_a_placement_alone_holds_its_number(tmp_path: Path) -> None:
    group = _group(tmp_path)
    placement_file(group, 42, 3).write_text("{}\n")
    (group / "7.edit-9.placement.json").write_text("{}\n")

    assert is_edit_file("42.edit-3.placement.json")
    assert not is_edit_file("42.edit-3.placement.png")
    assert not is_edit_file("x.edit-3.placement.json")
    assert edit_numbers(group, 42) == [3]
    assert next_edit(group, 42) == 4


@pytest.mark.spec(
    "tattoo:bake:a-bake-writes-the-composite-the-placement-and-the-record"
)
def test_placement_request_writes_the_composite_the_placement_and_the_record(
    tmp_path: Path,
) -> None:
    group, image = _scene(tmp_path)

    asked = _place(image, _png(_render(0.5)))

    assert _listing(group) == [
        "42.edit-1.composite.png",
        "42.edit-1.json",
        "42.edit-1.placement.json",
        "42.png",
    ]
    assert asked.number == 1
    placement: PlacementRecord = read(placement_file(group, 42, 1), PLACEMENT_FILE)
    assert placement == {
        "schema": PLACEMENT_FILE.schema,
        **_values(),
        "places_on": None,
    }
    assert read(asked.record, EDIT_FILE)["source"] == "42.png"


@pytest.mark.spec_exempt(
    "structural: the composite, then the placement, then the record"
)
def test_placement_request_writes_in_the_order_a_request_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    group, image = _scene(tmp_path)
    held_at_write: list[tuple[str, list[str]]] = []
    written = edit_module.write

    def spy(path: Path, kind: object, body: object) -> None:
        held_at_write.append((path.name, _listing(group)))
        written(path, kind, body)  # ty: ignore[invalid-argument-type]

    monkeypatch.setattr(edit_module, "write", spy)

    _place(image, _png(_render(0.5)))

    assert held_at_write == [
        ("42.edit-1.placement.json", ["42.edit-1.composite.png", "42.png"]),
        (
            "42.edit-1.json",
            ["42.edit-1.composite.png", "42.edit-1.placement.json", "42.png"],
        ),
    ]


@pytest.mark.spec("edit:refusals:a-composite-with-no-ink-is-refused")
def test_placement_request_a_refused_composite_writes_nothing(tmp_path: Path) -> None:
    group, image = _scene(tmp_path)
    before = _listing(group)

    with pytest.raises(Refusal, match="ink"):
        _place(image, _png(_render()))

    assert _listing(group) == before


@pytest.mark.spec("tattoo:bake-chain:a-bake-on-a-baked-edit-chains")
def test_placement_chain_a_bake_on_a_baked_edit_names_the_edit_it_is_placed_on(
    tmp_path: Path,
) -> None:
    group, image = _scene(tmp_path)
    _place(image, _png(_render(0.9)))
    baked = group / "42.edit-1.png"
    baked.write_bytes(_png(_render(0.9)))

    chained = _place(baked, _png(_render(0.45)))

    assert chained.number == 2
    assert read(chained.record, EDIT_FILE)["source"] == "42.edit-1.png"
    assert read(placement_file(group, 42, 2), PLACEMENT_FILE)["places_on"] == 1
    assert read(placement_file(group, 42, 1), PLACEMENT_FILE)["places_on"] is None


@pytest.mark.spec("tattoo:bake-chain:a-second-bake-on-the-same-image-is-a-new-edit")
def test_placement_chain_a_second_bake_on_one_image_leaves_the_first_as_it_was(
    tmp_path: Path,
) -> None:
    group, image = _scene(tmp_path)
    first = _place(image, _png(_render(0.5)))
    kept = {path.name: path.read_bytes() for path in group.iterdir()}

    second = _place(image, _png(_render(0.6)))

    assert (first.number, second.number) == (1, 2)
    for name, body in kept.items():
        assert (group / name).read_bytes() == body
    for number in (1, 2):
        placement = read(placement_file(group, 42, number), PLACEMENT_FILE)
        assert placement["places_on"] is None


@pytest.mark.spec("tattoo:bake-chain:a-pending-edit-cannot-be-placed-on")
def test_placement_chain_a_pending_edit_is_refused_naming_its_wait(
    tmp_path: Path,
) -> None:
    group, image = _scene(tmp_path)
    _place(image, _png(_render(0.5)))
    before = _listing(group)

    with pytest.raises(Refusal, match=r"edit 1 has no image yet.*render session"):
        _place(group / "42.edit-1.png", _png(_render(0.3)))

    assert _listing(group) == before


def _edit_by_hand(group: Path, number: int, source: str, *, imaged: bool) -> None:
    """Write the files of edit `number` from `source`, with its image if `imaged`."""
    image, record, composite = edit_files(group, RENDER_SEED, number)
    record.write_text(json.dumps({"schema": EDIT_FILE.schema, "source": source}))
    composite.write_bytes(b"x")
    placement_file(group, RENDER_SEED, number).write_text("{}\n")
    if imaged:
        image.write_bytes(b"x")


@pytest.mark.spec("tattoo:placement-file:the-listings-skip-the-placement")
def test_placement_listing_a_placement_is_no_render(tmp_path: Path) -> None:
    group = _group(tmp_path)
    (group / "42.png").write_bytes(b"x")
    _edit_by_hand(group, 1, "42.png", imaged=True)

    assert rendered_seeds(group, ".png") == [42]
    assert edit_numbers(group, 42) == [1]


@pytest.mark.spec("tattoo:placement-file:a-discarded-edit-takes-its-placement")
def test_placement_discard_an_edit_takes_its_placement_and_the_chain_made_from_it(
    tmp_path: Path,
) -> None:
    group = _group(tmp_path)
    (group / "42.png").write_bytes(b"x")
    _edit_by_hand(group, 1, "42.png", imaged=True)
    _edit_by_hand(group, 2, "42.edit-1.png", imaged=False)
    _edit_by_hand(group, 3, "42.png", imaged=False)

    deleted = discard_edit(group / "42.edit-1.png")

    assert sorted(path.name for path in deleted) == [
        "42.edit-1.composite.png",
        "42.edit-1.json",
        "42.edit-1.placement.json",
        "42.edit-1.png",
        "42.edit-2.composite.png",
        "42.edit-2.json",
        "42.edit-2.placement.json",
    ]
    assert _listing(group) == [
        "42.edit-3.composite.png",
        "42.edit-3.json",
        "42.edit-3.placement.json",
        "42.png",
    ]


@pytest.mark.spec(
    "tattoo:placement-file:a-deleted-render-takes-the-placement-of-its-edits"
)
def test_placement_discard_a_render_takes_the_placement_of_each_of_its_edits(
    tmp_path: Path,
) -> None:
    group = _group(tmp_path)
    (group / "42.png").write_bytes(b"x")
    (group / "7.png").write_bytes(b"x")
    _edit_by_hand(group, 1, "42.png", imaged=True)
    _edit_by_hand(group, 2, "42.edit-1.png", imaged=False)
    other = edit_files(group, 7, 1)
    other[1].write_text(json.dumps({"schema": EDIT_FILE.schema, "source": "7.png"}))
    placement_file(group, 7, 1).write_text("{}\n")

    discard_render(group / "42.png")

    assert _listing(group) == ["7.edit-1.json", "7.edit-1.placement.json", "7.png"]
