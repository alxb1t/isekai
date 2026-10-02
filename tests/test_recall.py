import json
from dataclasses import replace
from pathlib import Path

import pytest

from evaluation.recall import Record, Row, count, reading, table, totals
from isekai.boundary.wd14 import FLOOR, prepare, read_labels
from isekai.foundation.refusal import Refusal
from tests.images import oversized_png
from tests.stages import fake_tagger

FIXTURE = Path(__file__).resolve().parent / "recall"
SHEET = {
    "hair_colour": ["brown hair"],
    "eye_colour": ["green eyes"],
    "clothes": ["shirt", "black shirt", "jacket"],
    "bangs": ["swept bangs"],
}
# Danbooru's spelling, underscores and all: the sheet says `brown hair`.
INDEX = """tag_id,name,category,count
9999999,sensitive,9,3994361
1,brown_hair,0,6000000
2,green_eyes,0,300000
"""
SCORED = ("hair_colour", "eye_colour", "clothes", "marks")


@pytest.mark.spec("evaluation:recall:a-missed-tag-is-named")
def test_a_tag_the_render_does_not_show_is_named_under_its_field() -> None:
    fields = count(SHEET, SCORED, {"brown hair", "green eyes", "jacket"})

    assert fields["clothes"] == {
        "asked": ["shirt", "black shirt", "jacket"],
        "missed": ["shirt", "black shirt"],
    }
    assert fields["hair_colour"]["missed"] == []

    seen = {"brown hair", "green eyes", "shirt", "black shirt", "jacket"}
    assert all(not f["missed"] for f in count(SHEET, SCORED, seen).values())


@pytest.mark.spec("evaluation:recall:only-scored-fields-are-counted")
def test_a_field_the_flow_does_not_score_is_not_counted() -> None:
    fields = count(SHEET, SCORED, set())

    assert list(fields) == list(SCORED)
    assert "bangs" not in fields

    row: Row = {
        "run": "r",
        "flow": "f",
        "group": 1,
        "seed": 1,
        "outcome": "read",
        "fields": fields,
    }

    assert fields["marks"] == {"asked": [], "missed": []}
    assert totals([row])["f"]["marks"] == {"read_back": 0, "asked": 0}


@pytest.mark.spec("evaluation:recall:the-table-re-derives-from-the-record")
def test_the_committed_table_re_derives_from_its_record() -> None:
    rec: Record = json.loads((FIXTURE / "recall.json").read_text())

    assert table(rec) == (FIXTURE / "recall.txt").read_text()


class _Undecodable:
    """A session whose graph is never reached: the image does not decode."""

    def run(self, photo: Path) -> list[float]:
        raise OSError(f"cannot identify image file {photo}")


@pytest.mark.spec("evaluation:recall:a-tag-read-back-is-counted")
def test_a_tag_at_the_floor_is_read_back_in_the_sheets_spelling(tmp_path: Path) -> None:
    labels = tuple(read_labels(INDEX))
    at_the_floor = replace(fake_tagger([0.0, FLOOR, 0.0]), labels=labels)
    below_it = replace(fake_tagger([0.0, 0.0, FLOOR - 0.01]), labels=labels)
    render = tmp_path / "1.png"

    assert reading(at_the_floor)(render) == {"brown hair"}
    assert reading(below_it)(render) == set()

    fields = count(SHEET, SCORED, reading(at_the_floor)(render))
    assert fields["hair_colour"] == {"asked": ["brown hair"], "missed": []}
    assert fields["eye_colour"] == {"asked": ["green eyes"], "missed": ["green eyes"]}

    undecodable = replace(fake_tagger(), session=_Undecodable())
    with pytest.raises(Refusal, match=r"1\.png does not decode"):
        reading(undecodable)(render)


class _Preparing:
    """A session that prepares the image as the real one does, then sees nothing."""

    def run(self, photo: Path) -> list[float]:
        prepare(photo, 8)
        return [0.0, 0.0, 0.0]


@pytest.mark.spec("evaluation:recall:an-unreadable-render-is-a-row")
def test_an_image_too_large_to_open_is_refused_naming_it(tmp_path: Path) -> None:
    render = tmp_path / "1.png"
    render.write_bytes(oversized_png())
    tagger = replace(fake_tagger(), session=_Preparing())

    with pytest.raises(Refusal, match=r"1\.png does not decode"):
        reading(tagger)(render)
