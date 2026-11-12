"""The propose route over the test client: its body, its answer, its guard.

The pairs themselves are proved in `tests/test_proposal.py` and `tests/test_propose.py`;
here the route's own work is: what it reads, what it refuses, what it answers, and that
it writes nothing.
"""

import io
import random
from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

import httpx2
import numpy as np
import pytest
from numpy.typing import NDArray

pytest.importorskip("fastapi")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

from isekai.boundary import pose as pose_boundary  # noqa: E402
from isekai.boundary import sam2 as sam2_boundary  # noqa: E402
from isekai.boundary.pose import Pose  # noqa: E402
from isekai.boundary.unpack import PLACEMENT_REMEDY  # noqa: E402
from isekai.foundation.run import Run, open_run  # noqa: E402
from isekai.interface.ui import HOST  # noqa: E402
from isekai.interface.ui.app import create_app  # noqa: E402
from isekai.interface.wiring import Wiring  # noqa: E402
from isekai.pipeline.proposing import Proposer  # noqa: E402
from isekai.shared.vocabulary import Vocabulary  # noqa: E402
from tests.conftest import snapshot  # noqa: E402
from tests.fakes import FakePoseFinder, FakeSegmenter  # noqa: E402
from tests.stages import FIELD_MAP, NO_GPUNIT, rendered_image  # noqa: E402

COLLECTION = "2026-10-19"
FLOW = "summon-anime-wai"
PORT = 8765
ADDRESS = f"http://{HOST}:{PORT}"
SIZE = (400, 300)
SEED = 42
HALF = 10
PROPOSE = f"/api/c/{COLLECTION}/place/propose"

Point = tuple[float, float]

LEFT = {5: (50.0, 100.0), 7: (150.0, 100.0), 9: (250.0, 100.0)}


def _pose() -> Pose:
    """Return a pose of one left arm along y=100, every score 0.9."""
    points = tuple(LEFT.get(index, (10.0, 10.0)) for index in range(17))
    return Pose((0.0, 0.0, 400.0, 300.0), points, (0.9,) * 17)


def _band(
    size: tuple[int, int], positive: Sequence[Point], negative: Sequence[Point]
) -> NDArray[np.bool_]:
    """Paint the rows within `HALF` of the positives' mean height."""
    width, height = size
    middle = round(sum(y for _, y in positive) / len(positive))
    mask = np.zeros((height, width), dtype=bool)
    mask[middle - HALF : middle + HALF + 1] = True
    return mask


class _Models:
    """The fake models a wiring hands out, and what they were asked."""

    def __init__(self, *, found: bool = True) -> None:
        self.opened = 0
        self.poses: list[FakePoseFinder] = []
        self._found = found

    def __call__(self) -> Proposer:
        """Open a proposer over fresh fakes: a pose for each image."""
        self.opened += 1
        pose = FakePoseFinder(_pose(), _pose() if self._found else None)
        self.poses.append(pose)
        return Proposer(pose, FakeSegmenter(_band))


@pytest.fixture
def library(tmp_path: Path) -> Path:
    """Return a library holding one empty collection."""
    (tmp_path / "lib" / COLLECTION / "sources").mkdir(parents=True)
    return tmp_path / "lib"


@pytest.fixture
def wired(library: Path, vocabulary: Vocabulary) -> Wiring:
    """Return a wiring over the collection with no proposer."""
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
def models() -> _Models:
    """Return the fake models, which count their opening."""
    return _Models()


def _app(
    wired: Wiring,
    library: Path,
    tmp_path: Path,
    proposer: Callable[[], Proposer] | None,
) -> TestClient:
    """Return a client over the application with `proposer` as its wiring's."""
    dist = tmp_path / "dist"
    dist.mkdir(exist_ok=True)
    (dist / "index.html").write_text("<!doctype html>")
    held = replace(wired, proposer=proposer)
    app = create_app(
        library,
        held,
        flows=(FLOW,),
        bundle=dist,
        wire=lambda runs: replace(held, runs_root=runs),
        host=HOST,
        port=PORT,
    )
    return TestClient(app, base_url=ADDRESS)


@pytest.fixture
def client(wired: Wiring, library: Path, tmp_path: Path, models: _Models) -> TestClient:
    """Return a client whose wiring proposes through the fake models."""
    return _app(wired, library, tmp_path, models)


def _photograph(path: Path, orientation: int = 1) -> None:
    """Write a JPEG of a 400x300 photograph, stored turned as `orientation` says."""
    stored = Image.new("RGB", SIZE, (200, 150, 120))
    if orientation == 6:
        stored = Image.new("RGB", SIZE[::-1], (200, 150, 120))
    exif = Image.Exif()
    exif[0x0112] = orientation
    stored.save(path, "JPEG", exif=exif)


