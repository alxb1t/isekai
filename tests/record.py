"""The record: whole outputs of one offline pass, written as JSON a test re-derives.

`uv run python -m tests.record` runs the pass and writes `tests/record/*.json`. A file
changes only when a person runs it; `tests/test_record.py` derives each file again into
a temporary directory and compares.
"""

import argparse
import dataclasses
import hashlib
import io
import json
import math
import os
import random
import re
import shutil
import tempfile
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response
from PIL import Image

from isekai.boundary.comfy import ComfyTransport
from isekai.foundation.artifacts import RENDER_FILE, read
from isekai.foundation.edit import load_edit
from isekai.foundation.flow import Workflow, graph_digest
from isekai.foundation.run import Run, open_run
from isekai.interface.cli import build_parser
from isekai.interface.cli import main as cli
from isekai.interface.ui import HOST
from isekai.interface.ui.app import create_app
from isekai.interface.wiring import Wiring
from isekai.pipeline.edit import request
from tests.e2e.wiring import fake
from tests.fakes import FakeComfyClient, RecordingComfyClient
from tests.images import jpeg_bytes, photo_jpeg

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORD = Path(__file__).resolve().parent / "record"
FIRST_FLOW = "summon-anime-wai"
FLOWS = (
    FIRST_FLOW,
    *sorted(
        path.name
        for path in (REPO_ROOT / "flows").iterdir()
        if path.is_dir() and path.name != FIRST_FLOW
    ),
)
SEED = 42
EDIT_SEED = 5
SIDE = 400
SKIN = (200, 150, 120)
SAMPLED = (10, 200, 30)
CROP_SIDE = 1216
# The tattoo's square, as rows and columns of the render.
INKED = slice(80, 120)
WIRING = "tests.record:wiring"
REGENERATE = "run uv run python -m tests.record and read the diff"

# The factory is called with the runs root alone, so the client is module state.
CLIENT: ComfyTransport | None = None
OUTS: list[io.StringIO] = []
ERRS: list[io.StringIO] = []


@dataclass(frozen=True)
class Done:
    """What one pass leaves: where it ran, its clients, and what each verb said."""

    root: Path
    library: Path
    collection: Path
    runs: Path
    run: Run
    renders: FakeComfyClient
    edits: RecordingComfyClient
    said: dict[str, str]


FILES: dict[str, Callable[[Done], object]] = {}


def dump(value: object) -> str:
    """Return a record file's text: indented, keys sorted, one final newline."""
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def recorded(name: str) -> object:
    """Return the JSON a committed record file holds."""
    return json.loads((RECORD / f"{name}.json").read_text())


def derive(done: Done) -> dict[str, str]:
    """Return each record file's text by name, in the order they were registered."""
    return {name: dump(value(done)) for name, value in FILES.items()}


def differing(directory: Path, derived: dict[str, str]) -> list[str]:
    """Return the names whose committed text is not the derived text, sorted.

    A file with no derivation, and a derivation with no file, count as differing.
    """
    committed = {path.stem: path.read_text() for path in directory.glob("*.json")}
    return sorted(
        name
        for name in committed.keys() | derived.keys()
        if committed.get(name) != derived.get(name)
    )


def write(directory: Path) -> None:
    """Run the pass and write each record file under `directory`."""
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as made:
        derived = derive(offline(Path(made)))
    for path in directory.glob("*.json"):
        if path.stem not in derived:
            path.unlink()
    for name, text in derived.items():
        (directory / f"{name}.json").write_text(text)


def main() -> int:
    """Write the record into `tests/record/`."""
    write(RECORD)
    print(f"wrote {', '.join(sorted(FILES))} under {RECORD.relative_to(REPO_ROOT)}")
    return 0


def wiring(*, runs: Path) -> Wiring:
    """Return the browser tests' wiring over `runs`, on the pass's client."""
    out, err = io.StringIO(), io.StringIO()
    OUTS.append(out)
    ERRS.append(err)
    return dataclasses.replace(fake(runs=runs), client=CLIENT, out=out, err=err)


