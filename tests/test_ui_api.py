"""The seven endpoints, against a running application.

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

import contextlib
import io
import json
import random
import threading
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

import isekai.interface.ui.app as app_module  # noqa: E402
import isekai.pipeline.review as review_module  # noqa: E402
from isekai.foundation.artifacts import (
    APPROVED_FILE,
    DRAFT_FILE,
    TAGS_FILE,
    Artifact,
    read,
)
from isekai.foundation.flow import Schema  # noqa: E402
from isekai.foundation.run import (  # noqa: E402
    CAPTIONS,
    REVIEW,
    TAGS,
    WD14,
    Run,
    open_run,
)
from isekai.interface.cli import build_parser  # noqa: E402
from isekai.interface.ui import HOST  # noqa: E402
from isekai.interface.ui.app import (  # noqa: E402
    RARE_BELOW,
    authorities,
    create_app,
)
from isekai.interface.ui.batch import Batch, Input, establish  # noqa: E402
from isekai.interface.wiring import Wiring  # noqa: E402
from isekai.pipeline.caption import FakeReader  # noqa: E402
from isekai.pipeline.review import ENCODER_WINDOW, approve, review  # noqa: E402
from isekai.pipeline.tagging import (  # noqa: E402
    FakeTagger,
    tag_hosted,
    tag_wd14,
)
from isekai.shared.field_map import Group  # noqa: E402
from isekai.shared.vocabulary import Vocabulary  # noqa: E402
from tests.conftest import snapshot  # noqa: E402
from tests.images import jpeg_bytes  # noqa: E402
from tests.stages import FIELD_MAP, caption, fake_tagger, sheet  # noqa: E402

FLOW = "summon-anime-wai"

# The address every client below is built against. Since v0.22.1 the app
# refuses a request not addressed to the loopback address it was bound to, so
# a test client has to speak that address rather than `TestClient`'s default
# `http://testserver` -- which is exactly the header an attacker's page sends.
PORT = 8765
ADDRESS = f"http://{HOST}:{PORT}"


@pytest.fixture
def wired(tmp_path: Path, vocabulary: Vocabulary) -> Wiring:
    """Return a ③-only wiring: no reader, no tagger, no transport."""
    return Wiring(
        reader=None,
        tagger=None,
        hosted_tagger=None,
        client=None,
        vocabulary=lambda: vocabulary,
        field_map=lambda _: FIELD_MAP,
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
        schema,
        vocabulary,
    )
    return run


def _clear_wd14(run: Run) -> None:
    """Remove the tag list `stages.sheet` wrote, leaving the sheet in place."""
    for path in run.directory(FLOW, WD14).iterdir():
        path.unlink()


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
    return TestClient(create_app(batch, host=HOST, port=PORT), base_url=ADDRESS)


@pytest.fixture
def client(wired: Wiring, made: Run, tmp_path: Path) -> TestClient:
    """Return a client over the surface, with a stand-in for the built bundle."""
    return _client(wired, made, tmp_path)


# --- the address every request is checked against -----------------------------


@pytest.mark.spec("ui:address:a-request-to-the-bound-address-is-answered")
def test_a_request_addressed_to_the_bound_address_is_answered(
    client: TestClient,
) -> None:
    # The `client` fixture speaks `ADDRESS`, so this is the ordinary path every
    # other test in this module rides: it is here to make the two refusals below
    # mean something other than "the middleware refuses everything".
    assert client.get("/api/batch").status_code == 200


@pytest.mark.spec("ui:address:another-host-is-refused")
def test_a_request_carrying_someone_elses_host_is_refused(
    client: TestClient,
) -> None:
    # DNS rebinding: the attacker's domain resolves to 127.0.0.1, so the socket
    # is right and only the name is wrong.
    answered = client.get("/api/batch", headers={"host": f"evil.example:{PORT}"})

    assert answered.status_code == 403
    assert answered.json() == {"refusal": "not addressed here"}


@pytest.mark.spec("ui:address:another-origin-is-refused")
def test_a_write_carrying_another_pages_origin_is_refused(
    client: TestClient, made: Run
) -> None:
    # The cross-site write: the browser sends this server's `Host` because that
    # is where it is connecting, and the attacking page's `Origin` because that
    # is where the script came from.
    answered = client.put(
        f"/api/inputs/{made.id}/draft",
        json={"fields": {}},
        headers={"origin": "http://evil.example"},
    )

    assert answered.status_code == 403
    assert answered.json() == {"refusal": "not from this page"}


@pytest.mark.spec("ui:address:every-loopback-spelling-is-answered")
def test_every_loopback_alias_of_the_bound_port_is_answered() -> None:
    # `localhost` is what an operator types and `127.0.0.1` is what the startup
    # line prints, so refusing either would be a defect rather than a defence --
    # and neither name can be made to point anywhere else.
    assert authorities("127.0.0.1", PORT) == authorities("localhost", PORT)
    assert f"localhost:{PORT}" in authorities("127.0.0.1", PORT)
    # A non-loopback bind answers to its own name only.
    assert authorities("example.test", PORT) == {f"example.test:{PORT}"}


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


@pytest.mark.spec("ui:source:a-missing-caption-names-its-command")
def test_a_missing_caption_is_served_with_the_command_that_writes_it(
    wired: Wiring, made: Run, tmp_path: Path
) -> None:
    beside = _client(wired, made, tmp_path).get(f"/api/inputs/{made.id}").json()
    assert beside["caption"] == "Dark brown hair, brown eyes."
    assert beside["caption_command"] is None

    for path in made.directory(FLOW, CAPTIONS).iterdir():
        path.unlink()
    response = _client(wired, made, tmp_path).get(f"/api/inputs/{made.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["caption"] is None
    command = body["caption_command"]
    assert command == f"python -m isekai caption --flow {FLOW} {made.id}"
    parsed = build_parser().parse_args(command.split()[3:])
    assert (parsed.verb, parsed.flows, parsed.photos) == ("caption", [FLOW], [made.id])


@pytest.mark.spec_exempt("structural: the join the page reads per input")
def test_an_input_carries_its_caption_its_fields_and_its_budget(
    client: TestClient, made: Run, schema: Schema
) -> None:
    body = client.get(f"/api/inputs/{made.id}").json()

    assert body["caption"] == "Dark brown hair, brown eyes."
    # Every field the schema declares, in schema order, never re-sorted -- the
    # tagger's own canonical spelling is what stage ② routed, not the fixture's.
    assert list(body["fields"]) == list(schema.names)
    assert body["fields"]["hair_colour"]
    assert body["draft"] == "001.draft.json"
    assert body["readonly"] is False
    # The shares and the overhead reconcile, because they come from one rule.
    budget = body["budget"]
    assert sum(budget["per_field"].values()) + budget["overhead"] == budget["total"]


@pytest.mark.spec_exempt(
    "structural: the encoder window is declared once, and the browser reads it "
    "from the budget"
)
def test_the_budget_carries_the_encoder_window(client: TestClient, made: Run) -> None:
    body = client.get(f"/api/inputs/{made.id}").json()

    assert body["budget"]["window"] == ENCODER_WINDOW


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
    assert "is approved" in response.json()["refusal"]
    assert snapshot(made.path) == before


@pytest.mark.spec("ui:approval:a-re-opened-input-is-editable")
def test_an_input_re_opened_with_a_new_version_is_editable_again(
    client: TestClient, made: Run
) -> None:
    """The state `review --flow F --new-version` produces, and what it is for.

    `v0.22.1` refused every update to an approved input, which made this state a
    dead end: the verb wrote a draft the surface would not edit, and the refusal
    it shipped said so outright, naming this version as the one that resolves it.
    The gate is now *approved and no later draft*, so the page shows the draft,
    offers the form and accepts the write (design.md D5).
    """
    fields = client.get(f"/api/inputs/{made.id}").json()["fields"]
    assert client.post(f"/api/inputs/{made.id}/approve").status_code == 200
    # Approved and read-only, until the operator asks for a new version.
    assert client.get(f"/api/inputs/{made.id}").json()["readonly"] is True

    review(made, FLOW, new_version=True)

    body = client.get(f"/api/inputs/{made.id}").json()
    assert body["readonly"] is False
    # The draft's sheet, not the approved artifact's -- and the approved
    # artifact is still named, because it has not gone anywhere.
    assert body["draft"] == "002.draft.json"
    assert body["approved"] == "001.approved.json"
    assert body["fields"] == fields

    response = client.put(f"/api/inputs/{made.id}/draft", json={"fields": fields})

    assert response.status_code == 200
    assert response.json()["draft"] == "002.draft.json"
    # The approved artifact is never edited in place, in either state.
    assert (
        read(made.directory(FLOW, REVIEW) / "001.approved.json", APPROVED_FILE)[
            "fields"
        ]
        == fields
    )


@pytest.mark.spec("ui:approval:a-re-opened-input-is-not-counted-approved")
def test_a_re_opened_input_reports_its_own_status_and_does_not_split_the_count(
    client: TestClient, made: Run
) -> None:
    """The hazard a third status creates, pinned from the side the count is on.

    `/api/batch["approved"]` was derived from the status string and
    `Batch.approved_count` reads the directory. They agree only while every
    input holding an approved artifact also *reports* approved -- which stops
    being true the moment a status exists meaning *has one, and is open again*.
    So the payload's count reads the directory too (design.md D5).
    """
    assert client.get("/api/batch").json()["inputs"][0]["status"] == "draft"
    assert client.post(f"/api/inputs/{made.id}/approve").status_code == 200
    assert client.get("/api/batch").json()["inputs"][0]["status"] == "approved"

    review(made, FLOW, new_version=True)

    body = client.get("/api/batch").json()
    assert body["inputs"][0]["status"] == "re-opened"
    # Neither approved nor a plain draft -- and the count still says what the
    # directory says, which is that an approved artifact is on disk.
    # The scenario's second `THEN`, against the directory rather than against
    # another of the server's own numbers: what is on disk is one approved
    # artifact, and the payload says one.
    assert body["approved"] == len(
        list(made.directory(FLOW, REVIEW).glob("*.approved.json"))
    )
    assert body["approved"] == 1


@pytest.mark.spec("ui:draft-update:a-stale-precondition-is-refused")
def test_an_update_written_against_a_stale_draft_is_refused(
    client: TestClient, made: Run
) -> None:
    """The page autosaves on a debounce, so two `PUT`s can be in flight at once.

    Nothing ordered them: they committed in whatever order the server finished
    them, so last write won where *last* was not the operator's last keystroke.
    `st_mtime` is the precondition because nothing else exists on disk -- the
    draft carries no timestamp, no revision counter and no digest (design.md D6).
    """
    body = client.get(f"/api/inputs/{made.id}").json()
    fields, saved = body["fields"], body["saved"]

    # The first of the two in-flight saves lands and moves the draft's mtime.
    first = client.put(
        f"/api/inputs/{made.id}/draft", json={"fields": fields, "saved": saved}
    )
    assert first.status_code == 200
    assert first.json()["saved"] != saved

    # The second was written against what the page read before the first, which
    # is exactly the state a debounce produces.
    second = client.put(
        f"/api/inputs/{made.id}/draft", json={"fields": fields, "saved": saved}
    )

    assert second.status_code == 409
    assert "changed since this page last read it" in second.json()["refusal"]
    # And the receipt the first save returned is the one that lets the page
    # carry on: echoing it back is accepted.
    third = client.put(
        f"/api/inputs/{made.id}/draft",
        json={"fields": fields, "saved": first.json()["saved"]},
    )
    assert third.status_code == 200


@pytest.mark.spec("ui:draft-update:no-precondition-is-accepted")
def test_an_update_stating_no_precondition_is_still_accepted(
    client: TestClient, made: Run
) -> None:
    # A payload carrying no `saved` states no precondition, and gets the
    # behaviour it had before -- the mtime is already on the wire as the field
    # every response returns, so a client that echoes it gets the check.
    fields = client.get(f"/api/inputs/{made.id}").json()["fields"]

    assert (
        client.put(f"/api/inputs/{made.id}/draft", json={"fields": fields}).status_code
        == 200
    )


@pytest.mark.spec("ui:approval:a-stale-lower-draft-does-not-reopen")
def test_a_stale_lower_draft_does_not_reopen_an_approved_input(
    client: TestClient, made: Run
) -> None:
    directory = made.directory(FLOW, REVIEW)
    stale = (directory / "001.draft.json").read_bytes()
    assert client.post(f"/api/inputs/{made.id}/approve").status_code == 200
    review(made, FLOW, new_version=True)
    assert client.post(f"/api/inputs/{made.id}/approve").status_code == 200
    # Below the approval: left by a crash, or restored by hand.
    (directory / "001.draft.json").write_bytes(stale)
    expected = read(directory / "002.approved.json", APPROVED_FILE)["fields"]

    body = client.get(f"/api/inputs/{made.id}").json()

    assert body["readonly"] is True
    assert body["draft"] is None
    assert body["approved"] == "002.approved.json"
    assert body["fields"] == expected


def _overlap(
    client: TestClient, made: Run, monkeypatch: pytest.MonkeyPatch
) -> dict[str, int]:
    """Send two updates stating one precondition, the second inside the first.

    The second starts while the first is between its check and its write, and
    is given the chance to pass the check before the first writes.
    """
    body = client.get(f"/api/inputs/{made.id}").json()
    saved = body["saved"]
    checked = threading.Event()
    answers: dict[str, int] = {}
    threads: list[threading.Thread] = []
    precondition, save = app_module._precondition, app_module.save_draft

    def check(batch: Batch, held: Input, payload: Mapping[str, Any]) -> None:
        if threading.current_thread().name == "second":
            checked.set()
        precondition(batch, held, payload)

    def put(name: str, hair: str) -> None:
        fields = {**body["fields"], "hair_colour": [hair]}
        answers[name] = client.put(
            f"/api/inputs/{made.id}/draft", json={"fields": fields, "saved": saved}
        ).status_code

    def write(run: Run, flow: str, fields: Mapping[str, Sequence[str]]) -> Path:
        if not threads:
            second = threading.Thread(
                target=put, args=("second", "black hair"), name="second"
            )
            threads.append(second)
            second.start()
            checked.wait(timeout=0.5)
        return save(run, flow, fields)

    monkeypatch.setattr(app_module, "_precondition", check)
    monkeypatch.setattr(app_module, "save_draft", write)
    put("first", "blonde")
    for thread in threads:
        thread.join()
    return answers


@pytest.mark.spec("ui:draft-update:overlapping-updates-cannot-both-commit")
def test_overlapping_draft_updates_cannot_both_commit(
    client: TestClient, made: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    answers = _overlap(client, made, monkeypatch)

    assert answers == {"first": 200, "second": 409}
    on_disk = json.loads((made.directory(FLOW, REVIEW) / "001.draft.json").read_text())
    assert on_disk["fields"]["hair_colour"] == ["blonde"]


@pytest.mark.spec_exempt("twin: the overlap test fails once the lock is gone")
def test_without_the_lock_overlapping_updates_both_commit(
    client: TestClient, made: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(app_module, "_DRAFT_UPDATE", contextlib.nullcontext())

    assert _overlap(client, made, monkeypatch) == {"first": 200, "second": 200}


def _update_during_approval(
    client: TestClient,
    made: Run,
    monkeypatch: pytest.MonkeyPatch,
    *,
    unlocked: bool = False,
) -> int:
    """Approve while an update is in flight, and return the update's status.

    The update starts inside the approval and is given the chance to pass its
    check first; if it does, its write waits until the approval has written.
    With the lock the check cannot run until the approval ends, so the chance is
    a bounded wait that times out; `unlocked`, the check always runs. Both waits
    are bounded and asserted, so a regression fails rather than hangs.
    """
    body = client.get(f"/api/inputs/{made.id}").json()
    checked, approved = threading.Event(), threading.Event()
    answers: list[int] = []
    precondition, approving = app_module._precondition, app_module.approve
    write = review_module.write

    def check(batch: Batch, held: Input, payload: Mapping[str, Any]) -> None:
        checked.set()
        precondition(batch, held, payload)

    def put() -> None:
        fields = {**body["fields"], "hair_colour": ["blonde"]}
        answers.append(
            client.put(
                f"/api/inputs/{made.id}/draft",
                json={"fields": fields, "saved": body["saved"]},
            ).status_code
        )

    def late[T: Mapping[str, object]](
        path: Path, kind: Artifact[T], artifact: T
    ) -> None:
        # By name: the endpoint runs on a worker thread, not on `update`.
        if path.name.endswith(".draft.json"):
            assert approved.wait(timeout=5), "the approval never finished"
        write(path, kind, artifact)

    def approve_(
        run: Run, flow: str, schema: Schema, vocabulary: Vocabulary
    ) -> tuple[Path | None, list[str]]:
        update.start()
        assert checked.wait(timeout=5 if unlocked else 0.5) is unlocked, (
            "the update's check ran inside the approval"
            if not unlocked
            else "the update's check never ran"
        )
        try:
            return approving(run, flow, schema, vocabulary)
        finally:
            approved.set()

    update = threading.Thread(target=put)
    monkeypatch.setattr(app_module, "_precondition", check)
    monkeypatch.setattr(app_module, "approve", approve_)
    monkeypatch.setattr(review_module, "write", late)
    assert client.post(f"/api/inputs/{made.id}/approve").status_code == 200
    update.join()
    return answers[0]


@pytest.mark.spec("ui:approval:an-update-overlapping-an-approval-is-refused")
def test_an_update_overlapping_an_approval_is_refused(
    client: TestClient, made: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = made.directory(FLOW, REVIEW)
    fields = read(directory / "001.draft.json", DRAFT_FILE)["fields"]

    assert _update_during_approval(client, made, monkeypatch) == 409
    assert sorted(path.name for path in directory.iterdir()) == ["001.approved.json"]
    assert read(directory / "001.approved.json", APPROVED_FILE)["fields"] == fields


@pytest.mark.spec_exempt("twin: the approval test fails once approval takes no lock")
def test_without_the_lock_an_update_writes_after_the_approval(
    client: TestClient, made: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(app_module, "_DRAFT_UPDATE", contextlib.nullcontext())

    assert _update_during_approval(client, made, monkeypatch, unlocked=True) == 200
    assert (made.directory(FLOW, REVIEW) / "001.draft.json").exists()


@pytest.mark.spec("ui:approval:approved-input-opens-read-only")
def test_an_input_approved_in_an_earlier_sitting_opens_read_only(
    wired: Wiring, made: Run, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    review(made, FLOW)
    approved, _ = approve(made, FLOW, schema, vocabulary)
    assert approved is not None
    expected = {
        name: list(tags)
        for name, tags in read(approved, APPROVED_FILE)["fields"].items()
    }

    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html>")
    batch = establish(wired, FLOW, [made.id], bundle=lambda: dist)
    reopened = TestClient(create_app(batch, host=HOST, port=PORT), base_url=ADDRESS)

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
def test_the_local_list_is_whole_and_the_hosted_list_is_filtered(
    wired: Wiring, made: Run, tmp_path: Path
) -> None:
    # The sheet the `made` fixture filled needed a tag list, so one is already on
    # disk; this test is about what the *real* local tagger writes, so it replaces
    # it rather than writing a second version beside it.
    _clear_wd14(made)
    tag_wd14(made, FLOW, fake_tagger)
    tag_hosted(
        made,
        FLOW,
        FakeTagger(tags=("brown hair", "fashion photography", "blue eyes")),
    )

    body = _client(wired, made, tmp_path).get(f"/api/inputs/{made.id}").json()

    # Whole: every tag the local tagger scored, because it is scored against the
    # vocabulary it emits and so every one of them is committable.
    assert body["wd14"] == [{"tag": "1girl", "confidence": 0.9}]
    # Filtered: `fashion photography` is in no field's reach, and on the
    # acceptance batch nine in ten of this model's tags were like it (D29).
    assert [one["tag"] for one in body["tags"]] == ["brown hair", "blue eyes"]


@pytest.mark.spec("ui:source:each-hosted-tag-is-offered-once")
def test_the_hosted_panel_shows_each_tag_once_and_the_local_one_shows_every_row(
    wired: Wiring, made: Run, tmp_path: Path
) -> None:
    """Deduplicated on the hosted side only, and the asymmetry is the point.

    `OfferedTag` is `{tag, posts}` where `posts` is a pure function of `tag`, so
    a repeat is a byte-identical object carrying no information -- and it was a
    duplicate Vue key. `ScoredTag` is `{tag, confidence}`, where two rows can
    legitimately differ, so `_wd14` is left whole: deduping it would falsify
    `ui:source:both-tag-lists-are-shown-raw-and-read-only`'s first `THEN`
    (design.md D7).
    """
    _clear_wd14(made)
    tag_wd14(made, FLOW, fake_tagger)
    tag_hosted(
        made,
        FLOW,
        FakeTagger(tags=("brown hair", "blue eyes", "brown hair")),
    )

    # The two tag artifacts, and only those: `establish()` opens a draft for
    # every input it is given, which is stage ③ starting normally rather than
    # the panel writing anything.
    before = {stage: snapshot(made.directory(FLOW, stage)) for stage in (WD14, TAGS)}

    body = _client(wired, made, tmp_path).get(f"/api/inputs/{made.id}").json()

    assert [one["tag"] for one in body["tags"]] == ["brown hair", "blue eyes"]
    # Unchanged, and asserted here rather than left to the test above: the two
    # lists are narrowed by different rules and this is the one that says so.
    assert [one["tag"] for one in body["wd14"]] == ["1girl"]
    # The scenario's last `THEN`: narrowing the panel is not narrowing the
    # artifact. A sibling test proves the hosted list keeps what the page drops;
    # this one is bound to the key that says *both* artifacts are untouched, so
    # it asserts that clause rather than borrowing it.
    assert {
        stage: snapshot(made.directory(FLOW, stage)) for stage in (WD14, TAGS)
    } == before


@pytest.mark.spec("ui:source:the-artifact-keeps-what-the-panel-drops")
def test_a_tag_withheld_from_the_page_is_still_in_the_artifact(
    wired: Wiring, made: Run, tmp_path: Path
) -> None:
    # Filtered on the way to the page, never on the way to disk. Narrowing the
    # record would make it disagree with what the model said, and looking behind
    # the router is the whole reason the artifact exists.
    written = tag_hosted(
        made,
        FLOW,
        FakeTagger(tags=("brown hair", "fashion photography", "blue eyes")),
    )

    body = _client(wired, made, tmp_path).get(f"/api/inputs/{made.id}").json()

    assert "fashion photography" not in [one["tag"] for one in body["tags"]]
    assert written is not None
    assert read(written, TAGS_FILE)["tags"] == [
        "brown hair",
        "fashion photography",
        "blue eyes",
    ]


@pytest.mark.spec("ui:source:vocabulary-membership-is-marked-by-the-server")
def test_membership_is_decided_server_side_and_the_count_travels_with_it(
    wired: Wiring, made: Run, tmp_path: Path, vocabulary: Vocabulary
) -> None:
    # Decided here, not in the browser: `/api/tags` answers a fragment query and
    # has no membership form, so asking per tag would be one round trip each.
    tag_hosted(
        made,
        FLOW,
        FakeTagger(tags=("brown hair", "fashion photography", "blue eyes")),
    )

    body = _client(wired, made, tmp_path).get(f"/api/inputs/{made.id}").json()
    marked = {one["tag"]: one for one in body["tags"]}

    assert marked["brown hair"]["posts"] == vocabulary.count("brown hair")
    assert marked["blue eyes"]["posts"] == vocabulary.count("blue eyes")
    # Every tag that reaches the page carries a number, because every tag that
    # reaches the page is in the vocabulary. There is no membership flag left to
    # send: it would be `true` on all of them.
    assert all(one["posts"] > 0 for one in body["tags"])
    assert all(set(one) == {"tag", "posts"} for one in body["tags"])


@pytest.mark.spec("ui:source:an-absent-tag-artifact-is-silent")
def test_an_input_with_neither_artifact_carries_null_and_still_serves(
    client: TestClient, made: Run
) -> None:
    # A run whose sheet was filled before v0.20 and whose tag lists were never
    # written. It cannot be produced by filling a sheet now -- the stage refuses
    # without a tag list -- so it is produced by removing the one the fixture
    # wrote, which is the state on disk either way. Both are null, the surface
    # answers 200, and nothing anywhere is a refusal (design.md D20).
    _clear_wd14(made)

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
    # The state a run is in when the hosted tagger has not been reached: a WD14
    # list and no hosted one. A missing hosted list is an absent aid, never a
    # blocked review (design.md D3).
    tag_wd14(made, FLOW, fake_tagger)

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


# --- the cheatsheet, which is the table read the other way ---------------------


@pytest.mark.spec("ui:cheatsheet:every-declared-criterion-is-answered")
def test_every_criterion_the_flow_declares_is_answered_and_no_other(
    client: TestClient, schema: Schema
) -> None:
    body = client.get("/api/fields").json()

    assert tuple(body["fields"]) == schema.names
    # `summon-anime-wai` declares sixteen of the twenty-one the table carries; the
    # five only `conjure-anime-wai` declares are absent rather than empty.
    assert "bangs" in FIELD_MAP.fields
    assert "bangs" not in body["fields"]


@pytest.mark.spec("ui:cheatsheet:an-empty-group-is-present")
def test_a_criterion_the_table_holds_nothing_for_is_present_and_empty(
    client: TestClient,
) -> None:
    body = client.get("/api/fields").json()

    assert FIELD_MAP.group("age_band") == ()
    assert body["fields"]["age_band"] == []
    assert "age_band" in body["fields"]


@pytest.mark.spec("ui:cheatsheet:candidates-are-ordered-by-post-count")
def test_candidates_are_ordered_by_descending_post_count(
    client: TestClient, vocabulary: Vocabulary
) -> None:
    body = client.get("/api/fields").json()

    group = body["fields"]["hair_silhouette"]
    assert len(group) > 1
    assert [one["posts"] for one in group] == sorted(
        (one["posts"] for one in group), reverse=True
    )
    for one in group:
        assert one["posts"] == vocabulary.count(one["tag"])
    # The browsable group, not the primaries alone: `brown hair` is browsable
    # under both hair criteria and routes to one of them.
    assert {one["tag"] for one in group} == set(FIELD_MAP.group("hair_silhouette"))


@pytest.mark.spec("ui:cheatsheet:the-excluded-list-is-not-served")
def test_the_excluded_list_reaches_no_group_and_is_not_in_the_response(
    wired: Wiring, made: Run, tmp_path: Path
) -> None:
    # The committed table's excluded list is empty, so the assertion is driven
    # from a table that has one -- otherwise it would pass vacuously.
    withheld = replace(FIELD_MAP, excluded=frozenset({"glasses"}))
    fields = dict(FIELD_MAP.fields)
    fields["accessories"] = Group(primary=(), also=())
    wired.field_map = lambda _: replace(withheld, fields=fields)

    body = _client(wired, made, tmp_path).get("/api/fields").json()

    assert set(body) == {"fields"}
    assert "glasses" not in json.dumps(body)
