"""The placement routes over the test client: stage-1 pairs, the preview, the guard.

The store and the preview are proved in `tests/test_tattoo_placement.py`; here the
routes' own work is: their bodies, their refusals as every refusal answers, their
headers, and that they write nothing of their own.
"""

import io
import math
import random
from dataclasses import replace
from pathlib import Path
from typing import Any

import httpx2
import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from isekai.foundation.artifacts import EDIT_FILE, PLACEMENT_FILE, read  # noqa: E402
from isekai.foundation.run import (  # noqa: E402
    Run,
    edit_files,
    open_run,
    placement_file,
)
from isekai.interface.ui import HOST  # noqa: E402
from isekai.interface.ui.app import create_app  # noqa: E402
from isekai.interface.wiring import Wiring  # noqa: E402
from isekai.pipeline.importing import STAGING  # noqa: E402
from isekai.pipeline.tattoos import STAGE1, TATTOOS  # noqa: E402
from isekai.shared.vocabulary import Vocabulary  # noqa: E402
from tests.conftest import snapshot  # noqa: E402
from tests.stages import FIELD_MAP, NO_GPUNIT, rendered_image  # noqa: E402

COLLECTION = "2026-10-19"
FLOW = "summon-anime-wai"
PORT = 8765
ADDRESS = f"http://{HOST}:{PORT}"
SKIN = (200, 150, 120)
ARM = (400, 300)
FILL = (180, 130, 219, 169)
CENTRE = (200, 150)
SEED = 42
ONTO_PHOTO = (30, 20)
ONTO_RENDER = (15, 10)


def _arm() -> bytes:
    """Return a PNG of flat skin with one dark square fill."""
    arm = Image.new("RGB", ARM, SKIN)
    ImageDraw.Draw(arm).rectangle(FILL, fill=(40, 30, 30))
    out = io.BytesIO()
    arm.save(out, "PNG")
    return out.getvalue()


def _around(radius: float, count: int) -> list[list[float]]:
    """Return `count` points on a circle of `radius` round the arm's centre."""
    return [
        [
            CENTRE[0] + radius * math.cos(2 * math.pi * step / count),
            CENTRE[1] + radius * math.sin(2 * math.pi * step / count),
        ]
        for step in range(count)
    ]


def _pairs(
    count: int, by: tuple[int, int], origin: tuple[int, int] = (0, 0)
) -> list[list[list[float]]]:
    """Return `count` pairs: a point on a wide circle, then it moved by `by`."""
    first = [[x + origin[0], y + origin[1]] for x, y in _around(60, count)]
    return [[a, [a[0] + by[0], a[1] + by[1]]] for a in first]


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
def photographed(wired: Wiring, tmp_path: Path) -> Run:
    """Return a run of a 400x300 photograph, with a render of seed 42 under v1."""
    photo = tmp_path / "ada.png"
    photo.write_bytes(_arm())
    run = open_run(photo, wired.runs_root)
    Image.new("RGB", ARM, (90, 90, 90)).save(rendered_image(run, 1, SEED))
    return run


def _staged(library: Path, client: TestClient, body: bytes) -> str:
    """Return the id of an open import holding `body` as the staged file `bow.png`."""
    staged = client.post("/api/staging").json()["id"]
    (library / STAGING / staged / "bow.png").write_bytes(body)
    return staged


def _upload(library: Path, client: TestClient, name: str = "bow") -> None:
    """Keep a tattoo called `name`, the arm's picture, and close its outline."""
    staged = _staged(library, client, _arm())
    kept = client.post(
        "/api/tattoos", json={"staging": staged, "file": "bow.png", "name": name}
    )
    assert kept.status_code == 200, kept.text
    outline = {
        "points": _around(34, 24),
        "closed": True,
        "white": 1.0,
        "neutral": True,
        "depth": 1.6,
    }
    assert client.put(f"/api/tattoos/{name}/outline", json=outline).status_code == 200


def _cut(client: TestClient, run: Run, name: str = "arm") -> None:
    """Cut a tattoo called `name` from `run`'s photograph."""
    made = client.post(
        f"/api/c/{COLLECTION}/tattoos",
        json={"name": name, "digest": run.digest, "flow": FLOW},
    )
    assert made.status_code == 200, made.text


