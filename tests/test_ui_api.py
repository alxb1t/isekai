"""The six endpoints, against a running application.

**This module runs in the gate.** FastAPI is pinned in the `dev` dependency
group, so `uv sync --locked` installs it and the four `ui` scenarios bound here
and nowhere else are actually proved. `tests/test_ui.py` asserts the framework is
present, so its absence is a failure rather than a silent skip.

The `importorskip` below is what remains of the older posture, and it is kept as
a belt for an environment synced without the dev group: a module-level `from
fastapi.testclient import TestClient` would fail *collection* there, which is
gate command five going red over a missing test tool rather than a defect.

This is deliberately not the eval tests' pattern. Those stay in the main suite by
faking their boundary in `tests/eval_fakes.py` and never importing the extra at
all; here the thing under test *is* the HTTP surface, so there is nothing to fake
that would leave anything worth asserting.

Everything that can be asserted without a server is in `tests/test_ui.py`.
"""

import io
import random
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from isekai.foundation.flow import Schema  # noqa: E402
from isekai.foundation.run import REVIEW, Run, open_run, read_artifact  # noqa: E402
from isekai.interface.ui.app import RARE_BELOW, create_app  # noqa: E402
from isekai.interface.ui.batch import establish  # noqa: E402
from isekai.interface.wiring import Wiring  # noqa: E402
from isekai.pipeline.caption import FakeReader  # noqa: E402
from isekai.pipeline.review import approve, review  # noqa: E402
from isekai.pipeline.sheet import FakeSorter  # noqa: E402
from isekai.pipeline.tagging import (  # noqa: E402
    FakeTagger,
    caption_tags,
    caption_wd14,
)
from isekai.shared.vocabulary import Vocabulary  # noqa: E402
from tests.conftest import snapshot  # noqa: E402
from tests.images import jpeg_bytes  # noqa: E402
from tests.stages import caption, fake_wd14, sheet  # noqa: E402

FLOW = "summon-v1"


@pytest.fixture
def wired(tmp_path: Path, vocabulary: Vocabulary) -> Wiring:
    """Return a ③-only wiring: no reader, no sorter, no transport."""
    return Wiring(
        reader=None,
        sorter=None,
        tagger=None,
        hosted_tagger=None,
        client=None,
        vocabulary=lambda: vocabulary,
        runs_root=tmp_path / "runs",
        rng=random.Random(0),
        out=io.StringIO(),
        err=io.StringIO(),
    )


@pytest.fixture
def made(wired: Wiring, tmp_path: Path, schema: Schema, vocabulary: Vocabulary) -> Run:
    """Return one run carrying a caption and a filled sheet for `FLOW`."""
    photo = tmp_path / "ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    run = open_run(photo, wired.runs_root)
    caption(run, FakeReader(prose="Dark brown hair, brown eyes."))
    sheet(
        run,
        FakeSorter(answers={"hair_colour": ["dark brown"], "eye_colour": ["brown"]}),
        schema,
        vocabulary,
    )
    return run


def _client(wired: Wiring, made: Run, tmp_path: Path) -> TestClient:
    """Return a client over the surface, with a stand-in for the built bundle.

    A function as well as a fixture, because `establish()` resolves every
    artifact path at startup -- so a test that writes a tag artifact has to write
    it *before* the batch is established, which a fixture ordering cannot express.
    """
    dist = tmp_path / "dist"
    dist.mkdir(exist_ok=True)
    (dist / "index.html").write_text("<!doctype html>")
    batch = establish(wired, FLOW, [made.id], bundle=lambda: dist)
    return TestClient(create_app(batch))


@pytest.fixture
def client(wired: Wiring, made: Run, tmp_path: Path) -> TestClient:
    """Return a client over the surface, with a stand-in for the built bundle."""
    return _client(wired, made, tmp_path)


# --- the batch, and the payload the page is drawn from ------------------------


