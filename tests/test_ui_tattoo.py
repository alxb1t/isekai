"""The tattoo routes over the test client: list, keep, cut, outline, ink view, guard.

The store and the ink view are proved in `tests/test_tattoo_library.py`; here the
route's own work is: its body, its refusals as every refusal answers, its headers.
"""

import io
import math
import random
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import httpx2
import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from isekai.foundation.run import Run, open_run  # noqa: E402
from isekai.interface.ui import HOST  # noqa: E402
from isekai.interface.ui.app import create_app  # noqa: E402
from isekai.interface.wiring import Wiring  # noqa: E402
from isekai.pipeline.importing import STAGING  # noqa: E402
from isekai.pipeline.tattoos import CUTS, DESIGN, OUTLINE, TATTOOS  # noqa: E402
from isekai.shared.vocabulary import Vocabulary  # noqa: E402
from tests.conftest import snapshot  # noqa: E402
from tests.stages import FIELD_MAP, NO_GPUNIT  # noqa: E402

COLLECTION = "2026-10-19"
FLOW = "summon-anime-wai"
PORT = 8765
ANY = "0123456789ab"
BOW_OUTLINE = f"/api/tattoos/bow/outline?digest={ANY}"
ADDRESS = f"http://{HOST}:{PORT}"
SKIN = (200, 150, 120)
ARM = (400, 300)
FILL = (180, 130, 219, 169)
CENTRE = (200, 150)


def _arm() -> bytes:
    """Return a PNG of flat skin with one dark square fill."""
    arm = Image.new("RGB", ARM, SKIN)
    ImageDraw.Draw(arm).rectangle(FILL, fill=(40, 30, 30))
    out = io.BytesIO()
    arm.save(out, "PNG")
    return out.getvalue()


def _around_the_fill(count: int = 24) -> list[list[float]]:
    """Return `count` points on a circle that holds the fill with skin to spare."""
    return [
        [
            CENTRE[0] + 34 * math.cos(2 * math.pi * step / count),
            CENTRE[1] + 34 * math.sin(2 * math.pi * step / count),
        ]
        for step in range(count)
    ]


def _body(
    points: list[list[float]] | None = None, closed: bool = True, **tone: float | bool
) -> dict[str, Any]:
    """Return an outline's body: the ring round the fill, closed, at the defaults."""
    return {
        "points": _around_the_fill() if points is None else points,
        "closed": closed,
        "white": 1.0,
        "neutral": True,
        "depth": 1.6,
    } | tone


def _ask(
    points: list[list[float]] | None = None, **more: float | bool | str
) -> dict[str, Any]:
    """Return an ink view's body."""
    return {
        "points": _around_the_fill() if points is None else points,
        "white": 1.0,
        "neutral": True,
        "depth": 1.6,
    } | more


@pytest.fixture
def library(tmp_path: Path) -> Path:
    """Return a library holding one empty collection."""
    (tmp_path / "lib" / COLLECTION / "sources").mkdir(parents=True)
    return tmp_path / "lib"


@pytest.fixture
def wired(library: Path, vocabulary: Vocabulary) -> Wiring:
    """Return a wiring over the collection: no reader, no tagger, no pod."""
    return Wiring(
        reader=None,
        tagger=None,
        hosted_tagger=None,
        client=None,
        vocabulary=lambda: vocabulary,
        field_map=lambda _: FIELD_MAP,
        runs_root=library / COLLECTION / "runs",
        rng=random.Random(0),
        out=io.StringIO(),
        err=io.StringIO(),
        volume=NO_GPUNIT,
    )


