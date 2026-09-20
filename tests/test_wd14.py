"""The WD14 boundary, exercised with no model file and no wheel installed.

**Nothing here imports `numpy`, `Pillow` or `onnxruntime`**, and that is the
point rather than a limitation: the `tagging` extra is not installed in the
environment the gate runs in, exactly as `eval` is not, so a suite that needed it
would be a suite that silently stops covering this capability. Everything that can
be decided without a wheel is decided in `select` and `read_labels`, and this file
is what holds that split honest.

**The one silent failure mode is the label-index ordering.** Row N of
`selected_tags.csv` names output neuron N, so a pair from two revisions mislabels
every tag while the vector still has the right length and every name in it is
still a real tag. `test_the_tag_returned_is_the_one_on_that_row_of_the_index` is
the assertion that catches it: a vector whose only high value sits at index 1
must yield the tag on row 1 and no other.
"""

import hashlib
import importlib
import sys
from pathlib import Path

import pytest

from isekai.boundary import provision
from isekai.boundary.provision import Manifest
from isekai.boundary.wd14 import (
    FLOOR,
    LABELS_DEST,
    MODEL_DEST,
    REMEDY,
    Label,
    Scored,
    read_labels,
    scored,
    select,
    verified_paths,
)
from isekai.evaluation import eval_models
from isekai.foundation.refusal import Refusal
from tests.stages import INDEX, FakeSession

# --- the label index ----------------------------------------------------------


@pytest.mark.spec("tagging:pin:the-label-index-and-the-model-are-verified-together")
def test_the_label_index_is_read_in_file_order_with_nothing_dropped() -> None:
    assert read_labels(INDEX) == [
        Label(name="sensitive", category=9),
        Label(name="1girl", category=0),
        Label(name="hatsune_miku", category=4),
    ]


@pytest.mark.spec("tagging:pin:the-label-index-and-the-model-are-verified-together")
def test_an_empty_label_index_refuses_naming_what_would_provision_it() -> None:
    with pytest.raises(Refusal) as refused:
        read_labels("tag_id,name,category,count\n")

    message = str(refused.value)
    assert LABELS_DEST in message
    assert REMEDY in message


@pytest.mark.spec("tagging:pin:the-label-index-and-the-model-are-verified-together")
def test_the_shipped_index_has_one_row_per_neuron_and_keeps_its_order() -> None:
    # The real file, read as bytes rather than through a fixture copy: a fixture
    # would let the shipped artifact and the parser drift apart silently. Skipped
    # rather than failed where it is not provisioned, because the file is 300 KB
    # of gitignored download and a fresh clone has not fetched it.
    shipped = Path("models") / LABELS_DEST
    if not shipped.is_file():
        pytest.skip(f"{LABELS_DEST} is not provisioned; run `{REMEDY}`")

    labels = read_labels(shipped.read_text())

    assert len(labels) == 10861
    assert labels[0].name == "general"
    assert [label.category for label in labels].count(0) == 8106


# --- what comes back ----------------------------------------------------------


@pytest.mark.spec("tagging:seam:offline-double-satisfies-the-interface")
def test_the_tag_returned_is_the_one_on_that_row_of_the_index() -> None:
    labels = read_labels(INDEX)

    # Row 1 is `1girl`. Rows 0 and 2 are below the floor, so a reading that was
    # off by one in either direction returns nothing at all rather than the
    # wrong tag -- which is the mislabelling this assertion exists to catch.
    assert select([0.0, 0.99, 0.0], labels) == [Scored(tag="1girl", confidence=0.99)]


@pytest.mark.spec("tagging:seam:offline-double-satisfies-the-interface")
def test_character_and_rating_rows_are_indexed_but_never_returned() -> None:
    labels = read_labels(INDEX)

    # Every neuron fires. Only the general row may come back.
    assert select([1.0, 1.0, 1.0], labels) == [Scored(tag="1girl", confidence=1.0)]


