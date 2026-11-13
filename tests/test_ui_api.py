"""The endpoints, against a running application.

They are the address guard, the library, a collection's hub, the tag search, the field
candidates, a run's review, photo, draft and approval, its renders, and the import's
upload, stream and preview.

**This module runs in the gate.** FastAPI is pinned in the `dev` dependency
group, so `uv sync --locked` installs it and the `ui` scenarios bound here are
proved. `tests/test_ui.py` asserts the framework is present, so its absence is a
failure rather than a silent skip.

The `importorskip` below is kept as a belt for an environment synced without the
dev group: a module-level `from fastapi.testclient import TestClient` would fail
*collection* there, which is the gate's `uv run pytest` going red over a missing
test tool rather than a defect.

This is deliberately not the evaluator tests' pattern. Those fake the embedder;
here the thing under test *is* the HTTP surface, so there is nothing to fake
that would leave anything worth asserting.

Everything that can be asserted without a server is in `tests/test_ui.py` and
`tests/test_ui_library.py`.
"""

import contextlib
import io
import json
import os
import queue
import random
import shlex
import shutil
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI, Response  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import isekai.foundation.run as run_module  # noqa: E402
import isekai.interface.render as render_module  # noqa: E402
import isekai.interface.ui.app as app_module  # noqa: E402
import isekai.pipeline.importing as importing_module  # noqa: E402
import isekai.pipeline.review as review_module  # noqa: E402
from isekai.boundary.gpu import Seams  # noqa: E402
from isekai.foundation.artifacts import (
    APPROVED_FILE,
    DRAFT_FILE,
    EDIT_FILE,
    SESSION_FILE,
    SHEET_FILE,
    TAGS_FILE,
    Artifact,
    Renders,
    SessionRecord,
    read,
)
from isekai.foundation.artifacts import replace as replace_record
from isekai.foundation.flow import (  # noqa: E402
    Flow,
    Schema,
    load_flow,
    manifest_digest,
)
from isekai.foundation.run import (  # noqa: E402
    APPROVED,
    CAPTIONS,
    DESCRIPTION,
    PHOTO,
    REVIEW,
    TAGS,
    WD14,
    Run,
    approval_of,
    assign,
    latest_artifact,
    open_run,
    versions,
)
from isekai.interface.cli import build_parser, dispatch  # noqa: E402
from isekai.interface.ui import HOST, events, library  # noqa: E402
from isekai.interface.ui.app import (  # noqa: E402
    RARE_BELOW,
    Held,
    authorities,
    create_app,
)
from isekai.interface.ui.jobs import Jobs  # noqa: E402
from isekai.interface.wiring import Wiring  # noqa: E402
from isekai.pipeline.caption import FakeReader  # noqa: E402
from isekai.pipeline.generate import image_of, prepare, prompt_artifact  # noqa: E402
from isekai.pipeline.review import (  # noqa: E402
    DRAFT,
    ENCODER_WINDOW,
    approve,
    cancellable,
    review,
    save_draft,
)
from isekai.pipeline.tagging import (  # noqa: E402
    FakeTagger,
    tag_hosted,
    tag_wd14,
)
from isekai.shared.field_map import Group  # noqa: E402
from isekai.shared.image import THUMB_SIDE  # noqa: E402
from isekai.shared.vocabulary import Vocabulary  # noqa: E402
from tests.conftest import snapshot, tree  # noqa: E402
from tests.fakes import FakeComfyClient  # noqa: E402
from tests.images import jpeg_bytes, photo_jpeg, png_bytes  # noqa: E402
from tests.stages import (  # noqa: E402
    FIELD_MAP,
    NO_GPUNIT,
    bare_wiring,
    caption,
    fake_tagger,
    render,
    rendered_image,
    sheet,
)

FLOW = "summon-anime-wai"
COLLECTION = "2026-10-19"
# The suite's own copy of the flows `config/ui.json` offers.
OFFERED = (FLOW, "conjure-anime-wai")
# The route every draft from an image is written through.
DRAFT_ROUTE = f"/api/c/{COLLECTION}/draft"

# The address every client below is built against. The app refuses a request
# not addressed to the loopback address it was bound to, so a test client has
# to speak that address rather than `TestClient`'s default
# `http://testserver` -- which is exactly the header an attacker's page sends.
PORT = 8765
ADDRESS = f"http://{HOST}:{PORT}"


def _at(run: Run, tail: str = "") -> str:
    """Return the review path naming `run` in `FLOW`: `/api/c/<c>/review/<d>/<f>`."""
    return f"/api/c/{COLLECTION}/review/{run.digest}/{FLOW}{tail}"