@pytest.mark.spec_exempt("structural: the shape the page is drawn from")
def test_the_batch_endpoint_names_the_flow_the_schema_and_the_vocabulary(
    client: TestClient, made: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    body = client.get("/api/batch").json()

    assert body["flow"] == FLOW
    assert body["schema"] == list(schema.names)
    assert body["vocabulary"] == len(vocabulary)
    assert body["approved"] == 0
    assert [held["id"] for held in body["inputs"]] == [made.id]
    assert body["inputs"][0]["width"] == 1200


@pytest.mark.spec_exempt("structural: the join the page reads per input")
def test_an_input_carries_its_caption_its_fields_and_its_budget(
    client: TestClient, made: Run, schema: Schema
) -> None:
    body = client.get(f"/api/inputs/{made.id}").json()

    assert body["caption"] == "Dark brown hair, brown eyes."
    # Every field the schema declares, in schema order, never re-sorted -- the
    # sorter's own canonical spelling is what stage ② wrote, not the fixture's.
    assert list(body["fields"]) == list(schema.names)
    assert body["fields"]["hair_colour"]
    assert body["draft"] == "001.draft.json"
    assert body["readonly"] is False
    # The shares and the overhead reconcile, because they come from one rule.
    budget = body["budget"]
    assert sum(budget["per_field"].values()) + budget["overhead"] == budget["total"]


# --- the vocabulary, ranked where the pipeline ranks it -----------------------


@pytest.mark.spec("ui:vocabulary:matches-are-ranked-by-post-count")
def test_matches_come_back_in_the_pipelines_own_order_with_their_counts(
    client: TestClient, vocabulary: Vocabulary
) -> None:
    body = client.get("/api/tags", params={"q": "hair", "limit": 50}).json()

    tags = [match["tag"] for match in body["matches"]]
    # The server's order is the order. Ranking in one place is what keeps the
    # decision identical however it is reached.
    assert tags == vocabulary.search("hair")
    assert all(
        match["posts"] == vocabulary.count(match["tag"]) for match in body["matches"]
    )
    assert body["total"] == len(vocabulary.search("hair"))
    # The post count is why this surface exists: it predicts how hard a tag
    # lands, and `rare` is the server's own judgement over it.
    assert all(
        match["rare"] == (match["posts"] < RARE_BELOW) for match in body["matches"]
    )


@pytest.mark.spec("ui:vocabulary:matches-are-ranked-by-post-count")
def test_the_limit_narrows_the_rows_without_changing_the_true_count(
    client: TestClient, vocabulary: Vocabulary
) -> None:
    body = client.get("/api/tags", params={"q": "hair", "limit": 2}).json()

    assert len(body["matches"]) == 2
    # The footer says how narrow the fragment got, so narrowing it is the way to
    # see fewer rows rather than scrolling.
    assert body["total"] == len(vocabulary.search("hair"))


@pytest.mark.spec("ui:vocabulary:an-unmatched-fragment-commits-nothing")
def test_a_fragment_no_tag_contains_yields_nothing_to_commit(
    client: TestClient,
) -> None:
    body = client.get("/api/tags", params={"q": "zzzznotatag"}).json()

    # There is no path to free text in a chip: a fragment matching nothing shows
    # no rows, and a row is the only thing that can be committed.
    assert body["matches"] == []
    assert body["total"] == 0


@pytest.mark.spec("ui:vocabulary:an-unmatched-fragment-commits-nothing")
def test_an_empty_fragment_returns_nothing_rather_than_everything(
    client: TestClient,
) -> None:
    body = client.get("/api/tags", params={"q": "  "}).json()

    # The dropdown appears on the first keystroke and not before. An empty
    # fragment is contained by every tag, so answering it literally would be
    # the 8,106-tag transfer this endpoint exists to delete.
    assert body["matches"] == []
    assert body["total"] == 0


# --- the write surface, and what approval closes ------------------------------


@pytest.mark.spec_exempt("structural: the autosave path, end to end over HTTP")
def test_a_draft_update_lands_on_disk_and_returns_a_receipt(
    client: TestClient, made: Run
) -> None:
    fields = client.get(f"/api/inputs/{made.id}").json()["fields"]
    fields["hair_colour"] = ["blonde"]

    body = client.put(f"/api/inputs/{made.id}/draft", json={"fields": fields}).json()

    assert body["draft"] == "001.draft.json"
    assert body["saved"] is not None
    assert client.get(f"/api/inputs/{made.id}").json()["fields"]["hair_colour"] == [
        "blonde"
    ]


@pytest.mark.spec("ui:approval:approved-input-refuses-a-draft-update")
def test_a_draft_update_against_an_approved_input_is_refused_and_writes_nothing(
    client: TestClient, made: Run
) -> None:
    fields = client.get(f"/api/inputs/{made.id}").json()["fields"]
    assert client.post(f"/api/inputs/{made.id}/approve").status_code == 200
    before = snapshot(made.path)

    # A stale tab in a second window is exactly this request.
    response = client.put(f"/api/inputs/{made.id}/draft", json={"fields": fields})

    assert response.status_code == 409
    assert "draft" in response.json()["refusal"]
    assert snapshot(made.path) == before


@pytest.mark.spec("ui:approval:approved-input-opens-read-only")
def test_an_input_approved_in_an_earlier_sitting_opens_read_only(
    wired: Wiring, made: Run, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    review(made, FLOW)
    approved, _ = approve(made, FLOW, schema, vocabulary)
    assert approved is not None
    expected = {
        name: list(tags) for name, tags in read_artifact(approved)["fields"].items()
    }

    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html>")
    batch = establish(wired, FLOW, [made.id], bundle=lambda: dist)
    reopened = TestClient(create_app(batch))

    body = reopened.get(f"/api/inputs/{made.id}").json()

    # Approval deletes the draft and reopening writes no replacement, so there is
    # nothing on disk for an edit to be written into (design.md D5).
    assert body["readonly"] is True
    assert body["draft"] is None
    assert body["approved"] == "001.approved.json"
    # `saved` reports the draft, which approval unlinks, so the approved
    # artifact carries its own time -- otherwise the manifest's `approved`
    # column would be blank for every row in it.
    assert body["saved"] is None
    assert body["approved_at"] is not None
    assert body["fields"] == expected
    assert not (made.directory(FLOW, REVIEW) / "001.draft.json").exists()


# --- the two tag lists the source pane shows ----------------------------------


@pytest.mark.spec("ui:source:both-tag-lists-are-shown-raw-and-read-only")
def test_the_payload_carries_both_lists_whole_and_in_the_order_produced(
    wired: Wiring, made: Run, tmp_path: Path
) -> None:
    session, labels = fake_wd14().double
    caption_wd14(made, FLOW, session, labels)
    caption_tags(
        made,
        FLOW,
        FakeTagger(tags=("brown hair", "fashion photography", "blue eyes")),
    )

    body = _client(wired, made, tmp_path).get(f"/api/inputs/{made.id}").json()

    assert body["wd14"] == [{"tag": "1girl", "confidence": 0.9}]
    # Whole and unnarrowed: `fashion photography` is not in the vocabulary and is
    # still on the page, because narrowing is stage ②'s job and seeing behind it
    # is the point (design.md D1).
    assert [one["tag"] for one in body["tags"]] == [
        "brown hair",
        "fashion photography",
        "blue eyes",
    ]


@pytest.mark.spec("ui:source:vocabulary-membership-is-marked-by-the-server")
def test_membership_and_post_counts_are_decided_server_side(
    wired: Wiring, made: Run, tmp_path: Path, vocabulary: Vocabulary
) -> None:
    # Marked here, not in the browser: `/api/tags` answers a *fragment* query and
    # there is no membership endpoint, so marking N tags client-side would be N
    # round trips. The vocabulary is already in this process.
    caption_tags(
        made,
        FLOW,
        FakeTagger(tags=("brown hair", "fashion photography", "blue eyes")),
    )

    body = _client(wired, made, tmp_path).get(f"/api/inputs/{made.id}").json()
    marked = {one["tag"]: one for one in body["tags"]}

    assert marked["brown hair"]["in_vocabulary"] is True
    assert marked["brown hair"]["posts"] == vocabulary.count("brown hair")
    assert marked["blue eyes"]["in_vocabulary"] is True
    # Out of the vocabulary, and carrying **no** count. The missing number is the
    # mark: a chip with no count reads as the model's word rather than
    # Danbooru's, which is the scepticism that defuses the anchoring risk.
    assert marked["fashion photography"]["in_vocabulary"] is False
    assert marked["fashion photography"]["posts"] is None


@pytest.mark.spec("ui:source:an-absent-tag-artifact-is-silent")
def test_an_input_with_neither_artifact_carries_null_and_still_serves(
    client: TestClient, made: Run
) -> None:
    # The `made` fixture captions and fills a sheet and tags nothing, which is
    # exactly a run captioned before v0.20. Both are null, the surface answers
    # 200, and nothing anywhere is a refusal (design.md D20).
    response = client.get(f"/api/inputs/{made.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["wd14"] is None
    assert body["tags"] is None
    assert body["caption"] == "Dark brown hair, brown eyes."


@pytest.mark.spec("ui:source:an-absent-tag-artifact-is-silent")
def test_one_list_present_and_the_other_absent_is_also_silent(
    wired: Wiring, made: Run, tmp_path: Path
) -> None:
    # The state every `summon-v1` run is in: a WD14 list and no hosted one,
    # because the flow declares no arm to tag on (design.md D3).
    session, labels = fake_wd14().double
    caption_wd14(made, FLOW, session, labels)

    body = _client(wired, made, tmp_path).get(f"/api/inputs/{made.id}").json()

    assert body["wd14"] is not None
    assert body["tags"] is None


@pytest.mark.spec("ui:source:the-caption-is-shown-one-sentence-to-a-block")
def test_the_caption_reaches_the_page_whole_and_the_browser_splits_it(
    client: TestClient, made: Run
) -> None:
    # The split is `ui/src/caption.ts`'s and the server does not do it: sending
    # prose to be split and back would be a round trip for a regex
    # (design.md D10). What the server owes is the prose, unmodified.
    body = client.get(f"/api/inputs/{made.id}").json()

    assert body["caption"] == "Dark brown hair, brown eyes."
