"""The record: whole outputs of one offline pass, written as JSON a test re-derives.

`uv run python -m tests.record` runs the pass and writes `tests/record/*.json`. A file
changes only when a person runs it; `tests/test_record.py` derives each file again into
a temporary directory and compares.
"""

import dataclasses
import hashlib
import io
import json
import os
import random
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from isekai.boundary.comfy import ComfyTransport
from isekai.foundation.artifacts import RENDER_FILE, read
from isekai.foundation.edit import load_edit
from isekai.foundation.flow import Workflow, graph_digest
from isekai.foundation.run import Run, open_run
from isekai.interface.cli import main as cli
from isekai.interface.wiring import Wiring
from isekai.pipeline.edit import request
from tests.e2e.wiring import fake
from tests.fakes import FakeComfyClient, RecordingComfyClient
from tests.images import jpeg_bytes

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


if __name__ == "__main__":
    # The wiring factory is imported as `tests.record`, so the pass runs in that
    # copy of the module and not in `__main__`, where `CLIENT` would never be set.
    import importlib

    raise SystemExit(importlib.import_module("tests.record").main())