@pytest.mark.spec("tagging:seam:offline-double-satisfies-the-interface")
def test_tags_come_back_sorted_by_confidence_descending() -> None:
    labels = [Label(name=name, category=0) for name in ("a", "b", "c")]

    assert [found.tag for found in select([0.5, 0.9, 0.7], labels)] == ["b", "c", "a"]


@pytest.mark.spec("tagging:seam:offline-double-satisfies-the-interface")
def test_the_floor_is_inclusive_and_what_sits_below_it_is_dropped() -> None:
    labels = [Label(name=name, category=0) for name in ("at", "below")]

    assert [found.tag for found in select([FLOOR, FLOOR - 0.01], labels)] == ["at"]


@pytest.mark.spec("tagging:seam:offline-double-satisfies-the-interface")
def test_the_floor_is_the_measured_one_and_not_a_rounder_number() -> None:
    # 0.35 would lose `blurry background 0.19`, `cowboy shot 0.20` and
    # `head tilt 0.28` -- three tags correction-mining measured the operator
    # adding by hand, which is the recall this stage exists to buy (design.md D13).
    assert FLOOR == 0.15


@pytest.mark.spec("tagging:pin:the-label-index-and-the-model-are-verified-together")
def test_a_vector_longer_than_the_index_refuses_rather_than_truncating() -> None:
    labels = read_labels(INDEX)

    with pytest.raises(Refusal) as refused:
        select([0.9, 0.9, 0.9, 0.9], labels)

    message = str(refused.value)
    assert "4 probabilities" in message
    assert "3 neurons" in message
    assert REMEDY in message


@pytest.mark.spec("tagging:pin:the-label-index-and-the-model-are-verified-together")
def test_a_vector_shorter_than_the_index_refuses_too() -> None:
    labels = read_labels(INDEX)

    with pytest.raises(Refusal):
        select([0.9, 0.9], labels)


# --- the two digests ----------------------------------------------------------


def _planted(models_dir: Path, present: dict[str, bytes]) -> Manifest:
    """Write `present` under `models_dir` and return a manifest declaring both.

    Both destinations are always declared; only the named ones are written. That
    is what lets a test say *the list is there and the graph is not* without the
    467 MB graph existing anywhere, so this runs on a fresh clone and in CI.
    """
    for dest, body in present.items():
        path = models_dir / dest
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    return {
        "pinned": "2026-09-14",
        "publishers": ["SmilingWolf"],
        "entries": [
            {
                "dest": dest,
                "sha256": hashlib.sha256(present.get(dest, b"")).hexdigest(),
                "bytes": len(present.get(dest, b"")),
                "sources": [
                    f"https://huggingface.co/SmilingWolf/wd-swinv2-tagger-v3"
                    f"/resolve/{'6' * 40}/{dest.split('/')[-1]}"
                ],
            }
            for dest in (LABELS_DEST, MODEL_DEST)
        ],
    }


@pytest.mark.spec("tagging:pin:the-label-index-and-the-model-are-verified-together")
def test_an_absent_label_index_refuses_naming_what_to_fetch(tmp_path: Path) -> None:
    with pytest.raises(Refusal) as refused:
        verified_paths(tmp_path)

    message = str(refused.value)
    assert LABELS_DEST in message
    assert REMEDY in message


@pytest.mark.spec("tagging:pin:the-label-index-and-the-model-are-verified-together")
def test_the_model_is_verified_and_not_only_the_label_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The list present and hashing correctly, the graph absent. Nothing but a
    # check on the *second* destination catches this, and without it the build
    # would open an unverified half-gigabyte file on the strength of a 300 KB one.
    manifest = _planted(tmp_path, {LABELS_DEST: INDEX.encode()})
    monkeypatch.setattr(provision, "load_manifest", lambda _path=None: manifest)

    with pytest.raises(Refusal) as refused:
        verified_paths(tmp_path)

    message = str(refused.value)
    assert MODEL_DEST in message
    assert REMEDY in message