@pytest.fixture
def client(wired: Wiring, tmp_path: Path) -> TestClient:
    """Return a client over the application, with a stand-in for the bundle."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html>")
    app = create_app(
        wired.runs_root.parent.parent,
        wired,
        flows=(FLOW,),
        bundle=dist,
        wire=lambda runs: replace(wired, runs_root=runs),
        host=HOST,
        port=PORT,
    )
    return TestClient(app, base_url=ADDRESS)


@pytest.fixture
def photographed(wired: Wiring, tmp_path: Path) -> Callable[..., Run]:
    """Return a maker of runs: a photograph of the bytes, opened in the collection."""

    def make(name: str = "ada.png", body: bytes | None = None) -> Run:
        photo = tmp_path / name
        photo.write_bytes(_arm() if body is None else body)
        return open_run(photo, wired.runs_root)

    return make


def _staged(library: Path, client: TestClient, name: str, body: bytes) -> str:
    """Return the id of an open import holding `body` as the staged file `name`."""
    staged = client.post("/api/staging").json()["id"]
    (library / STAGING / staged / name).write_bytes(body)
    return staged


def _tattoo_png() -> bytes:
    """Return a small clean PNG, a tattoo an upload keeps."""
    out = io.BytesIO()
    Image.new("RGB", (60, 40), (20, 30, 40)).save(out, "PNG")
    return out.getvalue()


def _jpeg_with_a_camera_tag() -> bytes:
    """Return a decodable JPEG that carries an EXIF `Make`, which a clean one lacks."""
    exif = Image.Exif()
    exif[0x010F] = "Camera"
    out = io.BytesIO()
    Image.new("RGB", (60, 40), (20, 30, 40)).save(out, "JPEG", exif=exif)
    return out.getvalue()


def _upload(
    library: Path, client: TestClient, name: str = "bow", body: bytes | None = None
) -> dict[str, Any]:
    """Keep a tattoo called `name` from a staged clean PNG; return the answer's body."""
    staged = _staged(
        library, client, "bow.png", _tattoo_png() if body is None else body
    )
    answered = client.post(
        "/api/tattoos", json={"staging": staged, "file": "bow.png", "name": name}
    )
    assert answered.status_code == 200, answered.text
    return answered.json()


def _cut(client: TestClient, run: Run, name: str = "arm") -> dict[str, Any]:
    """Cut a tattoo called `name` from `run`'s photograph; return the answer's body."""
    answered = client.post(
        f"/api/c/{COLLECTION}/tattoos",
        json={"name": name, "digest": run.digest, "flow": FLOW},
    )
    assert answered.status_code == 200, answered.text
    return answered.json()


@pytest.mark.spec("tattoo:library:the-list-names-each-tattoo")
def test_tattoo_route_read_lists_each_in_the_order_kept_with_the_limits(
    library: Path, client: TestClient, photographed: Callable[..., Run]
) -> None:
    run = photographed()
    assert client.get(f"/api/tattoos?digest={run.digest}").json()["tattoos"] == []
    _upload(library, client, "bow")
    _cut(client, run, "arm")

    listed = client.get(f"/api/tattoos?digest={run.digest}").json()

    assert listed["stage1"] == {}
    assert [one["name"] for one in listed["tattoos"]] == ["bow", "arm"]
    bow, arm = listed["tattoos"]
    assert (bow["kind"], bow["size"], bow["outlined"]) == ("image", [60, 40], False)
    assert (arm["kind"], arm["size"], arm["outlined"]) == ("cut", list(ARM), False)
    assert listed["limits"] == {
        "long_side": 4096,
        "outline_min": 20,
        "outline_max": 120,
        "depth_min": 1.0,
        "depth_max": 2.0,
        "photo_depth": 1.6,
        "image_depth": 1.0,
        "floor_stage1": 6,
        "floor_stage2": 8,
        "floor_direct": 6,
        "preview_floor": 3,
        "preview_margin": 96,
        "preview_wait_ms": 1000,
        "pair_radius": 8,
        "region_min": 3,
    }


@pytest.mark.spec_exempt("structural: a tattoo is read with its outline, or refused")
def test_tattoo_route_read_one_answers_its_record_and_outline_or_refuses_the_name(
    library: Path, client: TestClient
) -> None:
    _upload(library, client, "bow")

    one = client.get(f"/api/tattoos/bow?digest={ANY}")
    missing = client.get(f"/api/tattoos/ghost?digest={ANY}")
    hidden = client.get(f"/api/tattoos/.keep?digest={ANY}")
    undigested = client.get("/api/tattoos/bow")

    assert undigested.status_code == 409
    assert "digest" in undigested.json()["refusal"]
    assert client.get("/api/tattoos").status_code == 409
    assert one.status_code == 200
    assert one.json()["name"] == "bow"
    assert one.json()["outline"] == {
        "points": [],
        "closed": False,
        "white": 1.0,
        "neutral": False,
        "depth": 1.0,
    }
    assert missing.status_code == 409
    assert "ghost" in missing.json()["refusal"]
    assert hidden.status_code == 409