@pytest.fixture
def wired(tmp_path: Path, vocabulary: Vocabulary) -> Wiring:
    """Return a ③-only wiring over one collection of a library: no reader, no tagger."""
    (tmp_path / "lib" / COLLECTION / "sources").mkdir(parents=True)
    return Wiring(
        reader=None,
        tagger=None,
        hosted_tagger=None,
        client=None,
        vocabulary=lambda: vocabulary,
        field_map=lambda _: FIELD_MAP,
        runs_root=tmp_path / "lib" / COLLECTION / "runs",
        rng=random.Random(0),
        out=io.StringIO(),
        err=io.StringIO(),
        volume=NO_GPUNIT,
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


def _source(run: Run) -> None:
    """Put the run's photograph in the collection's `sources/`, as an import would."""
    (run.path.parent.parent / "sources" / "ada.jpg").write_bytes(run.photo.read_bytes())


def _clear_wd14(run: Run) -> None:
    """Remove the tag list `stages.sheet` wrote, leaving the sheet in place."""
    for path in run.directory(PHOTO, WD14).iterdir():
        path.unlink()


def _client(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    *,
    drafted: bool = True,
    offered: Sequence[str] = OFFERED,
) -> TestClient:
    """Return a client over the app, with a stand-in for the built bundle.

    `drafted` takes the draft opening the sheet would, so a test may write
    before it reads; `offered` is the surface's flows. The library is the folder
    holding the wiring's collection.
    """
    dist = tmp_path / "dist"
    dist.mkdir(exist_ok=True)
    (dist / "index.html").write_text("<!doctype html>")
    if drafted:
        review(made, FLOW)
    app = create_app(
        wired.runs_root.parent.parent,
        wired,
        flows=offered,
        bundle=dist,
        wire=lambda runs: replace(wired, runs_root=runs),
        host=HOST,
        port=PORT,
    )
    return TestClient(app, base_url=ADDRESS)


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
    assert client.get("/api/library").status_code == 200


@pytest.mark.spec("ui:address:another-host-is-refused")
def test_a_request_carrying_someone_elses_host_is_refused(
    client: TestClient, made: Run
) -> None:
    # DNS rebinding: the attacker's domain resolves to 127.0.0.1, so the socket
    # is right and only the name is wrong. The write is one a handler would
    # accept, so a guard that answered after the handler leaves the run changed.
    fields = client.get(_at(made)).json()["fields"]
    fields["hair_colour"] = ["blonde"]
    before = snapshot(made.path)

    answered = client.put(
        _at(made, "/draft"),
        json={"fields": fields},
        headers={"host": f"evil.example:{PORT}"},
    )

    assert answered.status_code == 403
    assert answered.json() == {"refusal": "not addressed here"}
    assert snapshot(made.path) == before


@pytest.mark.spec("ui:address:another-origin-is-refused")
def test_a_write_carrying_another_pages_origin_is_refused(
    client: TestClient, made: Run
) -> None:
    # The cross-site write: the browser sends this server's `Host` because that
    # is where it is connecting, and the attacking page's `Origin` because that
    # is where the script came from.
    fields = client.get(_at(made)).json()["fields"]
    fields["hair_colour"] = ["blonde"]
    before = snapshot(made.path)

    answered = client.put(
        _at(made, "/draft"),
        json={"fields": fields},
        headers={"origin": "http://evil.example"},
    )

    assert answered.status_code == 403
    assert answered.json() == {"refusal": "not from this page"}
    assert snapshot(made.path) == before


@pytest.mark.spec("ui:address:a-cross-site-request-without-origin-is-refused")
def test_a_cross_site_request_without_origin_is_refused(
    client: TestClient, made: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    # An image tag on another page probing for the photograph: no `Origin`, and
    # the browser marks it `cross-site` all the same.
    read: list[object] = []
    monkeypatch.setattr(app_module, "FileResponse", lambda path: read.append(path))
    answered = client.get(_at(made, "/photo"), headers={"sec-fetch-site": "cross-site"})

    assert answered.status_code == 403
    assert answered.json() == {"refusal": "not from this page"}
    assert read == []


@pytest.mark.spec_exempt(
    "structural: twin of test_a_cross_site_request_without_origin_is_refused"
)
def test_a_request_from_this_page_reads_the_photograph(
    client: TestClient, made: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    read: list[object] = []

    def record(path: object, **_keywords: object) -> Response:
        read.append(path)
        return Response()

    monkeypatch.setattr(app_module, "FileResponse", record)
    answered = client.get(
        _at(made, "/photo"), headers={"sec-fetch-site": "same-origin"}
    )

    assert answered.status_code == 200
    assert read == [made.photo]


@pytest.mark.spec_exempt("structural: this page's own requests are answered")
def test_a_request_without_origin_from_this_page_or_no_browser_is_answered(
    client: TestClient,
) -> None:
    for site in ("same-origin", "none"):
        answered = client.get("/api/library", headers={"sec-fetch-site": site})
        assert answered.status_code == 200, site
    assert client.get("/api/library").status_code == 200
    assert (
        client.get("/api/library", headers={"sec-fetch-site": "same-site"}).status_code
        == 403
    )


@pytest.mark.spec("ui:address:every-loopback-spelling-is-answered")
def test_every_loopback_alias_of_the_bound_port_is_answered(
    client: TestClient, made: Run
) -> None:
    # `localhost` is what an operator types and `127.0.0.1` is what the startup
    # line prints, so refusing either would be a defect rather than a defence --
    # and neither name can be made to point anywhere else.
    assert authorities("127.0.0.1", PORT) == authorities("localhost", PORT)
    assert f"localhost:{PORT}" in authorities("127.0.0.1", PORT)
    # A non-loopback bind answers to its own name only.
    assert authorities("example.test", PORT) == {f"example.test:{PORT}"}
    # The middleware answers each spelling, not only the helper that lists them.
    for host in (f"localhost:{PORT}", f"[::1]:{PORT}"):
        assert client.get("/api/library", headers={"host": host}).status_code == 200
    fields = client.get(_at(made)).json()["fields"]
    fields["hair_colour"] = ["blonde"]
    written = client.put(
        _at(made, "/draft"),
        json={"fields": fields},
        headers={"host": f"localhost:{PORT}", "origin": f"http://localhost:{PORT}"},
    )
    assert written.status_code == 200
    assert client.get(_at(made)).json()["fields"]["hair_colour"] == ["blonde"]


# --- the collection, and the payload the page is drawn from ------------------------


@pytest.mark.spec_exempt("structural: the shape the page is drawn from")
def test_the_hub_and_the_input_name_the_flow_the_schema_and_the_vocabulary(
    client: TestClient, made: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    _source(made)
    hub = client.get(f"/api/c/{COLLECTION}/hub").json()
    body = client.get(_at(made)).json()

    assert hub["collection"] == COLLECTION
    assert FLOW in hub["flows"]
    assert [one["digest"] for one in hub["sources"]] == [made.digest]
    assert hub["sources"][0]["cells"][FLOW]["stage"] == "draft"
    assert body["flow"] == FLOW
    assert body["id"] == made.digest
    assert body["schema"] == list(schema.names)
    assert body["vocabulary"] == len(vocabulary)
    assert body["width"] == 1200


@pytest.mark.spec("ui:hub:a-prepared-tick-stays")
@pytest.mark.spec("ui:hub:a-tagged-cell-with-no-work-unticks")
def test_an_untick_is_refused_on_work_and_takes_an_empty_tagged_flow(
    client: TestClient, made: Run
) -> None:
    _source(made)
    before = snapshot(made.path)

    answered = client.post(
        f"/api/c/{COLLECTION}/assign",
        json={"sources": ["ada.jpg"], "flow": FLOW, "remove": True},
    ).json()

    assert f"{made.id}: {FLOW} holds work" in answered["refused"]["ada.jpg"]
    assert snapshot(made.path) == before

    def stage() -> str | None:
        hub = client.get(f"/api/c/{COLLECTION}/hub").json()
        return hub["sources"][0]["cells"][CONJURE]["stage"]

    def assign(remove: bool) -> None:
        client.post(
            f"/api/c/{COLLECTION}/assign",
            json={"sources": ["ada.jpg"], "flow": CONJURE, "remove": remove},
        )

    tags = snapshot(made.directory(PHOTO, WD14))
    assign(remove=False)
    assert stage() == "tagged"
    assign(remove=True)
    assert stage() is None
    assert not made.directory(CONJURE).exists()
    assert snapshot(made.directory(PHOTO, WD14)) == tags


@pytest.mark.spec("ui:routes:a-run-is-named-by-its-digest")
def test_a_review_url_names_its_run_by_the_digest_its_identifier_begins_with(
    client: TestClient, made: Run
) -> None:
    body = client.get(_at(made)).json()

    assert body["run"] == made.id
    assert made.id.startswith(body["id"]) and len(body["id"]) == 12
    unknown = client.get(f"/api/c/{COLLECTION}/review/{'0' * 12}/{FLOW}")
    assert unknown.status_code == 409
    assert "no run named" in unknown.json()["refusal"]
    elsewhere = client.get(f"/api/c/no-such-collection/review/{made.digest}/{FLOW}")
    assert "no collection named 'no-such-collection'" in elsewhere.json()["refusal"]


@pytest.mark.spec_exempt("structural: a screen's path loads the shell, an API's not")
def test_any_other_path_is_the_page_and_an_unknown_api_path_is_not_found(
    client: TestClient,
) -> None:
    page = client.get(f"/c/{COLLECTION}/review/0d4b7e6fb2a8/{FLOW}")
    assert page.status_code == 200
    assert page.text == "<!doctype html>"
    assert client.get("/api/nothing-here").status_code == 404


@pytest.mark.spec("ui:review:opening-a-sheet-writes-its-draft")
def test_opening_a_sheet_with_no_draft_writes_one_and_opening_again_writes_none(
    wired: Wiring, made: Run, tmp_path: Path
) -> None:
    client = _client(wired, made, tmp_path, drafted=False)
    directory = made.directory(FLOW, REVIEW)
    assert not directory.exists()

    body = client.get(_at(made)).json()

    assert body["draft"] == "001.draft.json"
    assert body["fields"]["hair_colour"]
    written = (directory / "001.draft.json").stat().st_mtime_ns
    client.get(_at(made))
    assert sorted(path.name for path in directory.iterdir()) == ["001.draft.json"]
    assert (directory / "001.draft.json").stat().st_mtime_ns == written


@pytest.mark.spec("ui:source:a-missing-caption-names-its-command")
def test_a_missing_caption_is_served_with_the_command_that_writes_it(
    wired: Wiring, made: Run, tmp_path: Path
) -> None:
    beside = _client(wired, made, tmp_path).get(_at(made)).json()
    assert beside["caption"] == "Dark brown hair, brown eyes."
    assert beside["caption_command"] is None

    for path in made.directory(PHOTO, CAPTIONS).iterdir():
        path.unlink()
    response = _client(wired, made, tmp_path).get(_at(made))

    assert response.status_code == 200
    body = response.json()
    assert body["caption"] is None
    command = body["caption_command"]
    # The fixture's runs root is not the default, so the command works when
    # pasted only if it names that root; the photograph's verb names no flow.
    parsed = build_parser().parse_args(shlex.split(command)[3:])
    assert (parsed.verb, parsed.flows, parsed.photos) == ("caption", None, [made.id])
    assert parsed.runs == made.path.parent


@pytest.mark.spec_exempt("structural: the join the page reads per input")
def test_an_input_carries_its_caption_its_fields_and_its_budget(
    client: TestClient, made: Run, schema: Schema
) -> None:
    body = client.get(_at(made)).json()

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
    body = client.get(_at(made)).json()

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
    # the 8,106-tag transfer this endpoint exists to avoid.
    assert body["matches"] == []
    assert body["total"] == 0


# --- the write surface, and what approval closes ------------------------------


@pytest.mark.spec_exempt("structural: the autosave path, end to end over HTTP")
def test_a_draft_update_lands_on_disk_and_returns_a_receipt(
    client: TestClient, made: Run
) -> None:
    fields = client.get(_at(made)).json()["fields"]
    fields["hair_colour"] = ["blonde"]

    body = client.put(_at(made, "/draft"), json={"fields": fields}).json()

    assert body["draft"] == "001.draft.json"
    assert body["saved"] is not None
    assert client.get(_at(made)).json()["fields"]["hair_colour"] == ["blonde"]


@pytest.mark.spec("ui:approval:approved-input-refuses-a-draft-update")
def test_a_draft_update_against_an_approved_input_is_refused_and_writes_nothing(
    client: TestClient, made: Run
) -> None:
    fields = client.get(_at(made)).json()["fields"]
    assert client.post(_at(made, "/approve")).status_code == 200
    before = snapshot(made.path)

    # A stale tab in a second window is exactly this request.
    response = client.put(_at(made, "/draft"), json={"fields": fields})

    assert response.status_code == 409
    assert "is approved" in response.json()["refusal"]
    assert snapshot(made.path) == before


_WRONG = (
    "assign-flow",
    "assign-sources",
    "commit",
    "quote-collections",
    "quote-without",
    "draft-flow",
    "draft-images",
    "renders-object",
    "renders-seeds",
)


def _wrong(
    made: Run, staged: str, fields: dict[str, Any]
) -> dict[str, tuple[str, str, dict[str, Any], str]]:
    """Return each body of the wrong shape as `(method, path, json, refusal text)`."""
    hub = f"/api/c/{COLLECTION}"
    return {
        "assign-flow": (
            "POST",
            f"{hub}/assign",
            {"flow": "nope", "sources": []},
            "not a flow this surface offers",
        ),
        "assign-sources": (
            "POST",
            f"{hub}/assign",
            {"flow": FLOW, "sources": "ada.jpg"},
            "`sources` is not a list of source names",
        ),
        "commit": (
            "POST",
            f"/api/staging/{staged}/commit",
            {"as_is": "x"},
            "`as_is` is not a list of file names",
        ),
        "quote-collections": (
            "POST",
            "/api/render/quote",
            {"collections": "b"},
            "the quote names no list of collections",
        ),
        "quote-without": (
            "POST",
            "/api/render/quote",
            {"collections": [COLLECTION], "without": "x"},
            "the quote names no list of photographs taken out",
        ),
        "draft-flow": (
            "POST",
            f"{hub}/draft",
            {"flow": "nope"},
            "not a flow this surface drafts",
        ),
        "draft-images": (
            "POST",
            f"{hub}/draft",
            {"flow": FLOW, "images": []},
            "the draft names no images",
        ),
        "renders-object": (
            "PUT",
            _at(made, "/draft"),
            {"fields": fields, "renders": "x"},
            "the update's `renders` is not a count and its seeds",
        ),
        "renders-seeds": (
            "PUT",
            _at(made, "/draft"),
            {"fields": fields, "renders": {"seeds": ["x"]}},
            "the update's renders seeds are not decimal numbers",
        ),
    }


@pytest.mark.spec("ui:damage:a-body-of-the-wrong-shape-is-refused-naming-what-it-lacks")
@pytest.mark.parametrize("row", _WRONG)
def test_a_body_of_the_wrong_shape_is_refused_naming_what_it_lacks(
    client: TestClient, made: Run, row: str
) -> None:
    staged = client.post("/api/staging").json()["id"]
    fields = client.get(_at(made)).json()["fields"]
    before = snapshot(made.path)
    method, path, body, text = _wrong(made, staged, fields)[row]

    answered = client.request(method, path, json=body)

    assert answered.status_code == 409
    assert text in answered.json()["refusal"]
    assert snapshot(made.path) == before


@pytest.mark.spec("import:refuse:a-file-over-the-limit-is-refused")
def test_an_upload_past_its_declared_length_is_refused_before_its_body_is_read(
    wired: Wiring, made: Run, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def handed(*_args: object, **_keywords: object) -> dict[str, Any]:
        raise AssertionError("the body was handed to the reader")

    monkeypatch.setattr(importing_module, "upload_limit", lambda *a, **k: 1024 * 1024)
    monkeypatch.setattr(importing_module.Reader, "put", handed)
    client = _client(wired, made, tmp_path)
    staged = client.post("/api/staging").json()["id"]

    answered = client.put(
        f"/api/staging/{staged}/files/big.jpg", content=b"x" * (1024 * 1024 + 1)
    )

    assert answered.status_code == 409
    assert "big.jpg" in answered.json()["refusal"]
    assert "past the 1 MB limit" in answered.json()["refusal"]


@pytest.mark.spec("ui:approval:a-re-opened-input-is-editable")
def test_an_input_re_opened_with_a_new_version_is_editable_again(
    client: TestClient, made: Run
) -> None:
    """The state `review --flow F --new-version` produces, and what it is for.

    Refusing every update to an approved input would make this state a dead end:
    the verb would write a draft the surface would not edit. The gate is
    *approved and no later draft*, so the page shows the draft, offers the form
    and accepts the write.
    """
    fields = client.get(_at(made)).json()["fields"]
    assert client.post(_at(made, "/approve")).status_code == 200
    # Approved and read-only, until the operator asks for a new version.
    assert client.get(_at(made)).json()["readonly"] is True

    review(made, FLOW, new_version=True)

    body = client.get(_at(made)).json()
    assert body["readonly"] is False
    # The draft's sheet, not the approved artifact's -- and the approved
    # artifact is still named, because it has not gone anywhere.
    assert body["draft"] == "002.draft.json"
    assert body["approved"] == "001.approved.json"
    assert body["fields"] == fields

    response = client.put(_at(made, "/draft"), json={"fields": fields})

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

    Derived from the status string, the approved count would agree with the
    directory only while every input holding an approved artifact also
    *reports* approved -- which stops being true the moment a status exists
    meaning *has one, and is open again*. So the count reads the directory.
    """
    _source(made)

    def status() -> str:
        (one,) = client.get(f"/api/c/{COLLECTION}/hub").json()["sources"]
        return str(one["cells"][FLOW]["status"])

    assert status() == "draft"
    assert client.post(_at(made, "/approve")).status_code == 200
    assert status() == "approved"

    review(made, FLOW, new_version=True)

    assert status() == "re-opened"
    (row,) = client.get("/api/library").json()["rows"]
    (counted,) = [one for one in row["flows"] if one["flow"] == FLOW]
    # The scenario's second `THEN`, against the directory rather than against
    # another of the server's own numbers.
    assert counted["approved"] == len(
        list(made.directory(FLOW, REVIEW).glob("*.approved.json"))
    )
    assert counted["approved"] == 1


@pytest.mark.spec("ui:draft-update:a-stale-precondition-is-refused")
def test_an_update_written_against_a_stale_draft_is_refused(
    client: TestClient, made: Run
) -> None:
    """Two pages open on one draft can each have a `PUT` in flight at once.

    Unordered, they would commit in whatever order the server finished them, so
    last write would win where *last* is not the operator's last keystroke.
    `st_mtime` is the precondition because nothing else exists on disk -- the
    draft carries no timestamp, no revision counter and no digest.
    """
    body = client.get(_at(made)).json()
    fields, saved = body["fields"], body["saved"]

    # The first of the two in-flight saves lands and moves the draft's mtime.
    first = client.put(_at(made, "/draft"), json={"fields": fields, "saved": saved})
    assert first.status_code == 200
    assert first.json()["saved"] != saved

    # The second was written against what the page read before the first, which
    # is the state a second page open on the draft produces.
    second = client.put(_at(made, "/draft"), json={"fields": fields, "saved": saved})

    assert second.status_code == 409
    assert "changed since this page last read it" in second.json()["refusal"]
    # And the receipt the first save returned is the one that lets the page
    # carry on: echoing it back is accepted.
    third = client.put(
        _at(made, "/draft"),
        json={"fields": fields, "saved": first.json()["saved"]},
    )
    assert third.status_code == 200


@pytest.mark.spec("ui:draft-update:a-stale-approval-is-refused")
def test_an_approval_written_against_a_stale_draft_is_refused(
    client: TestClient, made: Run
) -> None:
    # An approval states the draft update's precondition, so a page that never
    # displayed the draft on disk cannot approve it.
    body = client.get(_at(made)).json()
    fields, saved = body["fields"], body["saved"]
    moved = client.put(_at(made, "/draft"), json={"fields": fields, "saved": saved})
    assert moved.json()["saved"] != saved

    stale = client.post(_at(made, "/approve"), json={"saved": saved})

    assert stale.status_code == 409
    assert "changed since this page last read it" in stale.json()["refusal"]
    assert not list(made.directory(FLOW, REVIEW).glob("*.approved.json"))


@pytest.mark.spec("ui:draft-update:a-stale-discard-is-refused")
def test_a_discard_written_against_a_stale_draft_is_refused(
    client: TestClient, made: Run
) -> None:
    # Another tab moved the draft after this page read it, so this page's
    # discard would delete edits it never showed.
    body = client.get(_at(made)).json()
    fields, saved = body["fields"], body["saved"]
    moved = client.put(_at(made, "/draft"), json={"fields": fields, "saved": saved})
    assert moved.json()["saved"] != saved

    stale = client.post(_at(made, "/discard"), json={"saved": saved})

    assert stale.status_code == 409
    assert "changed since this page last read it" in stale.json()["refusal"]
    assert stale.json()["refusal"].endswith("then discard again")
    assert (made.directory(FLOW, REVIEW) / "001.draft.json").is_file()


@pytest.mark.spec("ui:revise:an-untracked-flow-refuses-its-image")
def test_a_revision_of_an_untracked_flow_is_refused_and_nothing_is_written(
    client: TestClient, made: Run
) -> None:
    _approved(client, made)
    group = made.directory(FLOW, "outputs", "001")
    group.mkdir(parents=True)
    (group / "7.render.json").write_text("{}\n")
    image = {"digest": made.digest, "version": 1, "seed": "7"}
    before = snapshot(made.path)

    answered = client.post(
        DRAFT_ROUTE,
        json={
            "flow": FLOW,
            "images": [{**image, "flow": FLOW}, {**image, "flow": "nope"}],
        },
    )

    assert answered.status_code == 409
    tracked, untracked = answered.json()["images"]
    assert tracked["refusal"] is None
    assert untracked["refusal"].startswith("nope: not a flow this build tracks")
    assert snapshot(made.path) == before


@pytest.mark.spec("ui:revise:an-image-no-run-can-hold-is-refused")
@pytest.mark.parametrize(
    ("version", "seed"), [(10**300, "7"), (1, "9" * 300)], ids=["version", "seed"]
)
def test_a_revision_of_a_version_or_seed_no_run_can_hold_is_refused(
    client: TestClient, made: Run, version: int, seed: str
) -> None:
    # Spelled as a file name, either number is longer than the system allows.
    _approved(client, made)
    before = snapshot(made.path)

    answered = client.post(
        DRAFT_ROUTE,
        json={
            "flow": FLOW,
            "images": [
                {"digest": made.digest, "flow": FLOW, "version": version, "seed": seed}
            ],
        },
    )

    assert answered.status_code == 409
    assert "is not one; send each image's digest" in answered.json()["refusal"]
    assert snapshot(made.path) == before


@pytest.mark.spec("ui:revise:a-discard-deletes-the-draft-the-page-read")
def test_a_discard_stating_the_draft_on_disk_deletes_it_and_no_approval(
    client: TestClient, made: Run
) -> None:
    approved = _approved(client, made)
    frozen = approved.read_bytes()
    review(made, FLOW, new_version=True)
    saved = client.get(_at(made)).json()["saved"]

    answered = client.post(_at(made, "/discard"), json={"saved": saved})

    assert answered.json() == {"discarded": "002.draft.json"}
    assert versions(made.directory(FLOW, REVIEW)) == [1]
    assert approved.read_bytes() == frozen


def _revised(client: TestClient, made: Run) -> Path:
    """Approve `made`, render seed 7 under it, and revise that image; return v1."""
    first = _approved(client, made)
    image = image_of(made, load_flow(FLOW), 1, 7)
    image.parent.mkdir(parents=True)
    image.write_bytes(png_bytes(8, 8))
    (image.parent / "7.render.json").write_text("{}\n")
    answered = client.post(
        DRAFT_ROUTE,
        json={
            "flow": FLOW,
            "images": [
                {"digest": made.digest, "flow": FLOW, "version": 1, "seed": "7"}
            ],
        },
    )
    assert answered.status_code == 200
    return first


@pytest.mark.spec("ui:revise:an-approved-revision-keeps-its-image")
def test_an_approved_revision_names_the_approval_its_image_and_its_fields(
    client: TestClient, made: Run
) -> None:
    first = _revised(client, made)
    body = client.get(_at(made)).json()
    # A second image is a change, so the copy approves.
    renders = {"count": 2, "seeds": ["7"]}
    saved = client.put(
        _at(made, "/draft"),
        json={"fields": body["fields"], "renders": renders, "saved": body["saved"]},
    ).json()["saved"]
    assert client.post(_at(made, "/approve"), json={"saved": saved}).status_code == 200

    approved = client.get(_at(made)).json()

    assert approved["readonly"] is True
    assert approved["approved"] == "002.approved.json"
    assert approved["revision"] == {
        "version": 1,
        "seed": "7",
        "fields": read(first, APPROVED_FILE)["fields"],
    }


@pytest.mark.spec("ui:revise:a-revision-keeps-its-image-after-its-seed-changes")
def test_a_revision_whose_seed_changed_names_the_image_it_was_written_from(
    client: TestClient, made: Run
) -> None:
    _revised(client, made)
    body = client.get(_at(made)).json()
    renders = {"count": 1, "seeds": ["9"]}
    saved = client.put(
        _at(made, "/draft"),
        json={"fields": body["fields"], "renders": renders, "saved": body["saved"]},
    ).json()["saved"]

    assert client.get(_at(made)).json()["revision"]["seed"] == "7"
    assert client.post(_at(made, "/approve"), json={"saved": saved}).status_code == 200
    assert client.get(_at(made)).json()["revision"]["seed"] == "7"


@pytest.mark.spec("ui:revise:a-waiting-draft-is-opened")
def test_revising_an_image_whose_flow_holds_a_waiting_draft_answers_that_draft(
    client: TestClient, made: Run
) -> None:
    _revised(client, made)
    image = {"digest": made.digest, "flow": FLOW, "version": 1, "seed": "7"}
    before = snapshot(made.path)

    answered = client.post(DRAFT_ROUTE, json={"flow": FLOW, "images": [image]})

    assert answered.status_code == 200
    assert answered.json() == {
        "drafts": [{**image, "draft": None, "waiting": "002.draft.json"}]
    }
    assert snapshot(made.path) == before


@pytest.mark.spec("ui:draft-update:no-precondition-is-accepted")
def test_an_update_stating_no_precondition_is_still_accepted(
    client: TestClient, made: Run
) -> None:
    # A payload carrying no `saved` states no precondition, and is written
    # without the check -- the mtime is already on the wire as the field every
    # response returns, so a client that echoes it gets the check.
    fields = client.get(_at(made)).json()["fields"]

    assert client.put(_at(made, "/draft"), json={"fields": fields}).status_code == 200


@pytest.mark.spec("ui:approval:a-stale-lower-draft-does-not-reopen")
def test_a_stale_lower_draft_does_not_reopen_an_approved_input(
    client: TestClient, made: Run
) -> None:
    directory = made.directory(FLOW, REVIEW)
    stale = (directory / "001.draft.json").read_bytes()
    assert client.post(_at(made, "/approve")).status_code == 200
    review(made, FLOW, new_version=True)
    assert client.post(_at(made, "/approve")).status_code == 200
    # Below the approval: left by a crash, or restored by hand.
    (directory / "001.draft.json").write_bytes(stale)
    expected = read(directory / "002.approved.json", APPROVED_FILE)["fields"]

    body = client.get(_at(made)).json()

    assert body["readonly"] is True
    assert body["draft"] is None
    assert body["approved"] == "002.approved.json"
    assert body["fields"] == expected


def _overlap(
    client: TestClient,
    made: Run,
    monkeypatch: pytest.MonkeyPatch,
    *,
    unlocked: bool = False,
) -> dict[str, tuple[int, dict[str, Any]]]:
    """Send two updates stating one precondition, the second inside the first.

    The second starts while the first is between its check and its write. The
    first writes once the second waits at the lock, or, `unlocked`, once the
    second has passed its check.
    """
    body = client.get(_at(made)).json()
    saved = body["saved"]
    reached = threading.Event()
    answers: dict[str, tuple[int, dict[str, Any]]] = {}
    threads: list[threading.Thread] = []
    precondition, save = app_module._precondition, app_module.save_draft
    lock = app_module._DRAFT_UPDATE

    class Waited:
        """The draft lock, saying when an update finds it held."""

        def __enter__(self) -> None:
            if not lock.acquire(blocking=False):
                reached.set()
                lock.acquire()

        def __exit__(self, *exc: object) -> None:
            lock.release()

    def check(one: Held, payload: Mapping[str, Any]) -> None:
        precondition(one, payload)
        # By its payload: the endpoint runs on a worker thread, not on `second`.
        if payload["fields"]["hair_colour"] == ["black hair"]:
            reached.set()

    def put(name: str, hair: str) -> None:
        fields = {**body["fields"], "hair_colour": [hair]}
        reply = client.put(_at(made, "/draft"), json={"fields": fields, "saved": saved})
        answers[name] = (reply.status_code, reply.json())

    def write(
        run: Run,
        flow: str,
        fields: Mapping[str, Sequence[str]],
        renders: Renders | None = None,
    ) -> Path:
        if not threads:
            second = threading.Thread(
                target=put, args=("second", "black hair"), name="second"
            )
            threads.append(second)
            second.start()
            assert reached.wait(WAIT), (
                "the second update reached neither lock nor check"
            )
        return save(run, flow, fields, renders)

    monkeypatch.setattr(app_module, "_precondition", check)
    monkeypatch.setattr(app_module, "save_draft", write)
    if not unlocked:
        monkeypatch.setattr(app_module, "_DRAFT_UPDATE", Waited())
    put("first", "blonde")
    for thread in threads:
        thread.join()
    return answers


@pytest.mark.spec("ui:draft-update:overlapping-updates-cannot-both-commit")
def test_overlapping_draft_updates_cannot_both_commit(
    client: TestClient, made: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    answers = _overlap(client, made, monkeypatch)

    assert (answers["first"][0], answers["second"][0]) == (200, 409)
    assert "changed since this page last read it" in answers["second"][1]["refusal"]
    on_disk = json.loads((made.directory(FLOW, REVIEW) / "001.draft.json").read_text())
    assert on_disk["fields"]["hair_colour"] == ["blonde"]


@pytest.mark.spec_exempt(
    "structural: twin of test_overlapping_draft_updates_cannot_both_commit"
)
def test_without_the_lock_overlapping_updates_both_commit(
    client: TestClient, made: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(app_module, "_DRAFT_UPDATE", contextlib.nullcontext())

    answers = _overlap(client, made, monkeypatch, unlocked=True)

    assert (answers["first"][0], answers["second"][0]) == (200, 200)


def _update_during_approval(
    client: TestClient,
    made: Run,
    monkeypatch: pytest.MonkeyPatch,
    *,
    unlocked: bool = False,
) -> int:
    """Approve while an update is in flight, and return the update's status.

    The update starts inside the approval, and the approval goes on once the
    update waits at the lock, or, `unlocked`, once it has passed its check; it
    asserts which one stopped it. An update past its check writes only after the
    approval has written. Both waits are bounded, so a regression fails rather
    than hangs.
    """
    body = client.get(_at(made)).json()
    reached, approved = threading.Event(), threading.Event()
    # Where the update was stopped: at the lock, or past its check.
    stopped: list[str] = []
    answers: list[int] = []
    precondition, approving = app_module._precondition, app_module.approve
    write = review_module.write
    lock = app_module._DRAFT_UPDATE

    class Waited:
        """The draft lock, saying when an update finds it held."""

        def __enter__(self) -> None:
            if not lock.acquire(blocking=False):
                stopped.append("lock")
                reached.set()
                lock.acquire()

        def __exit__(self, *exc: object) -> None:
            lock.release()

    def check(one: Held, payload: Mapping[str, Any]) -> None:
        # The approval states a precondition too; only the update's is the signal.
        if "fields" in payload:
            stopped.append("check")
            reached.set()
        precondition(one, payload)

    def put() -> None:
        fields = {**body["fields"], "hair_colour": ["blonde"]}
        answers.append(
            client.put(
                _at(made, "/draft"),
                json={"fields": fields, "saved": body["saved"]},
            ).status_code
        )

    def late[T: Mapping[str, object]](
        path: Path, kind: Artifact[T], artifact: T
    ) -> None:
        # By name: the endpoint runs on a worker thread, not on `update`.
        if path.name.endswith(".draft.json"):
            assert approved.wait(WAIT), "the approval never finished"
        write(path, kind, artifact)

    def approve_(
        run: Run,
        flow: str,
        schema: Schema,
        vocabulary: Vocabulary,
        *,
        excluded: frozenset[str] = frozenset(),
        definition: Flow | None = None,
    ) -> tuple[Path | None, list[str]]:
        update.start()
        assert reached.wait(WAIT), "the update reached neither lock nor check"
        assert stopped == (["check"] if unlocked else ["lock"]), (
            "the update's check ran inside the approval"
            if not unlocked
            else "the update found a lock the approval should not hold"
        )
        try:
            return approving(
                run,
                flow,
                schema,
                vocabulary,
                excluded=excluded,
                definition=definition,
            )
        finally:
            approved.set()

    update = threading.Thread(target=put)
    monkeypatch.setattr(app_module, "_precondition", check)
    monkeypatch.setattr(app_module, "approve", approve_)
    monkeypatch.setattr(review_module, "write", late)
    if not unlocked:
        monkeypatch.setattr(app_module, "_DRAFT_UPDATE", Waited())
    assert client.post(_at(made, "/approve")).status_code == 200
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


@pytest.mark.spec_exempt(
    "structural: twin of test_an_update_overlapping_an_approval_is_refused"
)
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

    reopened = _client(wired, made, tmp_path)

    body = reopened.get(_at(made)).json()

    # Approval deletes the draft and reopening writes no replacement, so there is
    # nothing on disk for an edit to be written into.
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


@pytest.mark.spec("ui:review:the-sheet-says-why-it-cannot-be-cancelled")
def test_an_approved_sheet_carries_why_it_cannot_be_cancelled(
    client: TestClient,
    made: Run,
    schema: Schema,
    vocabulary: Vocabulary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _approved(client, made)
    assert client.get(_at(made)).json()["cancel"] is None

    # A render running for the collection holds the cancel, whatever the review
    # stage says.
    with monkeypatch.context() as held:
        held.setattr(
            Jobs, "slot", lambda self, kind: _rendering_slot("20261024T091200Z")
        )
        assert client.get(_at(made)).json()["cancel"] == "A render session is running."
        refused = client.post(_at(made, "/cancel"))
        assert refused.status_code == 409
        assert "A render session is running." in refused.json()["refusal"]
    assert (made.directory(FLOW, REVIEW) / "001.approved.json").exists()

    cancelled = client.post(_at(made, "/cancel"))

    assert cancelled.json() == {"back": "001.draft.json", "cancelled": True}
    assert client.get(_at(made)).json()["readonly"] is False
    # At its draft, a flow has nothing to cancel, and the answer says so.
    again = client.post(_at(made, "/cancel"))
    assert again.json() == {"back": "001.draft.json", "cancelled": False}

    # Approved again, and its prompt assembled: the payload says why not.
    _approved(client, made)
    prompt_artifact(made, load_flow(FLOW), schema)
    reason = cancellable(made, FLOW)
    assert reason is not None and f"{FLOW}/prompts/001.json came from it" in reason

    assert client.get(_at(made)).json()["cancel"] == reason
    refused = client.post(_at(made, "/cancel"))
    assert refused.status_code == 409
    assert (made.directory(FLOW, REVIEW) / "001.approved.json").exists()

    # A copy has no draft to go back to: its cancel deletes it.
    control = "control-anime-wai"
    sheet(made, schema, vocabulary, flow=control)
    copy, _ = approve(made, control, schema, vocabulary, source=FLOW)
    assert copy is not None
    at_control = f"/api/c/{COLLECTION}/review/{made.digest}/{control}/cancel"
    assert client.post(at_control).json() == {"back": None, "cancelled": True}
    assert not copy.exists()


# --- the two tag lists the source pane shows ----------------------------------


@pytest.mark.spec("ui:source:both-tag-lists-are-shown-raw-and-read-only")
def test_the_local_list_is_whole_and_the_hosted_list_is_filtered(
    wired: Wiring, made: Run, tmp_path: Path
) -> None:
    # The sheet the `made` fixture filled needed a tag list, so one is already on
    # disk; this test is about what the *real* local tagger writes, so it replaces
    # it rather than writing a second version beside it.
    _clear_wd14(made)
    tag_wd14(made, fake_tagger)
    tag_hosted(
        made,
        FakeTagger(tags=("brown hair", "fashion photography", "blue eyes")),
    )

    body = _client(wired, made, tmp_path).get(_at(made)).json()

    # Whole: every tag the local tagger scored, because it is scored against the
    # vocabulary it emits and so every one of them is committable.
    assert body["wd14"] == [{"tag": "1girl", "confidence": 0.9}]
    # Filtered: `fashion photography` is in no field's reach, and on the
    # acceptance collection nine in ten of this model's tags were like it.
    assert [one["tag"] for one in body["tags"]] == ["brown hair", "blue eyes"]


@pytest.mark.spec("ui:source:each-hosted-tag-is-offered-once")
def test_the_hosted_panel_shows_each_tag_once_and_the_local_one_shows_every_row(
    wired: Wiring, made: Run, tmp_path: Path
) -> None:
    """Deduplicated on the hosted side only, and the asymmetry is the point.

    `OfferedTag` is `{tag, posts}` where `posts` is a pure function of `tag`, so
    a repeat is a byte-identical object carrying no information -- and it would
    be a duplicate Vue key. `ScoredTag` is `{tag, confidence}`, where two rows
    can legitimately differ, so `_wd14` is left whole: deduping it would falsify
    `ui:source:both-tag-lists-are-shown-raw-and-read-only`'s first `THEN`.
    """
    _clear_wd14(made)
    tag_wd14(made, fake_tagger)
    tag_hosted(
        made,
        FakeTagger(tags=("brown hair", "blue eyes", "brown hair")),
    )

    # The two tag artifacts, and only those: opening the sheet takes a draft,
    # which is stage ③ starting normally rather than the panel writing anything.
    before = {stage: snapshot(made.directory(PHOTO, stage)) for stage in (WD14, TAGS)}

    body = _client(wired, made, tmp_path).get(_at(made)).json()

    assert [one["tag"] for one in body["tags"]] == ["brown hair", "blue eyes"]
    # Unchanged, and asserted here rather than left to the test above: the two
    # lists are narrowed by different rules and this is the one that says so.
    assert [one["tag"] for one in body["wd14"]] == ["1girl"]
    # The scenario's last `THEN`: narrowing the panel is not narrowing the
    # artifact. A sibling test proves the hosted list keeps what the page drops;
    # this one is bound to the key that says *both* artifacts are untouched, so
    # it asserts that clause rather than borrowing it.
    assert {
        stage: snapshot(made.directory(PHOTO, stage)) for stage in (WD14, TAGS)
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
        FakeTagger(tags=("brown hair", "fashion photography", "blue eyes")),
    )

    body = _client(wired, made, tmp_path).get(_at(made)).json()

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
        FakeTagger(tags=("brown hair", "fashion photography", "blue eyes")),
    )

    body = _client(wired, made, tmp_path).get(_at(made)).json()
    marked = {one["tag"]: one for one in body["tags"]}

    assert marked["brown hair"]["posts"] == vocabulary.count("brown hair")
    assert marked["blue eyes"]["posts"] == vocabulary.count("blue eyes")
    # Every tag that reaches the page carries a number, because every tag that
    # reaches the page is in the vocabulary. There is no membership flag to
    # send: it would be `true` on all of them.
    assert all(one["posts"] > 0 for one in body["tags"])
    assert all(set(one) == {"tag", "posts"} for one in body["tags"])


@pytest.mark.spec("ui:source:an-absent-tag-artifact-is-silent")
def test_an_input_with_neither_artifact_carries_null_and_still_serves(
    client: TestClient, made: Run
) -> None:
    # A run whose sheet was filled before the tagging stages existed and whose
    # tag lists were never written. It cannot be produced by filling a sheet --
    # the stage refuses without a tag list -- so it is produced by removing the
    # one the fixture wrote, which is the state on disk either way. Both are
    # null, the surface answers 200, and nothing anywhere is a refusal: the tag
    # lists are an aid, and a missing aid never blocks review.
    _clear_wd14(made)

    response = client.get(_at(made))

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
    # blocked review.
    tag_wd14(made, fake_tagger)

    body = _client(wired, made, tmp_path).get(_at(made)).json()

    assert body["wd14"] is not None
    assert body["tags"] is None


@pytest.mark.spec("ui:source:the-caption-is-shown-one-sentence-to-a-block")
def test_the_caption_reaches_the_page_whole_and_the_browser_splits_it(
    client: TestClient, made: Run
) -> None:
    # The split is `ui/src/caption.ts`'s and the server does not do it: sending
    # prose to be split and back would be a round trip for a regex. What the
    # server owes is the prose, unmodified.
    body = client.get(_at(made)).json()

    assert body["caption"] == "Dark brown hair, brown eyes."


# --- the cheatsheet, which is the table read the other way ---------------------


@pytest.mark.spec("ui:cheatsheet:every-declared-criterion-is-answered")
def test_every_criterion_the_flow_declares_is_answered_and_no_other(
    client: TestClient, schema: Schema
) -> None:
    body = client.get("/api/fields", params={"flow": FLOW}).json()

    assert tuple(body["fields"]) == schema.names
    # `summon-anime-wai` declares sixteen of the twenty-one the table carries; the
    # five only `conjure-anime-wai` declares are absent rather than empty.
    assert "bangs" in FIELD_MAP.fields
    assert "bangs" not in body["fields"]


@pytest.mark.spec("ui:cheatsheet:an-empty-group-is-present")
def test_a_criterion_the_table_holds_nothing_for_is_present_and_empty(
    client: TestClient,
) -> None:
    body = client.get("/api/fields", params={"flow": FLOW}).json()

    assert FIELD_MAP.group("age_band") == ()
    assert body["fields"]["age_band"] == []
    assert "age_band" in body["fields"]


@pytest.mark.spec("ui:cheatsheet:candidates-are-ordered-by-post-count")
def test_candidates_are_ordered_by_descending_post_count(
    client: TestClient, vocabulary: Vocabulary
) -> None:
    body = client.get("/api/fields", params={"flow": FLOW}).json()

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
    # The fixture table's excluded list is empty, so the assertion is driven
    # from a table that has one -- otherwise it would pass vacuously.
    withheld = replace(FIELD_MAP, excluded=frozenset({"glasses"}))
    fields = dict(FIELD_MAP.fields)
    fields["accessories"] = Group(primary=(), also=())
    wired.field_map = lambda _: replace(withheld, fields=fields)

    client = _client(wired, made, tmp_path)
    body = client.get("/api/fields", params={"flow": FLOW}).json()

    assert set(body) == {"fields"}
    assert "glasses" not in json.dumps(body)


@pytest.mark.spec("field-map:excluded:the-tag-search-skips-an-excluded-tag")
def test_the_tag_search_offers_no_excluded_tag(
    wired: Wiring, made: Run, tmp_path: Path, vocabulary: Vocabulary
) -> None:
    withheld = replace(FIELD_MAP, excluded=frozenset({"glasses"}))
    fields = dict(FIELD_MAP.fields)
    fields["accessories"] = Group(primary=(), also=())
    wired.field_map = lambda _: replace(withheld, fields=fields)

    client = _client(wired, made, tmp_path)
    body = client.get("/api/tags", params={"q": "s", "limit": 100}).json()

    offered = [t for t in vocabulary.search("s") if t != "glasses"]
    assert [match["tag"] for match in body["matches"]] == offered
    assert body["total"] == len(offered)


@pytest.mark.spec("field-map:excluded:approval-refuses-an-excluded-tag")
def test_approve_refuses_an_excluded_tag_the_draft_saved(
    wired: Wiring, made: Run, tmp_path: Path
) -> None:
    wired.field_map = lambda _: replace(FIELD_MAP, excluded=frozenset({"glasses"}))
    client = _client(wired, made, tmp_path)
    fields = {**client.get(_at(made)).json()["fields"], "accessories": ["glasses"]}

    saved = client.put(_at(made, "/draft"), json={"fields": fields})
    approved = client.post(_at(made, "/approve"))

    assert saved.status_code == 200
    assert approved.status_code == 409
    assert "glasses" in approved.json()["refusal"]


@pytest.mark.spec("review:budget:a-sheet-past-the-window-only-assembled-warns")
def test_approve_answers_the_assembled_warning(
    client: TestClient, made: Run, vocabulary: Vocabulary
) -> None:
    every = list(vocabulary.counts)
    fields = {
        **client.get(_at(made)).json()["fields"],
        "clothes": every,
        "accessories": every[:3],
    }

    saved = client.put(_at(made, "/draft"), json={"fields": fields})
    approved = client.post(_at(made, "/approve"))

    assert saved.json()["budget"]["total"] > ENCODER_WINDOW
    assert approved.status_code == 200
    assert len(approved.json()["warnings"]) == 1
    assert "the assembled prompt is about" in approved.json()["warnings"][0]


# --- damage is refused by name ------------------------------------------------


def _latest(stage: str, label: str | None = None) -> Callable[[TestClient, Run], Path]:
    """Return a finder for the highest `label` artifact in `stage`.

    The description's stages are the photograph's, under `photo/`; every other is
    the flow's.
    """
    owner = PHOTO if stage in DESCRIPTION else FLOW

    def find(_client: TestClient, run: Run) -> Path:
        path = latest_artifact(run.directory(owner, stage), label)
        assert path is not None
        return path

    return find


def _damage(path: Path, change: Callable[[dict[str, Any]], None]) -> None:
    """Rewrite the JSON file at `path` with `change` applied."""
    body = json.loads(path.read_text())
    change(body)
    path.write_text(json.dumps(body))


def _approved(client: TestClient, run: Run) -> Path:
    assert client.post(_at(run, "/approve")).status_code == 200
    return _latest(REVIEW, APPROVED)(client, run)


def _hosted(client: TestClient, run: Run) -> Path:
    tag_hosted(run, FakeTagger(tags=("brown hair",)))
    return _latest(TAGS)(client, run)


def _set(key: str, value: object) -> Callable[[dict[str, Any]], None]:
    return lambda body: body.__setitem__(key, value)


def _drop(key: str) -> Callable[[dict[str, Any]], None]:
    return lambda body: body.pop(key)


@pytest.mark.spec("ui:damage:a-damaged-file-is-refused-by-name")
@pytest.mark.parametrize(
    ("find", "change", "named", "verb"),
    [
        (_latest(REVIEW, DRAFT), _drop("fields"), "`fields`", "review"),
        (
            _latest(REVIEW, DRAFT),
            lambda body: body["fields"].__setitem__("hair_colour", "brown hair"),
            "`hair_colour`",
            "review",
        ),
        # No command rewrites an approved sheet -- `review` copies it and
        # refuses the same damage -- so the fix is the file to restore.
        (_approved, _set("fields", ["brown hair"]), "`fields`", None),
        (
            _approved,
            _set("schema", {"name": "sheet", "version": 1}),
            "declares kind 'sheet'",
            None,
        ),
        (_latest(CAPTIONS), _drop("prose"), "`prose`", "caption"),
        (
            _latest(WD14),
            _set("tags", [{"tag": "1girl"}]),
            "tag entry 0",
            "tag",
        ),
        (_hosted, _set("tags", "brown hair"), "`tags`", "tag"),
        (_hosted, _set("tags", ["brown hair", 3]), "`tags`", "tag"),
    ],
    ids=[
        "draft",
        "draft-field",
        "approved",
        "approved-kind",
        "caption",
        "wd14",
        "hosted-string",
        "hosted-entry",
    ],
)
def test_a_damaged_file_is_refused_by_name(
    client: TestClient,
    made: Run,
    find: Callable[[TestClient, Run], Path],
    change: Callable[[dict[str, Any]], None],
    named: str,
    verb: str | None,
) -> None:
    damaged = find(client, made)
    _damage(damaged, change)

    response = client.get(_at(made))

    assert response.status_code == 409
    refusal = response.json()["refusal"]
    assert damaged.name in refusal and named in refusal
    if verb is None:
        assert f"restore it in {damaged}" in refusal
        assert "python -m isekai" not in refusal
    else:
        # Parsed, not matched: the fixture's runs root is not the default, so
        # the command works when pasted only if it names that root. The
        # photograph's verbs name no flow.
        command = refusal.split("`python -m isekai ")[1].split("`")[0]
        parsed = build_parser().parse_args(shlex.split(command))
        assert (parsed.verb, parsed.flows, parsed.new_version, parsed.photos) == (
            verb,
            None if verb in ("caption", "tag") else [FLOW],
            True,
            [made.id],
        )
        assert parsed.runs == made.path.parent
    assert client.get(f"/api/c/{COLLECTION}/hub").status_code == 200


@pytest.mark.spec("ui:damage:a-damaged-file-is-refused-by-name")
def test_a_damage_remedy_under_the_default_root_names_no_runs_flag(
    client: TestClient, made: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(run_module, "RUNS_ROOT", made.path.parent)
    _damage(_latest(CAPTIONS)(client, made), _drop("prose"))

    refusal = client.get(_at(made)).json()["refusal"]

    assert f"`python -m isekai caption --new-version {made.id}`" in refusal


@pytest.mark.spec("ui:damage:a-damaged-file-is-refused-by-name")
def test_a_damage_remedy_under_a_root_holding_a_space_pastes_as_one_argument(
    wired: Wiring, made: Run, tmp_path: Path
) -> None:
    root = tmp_path / "my lib" / COLLECTION / "runs"
    (root.parent / "sources").mkdir(parents=True)
    root.mkdir()
    shutil.move(made.path, root / made.id)
    moved = Run(made.id, root / made.id)
    client = _client(replace(wired, runs_root=root), moved, tmp_path)
    _damage(_latest(CAPTIONS)(client, moved), _drop("prose"))

    refusal = client.get(_at(moved)).json()["refusal"]

    # Split as the shell splits it: an unquoted root would come apart at the space.
    command = refusal.split("`python -m isekai ")[1].split("`")[0]
    parsed = build_parser().parse_args(shlex.split(command))
    assert (parsed.verb, parsed.runs, parsed.photos) == ("caption", root, [moved.id])


@pytest.mark.spec("ui:damage:a-malformed-update-is-refused-naming-the-field")
@pytest.mark.parametrize(
    ("fields", "named"),
    [
        ({"hair_colour": "brown hair"}, "hair_colour"),
        ({"hair_colour": ["brown hair", 3]}, "hair_colour"),
        ({"hair_colour": None}, "hair_colour"),
        ("brown hair", "`fields`"),
    ],
    ids=["a-string", "a-number-inside", "null", "not-an-object"],
)
def test_a_malformed_update_is_refused_naming_the_field(
    client: TestClient, made: Run, fields: object, named: str
) -> None:
    before = snapshot(made.path)

    response = client.put(_at(made, "/draft"), json={"fields": fields})

    assert response.status_code == 409
    assert named in response.json()["refusal"]
    assert snapshot(made.path) == before


# --- The large view -----------------------------------------------------------


def _rendered_twice(
    made: Run, schema: Schema, vocabulary: Vocabulary
) -> tuple[list[int], list[int]]:
    """Approve `made` twice, rendering under each, and return each version's seeds.

    Each image is a real one, so a thumbnail can be made of it.
    """
    flow = load_flow(FLOW)
    client = FakeComfyClient(view_bytes=photo_jpeg((90, 60, 30), (640, 800)))
    review(made, FLOW)
    approve(made, FLOW, schema, vocabulary)
    prepare(made, {FLOW: flow})
    first = [one.seed for one in render(made, flow, client, seeds=[11], poll=0)]
    review(made, FLOW, new_version=True)
    approve(made, FLOW, schema, vocabulary)
    prepare(made, {FLOW: flow})
    second = [one.seed for one in render(made, flow, client, seeds=[22], poll=0)]
    return first, second


@pytest.mark.spec("ui:renders:a-thumbnail-is-made-once")
def test_a_thumbnail_asked_for_twice_is_read_from_the_cache_the_second_time(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _source(made)
    _rendered_twice(made, schema, vocabulary)
    client = _client(wired, made, tmp_path, drafted=False)
    shrinks: list[Path] = []
    shrink = library._shrunk

    def counted(image: Path) -> bytes:
        shrinks.append(image)
        return shrink(image)

    monkeypatch.setattr(library, "_shrunk", counted)
    thumb = f"/api/c/{COLLECTION}/renders/{made.digest}/{FLOW}/v1/11/thumb"

    first = client.get(thumb)
    second = client.get(thumb)

    assert first.status_code == second.status_code == 200
    assert first.headers["content-type"] == "image/jpeg"
    assert second.content == first.content
    assert len(shrinks) == 1
    cached = tmp_path / "lib" / ".cache" / made.digest / FLOW / "outputs" / "001"
    (thumb_file,) = cached.glob("11.*.jpg")
    assert thumb_file.read_bytes() == first.content


@pytest.mark.spec("ui:delete-render:the-route-deletes-the-render-and-its-thumbnail")
def test_deleting_a_render_deletes_its_files_and_thumbnail(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    _source(made)
    _rendered_twice(made, schema, vocabulary)
    client = _client(wired, made, tmp_path, drafted=False)
    at = f"/api/c/{COLLECTION}/renders/{made.digest}/{FLOW}"
    for place in ("v1/11", "v2/22"):
        assert client.get(f"{at}/{place}/thumb").status_code == 200
    cache = tmp_path / "lib" / ".cache" / made.digest / FLOW / "outputs"
    outputs = made.directory(FLOW, "outputs")
    shutil.copytree(made.path.parents[1], tmp_path / "twin")
    twin_run = tmp_path / "twin" / "runs" / made.path.name
    twin = bare_wiring(runs_root=tmp_path)
    twinned = dispatch(
        build_parser().parse_args(
            ["discard", str(twin_run / FLOW / "outputs" / "001" / "11.png")]
        ),
        twin,
    )

    deleted = client.delete(f"{at}/v1/11")

    assert twinned == 0
    assert deleted.status_code == 200
    assert deleted.json() == {"deleted": True}
    assert set(tree(made.path)) == set(tree(twin_run))
    assert tree(made.path) == tree(twin_run)
    assert not (outputs / "001" / "11.png").exists()
    assert not (outputs / "001" / "11.render.json").exists()
    assert list(cache.glob("001/11.*.jpg")) == []
    assert (outputs / "002" / "22.png").is_file()
    assert len(list(cache.glob("002/22.*.jpg"))) == 1
    reviewed = made.directory(FLOW, "review")
    assert not (reviewed / "001.approved.json").exists()
    assert (reviewed / "002.approved.json").is_file()
    # Its address now names no render, and says so rather than a record left.
    gone = client.get(f"{at}/v1/11")
    assert gone.status_code == 409
    assert (
        gone.json()["refusal"]
        == "11.png: no render is here, its record and its image are gone"
    )

    # The last approval's only render goes, and the flow keeps only its assignment.
    assert client.delete(f"{at}/v2/22").status_code == 200
    assert list(made.directory(FLOW).iterdir()) == []


@pytest.mark.spec("ui:delete-render:refused-while-a-render-runs")
def test_deleting_a_render_is_refused_while_a_render_runs(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _source(made)
    _rendered_twice(made, schema, vocabulary)
    client = _client(wired, made, tmp_path, drafted=False)
    before = snapshot(made.path)
    alone = _rendering_slot("20261024T091200Z")
    # A session over two collections names the first; the second is rendering too.
    second = {**alone, "collection": "earlier", "collections": ["earlier", COLLECTION]}
    for slot in (alone, second):
        monkeypatch.setattr(Jobs, "slot", lambda self, kind, slot=slot: slot)

        refused = client.delete(
            f"/api/c/{COLLECTION}/renders/{made.digest}/{FLOW}/v1/11"
        )

        assert refused.status_code == 409
        assert "A render session is running." in refused.json()["refusal"]
        assert snapshot(made.path) == before


def _bake(
    made: Run, k: int, source: str, *, colour: tuple[int, int, int] | None = None
) -> Path:
    """Write bake `k` of seed 11 under version 1, an image of `colour` when given.

    Return its record.
    """
    from PIL import Image

    group = made.directory(FLOW, "outputs", "001")
    image, record, _ = run_module.edit_files(group, 11, k)
    body = {"schema": EDIT_FILE.schema, "edit": "tattoo", "source": source}
    record.write_text(json.dumps(body))
    if colour is not None:
        Image.new("RGB", (64, 80), colour).save(image)
    return record


def _baked(
    wired: Wiring, made: Run, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> tuple[TestClient, str]:
    """Return a client and the large view's path over a render with two bakes.

    Bake 1 is imaged and made from the render, bake 2 is queued and made from bake 1.
    """
    _source(made)
    _rendered_twice(made, schema, vocabulary)
    _bake(made, 1, "11.png", colour=(200, 30, 30))
    _bake(made, 2, "11.edit-1.png")
    at = f"/api/c/{COLLECTION}/renders/{made.digest}/{FLOW}/v1/11"
    return _client(wired, made, tmp_path, drafted=False), at


@pytest.mark.spec("ui:bakes:a-bakes-image-and-thumbnail-are-served")
@pytest.mark.spec("ui:bakes:a-bakes-record-names-its-edit")
def test_bake_routes_serve_a_bakes_record_image_and_thumbnail(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, at = _baked(wired, made, tmp_path, schema, vocabulary)
    shrinks: list[Path] = []
    shrink = library._shrunk

    def counted(image: Path) -> bytes:
        shrinks.append(image)
        return shrink(image)

    monkeypatch.setattr(library, "_shrunk", counted)
    image = run_module.edit_files(made.directory(FLOW, "outputs", "001"), 11, 1)[0]

    first, second = client.get(f"{at}/edit/1"), client.get(f"{at}/edit/2")

    assert first.json() == {
        "k": 1,
        "state": "baked",
        "placed_on": None,
        "baked_at": image.stat().st_mtime,
        "edit": "tattoo",
        "reason": None,
    }
    assert second.json() == {
        "k": 2,
        "state": "queued",
        "placed_on": 1,
        "baked_at": None,
        "edit": "tattoo",
        "reason": None,
    }
    served = client.get(f"{at}/edit/1/image")
    assert served.status_code == 200
    assert served.content == image.read_bytes()
    thumbs = [client.get(f"{at}/edit/1/thumb") for _ in range(2)]
    assert [one.status_code for one in thumbs] == [200, 200]
    assert thumbs[0].headers["content-type"] == "image/jpeg"
    assert thumbs[0].content.startswith(b"\xff\xd8")
    assert thumbs[1].content == thumbs[0].content
    assert shrinks == [image]


@pytest.mark.spec("ui:bakes:a-queued-bake-has-no-image")
def test_bake_routes_a_queued_bake_has_no_image_and_names_its_session(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    client, at = _baked(wired, made, tmp_path, schema, vocabulary)
    runs = tmp_path / "lib" / COLLECTION / "runs"

    for tail in ("image", "thumb"):
        refused = client.get(f"{at}/edit/2/{tail}")

        assert refused.status_code == 409
        assert f"`python -m isekai render {runs}`" in refused.json()["refusal"]


@pytest.mark.spec("ui:bakes:an-unknown-bake-is-refused")
@pytest.mark.parametrize(
    "k",
    [
        "3",
        "0",
        "x",
        "1.5",
        "-1",
        "²",
        "4",
        # Past the digits Python converts to an int by default.
        pytest.param("9" * 4301, id="past-the-int-conversion-limit"),
    ],
)
def test_bake_routes_a_number_the_seed_has_no_edit_for_is_refused(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
    k: str,
) -> None:
    client, at = _baked(wired, made, tmp_path, schema, vocabulary)
    # An image or a composite alone is no bake.
    group = made.directory(FLOW, "outputs", "001")
    run_module.edit_files(group, 11, 4)[2].write_bytes(b"png")

    for tail in ("", "/image", "/thumb"):
        refused = client.get(f"{at}/edit/{k}{tail}")

        assert refused.status_code == 409, tail
        assert f"holds no bake {k!r}" in refused.json()["refusal"]


@pytest.mark.spec("ui:bakes:a-damaged-record-marks-its-bake")
def test_bake_routes_a_damaged_record_refuses_each_route_naming_its_file(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    client, at = _baked(wired, made, tmp_path, schema, vocabulary)
    record = _bake(made, 2, "11.edit-1.png", colour=(30, 30, 200))
    record.write_text("{ not json")

    for tail in ("", "/image", "/thumb"):
        refused = client.get(f"{at}/edit/2{tail}")

        assert refused.status_code == 409, tail
        assert record.name in refused.json()["refusal"]
    assert client.get(f"{at}/edit/1/image").status_code == 200


@pytest.mark.spec("ui:bakes:the-chain-lists-the-bakes-in-order")
def test_bake_detail_a_renders_detail_lists_its_bakes_by_number(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    client, at = _baked(wired, made, tmp_path, schema, vocabulary)
    image = run_module.edit_files(made.directory(FLOW, "outputs", "001"), 11, 1)[0]

    detail = client.get(at).json()

    assert detail["bakes"] == [
        {
            "k": 1,
            "state": "baked",
            "placed_on": None,
            "baked_at": image.stat().st_mtime,
            "edit": "tattoo",
            "reason": None,
        },
        {
            "k": 2,
            "state": "queued",
            "placed_on": 1,
            "baked_at": None,
            "edit": "tattoo",
            "reason": None,
        },
    ]
    other = f"/api/c/{COLLECTION}/renders/{made.digest}/{FLOW}/v2/22"
    assert client.get(other).json()["bakes"] == []


@pytest.mark.spec("ui:bakes:a-damaged-record-marks-its-bake")
def test_bake_detail_a_damaged_record_marks_its_own_bake(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    client, at = _baked(wired, made, tmp_path, schema, vocabulary)
    record = _bake(made, 2, "11.edit-1.png")
    record.write_text("{ not json")

    first, second = client.get(at).json()["bakes"]

    assert (first["k"], first["state"], first["reason"]) == (1, "baked", None)
    assert (second["k"], second["state"]) == (2, "damaged")
    assert record.name in second["reason"]
    assert (second["edit"], second["placed_on"]) == (None, None)


@pytest.mark.spec("ui:bakes:deleting-a-render-deletes-its-bakes-thumbnails")
def test_bake_detail_deleting_a_render_deletes_its_bakes_thumbnails(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    client, at = _baked(wired, made, tmp_path, schema, vocabulary)
    for place in ("", "/edit/1"):
        assert client.get(f"{at}{place}/thumb").status_code == 200
    cached = tmp_path / "lib" / ".cache" / made.digest / FLOW / "outputs" / "001"
    # Another collection's thumbnail of the same bake stays.
    elsewhere = cached / "11.edit-1.bbb.jpg"
    elsewhere.write_bytes(b"jpg")
    assert len(list(cached.glob("11.edit-1.*.jpg"))) == 2

    assert client.delete(at).status_code == 200

    assert list(cached.glob("11.*.jpg")) == [elsewhere]
    group = made.directory(FLOW, "outputs", "001")
    assert not run_module.edit_files(group, 11, 1)[0].exists()


@pytest.mark.spec("ui:renders:a-source-thumbnail-is-upright")
def test_a_source_thumbnail_is_turned_upright_and_read_from_the_cache_again(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PIL import Image

    # Orientation 6 turns a wide file a quarter turn: upright, it is tall.
    turned = Image.Exif()
    turned[0x0112] = 6
    sources = tmp_path / "lib" / COLLECTION / "sources"
    (sources / "turned.jpg").write_bytes(
        photo_jpeg((30, 60, 90), (800, 400), exif=turned.tobytes())
    )
    made: list[Path] = []
    upright = library._upright

    def counted(source: Path) -> bytes:
        made.append(source)
        return upright(source)

    monkeypatch.setattr(library, "_upright", counted)
    thumb = f"/api/c/{COLLECTION}/sources/turned.jpg/thumb"

    first = client.get(thumb)
    second = client.get(thumb)

    assert first.status_code == second.status_code == 200
    assert first.headers["content-type"] == "image/jpeg"
    with Image.open(io.BytesIO(first.content)) as shown:
        width, height = shown.size
    assert height > width
    assert second.content == first.content
    assert len(made) == 1
    whole = client.get(f"/api/c/{COLLECTION}/sources/turned.jpg")
    assert whole.content == (sources / "turned.jpg").read_bytes()
    assert (
        client.get(f"/api/c/{COLLECTION}/sources/absent.jpg/thumb").status_code == 409
    )


@pytest.mark.spec("ui:renders:a-photograph-is-served-as-its-bytes")
def test_a_source_named_as_a_page_is_served_as_the_image_it_is(
    client: TestClient, made: Run, tmp_path: Path
) -> None:
    sources = tmp_path / "lib" / COLLECTION / "sources"
    (sources / "portrait.html").write_bytes(png_bytes(40, 30))

    whole = client.get(f"/api/c/{COLLECTION}/sources/portrait.html")
    photo = client.get(_at(made, "/photo"))

    assert whole.status_code == 200
    assert whole.headers["content-type"] == "image/png"
    assert whole.headers["x-content-type-options"] == "nosniff"
    assert photo.headers["content-type"] == "image/jpeg"
    assert photo.headers["x-content-type-options"] == "nosniff"
    # A source in a format the render does not read, placed by hand, is served as
    # an upright JPEG of it, so the viewer shows what its thumbnail does.
    from PIL import Image

    held, turned = io.BytesIO(), Image.Exif()
    turned[0x0112] = 6
    Image.new("RGB", (40, 30), (30, 60, 90)).save(held, "WEBP", exif=turned.tobytes())
    (sources / "pose.webp").write_bytes(held.getvalue())
    other = client.get(f"/api/c/{COLLECTION}/sources/pose.webp")
    assert other.status_code == 200
    assert other.headers["content-type"] == "image/jpeg"
    assert other.headers["x-content-type-options"] == "nosniff"
    with Image.open(io.BytesIO(other.content)) as shown:
        assert (shown.format, shown.size) == ("JPEG", (30, 40))


@pytest.mark.spec("ui:renders:a-damaged-approval-marks-its-version")
def test_a_damaged_approval_heads_its_large_view_damaged(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    _source(made)
    _rendered_twice(made, schema, vocabulary)
    client = _client(wired, made, tmp_path, drafted=False)
    older = approval_of(made, FLOW, 1)
    body = json.loads(older.read_text())
    older.write_text(json.dumps({**body, "renders": {"count": 0}}))
    renders = f"/api/c/{COLLECTION}/renders/{made.digest}/{FLOW}"

    damaged = client.get(f"{renders}/v1/11")
    newer = client.get(f"{renders}/v2/22")

    assert damaged.status_code == 200
    assert older.name in damaged.json()["damaged"]
    assert damaged.json()["count"] is None
    assert newer.json()["damaged"] is None


def _approved_again(
    made: Run,
    schema: Schema,
    vocabulary: Vocabulary,
    renders: Renders | None = None,
    **fields: list[str],
) -> None:
    """Open the next draft of `made`, change `fields` and `renders`, and approve it."""
    draft = review(made, FLOW, new_version=True)
    assert draft is not None
    held = read(draft, DRAFT_FILE)["fields"]
    save_draft(made, FLOW, {**held, **fields}, renders)
    approve(made, FLOW, schema, vocabulary)


@pytest.mark.spec("ui:compare:a-version-is-named-by-what-changed")
def test_a_version_is_headed_a_revision_or_a_re_roll_of_the_one_it_came_from(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    flow = load_flow(FLOW)
    comfy = FakeComfyClient(view_bytes=photo_jpeg((90, 60, 30), (640, 800)))

    def rendered(seed: int) -> None:
        prepare(made, {FLOW: flow})
        render(made, flow, comfy, seeds=[seed], poll=0)

    _source(made)
    review(made, FLOW)
    approve(made, FLOW, schema, vocabulary)
    rendered(7)
    _approved_again(made, schema, vocabulary, clothes=["collared shirt"])
    rendered(7)
    _approved_again(made, schema, vocabulary, {"count": 1, "seeds": [5]})
    rendered(5)
    client = _client(wired, made, tmp_path, drafted=False)
    large = f"/api/c/{COLLECTION}/renders/{made.digest}/{FLOW}"

    views = [client.get(f"{large}/{at}").json() for at in ("v3/5", "v2/7", "v1/7")]

    assert [(one["version"], one["came_from"], one["kind"]) for one in views] == [
        (3, 2, "re-roll"),
        (2, 1, "revision"),
        (1, None, None),
    ]
    assert (views[0]["count"], views[0]["seeds"]) == (1, ["5"])


@pytest.mark.spec("ui:compare:a-seed-pairs-with-its-newest-older-version")
def test_a_seed_rendered_under_three_versions_compares_the_third_with_the_second(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    flow = load_flow(FLOW)
    comfy = FakeComfyClient(view_bytes=photo_jpeg((90, 60, 30), (640, 800)))
    _source(made)
    review(made, FLOW)
    approve(made, FLOW, schema, vocabulary)

    def rendered() -> None:
        prepare(made, {FLOW: flow})
        assert [one.seed for one in render(made, flow, comfy, seeds=[7], poll=0)] == [7]

    rendered()
    _approved_again(made, schema, vocabulary)
    rendered()
    _approved_again(made, schema, vocabulary, clothes=["collared shirt"])
    rendered()
    client = _client(wired, made, tmp_path, drafted=False)
    large = f"/api/c/{COLLECTION}/renders/{made.digest}/{FLOW}/v3/7"

    view = client.get(large).json()
    # The pick opens on `compare`, so its ↵ asks for that image.
    pair = client.get(f"{large}/compare/{FLOW}/v{view['compare']}/7").json()

    assert view["compare"] == 2
    assert (pair["left"]["version"], pair["right"]["version"]) == (2, 3)


FLAT = "summon-flat-anime-wai"


@pytest.mark.spec("ui:compare:any-two-images-of-a-cell")
def test_compare_takes_any_two_images_of_a_source(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    flow, flat = load_flow(FLOW), load_flow(FLAT)
    comfy = FakeComfyClient(view_bytes=photo_jpeg((90, 60, 30), (640, 800)))

    def rendered(seed: int, one: Flow = flow) -> None:
        prepare(made, {one.id: one})
        render(made, one, comfy, seeds=[seed], poll=0)

    _source(made)
    review(made, FLOW)
    approve(made, FLOW, schema, vocabulary)
    rendered(7)
    _approved_again(made, schema, vocabulary, {"count": 1, "seeds": [5]})
    rendered(5)
    _approved_again(made, schema, vocabulary, {"count": 1, "seeds": [7]})
    rendered(7)
    _approved_again(made, schema, vocabulary, clothes=["collared shirt"])
    rendered(7)
    # The hub follows write time within an approval, the large view seed order.
    image = image_of(made, flow, 4, 7)
    for seed, at in ((7, 1), (9, 2), (2, 3)):
        target = image_of(made, flow, 4, seed)
        target.write_bytes(image.read_bytes())
        os.utime(target, (at, at))
    sheet(made, schema, vocabulary, flow=FLAT, flow_digest=manifest_digest(FLAT))
    review(made, FLAT)
    approve(made, FLAT, schema, vocabulary)
    rendered(5, flat)
    # Conjure holds no image of the source, so it has no row.
    client = _client(
        wired, made, tmp_path, drafted=False, offered=(FLOW, CONJURE, FLAT)
    )
    large = f"/api/c/{COLLECTION}/renders/{made.digest}/{FLOW}"

    view = client.get(f"{large}/v4/7").json()
    pair = client.get(f"{large}/v4/7/compare/{FLAT}/v1/5").json()
    within = client.get(f"{large}/v2/5/compare/{FLOW}/v4/7").json()
    photo = client.get(f"{large}/v4/7/compare/photo").json()
    itself = client.get(f"{large}/v4/7/compare/{FLOW}/v4/7")

    # The large view and Compare retain seed order.
    assert "images" not in view
    assert [
        (row["flow"], [(one["version"], one["seed"]) for one in row["images"]])
        for row in view["source"]
    ] == [
        (FLOW, [(1, "7"), (2, "5"), (3, "7"), (4, "2"), (4, "7"), (4, "9")]),
        (FLAT, [(1, "5")]),
    ]
    assert "cell" not in view
    # The image picked is on the left, the one compare started from on the right,
    # each served by its head, and no changed field.
    assert [
        (side["flow"], side["version"], side["seed"])
        for side in (pair["left"], pair["right"])
    ] == [
        (FLAT, 1, "5"),
        (FLOW, 4, "7"),
    ]
    assert set(pair) == {"left", "right"}
    # An older image's compare puts the newer it picked on the left.
    assert [
        (side["version"], side["seed"]) for side in (within["left"], within["right"])
    ] == [
        (4, "7"),
        (2, "5"),
    ]
    # The photograph's pair is the pair alone.
    assert photo == {"left": None, "right": pair["right"]}
    assert itself.status_code == 409
    assert "compared with itself" in itself.json()["refusal"]


@pytest.mark.spec("ui:damage:a-malformed-update-is-refused-naming-the-field")
def test_a_seed_of_digits_outside_ascii_is_refused_naming_the_seeds(
    client: TestClient, made: Run
) -> None:
    before = snapshot(made.path)

    response = client.put(
        _at(made, "/draft"),
        json={"fields": {}, "renders": {"count": 1, "seeds": ["²"]}},
    )

    assert response.status_code == 409
    assert "renders seeds" in response.json()["refusal"]
    assert snapshot(made.path) == before


@pytest.mark.spec("ui:renders:an-address-naming-no-version-is-refused")
def test_a_version_of_digits_outside_ascii_is_refused_not_failed(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    _source(made)
    _rendered_twice(made, schema, vocabulary)
    client = _client(wired, made, tmp_path, drafted=False)

    answered = client.get(f"/api/c/{COLLECTION}/renders/{made.digest}/{FLOW}/v²/11")

    assert answered.status_code == 409
    assert "names no version" in answered.json()["refusal"]


# --- Draft from this, into another flow -----------------------------------------

CONJURE = "conjure-anime-wai"


def _drafting(made: Run, schema: Schema, vocabulary: Vocabulary) -> str:
    """Approve and render summon at seed 7, and return conjure's review route."""
    flow = load_flow(FLOW)
    comfy = FakeComfyClient(view_bytes=photo_jpeg((90, 60, 30), (640, 800)))
    _source(made)
    draft = review(made, FLOW)
    assert draft is not None
    save_draft(made, FLOW, {**read(draft, DRAFT_FILE)["fields"], "expression": []})
    approve(made, FLOW, schema, vocabulary)
    prepare(made, {FLOW: flow})
    render(made, flow, comfy, seeds=[7], poll=0)
    return f"/api/c/{COLLECTION}/review/{made.digest}/{CONJURE}"


def _summon_image(made: Run, version: int = 1) -> dict[str, Any]:
    """Return summon's image at seed 7 under approval `version`, as a page names it."""
    return {"digest": made.digest, "flow": FLOW, "version": version, "seed": "7"}


def _into_conjure(made: Run, version: int = 1) -> dict[str, Any]:
    """Return the request drafting conjure from summon's image under `version`."""
    return {"flow": CONJURE, "images": [_summon_image(made, version)]}


def _drafted(made: Run, name: str = "001.draft.json") -> dict[str, Any]:
    """Return the page's answer for summon's image drafted into conjure as `name`."""
    return {"drafts": [{**_summon_image(made), "draft": name, "waiting": None}]}


@pytest.mark.spec("ui:conjure-from:the-large-view-names-its-targets")
def test_a_large_view_offers_every_offered_flow_its_own_first(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    _drafting(made, schema, vocabulary)
    # Conjure is assigned to no source, and is a target: the draft assigns.
    # Control is assigned and offered by no surface here, so it is no target.
    assign(made, "control-anime-wai")
    client = _client(wired, made, tmp_path, drafted=False, offered=(CONJURE, FLOW))

    body = client.get(f"/api/c/{COLLECTION}/renders/{made.digest}/{FLOW}/v1/7").json()

    assert body["targets"] == [FLOW, CONJURE]

    # A flow the surface does not offer is no target, and its draft is refused
    # writing nothing.
    alone = _client(wired, made, tmp_path, drafted=False, offered=(FLOW,))
    before = snapshot(made.path)

    narrowed = alone.get(
        f"/api/c/{COLLECTION}/renders/{made.digest}/{FLOW}/v1/7"
    ).json()
    pressed = alone.post(DRAFT_ROUTE, json=_into_conjure(made))

    assert narrowed["targets"] == [FLOW]
    assert pressed.status_code == 409
    assert snapshot(made.path) == before


@pytest.mark.spec("ui:conjure-from:a-refused-draft-writes-nothing")
def test_a_draft_from_a_refused_source_writes_nothing(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    _drafting(made, schema, vocabulary)
    client = _client(wired, made, tmp_path, drafted=False)
    before = snapshot(made.path)

    answered = client.post(DRAFT_ROUTE, json=_into_conjure(made, 9))

    assert answered.status_code == 409
    assert "009.approved.json" in answered.json()["refusal"]
    assert snapshot(made.path) == before

    # A damaged approval body is refused before the target is assigned or filled.
    approved = made.directory(FLOW, "review") / "001.approved.json"
    intact = approved.read_bytes()
    approved.write_text(json.dumps({**json.loads(intact), "fields": None}))
    before = snapshot(made.path)

    damaged = client.post(DRAFT_ROUTE, json=_into_conjure(made))

    assert damaged.status_code == 409
    assert "001.approved.json" in damaged.json()["refusal"]
    assert snapshot(made.path) == before
    assert not made.directory(CONJURE).exists()

    # So is a damaged tag list of the photograph's, which would fill the target's sheet.
    approved.write_bytes(intact)
    (made.directory(PHOTO, WD14) / "001.json").write_text("{}")
    before = snapshot(made.path)

    untagged = client.post(DRAFT_ROUTE, json=_into_conjure(made))

    assert untagged.status_code == 409
    assert snapshot(made.path) == before
    assert not made.directory(CONJURE).exists()


@pytest.mark.spec("ui:conjure-from:a-waiting-edit-is-opened")
def test_a_draft_from_onto_an_edited_waiting_draft_answers_it_and_writes_nothing(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    _drafting(made, schema, vocabulary)
    client = _client(wired, made, tmp_path, drafted=False)
    assert client.post(DRAFT_ROUTE, json=_into_conjure(made)).json() == _drafted(made)
    draft = made.directory(CONJURE, "review") / "001.draft.json"
    save_draft(made, CONJURE, {**read(draft, DRAFT_FILE)["fields"], "clothes": []})
    before = snapshot(made.path)

    answered = client.post(DRAFT_ROUTE, json=_into_conjure(made))

    waiting = {**_summon_image(made), "draft": None, "waiting": "001.draft.json"}
    assert answered.json() == {"drafts": [waiting]}
    assert snapshot(made.path) == before


@pytest.mark.spec("ui:conjure-from:review-reads-the-draft-against-the-sheet")
def test_review_reads_a_drafted_draft_against_its_sheet_and_its_image(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    route = _drafting(made, schema, vocabulary)
    sheet(made, load_flow(CONJURE).schema, vocabulary, flow=CONJURE)
    client = _client(wired, made, tmp_path, drafted=False)

    drafted = client.post(DRAFT_ROUTE, json=_into_conjure(made))
    body = client.get(route).json()

    assert drafted.json() == _drafted(made)
    target = made.path / CONJURE / "sheets" / "001.json"
    own = read(target, SHEET_FILE)["fields"]
    assert body["drafted"] == {"fields": own, "version": 1}
    assert body["fields"]["expression"] == [] != own["expression"]
    image = image_of(made, load_flow(FLOW), 1, 7)
    held = image.read_bytes()
    copy = client.get(f"{route}/source/1")
    assert copy.status_code == 200
    assert copy.content == held

    # The copy outlives the image it was drafted from.
    image.unlink()
    assert client.get(route).json()["drafted"] == {"fields": own, "version": 1}
    assert client.get(f"{route}/source/1").content == held
    assert client.get(f"{route}/source/2").status_code == 409

    _damage(target, _drop("fields"))
    refused = client.get(route)

    # `review --new-version` copies the same damaged sheet, so a hand restores it.
    assert refused.status_code == 409
    assert f"restore {target} by hand" in refused.json()["refusal"]


@pytest.mark.spec("ui:conjure-from:an-approved-draft-keeps-its-marks")
def test_review_keeps_an_approved_drafted_drafts_marks(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    route = _drafting(made, schema, vocabulary)
    client = _client(wired, made, tmp_path, drafted=False)
    client.post(DRAFT_ROUTE, json=_into_conjure(made))
    approve(made, CONJURE, load_flow(CONJURE).schema, vocabulary)

    body = client.get(route).json()

    target = made.path / CONJURE / "sheets" / "001.json"
    own = read(target, SHEET_FILE)["fields"]
    assert body["readonly"] is True
    assert body["drafted"] == {"fields": own, "version": 1}

    _damage(target, _drop("fields"))
    refused = client.get(route)

    # The approval is intact: the file to restore is the sheet it was drafted on.
    assert refused.status_code == 409
    assert f"restore {target} by hand" in refused.json()["refusal"]
    assert "001.approved.json" not in refused.json()["refusal"]


@pytest.mark.spec("ui:source:every-flow-shows-the-photographs-caption")
def test_every_flow_shows_the_photographs_caption(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    route = _drafting(made, schema, vocabulary)
    client = _client(wired, made, tmp_path, drafted=False)
    client.post(DRAFT_ROUTE, json=_into_conjure(made))

    bodies = [client.get(at).json() for at in (_at(made), route)]

    for body in bodies:
        assert body["caption"] == "Dark brown hair, brown eyes."
        assert body["caption_command"] is None
        assert "caption_from" not in body
    assert not made.directory(CONJURE, CAPTIONS).exists()


@pytest.mark.spec("ui:source:every-flow-shows-the-photographs-lists")
def test_every_flow_shows_the_photographs_lists(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    tag_hosted(made, FakeTagger(tags=("brown hair", "fashion photography")))
    route = _drafting(made, schema, vocabulary)
    client = _client(wired, made, tmp_path, drafted=False)
    client.post(DRAFT_ROUTE, json=_into_conjure(made))

    own, drafted = (client.get(at).json() for at in (_at(made), route))

    assert own["wd14"] and drafted["wd14"] == own["wd14"]
    assert [one["tag"] for one in drafted["tags"]] == ["brown hair"]
    assert drafted["tags"] == own["tags"]


@pytest.mark.spec("ui:draft-from:an-unedited-waiting-draft-is-replaced")
def test_a_draft_into_a_target_whose_waiting_draft_is_its_sheet_replaces_it(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    route = _drafting(made, schema, vocabulary)
    sheet(made, load_flow(CONJURE).schema, vocabulary, flow=CONJURE)
    assert review(made, CONJURE) is not None
    client = _client(wired, made, tmp_path, drafted=False)

    answered = client.post(DRAFT_ROUTE, json=_into_conjure(made))

    assert answered.json() == _drafted(made)
    assert versions(made.directory(CONJURE, REVIEW)) == [1]
    assert client.get(route).json()["drafted"]["version"] == 1


@pytest.mark.spec("ui:draft-from:a-selection-drafts-into-the-flow-chosen")
def test_a_selection_from_two_runs_drafts_each_into_the_flow_chosen(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    photo = tmp_path / "bo.jpg"
    photo.write_bytes(jpeg_bytes(900, 1200))
    other = open_run(photo, wired.runs_root)
    images = []
    for run, seed in ((made, 7), (other, 8)):
        sheet(run, schema, vocabulary)
        review(run, FLOW)
        approve(run, FLOW, schema, vocabulary)
        rendered_image(run, 1, seed)
        images.append(
            {"digest": run.digest, "flow": FLOW, "version": 1, "seed": str(seed)}
        )
    client = _client(wired, made, tmp_path, drafted=False)

    # A later source's damaged tags refuse the whole selection before any fill.
    tags = other.directory(PHOTO, WD14) / "001.json"
    intact = tags.read_bytes()
    tags.write_text("{}")
    before = {run.id: snapshot(run.path) for run in (made, other)}
    refused = client.post(DRAFT_ROUTE, json={"flow": CONJURE, "images": images})
    assert refused.status_code == 409
    assert [one["refusal"] is None for one in refused.json()["images"]] == [True, False]
    assert {run.id: snapshot(run.path) for run in (made, other)} == before
    tags.write_bytes(intact)

    # An existing but damaged target sheet is checked before the earlier fill too.
    target = other.directory(CONJURE, "sheets") / "001.json"
    target.parent.mkdir(parents=True)
    target.write_text("{}")
    before = {run.id: snapshot(run.path) for run in (made, other)}
    refused = client.post(DRAFT_ROUTE, json={"flow": CONJURE, "images": images})
    assert refused.status_code == 409
    assert [one["refusal"] is None for one in refused.json()["images"]] == [True, False]
    assert {run.id: snapshot(run.path) for run in (made, other)} == before
    target.unlink()

    answered = client.post(DRAFT_ROUTE, json={"flow": CONJURE, "images": images})

    assert answered.status_code == 200
    for run, seed in ((made, 7), (other, 8)):
        draft = read(run.directory(CONJURE, REVIEW) / "001.draft.json", DRAFT_FILE)
        assert "drafted_from" not in draft["producer"]
        assert "image" not in draft["producer"]
        assert draft["renders"] == {"count": 1, "seeds": [seed]}


# --- render sessions ----------------------------------------------------------


def _rendering_slot(session: str) -> dict[str, Any]:
    """Return the render slot as it reads while a render of `COLLECTION` runs."""
    return {
        "kind": "render",
        "collection": COLLECTION,
        "state": "running",
        "session": {"id": session},
    }


def _record(made: Run, name: str, started: str, outcome: str) -> SessionRecord:
    """Write and return a session record of `made`'s collection, one image landed."""
    record: SessionRecord = {
        "schema": SESSION_FILE.schema,
        "id": name,
        "started": started,
        "ended": None if outcome == "running" else started,
        "limit": 1200,
        "asked": {FLOW: 1},
        "steps": {"pod": "ready"},
        "images": [{"digest": made.digest, "flow": FLOW, "version": 1, "seed": "7"}],
        "outcome": outcome,
        "message": None,
    }
    folder = made.path.parent.parent / "sessions"
    replace_record(folder / f"{name}.json", SESSION_FILE, record)
    return record


@pytest.mark.spec("ui:sessions:a-session-reads-its-record")
def test_a_session_is_served_from_its_record_and_an_unknown_id_refused(
    client: TestClient, made: Run
) -> None:
    written = _record(made, "20261024T080000Z", "2026-10-24T08:00:00Z", "done")

    served = client.get(f"/api/c/{COLLECTION}/sessions/20261024T080000Z").json()

    assert (served["images"], served["steps"], served["outcome"]) == (
        written["images"],
        written["steps"],
        "done",
    )
    for unknown in ("20261024T070000Z", "latest"):
        refused = client.get(f"/api/c/{COLLECTION}/sessions/{unknown}")
        assert refused.status_code == 409
        assert refused.json()["refusal"] == f"{COLLECTION} holds no session {unknown!r}"


def _quoting_two(
    wired: Wiring, made: Run, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> TestClient:
    """Return a keyed client over `COLLECTION` and `second`, each one image short."""
    keyed = replace(wired, session=Seams(environ={"RUNPOD_API_KEY": "k"}))
    client = _client(keyed, made, tmp_path)
    approve(made, FLOW, schema, vocabulary)
    other = tmp_path / "lib" / "second"
    (other / "sources").mkdir(parents=True)
    photo = other / "sources" / "bea.jpg"
    photo.write_bytes(jpeg_bytes(1200, 932))
    run = open_run(photo, other / "runs")
    caption(run, FakeReader(prose="Black hair, grey eyes."))
    sheet(run, schema, vocabulary)
    review(run, FLOW)
    approve(run, FLOW, schema, vocabulary)
    return client


@pytest.mark.spec("ui:render:the-dialog-quotes-every-collection")
def test_one_quote_covers_every_ticked_collection(
    wired: Wiring, made: Run, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    client = _quoting_two(wired, made, tmp_path, schema, vocabulary)
    timing = render_module.load_timing()
    both = [COLLECTION, "second"]

    quoted = client.post("/api/render/quote", json={"collections": both}).json()
    alone = client.post("/api/render/quote", json={"collections": ["second"]}).json()

    assert [row["collection"] for row in quoted["collections"]] == both
    assert [row["images"] for row in quoted["collections"]] == [1, 1]
    once = timing.boot_s + timing.teardown_s
    assert quoted["estimate"]["seconds"] == once + 2 * timing.per_image_s
    assert quoted["disabled"] is None
    assert [row["collection"] for row in alone["collections"]] == ["second"]
    assert alone["estimate"]["seconds"] == once + timing.per_image_s
    # With none named, every collection short of images is quoted.
    every = client.post("/api/render/quote", json={}).json()
    assert {row["collection"] for row in every["collections"]} == set(both)
    # The bar counts the images other collections lack, which its dialog renders.
    offer = client.get(f"/api/c/{COLLECTION}/render").json()
    assert (offer["images"], offer["others"]) == (1, 1)
    refused = client.post(
        "/api/render", json={"collections": [], "images": 2, "bakes": 0}
    )
    assert refused.status_code == 409
    assert "names no collections" in refused.json()["refusal"]


@pytest.mark.spec("ui:render:past-the-ceiling-disables-render")
def test_an_estimate_past_the_ceiling_disables_render_naming_it(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _quoting_two(wired, made, tmp_path, schema, vocabulary)
    slow = replace(render_module.load_timing(), per_image_s=3 * 60 * 60)
    monkeypatch.setattr(render_module, "load_timing", lambda: slow)
    both = [COLLECTION, "second"]

    quoted = client.post("/api/render/quote", json={"collections": both}).json()
    started = client.post(
        "/api/render",
        json={
            "collections": both,
            "limit_s": quoted["estimate"]["limit_s"],
            "images": 2,
            "bakes": 0,
        },
    )

    ceiling = quoted["ceiling_s"]
    assert quoted["disabled"] == (
        f"The estimate passes gpunit.toml's ceiling of {ceiling}s; untick a collection."
    )
    assert started.status_code == 409
    assert f"ceiling of {ceiling}s" in started.json()["refusal"]


def _counted(made: Run, schema: Schema, vocabulary: Vocabulary) -> None:
    """Approve `made` and render its one image, seed 7, so no image is short."""
    flow = load_flow(FLOW)
    review(made, FLOW)
    approve(made, FLOW, schema, vocabulary)
    prepare(made, {FLOW: flow})
    client = FakeComfyClient(view_bytes=photo_jpeg((90, 60, 30), (640, 800)))
    render(made, flow, client, seeds=[7], poll=0)


def _queue(made: Run, k: int = 1) -> Path:
    """Queue bake `k` of seed 7 under version 1: its record and no image."""
    group = made.directory(FLOW, "outputs", "001")
    group.mkdir(parents=True, exist_ok=True)
    record = run_module.edit_files(group, 7, k)[1]
    body = {"schema": EDIT_FILE.schema, "edit": "tattoo", "source": "7.png"}
    record.write_text(json.dumps(body))
    return record


def _keyed(wired: Wiring) -> Wiring:
    """Return `wired` with a RunPod key in the surface's environment."""
    return replace(wired, session=Seams(environ={"RUNPOD_API_KEY": "k"}))


@pytest.mark.spec("ui:render:a-bake-alone-is-a-session")
def test_bake_offer_a_bake_alone_is_offered_and_quoted(
    wired: Wiring, made: Run, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    _source(made)
    _counted(made, schema, vocabulary)
    client = _client(_keyed(wired), made, tmp_path, drafted=False)
    offer = f"/api/c/{COLLECTION}/render"

    bare = client.get(offer).json()
    _queue(made)
    offered = client.get(offer).json()
    quote = client.post("/api/render/quote", json={"collections": [COLLECTION]}).json()

    assert (bare["images"], bare["bakes"], bare["other_bakes"]) == (0, 0, 0)
    assert "already has its Count" in bare["disabled"]
    assert (offered["images"], offered["bakes"], offered["others"]) == (0, 1, 0)
    assert (offered["other_bakes"], offered["disabled"]) == (0, None)
    (row,) = quote["collections"]
    assert (row["images"], row["flows"]) == (0, [])
    assert row["bakes"] == [
        {
            "flow": FLOW,
            "name": "ada.jpg",
            "digest": made.digest,
            "run": made.id,
            "version": 1,
            "seed": "7",
            "k": 1,
        }
    ]
    timing = render_module.load_timing()
    assert quote["estimate"]["seconds"] == (
        timing.boot_s + timing.per_edit_s + timing.teardown_s
    )
    assert quote["disabled"] is None


@pytest.mark.spec("ui:render:the-dialog-lists-each-queued-bake")
def test_bake_offer_the_quote_lists_each_bake_beside_the_images_and_counts_the_others(
    wired: Wiring, made: Run, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    client = _quoting_two(wired, made, tmp_path, schema, vocabulary)
    _queue(made)
    both = [COLLECTION, "second"]

    here = client.get(f"/api/c/{COLLECTION}/render").json()
    there = client.get("/api/c/second/render").json()
    quoted = client.post("/api/render/quote", json={"collections": both}).json()

    assert [(one["images"], one["bakes"]) for one in (here, there)] == [(1, 1), (1, 0)]
    assert [(one["others"], one["other_bakes"]) for one in (here, there)] == [
        (1, 0),
        (1, 1),
    ]
    first, second = quoted["collections"]
    assert [(one["flow"], one["images"]) for one in first["flows"]] == [(FLOW, 1)]
    assert [(one["seed"], one["k"], one["version"]) for one in first["bakes"]] == [
        ("7", 1, 1)
    ]
    assert second["bakes"] == []
    timing = render_module.load_timing()
    assert quoted["estimate"]["seconds"] == (
        timing.boot_s + timing.teardown_s + 2 * timing.per_image_s + timing.per_edit_s
    )


@pytest.mark.spec("ui:render:a-changed-bake-count-is-refused")
def test_bake_confirm_a_confirmation_naming_no_bakes_or_another_number_is_refused(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _source(made)
    _counted(made, schema, vocabulary)
    _queue(made)
    client = _client(_keyed(wired), made, tmp_path, drafted=False)
    started: list[object] = []
    monkeypatch.setattr(Jobs, "render", lambda self, *args, **kw: started.append(kw))
    asked = {"collections": [COLLECTION], "keep_open": False}
    limit = client.post("/api/render/quote", json=asked).json()["estimate"]["limit_s"]
    body = {**asked, "limit_s": limit, "images": 0}

    for odd in ({}, {"bakes": True}, {"bakes": "1"}):
        refused = client.post("/api/render", json={**body, **odd})

        assert refused.status_code == 409, odd
        assert "names no quoted bakes" in refused.json()["refusal"]
    for shown in (0, 2):
        refused = client.post("/api/render", json={**body, "bakes": shown})

        assert refused.status_code == 409, shown
        assert f"it now renders 1 bakes, not {shown}" in refused.json()["refusal"]
    assert started == []


@pytest.mark.spec("ui:render:a-bake-alone-is-a-session")
def test_bake_confirm_a_bake_alone_starts_a_render_that_plans_no_image(
    wired: Wiring,
    made: Run,
    tmp_path: Path,
    schema: Schema,
    vocabulary: Vocabulary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _source(made)
    _counted(made, schema, vocabulary)
    _queue(made)
    client = _client(_keyed(wired), made, tmp_path, drafted=False)
    seen: dict[str, object] = {}

    def start(self: Jobs, collections: object, **kwargs: object) -> dict[str, Any]:
        seen.update(kwargs)
        return {}

    monkeypatch.setattr(Jobs, "render", start)
    asked = {"collections": [COLLECTION], "keep_open": False}
    limit = client.post("/api/render/quote", json=asked).json()["estimate"]["limit_s"]

    confirmed = client.post(
        "/api/render", json={**asked, "limit_s": limit, "images": 0, "bakes": 1}
    )

    assert confirmed.status_code == 200
    assert (seen["total"], seen["limit"], seen["without"]) == (0, limit, [])


@pytest.mark.spec("ui:render:a-photograph-taken-out-takes-its-bakes")
def test_bake_offer_a_photograph_taken_out_leaves_the_quote_with_its_bakes(
    wired: Wiring, made: Run, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    client = _quoting_two(wired, made, tmp_path, schema, vocabulary)
    _queue(made)
    taken = {"collection": COLLECTION, "run": made.id, "flow": FLOW}
    asked = {"collections": [COLLECTION], "without": [taken]}

    kept = client.post("/api/render/quote", json={"collections": [COLLECTION]}).json()
    out = client.post("/api/render/quote", json=asked).json()

    (row,) = kept["collections"]
    assert (row["images"], len(row["bakes"])) == (1, 1)
    assert out["collections"] == []
    assert out["disabled"] == render_module.NOTHING_SHORT


# --- the import sheet ---------------------------------------------------------

HEIC = Path(__file__).resolve().parent / "fixtures" / "sources" / "plain.heic"

# How long a test waits on the reader before it fails rather than hangs.
WAIT = 10.0

_READ = frozenset({"ready", "converted", "not cleaned", "skipped", "refused"})


def _broadcast(client: TestClient) -> events.Broadcast:
    """Return the stream every event of `client`'s app is published on."""
    app = client.app
    assert isinstance(app, FastAPI)
    return app.state.broadcast


def _upload(
    client: TestClient, staged: str, name: str, body: bytes
) -> tuple[int, dict[str, Any]]:
    """Return the status and body answering an upload of `body` as `name`."""
    answer = client.put(f"/api/staging/{staged}/files/{name}", content=body)
    return answer.status_code, answer.json()


def _until_each_read(
    feed: "queue.Queue[events.Event]", uploads: Mapping[str, set[str]]
) -> dict[str, list[Any]]:
    """Return each import's `file` events, in order, until every upload is read."""
    seen: dict[str, list[Any]] = {staged: [] for staged in uploads}
    left = {staged: set(each) for staged, each in uploads.items()}
    while any(left.values()):
        kind, data = feed.get(timeout=WAIT)
        if kind == "file" and data["staging"] in seen:
            seen[data["staging"]].append(data)
            if data["state"] in _READ:
                left[data["staging"]].discard(data["upload"])
    return seen


def _until_read(
    feed: "queue.Queue[events.Event]", staged: str, uploads: set[str]
) -> list[Any]:
    """Return import `staged`'s `file` events, in order, until every upload is read."""
    return _until_each_read(feed, {staged: uploads})[staged]


@pytest.mark.spec("ui:sheet:an-upload-is-answered-before-reading")
def test_an_upload_is_answered_before_it_is_read_and_files_are_read_in_turn(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    released = threading.Event()
    reading: list[str] = []
    inside: list[int] = [0, 0]  # now, most at once
    real = importing_module.read

    def held(file: Path, staging: Path, limit: int) -> importing_module.Staged:
        inside[0] += 1
        inside[1] = max(inside)
        released.wait(WAIT)
        reading.append(file.name)
        try:
            return real(file, staging, limit)
        finally:
            inside[0] -= 1

    monkeypatch.setattr(importing_module, "read", held)
    staged = client.post("/api/staging").json()["id"]
    feed = _broadcast(client).subscribe()

    answers = [
        _upload(client, staged, name, photo_jpeg(colour, (40, 30)))
        for name, colour in (("first.jpg", (200, 0, 0)), ("second.jpg", (0, 200, 0)))
    ]

    assert [status for status, _ in answers] == [202, 202]
    assert [body["state"] for _, body in answers] == ["waiting", "waiting"]
    released.set()
    _until_read(feed, staged, {body["upload"] for _, body in answers})
    assert reading == ["first.jpg", "second.jpg"]
    assert inside[1] == 1


@pytest.mark.spec("import:stage:a-failed-move-puts-the-files-back")
def test_a_commit_whose_name_is_taken_as_it_lands_is_refused_and_the_files_stay_staged(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    feed = _broadcast(client).subscribe()
    staged = client.post("/api/staging").json()["id"]
    _, photo = _upload(client, staged, "a.jpg", photo_jpeg((200, 0, 0), (40, 30)))
    (read,) = _until_read(feed, staged, {photo["upload"]})[-1:]
    real = os.rename

    def taken_first(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        if Path(src).name == ".collection":
            (tmp_path / "lib" / "trip").mkdir()
            (tmp_path / "lib" / "trip" / "x").write_bytes(b"rival")
        real(src, dst)

    monkeypatch.setattr(importing_module.os, "rename", taken_first)

    refused = client.post(f"/api/staging/{staged}/commit", json={"collection": "trip"})

    assert refused.status_code == 409
    assert "a folder of that name is in the library" in refused.json()["refusal"]
    assert client.get(f"/api/staging/{staged}/files/{read['name']}").status_code == 200


@pytest.mark.spec("ui:sheet:the-stream-reports-each-files-reading")
def test_the_imports_stream_reports_a_file_waiting_converting_then_converted(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    broadcast = _broadcast(client)
    staged = client.post("/api/staging").json()["id"]
    other = client.post("/api/staging").json()["id"]
    feed = broadcast.subscribe()
    # The snapshot is read before its frame is made, so nothing uploads first.
    snapshotted = threading.Event()
    converted = threading.Event()
    framed = events.frame

    def frame(kind: str, data: dict[str, Any]) -> str:
        if kind == "snapshot":
            snapshotted.set()
        if kind == "file" and data["state"] == "converted":
            converted.set()
        return framed(kind, data)

    monkeypatch.setattr(events, "frame", frame)
    failures: list[BaseException] = []

    def upload_once_open() -> None:
        try:
            assert snapshotted.wait(WAIT), "the stream framed no snapshot"
            _, plain = _upload(client, staged, "plain.heic", HEIC.read_bytes())
            _, away = _upload(
                client, other, "elsewhere.jpg", photo_jpeg((9, 9, 9), (40, 30))
            )
            _until_each_read(feed, {staged: {plain["upload"]}, other: {away["upload"]}})
            assert converted.wait(WAIT), "the stream framed no converted event"
        except BaseException as failed:  # re-raised on the test's own thread
            failures.append(failed)
        finally:
            broadcast.close()

    helper = threading.Thread(target=upload_once_open, daemon=True)
    helper.start()
    body = client.get(f"/events?staging={staged}").text
    helper.join(WAIT)
    if failures:
        raise failures[0]

    frames = [
        (lines[0].removeprefix("event: "), json.loads(lines[1].removeprefix("data: ")))
        for lines in (block.split("\n") for block in body.split("\n\n"))
        if lines[0].startswith("event: ")
    ]
    assert frames[0][0] == "snapshot"
    assert frames[0][1]["files"] == {}
    files = [data for kind, data in frames if kind == "file"]
    assert [(one["file"], one["state"]) for one in files] == [
        ("plain.heic", "waiting"),
        ("plain.heic", "converting"),
        ("plain.heic", "converted"),
    ]
    assert files[-1]["name"] == "plain.jpg"


@pytest.mark.spec("ui:sheet:a-staged-file-serves-its-preview")
def test_a_staged_files_preview_is_a_downscaled_jpeg_kept_nowhere(
    client: TestClient, tmp_path: Path
) -> None:
    feed = _broadcast(client).subscribe()
    staged = client.post("/api/staging").json()["id"]
    _, wide = _upload(
        client, staged, "wide.jpg", photo_jpeg((30, 60, 90), (1600, 1200))
    )
    (read,) = _until_read(feed, staged, {wide["upload"]})[-1:]
    before = snapshot(tmp_path / "lib")

    answered = client.get(f"/api/staging/{staged}/files/{read['name']}/thumb")

    assert answered.status_code == 200
    assert answered.headers["content-type"] == "image/jpeg"
    assert answered.headers["cache-control"] == "no-store"
    from PIL import Image

    with Image.open(io.BytesIO(answered.content)) as shown:
        assert shown.format == "JPEG"
        assert max(shown.size) == THUMB_SIDE
    assert snapshot(tmp_path / "lib") == before


@pytest.mark.spec("ui:sheet:the-tiles-take-the-keys")
def test_staging_serves_a_read_file_full_size_until_it_is_removed(
    client: TestClient, tmp_path: Path
) -> None:
    feed = _broadcast(client).subscribe()
    staged = client.post("/api/staging").json()["id"]
    _, wide = _upload(
        client, staged, "wide.jpg", photo_jpeg((30, 60, 90), (1600, 1200))
    )
    (read,) = _until_read(feed, staged, {wide["upload"]})[-1:]
    file = f"/api/staging/{staged}/files/{read['name']}"

    answered = client.get(file)

    assert answered.status_code == 200
    assert answered.headers["content-type"] == "image/jpeg"
    assert answered.headers["cache-control"] == "no-store"
    assert answered.headers["x-content-type-options"] == "nosniff"
    from PIL import Image

    with Image.open(io.BytesIO(answered.content)) as shown:
        assert shown.size == (1600, 1200)

    assert client.delete(file).status_code == 200
    assert client.get(file).status_code == 409
    assert client.delete(file).status_code == 409


@pytest.mark.spec("ui:sessions:a-terminal-render-stays-live")
def test_a_terminal_session_is_live_without_a_job_slot(
    client: TestClient, made: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    from isekai.interface.render import Record

    monkeypatch.setattr(Jobs, "slot", lambda self, kind: None)
    name = "20261024T091200Z"
    record = Record(made.path.parent.parent / "sessions", name, 1200, {FLOW: 1})
    # A damaged record in another collection is that collection's refusal, not
    # this read's.
    other = made.path.parent.parent.parent / "another"
    (other / "sources").mkdir(parents=True)
    (other / "sessions").mkdir()
    (other / "sessions" / "20261024T080000Z.json").write_text("{")
    record.open()
    try:
        response = client.get(f"/api/c/{COLLECTION}/sessions/{name}")
        assert response.json()["outcome"] == "running"
        running = client.get("/api/sessions/running").json()["sessions"]
        assert [(one["collection"], one["id"]) for one in running] == [
            (COLLECTION, name)
        ]
        record.image({"digest": made.digest, "flow": FLOW, "version": 1, "seed": "7"})
        assert (
            len(client.get(f"/api/c/{COLLECTION}/sessions/{name}").json()["images"])
            == 1
        )
    finally:
        record.close()
    assert client.get(f"/api/c/{COLLECTION}/sessions/{name}").json()["outcome"] is None
    assert client.get("/api/sessions/running").json()["sessions"] == []

    # The complete traversal survives the name-sorted scan, including in the
    # second collection's record; old records above need no order field.
    order = [other.name, COLLECTION]
    held = [
        Record(folder / "sessions", "20261024T091300Z", 1200, {FLOW: 1}, order=order)
        for folder in (other, made.path.parent.parent)
    ]
    for one in held:
        one.open()
    try:
        running = client.get("/api/sessions/running").json()["sessions"]
        assert [one["collection"] for one in running] == [COLLECTION, other.name]
        assert all(one["collection_order"] == order for one in running)
    finally:
        for one in held:
            one.close()