@pytest.mark.spec("tagging:pin:the-label-index-and-the-model-are-verified-together")
def test_a_half_whose_bytes_do_not_match_its_digest_stops_the_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Both present, and the graph's bytes swapped after the manifest was built.
    # `DigestMismatch` is the right failure and is deliberately not caught into a
    # `Refusal`: its message names the file, the digest expected and the digest
    # computed, which is what a human deciding "stale pin or swapped file" reads.
    manifest = _planted(tmp_path, {LABELS_DEST: INDEX.encode(), MODEL_DEST: b"graph"})
    (tmp_path / MODEL_DEST).write_bytes(b"not the graph")
    monkeypatch.setattr(provision, "load_manifest", lambda _path=None: manifest)

    with pytest.raises(provision.DigestMismatch):
        verified_paths(tmp_path)


@pytest.mark.spec("tagging:pin:the-label-index-and-the-model-are-verified-together")
def test_both_halves_present_and_matching_resolve_to_their_two_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = _planted(tmp_path, {LABELS_DEST: INDEX.encode(), MODEL_DEST: b"graph"})
    monkeypatch.setattr(provision, "load_manifest", lambda _path=None: manifest)

    assert verified_paths(tmp_path) == (tmp_path / LABELS_DEST, tmp_path / MODEL_DEST)


@pytest.mark.spec("tagging:pin:the-check-fires-at-first-use")
def test_importing_the_boundary_opens_no_file_and_computes_no_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A machine that never captions must not pay for a 467 MB file, so `wiring`
    # resolves a tagger per flow and nothing is constructed until one asks
    # (design.md D14). Re-imported with both the manifest reader and the resolver
    # rigged to raise: reaching either at import time is the defect.
    def refuse(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("the boundary reached provisioning at import time")

    monkeypatch.setattr(provision, "load_manifest", refuse)
    monkeypatch.setattr(eval_models, "resolve", refuse)
    monkeypatch.delitem(sys.modules, "isekai.boundary.wd14")

    boundary = importlib.import_module("isekai.boundary.wd14")

    assert callable(boundary.open_session)


@pytest.mark.spec("tagging:pin:the-check-fires-at-first-use")
def test_no_wheel_the_tagging_extra_carries_is_imported_at_module_scope() -> None:
    # The rule the `-S` guard rests on: this file is the only one in the package
    # that touches `onnxruntime`, `numpy` or `Pillow`, and it touches them inside
    # the functions that need them.
    import isekai.boundary.wd14 as boundary

    source = Path(boundary.__file__ or "").read_text()

    for wheel in ("import numpy", "from PIL import", "import onnxruntime"):
        assert f"\n{wheel}" not in source, f"{wheel} is at module scope"
        assert f"    {wheel}" in source, f"{wheel} is not imported at all"


@pytest.mark.spec_exempt("structural: the seam's shape, which the doubles satisfy")
def test_the_fake_session_satisfies_the_interface_the_real_one_does(
    tmp_path: Path,
) -> None:
    from isekai.boundary.wd14 import Session

    fake: Session = FakeSession([0.0, 0.9, 0.0])
    photo = tmp_path / "aunt-ada.jpg"

    assert fake.run(photo) == [0.0, 0.9, 0.0]
    assert FakeSession([0.0]).calls == 0


@pytest.mark.spec("tagging:seam:offline-double-satisfies-the-interface")
def test_the_session_is_handed_the_photograph_and_nothing_else(
    tmp_path: Path,
) -> None:
    # The seam takes a `Path` rather than a prepared array precisely so the
    # double needs no wheel. Nothing but the photograph crosses it: no briefing,
    # no schema, no flow identifier.
    session = FakeSession([0.0, 0.9, 0.0])
    photo = tmp_path / "aunt-ada.jpg"

    scored(photo, session, read_labels(INDEX))

    assert session.seen == [photo]