@pytest.fixture
def photographed(wired: Wiring, tmp_path: Path) -> Run:
    """Return a run of a 400x300 photograph, with a render of seed 42 under v1."""
    photo = tmp_path / "ada.jpg"
    _photograph(photo)
    run = open_run(photo, wired.runs_root)
    Image.new("RGB", SIZE, (220, 220, 220)).save(rendered_image(run, 1, SEED))
    return run


def _body(run: Run, **more: object) -> dict[str, object]:
    """Return a propose body on `run`'s render of seed 42, points along the left arm."""
    return {
        "digest": run.digest,
        "flow": FLOW,
        "version": "v1",
        "seed": str(SEED),
        "points": [[100, 105], [140, 95]],
    } | more


def _ask(client: TestClient, body: dict[str, object]) -> httpx2.Response:
    return client.post(PROPOSE, json=body)


@pytest.mark.spec("placement-proposal:pairs:the-answer-is-kept-nowhere")
def test_propose_route_answers_the_arm_and_its_pairs_and_keeps_nothing(
    library: Path, client: TestClient, photographed: Run, models: _Models
) -> None:
    before = snapshot(library)

    answered = _ask(client, _body(photographed))

    assert answered.status_code == 200, answered.text
    assert answered.headers["cache-control"] == "no-store"
    assert snapshot(library) == before
    body = answered.json()
    assert body["arm"] == "left"
    assert body["pairs"]
    for pair in body["pairs"]:
        assert len(pair) == 2 and all(len(point) == 2 for point in pair)
    assert body["pairs"][-3:] == [[[x, y], [x, y]] for x, y in LEFT.values()]
    assert models.opened == 1


@pytest.mark.spec_exempt("structural: the photograph is read upright, the render as is")
def test_propose_route_reads_the_photograph_upright(
    tmp_path: Path, library: Path, wired: Wiring, models: _Models
) -> None:
    photo = tmp_path / "turned.jpg"
    _photograph(photo, orientation=6)
    run = open_run(photo, wired.runs_root)
    Image.new("RGB", SIZE, (220, 220, 220)).save(rendered_image(run, 1, SEED))
    client = _app(wired, library, tmp_path, models)

    answered = _ask(client, _body(run))

    assert answered.status_code == 200, answered.text
    seen, drawn = models.poses[0].seen
    assert seen.size == SIZE
    assert drawn.size == SIZE
    assert seen.mode == drawn.mode == "RGB"


@pytest.mark.spec(
    "placement-proposal:pairs:no-person-or-no-usable-bone-proposes-nothing"
)
def test_propose_route_no_person_in_the_render_is_an_empty_answer_not_a_refusal(
    wired: Wiring, library: Path, tmp_path: Path, photographed: Run
) -> None:
    client = _app(wired, library, tmp_path, _Models(found=False))

    answered = _ask(client, _body(photographed))

    assert answered.status_code == 200, answered.text
    assert answered.json() == {"arm": None, "pairs": []}


@pytest.mark.spec("placement-proposal:pairs:a-bad-point-is-refused")
@pytest.mark.parametrize(
    "points",
    [
        [],
        "x",
        [[-1, 5]],
        [[5, -0.5]],
        [["a", 5]],
        [[5]],
        [[1, 2, 3]],
        [[True, 5]],
        [None],
        [[1, 2], [3, "4"]],
    ],
)
def test_propose_route_a_bad_point_is_refused_and_no_model_is_opened(
    client: TestClient, photographed: Run, models: _Models, points: object
) -> None:
    refused = _ask(client, _body(photographed, points=points))

    assert refused.status_code == 409
    assert (
        "points" in refused.json()["refusal"] or "point " in refused.json()["refusal"]
    )
    assert models.opened == 0


@pytest.mark.spec("placement-proposal:pairs:a-bad-point-is-refused")
def test_propose_route_a_point_past_a_float_is_refused_naming_it(
    client: TestClient, photographed: Run, models: _Models
) -> None:
    text = (
        '{"digest": "%s", "flow": "%s", "version": "v1", "seed": "42", '
        '"points": [[1, 2], [1e999, 4]]}' % (photographed.digest, FLOW)
    )

    refused = client.post(
        PROPOSE, content=text, headers={"Content-Type": "application/json"}
    )

    assert refused.status_code == 409
    assert "point 2" in refused.json()["refusal"]
    assert models.opened == 0