def _stage1(digest: str, name: str = "bow") -> str:
    """Return the stage-1 route of `name` on the photograph `digest`."""
    return f"/api/tattoos/{name}/stage1/{digest}"


def _ask(run: Run, target: str, pairs: object, **more: object) -> dict[str, object]:
    """Return a preview's body on `run`'s render of seed 42."""
    return {
        "target": target,
        "digest": run.digest,
        "flow": FLOW,
        "version": "v1",
        "seed": str(SEED),
        "edit": None,
        "pairs": pairs,
        "limb": None,
        "exclusions": [],
    } | more


def _preview(client: TestClient, name: str, body: dict[str, object]) -> httpx2.Response:
    """Post a preview of tattoo `name`."""
    return client.post(f"/api/c/{COLLECTION}/tattoos/{name}/preview", json=body)


@pytest.mark.spec("tattoo:stage1:pairs-are-saved-as-they-are-sent")
def test_placement_route_stage1_put_saves_what_is_sent_and_get_reads_it(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _upload(library, client)
    pairs = _pairs(6, ONTO_PHOTO)
    at = _stage1(photographed.digest)

    saved = client.put(at, json={"pairs": pairs, "not_on_photo": False})
    more = client.put(
        at, json={"pairs": [*pairs, [[5, 5], [9, 9]]], "not_on_photo": True}
    )
    read = client.get(at)

    assert saved.status_code == more.status_code == read.status_code == 200
    assert saved.json() == {"pairs": pairs, "not_on_photo": False}
    assert read.json() == more.json()
    assert len(read.json()["pairs"]) == 7
    assert read.json()["not_on_photo"] is True


@pytest.mark.spec("tattoo:stage1:a-photograph-with-no-file-has-no-pairs")
def test_placement_route_stage1_get_of_a_photograph_never_placed_is_empty(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _upload(library, client)
    before = snapshot(library)

    read = client.get(_stage1(photographed.digest))

    assert read.json() == {"pairs": [], "not_on_photo": False}
    assert snapshot(library) == before
    assert not (library / TATTOOS / "bow" / STAGE1).exists()


@pytest.mark.spec("tattoo:stage1:the-picker-is-told-each-tattoos-state")
def test_placement_route_stage1_the_list_carries_each_states_on_the_digest_asked(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _upload(library, client, "bow")
    _upload(library, client, "wing")
    _upload(library, client, "plain")
    pairs = _pairs(6, ONTO_PHOTO)
    client.put(
        _stage1(photographed.digest), json={"pairs": pairs, "not_on_photo": False}
    )
    client.put(
        _stage1(photographed.digest, "wing"), json={"pairs": [], "not_on_photo": True}
    )

    listed = client.get(f"/api/tattoos?digest={photographed.digest}").json()

    assert listed["stage1"] == {
        "bow": {"pairs": pairs, "not_on_photo": False},
        "wing": {"pairs": [], "not_on_photo": True},
    }
    assert "stage1" not in client.get("/api/tattoos").json()
    assert client.get("/api/tattoos?digest=ffffffffffff").json()["stage1"] == {}


@pytest.mark.spec("tattoo:stage1:a-bad-point-is-refused")
def test_placement_route_stage1_refuses_as_every_refusal_does_and_leaves_the_file(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _upload(library, client)
    at = _stage1(photographed.digest)
    client.put(at, json={"pairs": _pairs(6, ONTO_PHOTO), "not_on_photo": False})
    file = library / TATTOOS / "bow" / STAGE1 / f"{photographed.digest}.json"
    before = file.read_bytes()

    negative = client.put(
        at, json={"pairs": [[[1, 1], [-2, 2]]], "not_on_photo": False}
    )
    outside = client.put(
        at, json={"pairs": [[[401, 1], [2, 2]]], "not_on_photo": False}
    )
    short = client.put(at, json={"pairs": []})
    ghost = client.put(
        _stage1(photographed.digest, "ghost"), json={"pairs": [], "not_on_photo": False}
    )
    wrong = client.put(_stage1("nope"), json={"pairs": [], "not_on_photo": False})

    assert negative.status_code == outside.status_code == 409
    assert "pair 1 holds (-2, 2)" in negative.json()["refusal"]
    assert "pair 1's tattoo point (401, 1)" in outside.json()["refusal"]
    assert short.status_code == 409
    assert "not_on_photo" in short.json()["refusal"]
    assert "ghost" in ghost.json()["refusal"]
    assert "no photograph's digest" in wrong.json()["refusal"]
    assert file.read_bytes() == before


@pytest.mark.spec("tattoo:stage1:a-cut-takes-no-stage-1-file")
def test_placement_route_stage1_a_cut_is_refused(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _cut(client, photographed)

    refused = client.put(
        _stage1(photographed.digest, "arm"),
        json={"pairs": _pairs(6, ONTO_PHOTO), "not_on_photo": False},
    )

    assert refused.status_code == 409
    assert "already in the photograph's pixels" in refused.json()["refusal"]
    assert not (library / TATTOOS / "arm" / STAGE1).exists()


@pytest.mark.spec("tattoo:placement-preview:a-jpeg-on-the-crop-of-the-targets-points")
def test_placement_route_preview_answers_a_jpeg_on_the_crop_its_box_header_names(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _upload(library, client)
    pairs = _pairs(6, ONTO_PHOTO)

    answered = _preview(client, "bow", _ask(photographed, "photo", pairs))

    assert answered.status_code == 200, answered.text
    assert answered.headers["content-type"] == "image/jpeg"
    x, y, width, height = (int(n) for n in answered.headers["x-preview-box"].split(","))
    assert 0 <= x and 0 <= y and x + width <= ARM[0] and y + height <= ARM[1]
    assert (width, height) != ARM
    with Image.open(io.BytesIO(answered.content)) as shown:
        assert shown.format == "JPEG"
        assert shown.size == (width, height)
    grey = answered.headers["x-ink-white"]
    assert grey.isdigit() and 0 <= int(grey) <= 255


@pytest.mark.spec("tattoo:placement-preview:the-ink-is-white-where-nothing-lands")
def test_placement_route_preview_of_the_render_stage_reads_the_stage_one_file(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _upload(library, client)
    client.put(
        _stage1(photographed.digest),
        json={"pairs": _pairs(6, ONTO_PHOTO), "not_on_photo": False},
    )
    stage2 = _pairs(6, ONTO_RENDER, ONTO_PHOTO)

    answered = _preview(client, "bow", _ask(photographed, "render", stage2))

    assert answered.status_code == 200, answered.text
    x, y, _, _ = (int(n) for n in answered.headers["x-preview-box"].split(","))
    with Image.open(io.BytesIO(answered.content)) as shown:
        landed = (CENTRE[0] + 45 - x, CENTRE[1] + 30 - y)
        ink, bare = shown.getpixel(landed), shown.getpixel((2, 2))
        assert isinstance(ink, tuple) and isinstance(bare, tuple)
        assert min(ink) < 128
        assert min(bare) > 250
    short = client.put(
        _stage1(photographed.digest),
        json={"pairs": _pairs(4, ONTO_PHOTO), "not_on_photo": False},
    )
    assert short.status_code == 200
    refused = _preview(client, "bow", _ask(photographed, "render", stage2))
    assert refused.status_code == 409
    assert "stage 1 holds 4 pairs" in refused.json()["refusal"]


@pytest.mark.spec("tattoo:placement-preview:a-cut-is-carried-by-one-stage")
def test_placement_route_preview_of_a_cut_needs_no_stage_one_file(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _cut(client, photographed)
    client.put(
        "/api/tattoos/arm/outline",
        json={
            "points": _around(34, 24),
            "closed": True,
            "white": 1.0,
            "neutral": True,
            "depth": 1.6,
        },
    )

    answered = _preview(
        client, "arm", _ask(photographed, "render", _pairs(4, ONTO_RENDER))
    )

    assert answered.status_code == 200, answered.text
    assert not (library / TATTOOS / "arm" / STAGE1).exists()


@pytest.mark.spec("tattoo:placement-preview:the-answer-is-kept-nowhere")
def test_placement_route_preview_is_no_store_and_writes_nothing(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _upload(library, client)
    before = snapshot(library)

    answered = _preview(
        client, "bow", _ask(photographed, "photo", _pairs(6, ONTO_PHOTO))
    )

    assert answered.headers["cache-control"] == "no-store"
    assert snapshot(library) == before


@pytest.mark.spec("tattoo:bake-chain:a-bake-on-a-baked-edit-chains")
def test_placement_route_preview_on_a_baked_edit_reads_that_edits_image(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _upload(library, client)
    group = photographed.directory(FLOW, "outputs", "001")
    image, _, _ = edit_files(group, SEED, 1)
    Image.new("RGB", (200, 150), (90, 90, 90)).save(image)
    body = _ask(photographed, "photo", _pairs(6, (10, 10)), edit=1)

    answered = _preview(client, "bow", body)

    assert answered.status_code == 200, answered.text
    x, y, width, height = (int(n) for n in answered.headers["x-preview-box"].split(","))
    assert (width, height) != ARM


@pytest.mark.spec("tattoo:bake-chain:a-pending-edit-cannot-be-placed-on")
def test_placement_route_preview_on_an_edit_with_no_image_is_refused(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _upload(library, client)
    group = photographed.directory(FLOW, "outputs", "001")
    edit_files(group, SEED, 1)[1].write_text("{}")
    before = snapshot(library)

    pending = _preview(
        client, "bow", _ask(photographed, "photo", _pairs(6, ONTO_PHOTO), edit=1)
    )

    assert pending.status_code == 409
    assert "edit 1 of 42 has no image yet" in pending.json()["refusal"]
    assert snapshot(library) == before


@pytest.mark.spec_exempt(
    "structural: a body missing a key, a lone point, a bad seed or edit and an "
    "unknown flow are refused"
)
@pytest.mark.parametrize(
    ("more", "match"),
    [
        ({"seed": "4x2"}, "is no seed"),
        ({"seed": "43"}, "no render is here"),
        ({"version": "x"}, "names no version"),
        ({"flow": "nowhere"}, "nowhere"),
        ({"edit": 0}, "no edit's number"),
        ({"edit": "1"}, "no edit's number"),
        ({"edit": True}, "no edit's number"),
        ({"target": "sky"}, "`photo` or `render`"),
        ({"pairs": [[[1, 2], None]] * 3}, "has a point with no match"),
        ({"pairs": _pairs(2, ONTO_PHOTO)}, "at least 3 pairs and this holds 2"),
    ],
)
def test_placement_route_preview_refuses_a_bad_body_as_every_refusal_does(
    library: Path,
    client: TestClient,
    photographed: Run,
    more: dict[str, Any],
    match: str,
) -> None:
    _upload(library, client)
    body = _ask(photographed, "photo", _pairs(6, ONTO_PHOTO)) | more

    refused = _preview(client, "bow", body)

    assert refused.status_code == 409
    assert match in refused.json()["refusal"]


@pytest.mark.spec_exempt("structural: a preview names what a body lacks")
def test_placement_route_preview_names_each_key_a_body_lacks(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _upload(library, client)

    refused = _preview(client, "bow", {"target": "photo"})

    assert refused.status_code == 409
    for key in ("digest", "flow", "version", "seed", "pairs", "limb", "exclusions"):
        assert key in refused.json()["refusal"]


def _bake(
    client: TestClient, name: str, run: Run, pairs: object, **more: object
) -> httpx2.Response:
    """Post a bake of tattoo `name` on `run`'s render of seed 42."""
    body = {k: v for k, v in _ask(run, "render", pairs).items() if k != "target"}
    return client.post(f"/api/c/{COLLECTION}/tattoos/{name}/bake", json=body | more)


def _stage1_held(client: TestClient, run: Run) -> None:
    """Save six stage-1 pairs of `bow` on `run`'s photograph."""
    saved = client.put(
        _stage1(run.digest),
        json={"pairs": _pairs(6, ONTO_PHOTO), "not_on_photo": False},
    )
    assert saved.status_code == 200, saved.text


@pytest.mark.spec(
    "tattoo:bake:a-bake-writes-the-composite-the-placement-and-the-record"
)
def test_placement_route_bake_queues_the_composite_the_placement_and_the_record(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _upload(library, client)
    _stage1_held(client, photographed)
    group = photographed.directory(FLOW, "outputs", "001")
    before = snapshot(library)

    baked = _bake(client, "bow", photographed, _pairs(8, ONTO_RENDER, ONTO_PHOTO))

    assert baked.status_code == 200, baked.text
    assert baked.json() == {"edit": 1}
    image, record, composite = edit_files(group, SEED, 1)
    added = set(snapshot(library)) - set(before)
    assert {Path(name).name for name in added} == {
        record.name,
        composite.name,
        placement_file(group, SEED, 1).name,
    }
    assert not image.exists()
    placement = read(placement_file(group, SEED, 1), PLACEMENT_FILE)
    assert (placement["tattoo"], placement["mode"]) == ("bow", "two-stage")
    assert placement["places_on"] is None
    assert placement["stage1"] == _pairs(6, ONTO_PHOTO)
    assert read(record, EDIT_FILE)["source"] == f"{SEED}.png"
    with Image.open(composite) as kept:
        assert kept.size == ARM


@pytest.mark.spec("tattoo:bake-chain:a-bake-on-a-baked-edit-chains")
def test_placement_route_bake_on_a_baked_edit_is_placed_on_that_edit(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _upload(library, client)
    _stage1_held(client, photographed)
    group = photographed.directory(FLOW, "outputs", "001")
    stage2 = _pairs(8, ONTO_RENDER, ONTO_PHOTO)
    assert _bake(client, "bow", photographed, stage2).status_code == 200
    Image.new("RGB", ARM, (90, 90, 90)).save(edit_files(group, SEED, 1)[0])

    chained = _bake(client, "bow", photographed, stage2, edit=1)

    assert chained.status_code == 200, chained.text
    assert chained.json() == {"edit": 2}
    assert read(placement_file(group, SEED, 2), PLACEMENT_FILE)["places_on"] == 1
    assert (
        read(edit_files(group, SEED, 2)[1], EDIT_FILE)["source"] == f"{SEED}.edit-1.png"
    )
    assert read(placement_file(group, SEED, 1), PLACEMENT_FILE)["places_on"] is None


@pytest.mark.spec("tattoo:bake-chain:a-pending-edit-cannot-be-placed-on")
def test_placement_route_bake_on_an_edit_with_no_image_is_refused_and_writes_nothing(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _upload(library, client)
    _stage1_held(client, photographed)
    group = photographed.directory(FLOW, "outputs", "001")
    edit_files(group, SEED, 1)[1].write_text("{}")
    before = snapshot(library)

    pending = _bake(
        client, "bow", photographed, _pairs(8, ONTO_RENDER, ONTO_PHOTO), edit=1
    )

    assert pending.status_code == 409
    assert "edit 1 of 42 has no image yet" in pending.json()["refusal"]
    assert snapshot(library) == before


@pytest.mark.spec("tattoo:bake:a-bake-short-of-its-floor-writes-nothing")
def test_placement_route_bake_a_stage_short_of_its_floor_is_refused_and_writes_nothing(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _upload(library, client)
    _stage1_held(client, photographed)
    before = snapshot(library)

    short = _bake(client, "bow", photographed, _pairs(7, ONTO_RENDER, ONTO_PHOTO))

    assert short.status_code == 409
    assert "at least 8 pairs" in short.json()["refusal"]
    assert snapshot(library) == before


@pytest.mark.spec("tattoo:bake:the-photograph-never-enters-the-run")
def test_placement_route_bake_of_a_cut_copies_no_photograph_into_the_run(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _cut(client, photographed)
    client.put(
        "/api/tattoos/arm/outline",
        json={
            "points": _around(34, 24),
            "closed": True,
            "white": 1.0,
            "neutral": True,
            "depth": 1.6,
        },
    )
    before = snapshot(library)

    baked = _bake(client, "arm", photographed, _pairs(8, ONTO_RENDER))

    assert baked.status_code == 200, baked.text
    after = snapshot(library)
    added = {name: body for name, body in after.items() if name not in before}
    assert len(added) == 3
    assert _arm() not in added.values()
    assert {name: after[name] for name in before} == before


@pytest.mark.spec_exempt(
    "structural: a bake names what a body lacks and refuses a bad one"
)
def test_placement_route_bake_refuses_a_body_lacking_a_key_or_naming_no_render(
    library: Path, client: TestClient, photographed: Run
) -> None:
    _upload(library, client)
    before = snapshot(library)

    lacking = client.post(f"/api/c/{COLLECTION}/tattoos/bow/bake", json={"seed": "42"})
    absent = _bake(client, "bow", photographed, _pairs(8, ONTO_RENDER), seed="43")

    assert lacking.status_code == 409
    for key in ("digest", "flow", "version", "pairs", "limb", "exclusions"):
        assert key in lacking.json()["refusal"]
    assert absent.status_code == 409
    assert "no render is here" in absent.json()["refusal"]
    assert snapshot(library) == before


def _taking_away(app: FastAPI) -> list[str]:
    """Return each route under `/api` that names a tattoo and deletes or renames one."""
    found = []
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", None) or set()
        if "/tattoos" not in path:
            continue
        if methods & {"DELETE", "PATCH"} or any(
            word in path for word in ("delete", "remove", "rename")
        ):
            found.append(f"{sorted(methods)} {path}")
    return found


def _placement_routes(app: FastAPI) -> list[tuple[str, str]]:
    """Return the method and path of each route that places a tattoo."""
    return [
        (method, getattr(route, "path", ""))
        for route in app.routes
        if "/stage1/" in getattr(route, "path", "")
        or getattr(route, "path", "").endswith(("/preview", "/bake"))
        for method in sorted(getattr(route, "methods", None) or ())
        if method != "HEAD"
    ]


@pytest.mark.spec("tattoo:library:no-route-deletes-or-renames")
def test_placement_route_guard_no_route_naming_a_tattoo_deletes_or_renames_one(
    client: TestClient,
) -> None:
    app = client.app
    assert isinstance(app, FastAPI)

    assert _taking_away(app) == []
    assert sorted(_placement_routes(app)) == [
        ("GET", "/api/tattoos/{name}/stage1/{digest}"),
        ("POST", "/api/c/{collection}/tattoos/{name}/bake"),
        ("POST", "/api/c/{collection}/tattoos/{name}/preview"),
        ("PUT", "/api/tattoos/{name}/stage1/{digest}"),
    ]


@pytest.mark.spec("tattoo:library:no-route-deletes-or-renames")
def test_placement_route_guard_twin_finds_a_delete_under_a_placement_route(
    client: TestClient,
) -> None:
    app = client.app
    assert isinstance(app, FastAPI)

    app.add_api_route(
        "/api/tattoos/{name}/stage1/{digest}",
        lambda name, digest: {},
        methods=["DELETE"],
    )
    app.add_api_route(
        "/api/c/{collection}/tattoos/{name}/rename", lambda name: {}, methods=["POST"]
    )

    taken = _taking_away(app)
    assert len(taken) == 2
    assert any("DELETE" in line for line in taken)
    assert any("rename" in line for line in taken)


@pytest.mark.spec("tattoo:ink-view:a-request-from-another-site-is-refused")
def test_placement_route_guard_answers_each_new_route_before_its_handler(
    client: TestClient,
) -> None:
    app = client.app
    assert isinstance(app, FastAPI)
    routes = _placement_routes(app)
    assert len(routes) == 4

    for method, path in routes:
        url = (
            path.replace("{collection}", COLLECTION)
            .replace("{name}", "bow")
            .replace("{digest}", "0123456789ab")
        )
        elsewhere = client.request(
            method, url, headers={"Origin": "http://evil.example"}
        )
        rebound = client.request(method, url, headers={"Host": "evil.example"})

        assert elsewhere.status_code == 403, (method, path)
        assert rebound.status_code == 403, (method, path)