@contextmanager
def using(client: ComfyTransport) -> Iterator[None]:
    """Name the pass's wiring in the environment with `client`, then restore both."""
    global CLIENT
    held, named = CLIENT, os.environ.get("ISEKAI_WIRING")
    os.environ["ISEKAI_WIRING"] = WIRING
    CLIENT = client
    try:
        yield
    finally:
        CLIENT = held
        if named is None:
            os.environ.pop("ISEKAI_WIRING", None)
        else:
            os.environ["ISEKAI_WIRING"] = named


def run_verb(done: Done, client: ComfyTransport, verb: str, *argv: str) -> str:
    """Run `verb` through the CLI over the pass's runs and return what it printed."""
    seen = len(OUTS)
    with using(client):
        status = cli([verb, *argv, "--runs", str(done.runs)])
    printed = "".join(out.getvalue() for out in OUTS[seen:])
    told = "".join(err.getvalue() for err in ERRS[seen:])
    assert status == 0, f"{verb} exited {status}: {told}"
    return printed


def drive(done: Done) -> None:
    """Run every verb of a run over every flow, keeping each verb's stdout in `done`."""
    photo = str(done.collection / "sources" / "ada.jpg")
    flows = [part for flow in FLOWS for part in ("--flow", flow)]
    json_lines = ("--progress", "json")
    steps = (
        ("caption", (photo,)),
        ("tag", (photo,)),
        ("assign", (done.run.id, *flows)),
        ("sheet", (done.run.id, *flows, *json_lines)),
        ("review", (done.run.id, *flows)),
        ("approve", (done.run.id, *flows)),
        ("generate", (done.run.id, *flows, "--seed", str(SEED), *json_lines)),
    )
    for verb, argv in steps:
        done.said[verb] = run_verb(done, done.renders, verb, *argv)


def png(pixels: "np.ndarray") -> bytes:
    """Return `pixels` encoded as a PNG."""
    body = io.BytesIO()
    Image.fromarray(pixels).save(body, "PNG")
    return body.getvalue()


def offline(root: Path) -> Done:
    """Run the whole pass under `root` and return what it left."""
    library = root / "lib"
    collection = library / "record"
    runs = collection / "runs"
    sources = collection / "sources"
    sources.mkdir(parents=True)
    photo = sources / "ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    render = png(np.full((SIDE, SIDE, 3), SKIN, dtype=np.uint8))
    crop = png(np.full((CROP_SIDE, CROP_SIDE, 3), SAMPLED, dtype=np.uint8))
    done = Done(
        root=root,
        library=library,
        collection=collection,
        runs=runs,
        run=open_run(photo, runs),
        renders=FakeComfyClient(view_bytes=render),
        edits=RecordingComfyClient(view_bytes=crop),
        said={},
    )
    drive(done)
    edit(done)
    return done


def edit(done: Done) -> None:
    """Request an edit of the first flow's render and sample it on the edit client."""
    image = done.run.path / FIRST_FLOW / "outputs" / "001" / f"{SEED}.png"
    composite = np.asarray(Image.open(image).convert("RGB")).copy()
    composite[INKED, INKED] = (composite[INKED, INKED] * 0.5 + 0.5).astype(np.uint8)
    kept = done.root / "composite.png"
    kept.write_bytes(png(composite))
    request(
        load_edit("tattoo-wai"),
        image,
        kept,
        overrides={},
        seed=EDIT_SEED,
        rng=random.Random(1),
    )
    cell = f"{done.run.id}/{FIRST_FLOW}"
    done.said["edit"] = run_verb(done, done.edits, "edit", "--pending", cell)
    held = {node["class_type"] for node in done.edits.submissions[-1].values()}
    assert "SetUnionControlNetType" in held, "the edit client saw no edit graph"