@pytest.mark.spec_exempt(
    "structural: a body missing a key, a bad seed, a version or a flow is refused"
)
@pytest.mark.parametrize(
    ("more", "match"),
    [
        ({"seed": "4x2"}, "is no seed"),
        ({"seed": "43"}, "no render is here"),
        ({"version": "x"}, "names no version"),
        ({"flow": "nowhere"}, "nowhere"),
    ],
)
def test_propose_route_refuses_a_bad_render_as_every_refusal_does(
    client: TestClient,
    photographed: Run,
    models: _Models,
    more: dict[str, Any],
    match: str,
) -> None:
    refused = _ask(client, _body(photographed, **more))

    assert refused.status_code == 409
    assert match in refused.json()["refusal"]
    assert models.opened == 0


@pytest.mark.spec_exempt("structural: a propose names what a body lacks")
def test_propose_route_names_each_key_a_body_lacks(
    client: TestClient, photographed: Run
) -> None:
    refused = client.post(PROPOSE, json={"seed": "42"})

    assert refused.status_code == 409
    for key in ("digest", "flow", "version", "points"):
        assert key in refused.json()["refusal"]


@pytest.mark.spec_exempt("structural: a wiring with no proposer refuses the route")
def test_propose_route_a_wiring_with_no_proposer_refuses_saying_so(
    wired: Wiring, library: Path, tmp_path: Path, photographed: Run
) -> None:
    client = _app(wired, library, tmp_path, None)

    refused = _ask(client, _body(photographed))

    assert refused.status_code == 409
    assert "no proposer" in refused.json()["refusal"]


@pytest.mark.spec("placement-proposal:pairs:a-missing-model-refuses-naming-the-fetch")
def test_propose_route_unprovisioned_models_refuse_naming_the_fetch(
    wired: Wiring, library: Path, tmp_path: Path, photographed: Run
) -> None:
    empty = tmp_path / "models"

    def unprovisioned() -> Proposer:
        return Proposer(
            pose_boundary.open_pose(empty), sam2_boundary.open_segmenter(empty)
        )

    client = _app(wired, library, tmp_path, unprovisioned)
    before = snapshot(library)

    refused = _ask(client, _body(photographed))

    assert refused.status_code == 409
    assert PLACEMENT_REMEDY in refused.json()["refusal"]
    assert snapshot(library) == before


@pytest.mark.spec_exempt("structural: an unreadable render or photograph is refused")
def test_propose_route_an_unreadable_image_is_refused(
    client: TestClient, photographed: Run
) -> None:
    photographed.photo.write_bytes(b"not an image")

    refused = _ask(client, _body(photographed))

    assert refused.status_code == 409
    assert "the photograph cannot be read" in refused.json()["refusal"]


def _propose_routes(app: FastAPI) -> list[tuple[str, str]]:
    """Return the method and path of each route that proposes pairs."""
    return [
        (method, getattr(route, "path", ""))
        for route in app.routes
        if getattr(route, "path", "").endswith("/place/propose")
        for method in sorted(getattr(route, "methods", None) or ())
        if method != "HEAD"
    ]


@pytest.mark.spec("tattoo:ink-view:a-request-from-another-site-is-refused")
def test_propose_guard_answers_the_new_route_before_its_handler(
    client: TestClient, photographed: Run, models: _Models
) -> None:
    app = client.app
    assert isinstance(app, FastAPI)
    assert _propose_routes(app) == [("POST", "/api/c/{collection}/place/propose")]
    body = _body(photographed)

    elsewhere = client.post(
        PROPOSE, json=body, headers={"Origin": "http://evil.example"}
    )
    rebound = client.post(PROPOSE, json=body, headers={"Host": "evil.example"})

    assert elsewhere.status_code == 403
    assert rebound.status_code == 403
    assert models.opened == 0


@pytest.mark.spec("tattoo:ink-view:a-request-from-another-site-is-refused")
def test_propose_guard_twin_the_same_body_from_this_page_is_answered(
    client: TestClient, photographed: Run, models: _Models
) -> None:
    here = client.post(PROPOSE, json=_body(photographed), headers={"Origin": ADDRESS})

    assert here.status_code == 200, here.text
    assert models.opened == 1


@pytest.mark.spec("placement-proposal:pairs:the-answer-is-kept-nowhere")
def test_propose_guard_twin_a_route_that_writes_a_file_changes_the_snapshot(
    library: Path, client: TestClient
) -> None:
    app = client.app
    assert isinstance(app, FastAPI)
    before = snapshot(library)

    def writes() -> dict[str, object]:
        (library / COLLECTION / "kept.json").write_text("{}")
        return {}

    app.add_api_route("/api/c/writes", writes, methods=["POST"])
    client.post("/api/c/writes")

    assert snapshot(library) != before