@pytest.mark.spec_exempt("structural: the design is served whole, and a cut has none")
def test_tattoo_route_read_design_serves_the_png_and_refuses_a_cut(
    library: Path, client: TestClient, photographed: Callable[..., Run]
) -> None:
    run = photographed()
    _upload(library, client, "bow")
    _cut(client, run, "arm")

    design = client.get(f"/api/tattoos/bow/design?digest={run.digest}")
    cut = client.get(f"/api/tattoos/arm/design?digest={run.digest}")

    assert design.status_code == 200
    assert design.headers["content-type"] == "image/png"
    assert design.content == (library / TATTOOS / "bow" / DESIGN).read_bytes()
    assert cut.status_code == 409
    assert "cut from a photograph" in cut.json()["refusal"]
    assert client.get(f"/api/tattoos/ghost/design?digest={ANY}").status_code == 409
    assert client.get("/api/tattoos/bow/design").status_code == 409


@pytest.mark.spec("tattoo:library:an-upload-is-kept-upright-and-bounded")
def test_tattoo_route_keep_takes_the_staged_file_and_cancels_its_staging(
    library: Path, client: TestClient
) -> None:
    staged = _staged(library, client, "bow.png", _tattoo_png())

    answered = client.post(
        "/api/tattoos", json={"staging": staged, "file": "bow.png", "name": "bow"}
    )

    assert answered.status_code == 200
    assert answered.json()["name"] == "bow"
    assert answered.json()["kind"] == "image"
    assert (library / TATTOOS / "bow" / DESIGN).is_file()
    assert not (library / STAGING).exists()
    assert client.get(f"/api/staging/{staged}/files/bow.png").status_code == 409


@pytest.mark.spec("tattoo:library:an-unclean-file-is-refused")
def test_tattoo_route_keep_refuses_a_file_still_carrying_metadata(
    library: Path, client: TestClient
) -> None:
    staged = _staged(library, client, "bow.jpg", _jpeg_with_a_camera_tag())

    answered = client.post(
        "/api/tattoos", json={"staging": staged, "file": "bow.jpg", "name": "bow"}
    )

    assert answered.status_code == 409
    assert "EXIF" in answered.json()["refusal"]
    assert not (library / TATTOOS).exists()
    assert (library / STAGING / staged / "bow.jpg").is_file()


@pytest.mark.spec("tattoo:library:a-taken-name-is-refused")
def test_tattoo_route_keep_a_taken_name_is_refused_and_the_staging_stays(
    library: Path, client: TestClient
) -> None:
    _upload(library, client, "bow")
    staged = _staged(library, client, "other.png", _tattoo_png())

    answered = client.post(
        "/api/tattoos", json={"staging": staged, "file": "other.png", "name": "bow"}
    )

    assert answered.status_code == 409
    assert answered.json()["refusal"] == "bow is kept; choose another name"
    assert (library / STAGING / staged / "other.png").is_file()


@pytest.mark.spec_exempt("structural: a keep that names no import or file is refused")
@pytest.mark.parametrize(
    "body",
    [
        {},
        {"staging": "gone", "file": "bow.png", "name": "bow"},
        {"staging": 3, "file": "bow.png", "name": "bow"},
    ],
)
def test_tattoo_route_keep_names_what_it_is_missing(
    client: TestClient, body: dict[str, Any]
) -> None:
    answered = client.post("/api/tattoos", json=body)

    assert answered.status_code == 409
    assert answered.json()["refusal"]


@pytest.mark.spec("tattoo:cut:a-cut-holds-no-image")
def test_tattoo_route_keep_cuts_a_tattoo_from_a_runs_photograph(
    library: Path, client: TestClient, photographed: Callable[..., Run]
) -> None:
    run = photographed()

    made = _cut(client, run, "arm")

    assert made["kind"] == "cut"
    assert made["cut_from"] == run.digest
    assert made["size"] == list(ARM)
    folder = library / TATTOOS / CUTS / run.digest / "arm"
    assert sorted(item.name for item in folder.iterdir()) == [OUTLINE, "tattoo.json"]
    assert not (library / TATTOOS / "arm").exists()


