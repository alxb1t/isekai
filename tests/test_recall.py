import json
from pathlib import Path

import pytest

from evaluation.recall import Record, Row, count, table, totals

FIXTURE = Path(__file__).resolve().parent / "recall"
SHEET = {
    "hair_colour": ["brown hair"],
    "eye_colour": ["green eyes"],
    "clothes": ["shirt", "black shirt", "jacket"],
    "bangs": ["swept bangs"],
}
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