def graphs(done: Done) -> dict[str, object]:
    """Return every flow's submitted graph and the edit's.

    A graph is its flow's when the digest in the flow's render record names it.
    """
    submitted = {graph_digest(graph): graph for graph in done.renders.submissions}
    assert len(submitted) == len(FLOWS), "the render client did not see every flow"
    flows: dict[str, Workflow] = {}
    for flow in FLOWS:
        record = done.run.path / flow / "outputs" / "001" / f"{SEED}.render.json"
        flows[flow] = submitted[read(record, RENDER_FILE)["graph_sha256"]]
    return {"flows": flows, "edit": done.edits.submissions[-1]}


FILES["graphs"] = graphs


def normalised(value: object, root: Path) -> object:
    """Return `value` with each `duration` set to 0.0 and `root` written `<root>`.

    The resolved spelling of `root` is rewritten before the given one, so a
    temporary directory under `/var` and one under `/private/var` read the same.
    e.g. {"duration": 1.5} -> {"duration": 0.0}, "<given>/a.jpg" -> "<root>/a.jpg"
    """
    if isinstance(value, dict):
        return {
            key: _zeroed(item) if key == "duration" else normalised(item, root)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [normalised(item, root) for item in value]
    if isinstance(value, str):
        return value.replace(str(root.resolve()), "<root>").replace(str(root), "<root>")
    return value


def _zeroed(seconds: object) -> float:
    """Return 0.0 for a number of seconds, and refuse anything else."""
    assert isinstance(seconds, int | float) and not isinstance(seconds, bool), seconds
    return 0.0


def entry(path: Path, root: Path) -> dict[str, object]:
    """Return a file's record: its JSON, its PNG's pixels, or its bytes' digest."""
    if path.suffix == ".json":
        return {"json": normalised(json.loads(path.read_text()), root)}
    if path.suffix == ".png":
        with Image.open(path) as image:
            pixels = hashlib.sha256()
            pixels.update(f"{image.mode} {image.size[0]}x{image.size[1]}".encode())
            pixels.update(image.tobytes())
        return {"pixels": pixels.hexdigest()}
    return {"bytes": hashlib.sha256(path.read_bytes()).hexdigest()}


def paths(done: Done) -> dict[str, object]:
    """Return every file under the runs root, by relative path, with its entry."""
    return {
        str(path.relative_to(done.runs)): entry(path, done.root)
        for path in sorted(done.runs.rglob("*"))
        if path.is_file()
    }


FILES["run"] = paths


def relative(default: object) -> object:
    """Return `default`, a path inside the repository written relative to it.

    A path outside the repository names a machine, and is refused.
    e.g. REPO_ROOT / ".data" / "runs" -> ".data/runs"
    """
    if not isinstance(default, Path):
        return default
    try:
        return default.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        raise ValueError(f"{default} is outside the repository") from None


def _argument(action: argparse.Action) -> dict[str, object]:
    """Return one argument as the record holds it, with no help text."""
    return {
        "dest": action.dest,
        "flags": action.option_strings,
        "nargs": action.nargs,
        "required": action.required,
        "default": relative(action.default),
        "choices": None if action.choices is None else list(action.choices),
        "type": None if action.type is None else cast("type", action.type).__name__,
        "metavar": action.metavar,
        "action": type(action).__name__,
    }


def walk(parser: argparse.ArgumentParser) -> dict[str, object]:
    """Return each verb of `parser` with its positionals, options and exclusive groups.

    e.g. {"sheet": {"positionals": [...], "options": [...], "groups": []}}
    """
    verbs: dict[str, object] = {}
    for action in parser._actions:
        if not isinstance(action, argparse._SubParsersAction):
            continue
        chosen = cast("dict[str, argparse.ArgumentParser]", action.choices)
        for name, verb in chosen.items():
            verbs[name] = {
                "positionals": [
                    _argument(each) for each in verb._actions if not each.option_strings
                ],
                "options": [
                    _argument(each) for each in verb._actions if each.option_strings
                ],
                "groups": [
                    {
                        "required": group.required,
                        "members": [each.dest for each in group._group_actions],
                    }
                    for group in verb._mutually_exclusive_groups
                ],
            }
    return verbs


def flags(done: Done) -> dict[str, object]:
    """Return every verb of the CLI's parser, walked."""
    del done
    return walk(build_parser())


FILES["verbs"] = flags


def shape(value: object) -> object:
    """Return the keys and types of `value`, and no value.

    A list is its first element's shape in a list, `[]` when empty.
    e.g. {"a": [{"b": 1}], "c": None} -> {"a": [{"b": "int"}], "c": "null"}
    """
    if isinstance(value, dict):
        return {key: shape(item) for key, item in value.items()}
    if isinstance(value, list):
        return [shape(value[0])] if value else []
    return "null" if value is None else type(value).__name__


PORT = 8765
POLL_SECONDS = 10.0
POLL_PAUSE = 0.02
BUNDLE_PAGE = "<!doctype html>"

Seen = dict[str, Any]
Fill = Callable[[Done, Seen], Mapping[str, object]]
Body = Callable[[Done, Seen], object]


def _nothing(done: Done, seen: Seen) -> dict[str, object]:
    return {}


def _no_body(done: Done, seen: Seen) -> None:
    return None


@dataclass(frozen=True)
class Call:
    """One request of the routes' pass.

    `fill` names the template's braces and `query` its parameters; `body` is the
    JSON, or the bytes of a file. `setup` runs first and is not recorded, so a call
    that consumes a staging opens its own. `polled` repeats the call until it
    answers 200, for a file an upload reads on a thread.
    """

    method: str
    template: str
    fill: Fill = _nothing
    body: Body = _no_body
    query: Fill = _nothing
    setup: tuple["Call", ...] = ()
    polled: bool = False

    @property
    def key(self) -> str:
        """Return `"<METHOD> <template>"`, the route this call is recorded under."""
        return f"{self.method} {self.template}"


# Routes that need a running child, so the record leaves them out.
CHILD_ROUTES = frozenset(
    {
        "POST /api/c/{collection}/prepare",
        "POST /api/render",
        "GET /api/sessions/running",
        "GET /api/c/{collection}/sessions/{name}",
        "GET /events",
    }
)


def served(done: Done) -> TestClient:
    """Return a client over the app, serving a copy of the pass's library.

    The copy lives under the pass's directory, so no call changes what the run's
    record reads. The wiring is the browser tests', the bundle a one-line page.
    """
    held = Path(tempfile.mkdtemp(prefix="served-", dir=done.root))
    library = held / "lib"
    shutil.copytree(done.library, library)
    bundle = held / "bundle"
    bundle.mkdir()
    (bundle / "index.html").write_text(BUNDLE_PAGE)
    wired = fake(runs=library / done.collection.name / "runs")
    app = create_app(
        library,
        wired,
        flows=FLOWS,
        bundle=bundle,
        wire=lambda runs: dataclasses.replace(wired, runs_root=runs),
        host=HOST,
        port=PORT,
    )
    return TestClient(app, base_url=f"http://{HOST}:{PORT}")


def _url(template: str, names: Mapping[str, object]) -> str:
    """Return `template` with each brace filled, a `:path` converter ignored.

    e.g. "/api/{rest:path}", {"rest": "a/b"} -> "/api/a/b"
    """
    return re.sub(r"\{(\w+)(?::\w+)?\}", lambda hit: str(names[hit[1]]), template)


def _send(client: TestClient, call: Call, done: Done, seen: Seen) -> Response:
    """Send `call` and return the response."""
    body = call.body(done, seen)
    return client.request(
        call.method,
        _url(call.template, call.fill(done, seen)),
        params={key: str(value) for key, value in call.query(done, seen).items()},
        content=body if isinstance(body, bytes) else None,
        json=None if isinstance(body, bytes) else body,
    )


def answer(client: TestClient, call: Call, done: Done, seen: Seen) -> dict[str, object]:
    """Run `call` after its setup, keep its JSON in `seen`, and return its record.

    The record is the status and the shape of a JSON answer, or the media type of
    another.
    """
    for before in call.setup:
        answer(client, before, done, seen)
    response = _send(client, call, done, seen)
    deadline = time.monotonic() + POLL_SECONDS
    while call.polled and response.status_code != 200 and time.monotonic() < deadline:
        time.sleep(POLL_PAUSE)
        response = _send(client, call, done, seen)
    kind = response.headers.get("content-type", "").split(";")[0]
    if kind == "application/json":
        seen[call.key] = response.json()
        return {"status": response.status_code, "shape": shape(seen[call.key])}
    seen[call.key] = None
    return {"status": response.status_code, "media_type": kind}


CENTRE = (200, 150)
ONTO_PHOTO = (30, 20)
ONTO_RENDER = (15, 10)
TATTOO = "bow"
CUT = "arm"
GRACE = "grace.jpg"
SECOND = "second"
VERSION = "v1"
OTHER_FLOW = FLOWS[1]
DRAFT_FLOW = FLOWS[2]
CORRECTED_SEED = 7

REVIEW = "/api/c/{collection}/review/{digest}/{flow}"
RENDER = "/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}"
COMPARE = "/compare/{other_flow}/{other_version}/{other_seed}"
EDIT = "/edit/{k}"
STAGED = "/api/staging/{staged}"
STAGED_FILE = "/api/staging/{staged}/files/{name}"
TATTOOS = "/api/c/{collection}/tattoos/{name}"
STAGE1 = "/api/tattoos/{name}/stage1/{digest}"


def _around(radius: float, count: int) -> list[list[float]]:
    """Return `count` points on a circle of `radius` round the tattoo's centre."""
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


def _arm() -> bytes:
    """Return a PNG of flat skin with one dark square, a tattoo an upload keeps."""
    arm = np.full((300, 400, 3), SKIN, dtype=np.uint8)
    arm[130:170, 180:220] = (40, 30, 30)
    return png(arm)


def _render(**more: object) -> Fill:
    """Return a fill naming the pass's first flow's render, `more` beside it."""
    return lambda done, seen: {
        "collection": done.collection.name,
        "digest": done.run.digest,
        "flow": FIRST_FLOW,
        "version": VERSION,
        "seed": str(SEED),
        **more,
    }


def _digest(done: Done, seen: Seen) -> dict[str, object]:
    return {"digest": done.run.digest}


def _staging(name: str) -> Fill:
    """Return a fill naming the file `name` in the staging last opened."""
    return lambda done, seen: {"staged": seen["POST /api/staging"]["id"], "name": name}


def _tattoo(done: Done, seen: Seen) -> dict[str, object]:
    return {"name": TATTOO, "digest": done.run.digest}


def _tattoo_in_run(done: Done, seen: Seen) -> dict[str, object]:
    return {"collection": done.collection.name, "name": TATTOO}


def _ring_body(done: Done, seen: Seen) -> dict[str, object]:
    return {
        "points": _around(34, 24),
        "closed": True,
        "white": 1.0,
        "neutral": True,
        "depth": 1.6,
    }


def _ink_body(done: Done, seen: Seen) -> dict[str, object]:
    return {
        "points": _around(34, 24),
        "white": 1.0,
        "neutral": True,
        "depth": 1.6,
        "digest": done.run.digest,
        "flow": FIRST_FLOW,
    }


def _placed(done: Done, seen: Seen, **more: object) -> dict[str, object]:
    """Return a placement's body on the pass's first render, `more` beside it."""
    return {
        "digest": done.run.digest,
        "flow": FIRST_FLOW,
        "version": VERSION,
        "seed": str(SEED),
        **more,
    }


def _preview_body(done: Done, seen: Seen) -> dict[str, object]:
    return _placed(
        done,
        seen,
        target="photo",
        edit=None,
        pairs=_pairs(6, ONTO_PHOTO),
        limb=None,
        exclusions=[],
    )


def _bake_body(done: Done, seen: Seen) -> dict[str, object]:
    return _placed(
        done,
        seen,
        edit=None,
        pairs=_pairs(8, ONTO_RENDER, ONTO_PHOTO),
        limb=None,
        exclusions=[],
    )


def _propose_body(done: Done, seen: Seen) -> dict[str, object]:
    return _placed(done, seen, points=[[100, 105], [140, 95]])


def _stage1_body(done: Done, seen: Seen) -> dict[str, object]:
    return {"pairs": _pairs(6, ONTO_PHOTO), "not_on_photo": False}


def _draft_body(done: Done, seen: Seen) -> dict[str, object]:
    image = {"digest": done.run.digest, "flow": FIRST_FLOW, "version": 1}
    return {"flow": DRAFT_FLOW, "images": [{**image, "seed": str(SEED)}]}


def _correction(done: Done, seen: Seen) -> dict[str, object]:
    """Return a draft's update: the first flow's fields, and a seed to render."""
    return {
        "fields": seen[f"GET {REVIEW}"]["fields"],
        "renders": {"count": 1, "seeds": [str(CORRECTED_SEED)]},
    }


def _draft_version(done: Done, seen: Seen) -> dict[str, object]:
    drafted = seen["POST /api/c/{collection}/draft"]["drafts"][0]["draft"]
    return {**_render(flow=DRAFT_FLOW)(done, seen), "version": int(drafted[:3])}


def _imported(done: Done, seen: Seen) -> dict[str, object]:
    return {"collection": SECOND, "name": GRACE}


def _upload(name: str, body: bytes) -> tuple[Call, ...]:
    """Return the calls that open a staging, upload `body` to it and wait for it."""
    return (
        Call("POST", "/api/staging"),
        Call(
            "PUT",
            STAGED_FILE,
            _staging(name),
            lambda done, seen: body,
        ),
        Call("GET", STAGED_FILE, _staging(name), polled=True),
    )


CALLS: list[Call] = [
    Call("GET", "/api/library"),
    Call("GET", "/api/c/{collection}/hub", _render()),
    Call("GET", "/api/tags", query=lambda done, seen: {"q": "hair"}),
    Call("GET", "/api/fields", query=lambda done, seen: {"flow": FIRST_FLOW}),
    Call("GET", REVIEW, _render()),
    Call("GET", f"{REVIEW}/photo", _render()),
    Call("GET", RENDER, _render()),
    Call(
        "GET",
        f"{RENDER}{COMPARE}",
        _render(other_flow=OTHER_FLOW, other_version=VERSION, other_seed=str(SEED)),
    ),
    Call("GET", f"{RENDER}/compare/photo", _render()),
    Call("GET", f"{RENDER}/image", _render()),
    Call("GET", f"{RENDER}/thumb", _render()),
    Call("GET", f"{RENDER}{EDIT}", _render(k="1")),
    Call("GET", f"{RENDER}{EDIT}/image", _render(k="1")),
    Call("GET", f"{RENDER}{EDIT}/thumb", _render(k="1")),
    Call("GET", "/api/c/{collection}/render", _render()),
    Call("GET", "/api/{rest:path}", _render(rest="nowhere")),
    Call("GET", "/{rest:path}", _render(rest="library")),
]

CALLS += [
    Call(
        "POST",
        "/api/c/{collection}/assign",
        _render(),
        lambda done, seen: {"flow": FIRST_FLOW, "sources": ["ada.jpg"]},
    ),
    Call("POST", "/api/c/{collection}/draft", _render(), _draft_body),
    Call("GET", f"{REVIEW}/source/{{version}}", _draft_version),
    Call("PUT", f"{REVIEW}/draft", _render(flow=DRAFT_FLOW), _correction),
    Call("POST", f"{REVIEW}/approve", _render(flow=DRAFT_FLOW)),
    Call("POST", f"{REVIEW}/cancel", _render(flow=DRAFT_FLOW)),
    Call("POST", f"{REVIEW}/discard", _render(flow=DRAFT_FLOW)),
    Call(
        "POST",
        "/api/c/{collection}/place/propose",
        _render(),
        _propose_body,
    ),
    Call(
        "POST",
        "/api/render/quote",
        body=lambda done, seen: {"collections": [done.collection.name]},
    ),
    Call("POST", "/api/billing/check"),
    Call("POST", "/api/jobs/{kind}/stop", lambda done, seen: {"kind": "render"}),
]

CALLS += [
    *_upload(GRACE, photo_jpeg(SKIN, (640, 480))),
    Call("GET", f"{STAGED_FILE}/thumb", _staging(GRACE)),
    Call(
        "POST",
        f"{STAGED}/commit",
        lambda done, seen: {"staged": seen["POST /api/staging"]["id"]},
        lambda done, seen: {"collection": SECOND, "as_is": [], "add": False},
    ),
    Call("GET", "/api/c/{collection}/sources/{name}", _imported),
    Call("GET", "/api/c/{collection}/sources/{name}/thumb", _imported),
    Call(
        "POST",
        "/api/tattoos",
        setup=_upload("bow.png", _arm()),
        body=lambda done, seen: {
            "staging": seen["POST /api/staging"]["id"],
            "file": "bow.png",
            "name": TATTOO,
        },
    ),
    Call(
        "POST",
        "/api/c/{collection}/tattoos",
        _render(),
        lambda done, seen: {
            "name": CUT,
            "digest": done.run.digest,
            "flow": FIRST_FLOW,
        },
    ),
    Call("GET", "/api/tattoos", query=_digest),
    Call("GET", "/api/tattoos/{name}", _tattoo, query=_digest),
    Call("GET", "/api/tattoos/{name}/design", _tattoo, query=_digest),
    Call("PUT", "/api/tattoos/{name}/outline", _tattoo, _ring_body, _digest),
    Call("GET", STAGE1, _tattoo),
    Call("PUT", STAGE1, _tattoo, _stage1_body),
    Call("POST", f"{TATTOOS}/ink", _tattoo_in_run, _ink_body),
    Call("POST", f"{TATTOOS}/preview", _tattoo_in_run, _preview_body),
    Call("POST", f"{TATTOOS}/bake", _tattoo_in_run, _bake_body),
]

CALLS += [
    Call("DELETE", RENDER, _render(flow=OTHER_FLOW)),
    Call("DELETE", "/api/tattoos/{name}", _tattoo, query=_digest),
    Call(
        "DELETE",
        STAGED_FILE,
        _staging("bow.png"),
        setup=_upload("bow.png", _arm()),
    ),
    Call("DELETE", STAGED, _staging("bow.png"), setup=_upload("bow.png", _arm())),
]


def routed(app: FastAPI) -> list[str]:
    """Return `"<METHOD> <template>"` for each route of `app` that answers a method."""
    return sorted(
        f"{method} {getattr(route, 'path', '')}"
        for route in app.routes
        if not _framework(route)
        for method in getattr(route, "methods", None) or ()
        if method != "HEAD"
    )


def _framework(route: object) -> bool:
    """Return whether `route` is the framework's, such as `/openapi.json`."""
    module = getattr(getattr(route, "endpoint", None), "__module__", "")
    return module.startswith(("fastapi.", "starlette."))


def uncovered(app: FastAPI) -> list[str]:
    """Return the routes of `app` that no call covers and none is left to a child."""
    held = {call.key for call in CALLS} | CHILD_ROUTES
    return [route for route in routed(app) if route not in held]


def answers(done: Done) -> dict[str, object]:
    """Run `CALLS` in order over a copy of the library; return each answer by route."""
    seen: Seen = {}
    recorded_answers: dict[str, object] = {}
    with served(done) as client:
        for call in CALLS:
            assert call.key not in recorded_answers, f"{call.key} is called twice"
            recorded_answers[call.key] = answer(client, call, done, seen)
    return recorded_answers


FILES["routes"] = answers


if __name__ == "__main__":
    # The wiring factory is imported as `tests.record`, so the pass runs in that
    # copy of the module and not in `__main__`, where `CLIENT` would never be set.
    import importlib

    raise SystemExit(importlib.import_module("tests.record").main())