@pytest.mark.spec_exempt("structural: a cut of an unknown run or a bad name is refused")
@pytest.mark.parametrize(
    ("body", "match"),
    [
        ({"name": "arm", "digest": "0123456789ab", "flow": FLOW}, "no run named"),
        ({"name": "arm", "digest": "RUN", "flow": "nowhere"}, "nowhere"),
        ({"digest": "RUN", "flow": FLOW}, "name"),
        ({"name": ".hid", "digest": "RUN", "flow": FLOW}, "choose another name"),
    ],
)
def test_tattoo_route_keep_a_cut_of_what_is_not_there_is_refused(
    library: Path,
    client: TestClient,
    photographed: Callable[..., Run],
    body: dict[str, Any],
    match: str,
) -> None:
    run = photographed()
    asked = {
        key: run.digest if value == "RUN" else value for key, value in body.items()
    }

    answered = client.post(f"/api/c/{COLLECTION}/tattoos", json=asked)

    assert answered.status_code == 409
    assert match in answered.json()["refusal"]
    assert not (library / TATTOOS).exists()


@pytest.mark.spec("tattoo:outline:an-outline-is-saved-as-it-is-sent")
def test_tattoo_route_outline_saves_each_send_and_reads_as_outlined_once_closed(
    library: Path, client: TestClient
) -> None:
    _upload(library, client, "bow", _arm())
    ring = _around_the_fill()

    opened = client.put(BOW_OUTLINE, json=_body(ring[:5], False))
    closed = client.put(BOW_OUTLINE, json=_body(ring, True))

    assert opened.status_code == 200
    assert opened.json()["closed"] is False
    assert len(opened.json()["points"]) == 5
    assert closed.json()["closed"] is True
    read = client.get(f"/api/tattoos/bow?digest={ANY}").json()
    assert read["outline"]["points"] == closed.json()["points"]
    assert read["outlined"] is True


@pytest.mark.spec("tattoo:outline:a-point-outside-the-image-is-refused")
def test_tattoo_route_outline_refuses_as_every_refusal_does_and_leaves_the_file(
    library: Path, client: TestClient
) -> None:
    _upload(library, client, "bow")
    client.put(BOW_OUTLINE, json=_body(_around_the_fill()[:3], False))
    before = (library / TATTOOS / "bow" / OUTLINE).read_bytes()

    outside = client.put(BOW_OUTLINE, json=_body([[1.0, 2.0], [61.0, 2.0]], False))

    assert outside.status_code == 409
    assert "point 2 (61, 2) lies outside the 60x40 image" in outside.json()["refusal"]
    assert (library / TATTOOS / "bow" / OUTLINE).read_bytes() == before


@pytest.mark.spec("tattoo:outline:a-tone-out-of-range-is-refused")
def test_tattoo_route_outline_refuses_a_tone_out_of_range_and_a_missing_key(
    library: Path, client: TestClient
) -> None:
    _upload(library, client, "bow")

    deep = client.put(BOW_OUTLINE, json=_body([], False, depth=9))
    flat = client.put(BOW_OUTLINE, json=_body([], False, white=0))
    short = client.put(BOW_OUTLINE, json={"points": []})
    ghost = client.put(
        f"/api/tattoos/ghost/outline?digest={ANY}", json=_body([], False)
    )

    assert "depth 9 is outside 1 to 2" in deep.json()["refusal"]
    assert "white scale 0" in flat.json()["refusal"]
    assert short.status_code == 409
    for key in ("closed", "white", "neutral", "depth"):
        assert key in short.json()["refusal"]
    assert ghost.status_code == 409
    assert "ghost" in ghost.json()["refusal"]


def _outlined(
    library: Path, client: TestClient, run: Run, name: str = "arm"
) -> dict[str, Any]:
    """Cut `name` from `run` and save the closed ring round the fill; return the cut."""
    made = _cut(client, run, name)
    saved = client.put(f"/api/tattoos/{name}/outline?digest={run.digest}", json=_body())
    assert saved.status_code == 200, saved.text
    return made


def _ink(
    client: TestClient, run: Run, name: str = "arm", **more: float | bool
) -> httpx2.Response:
    """Ask the ink view of the cut `name` on `run`."""
    return client.post(
        f"/api/c/{COLLECTION}/tattoos/{name}/ink",
        json=_ask(digest=run.digest, flow=FLOW) | more,
    )


@pytest.mark.spec("tattoo:ink-view:a-jpeg-on-the-outlines-crop")
def test_ink_preview_route_answers_a_jpeg_on_the_crop_its_box_header_names(
    library: Path, client: TestClient, photographed: Callable[..., Run]
) -> None:
    run = photographed()
    _outlined(library, client, run)

    answered = _ink(client, run)

    assert answered.status_code == 200
    assert answered.headers["content-type"] == "image/jpeg"
    x, y, width, height = (int(n) for n in answered.headers["x-ink-box"].split(","))
    assert 0 <= x and 0 <= y and x + width <= ARM[0] and y + height <= ARM[1]
    assert (width, height) != ARM
    with Image.open(io.BytesIO(answered.content)) as shown:
        assert shown.format == "JPEG"
        assert shown.size == (width, height)


@pytest.mark.spec("tattoo:ink-view:the-answer-carries-the-automatic-white-point")
def test_ink_preview_route_names_the_automatic_grey_in_a_header(
    library: Path, client: TestClient, photographed: Callable[..., Run]
) -> None:
    run = photographed()
    _outlined(library, client, run)

    answered = _ink(client, run, white=0.5)

    grey = answered.headers["x-ink-white"]
    assert grey.isdigit()
    assert 0 <= int(grey) <= 255


@pytest.mark.spec("tattoo:ink-view:the-answer-is-kept-nowhere")
def test_ink_preview_route_is_no_store_and_writes_nothing(
    library: Path, client: TestClient, photographed: Callable[..., Run]
) -> None:
    run = photographed()
    _outlined(library, client, run)
    before = snapshot(library)

    answered = _ink(client, run)

    assert answered.headers["cache-control"] == "no-store"
    assert snapshot(library) == before


@pytest.mark.spec_exempt("structural: an upload's ink view needs no run")
def test_ink_preview_route_of_an_upload_reads_its_design(
    library: Path, client: TestClient, photographed: Callable[..., Run]
) -> None:
    run = photographed()
    _upload(library, client, "ink", _arm())
    client.put(
        f"/api/tattoos/ink/outline?digest={run.digest}",
        json=_body(neutral=False, depth=1.0),
    )

    answered = _ink(client, run, "ink", neutral=False, depth=1.0)
    undigested = client.post(
        f"/api/c/{COLLECTION}/tattoos/ink/ink", json=_ask(neutral=False, depth=1.0)
    )

    assert answered.status_code == 200, answered.text
    assert answered.headers["content-type"] == "image/jpeg"
    assert answered.headers["x-ink-white"].isdigit()
    assert undigested.status_code == 409
    assert "digest, flow" in undigested.json()["refusal"]


@pytest.mark.spec("tattoo:ink-view:an-open-outline-is-refused")
def test_ink_preview_route_refuses_an_open_outline(
    library: Path, client: TestClient, photographed: Callable[..., Run]
) -> None:
    run = photographed()
    _cut(client, run)
    client.put(
        f"/api/tattoos/arm/outline?digest={run.digest}", json=_body(closed=False)
    )

    answered = _ink(client, run)

    assert answered.status_code == 409
    assert "the outline is open" in answered.json()["refusal"]


@pytest.mark.spec("tattoo:ink-view:an-unknown-tattoo-is-refused")
def test_ink_preview_route_refuses_an_unknown_tattoo_naming_it(
    client: TestClient, photographed: Callable[..., Run]
) -> None:
    answered = _ink(client, photographed(), "ghost")

    assert answered.status_code == 409
    assert "ghost" in answered.json()["refusal"]


@pytest.mark.spec("tattoo:cut:a-cut-serves-only-its-own-photograph")
def test_ink_preview_route_refuses_a_cut_asked_on_another_photograph(
    library: Path, client: TestClient, photographed: Callable[..., Run]
) -> None:
    run = photographed()
    other = photographed("grace.png", _arm() + b"\0")
    _outlined(library, client, run)

    answered = _ink(client, other)

    assert other.digest != run.digest
    assert answered.status_code == 409
    assert f"cut from photograph {run.digest}" in answered.json()["refusal"]


@pytest.mark.spec("tattoo:ink-view:a-request-from-another-site-is-refused")
def test_ink_preview_route_refuses_a_request_from_another_site(
    library: Path, client: TestClient, photographed: Callable[..., Run]
) -> None:
    run = photographed()
    _outlined(library, client, run)

    answered = client.post(
        f"/api/c/{COLLECTION}/tattoos/arm/ink",
        json=_ask(digest=run.digest, flow=FLOW),
        headers={"Origin": "http://evil.example"},
    )

    assert answered.status_code == 403
    assert answered.json() == {"refusal": "not from this page"}


REMOVAL = "/api/tattoos/{name}"


def _taking_away(app: FastAPI) -> list[str]:
    """Return each tattoo route that renames, or removes other than by `REMOVAL`."""
    found = []
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", None) or set()
        if not path.startswith("/api/tattoos"):
            continue
        removes_elsewhere = "DELETE" in methods and path != REMOVAL
        if (
            removes_elsewhere
            or "PATCH" in methods
            or any(word in path for word in ("delete", "remove", "rename"))
        ):
            found.append(f"{sorted(methods)} {path}")
    return found


def _new_routes(app: FastAPI) -> list[tuple[str, str]]:
    """Return the method and path of each route that names a tattoo."""
    return [
        (method, getattr(route, "path", ""))
        for route in app.routes
        if "/tattoos" in getattr(route, "path", "")
        for method in sorted(getattr(route, "methods", None) or ())
        if method != "HEAD"
    ]


@pytest.mark.spec("tattoo:library:no-route-renames")
def test_tattoo_route_guard_none_under_api_tattoos_renames_and_one_removes(
    client: TestClient,
) -> None:
    app = client.app
    assert isinstance(app, FastAPI)

    assert _taking_away(app) == []
    assert ("GET", "/api/tattoos") in _new_routes(app)
    assert ("DELETE", REMOVAL) in _new_routes(app)


@pytest.mark.spec("tattoo:library:no-route-renames")
def test_tattoo_route_guard_twin_finds_a_rename_and_a_delete_elsewhere_when_added(
    client: TestClient,
) -> None:
    app = client.app
    assert isinstance(app, FastAPI)

    app.add_api_route("/api/tattoos/{name}/design", lambda name: {}, methods=["DELETE"])
    app.add_api_route("/api/tattoos/{name}/rename", lambda name: {}, methods=["PUT"])

    taken = _taking_away(app)
    assert len(taken) == 2
    assert any("DELETE" in line for line in taken)
    assert any("rename" in line for line in taken)


@pytest.mark.spec("tattoo:library:a-removed-tattoo-is-gone")
def test_tattoo_route_delete_removes_an_upload_and_a_cut(
    library: Path, client: TestClient, photographed: Callable[..., Run]
) -> None:
    run = photographed()
    _upload(library, client, "bow")
    _upload(library, client, "wing")
    _cut(client, run, "arm")

    upload = client.delete(f"/api/tattoos/bow?digest={run.digest}")
    cut = client.delete(f"/api/tattoos/arm?digest={run.digest}")

    assert (upload.status_code, upload.json()) == (200, {})
    assert (cut.status_code, cut.json()) == (200, {})
    listed = client.get(f"/api/tattoos?digest={run.digest}").json()["tattoos"]
    assert [one["name"] for one in listed] == ["wing"]
    assert not (library / TATTOOS / "bow").exists()
    assert not (library / TATTOOS / CUTS / run.digest).exists()
    assert _upload(library, client, "bow")["name"] == "bow"


@pytest.mark.spec("tattoo:library:a-removal-reaches-only-the-named-tattoo")
def test_tattoo_route_delete_refuses_a_missing_digest_and_an_unknown_name(
    library: Path, client: TestClient, photographed: Callable[..., Run]
) -> None:
    run = photographed()
    _upload(library, client, "bow")
    _cut(client, run, "arm")
    before = snapshot(library)

    undigested = client.delete("/api/tattoos/bow")
    unknown = client.delete(f"/api/tattoos/ghost?digest={run.digest}")
    hidden = client.delete(f"/api/tattoos/.cuts?digest={run.digest}")
    bad = client.delete(f"/api/tattoos/bow?digest={'../' * 4}")
    other = client.delete(f"/api/tattoos/arm?digest={ANY}")

    for answered in (undigested, unknown, hidden, bad, other):
        assert answered.status_code == 409
    assert "digest" in undigested.json()["refusal"]
    assert "ghost" in unknown.json()["refusal"]
    assert f"cut from photograph {run.digest}" in other.json()["refusal"]
    assert snapshot(library) == before


@pytest.mark.spec("tattoo:ink-view:a-request-from-another-site-is-refused")
def test_tattoo_route_guard_answers_every_new_route_before_its_handler(
    client: TestClient,
) -> None:
    app = client.app
    assert isinstance(app, FastAPI)
    routes = _new_routes(app)
    assert len(routes) >= 7

    for method, path in routes:
        url = path.replace("{collection}", COLLECTION).replace("{name}", "bow")
        elsewhere = client.request(
            method, url, headers={"Origin": "http://evil.example"}
        )
        rebound = client.request(method, url, headers={"Host": "evil.example"})

        assert elsewhere.status_code == 403, (method, path)
        assert rebound.status_code == 403, (method, path)
