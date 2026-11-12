"""The bytes of every run file kind, and the one module that may write them.

A golden file per kind pins what today's writers produce, so moving the shapes
into one contract is proven to move no byte. The tripwire is an AST scan like
`tests/test_layers.py`'s.
"""

import ast
import io
import random
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from isekai.boundary.comfy import read_runtime
from isekai.foundation.artifacts import DRAFT_FILE, PlacementValues, read
from isekai.foundation.edit import load_edit
from isekai.foundation.flow import Schema
from isekai.foundation.run import (
    OUTPUTS,
    Run,
    open_run,
    placement_file,
    record_failure,
)
from isekai.interface.render import Record
from isekai.pipeline.caption import READER_OPTIONS, FakeReader
from isekai.pipeline.edit import Requested, request_placed
from isekai.pipeline.generate import prompt_artifact, render
from isekai.pipeline.review import approve, review, save_draft
from isekai.pipeline.tagging import TAGGER_OPTIONS, FakeTagger, tag_hosted, tag_wd14
from isekai.shared.vocabulary import Vocabulary
from tests.fakes import READER_ARTIFACTS, SESSION_IMAGE, FakeComfyClient
from tests.images import jpeg_bytes
from tests.stages import FLOW, caption, fake_tagger, sheet

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN = Path(__file__).resolve().parent / "golden"

# The module that owns every run file's shape, and so the one that writes them.
CONTRACT = "isekai/foundation/artifacts.py"

# The call that writes a run file by hand.
WRITER = "write_json"

# The call that writes bytes, and the modules that call it for a byte or a library
# file and never a run file, each with what it writes.
BYTE_WRITER = "write_atomically"
BYTE_WRITERS = {
    "isekai/foundation/run.py": "the photograph's copy",
    "isekai/interface/compare_view.py": "the comparison page",
    "isekai/interface/ui/library.py": "a thumbnail or an upright source",
    "isekai/pipeline/edit.py": "an edit's composite and its stitched image",
    "isekai/pipeline/generate.py": "a render's image",
    "isekai/pipeline/importing.py": "an imported source image",
    "isekai/pipeline/review.py": "a source image's copy",
    "isekai/pipeline/tattoos.py": "a tattoo library's outline, files and stage record",
    "isekai/shared/ink.py": "an ink layer's image",
}


# --- the golden bytes ---------------------------------------------------------


def _run(tmp_path: Path) -> Run:
    photo = tmp_path / "ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    return open_run(photo, tmp_path / "runs")


def _frame(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    return run.frame_path


def _error(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    directory = run.directory(FLOW.id, OUTPUTS, "001")
    return record_failure(
        directory,
        1,
        "transient",
        {"stage": "render", "seed": 42, "detail": "the endpoint did not answer"},
    )


# The caption and tags goldens hold a pinned producer's keys.
def _caption(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    reader = FakeReader(
        prose="Brown hair, brown eyes.",
        artifacts=READER_ARTIFACTS,
        options=READER_OPTIONS,
    )
    path = caption(run, reader)
    assert path is not None
    return path


def _wd14(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    path = tag_wd14(run, fake_tagger)
    assert path is not None
    return path


def _tags(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    tagger = FakeTagger(artifacts=READER_ARTIFACTS, options=TAGGER_OPTIONS)
    path = tag_hosted(run, tagger)
    assert path is not None
    return path


def _sheet(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    path = sheet(run, schema, vocabulary)
    assert path is not None
    return path


def _sheet_empty(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    path = sheet(run, schema, vocabulary, tags=None, tagged=False)
    assert path is not None
    return path


def _draft(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    _sheet(run, schema, vocabulary)
    path = review(run, FLOW.id)
    assert path is not None
    return path


def _draft_saved(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    draft = _draft(run, schema, vocabulary)
    fields = {name: list(tags) for name, tags in _fields(draft).items()}
    fields["expression"] = []
    save_draft(run, FLOW.id, fields)
    return draft


def _approved(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    # From an edited draft, so this golden pins `edited: true`; the edit's own
    # rewrite is `draft-saved`'s.
    _draft_saved(run, schema, vocabulary)
    path, _ = approve(run, FLOW.id, schema, vocabulary)
    assert path is not None
    return path


def _fields(path: Path) -> dict[str, list[str]]:
    return read(path, DRAFT_FILE)["fields"]


def _prompt(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    _approved(run, schema, vocabulary)
    return prompt_artifact(run, FLOW, schema)


def _render(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    _prompt(run, schema, vocabulary)
    client = FakeComfyClient()
    (made,) = render(
        run,
        FLOW,
        client,
        image=SESSION_IMAGE,
        runtime=lambda: read_runtime(client),
        seeds=[42],
        poll=0,
        clock=iter([10.0, 72.5]).__next__,
    )
    return made.provenance


# The edit and the placement come from `tests/test_edit_placement.py`'s inputs,
# restated: a flat render, and a composite that multiplies the tattoo's square.
SKIN = (200, 150, 120)
SIDE = 400
INKED = slice(80, 120)
RENDER_SEED = 42
SESSION_ID = "20261024T091200Z"


def _png(pixels: "np.ndarray") -> bytes:
    body = io.BytesIO()
    Image.fromarray(pixels).save(body, "PNG")
    return body.getvalue()


def _flat_render(factor: float = 1.0) -> "np.ndarray":
    """Return a flat render, its tattoo's square multiplied by `factor`."""
    pixels = np.full((SIDE, SIDE, 3), SKIN, dtype=np.uint8)
    square = pixels[INKED, INKED].astype(np.float32) * factor
    pixels[INKED, INKED] = (square + 0.5).astype(np.uint8)
    return pixels


def _values() -> PlacementValues:
    return {
        "tattoo": "swallow",
        "kind": "image",
        "cut_from": None,
        "mode": "two-stage",
        "outline": {
            "points": [[0.0, 0.0], [40.0, 0.0], [40.0, 40.0]],
            "white": 1.0,
            "neutral": False,
            "depth": 1.0,
        },
        "stage1": [[[1.0, 2.0], [3.0, 4.0]]],
        "pairs": [[[5.0, 6.0], [7.0, 8.0]]],
        "limb": None,
        "exclusions": [],
    }


def _placed(run: Run) -> Requested:
    group = run.directory(FLOW.id, OUTPUTS, "001")
    group.mkdir(parents=True)
    source = group / f"{RENDER_SEED}.png"
    source.write_bytes(_png(_flat_render()))
    return request_placed(
        load_edit("tattoo-wai"),
        source,
        _png(_flat_render(0.5)),
        _values(),
        overrides={},
        seed=5,
        rng=random.Random(1),
    )


def _edit(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    return _placed(run).record


def _placement(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    asked = _placed(run)
    return placement_file(asked.composite.parent, RENDER_SEED, asked.number)


def _session(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    # Not ended: `end` reads the clock.
    folder = run.path.parent / "sessions"
    record = Record(folder, SESSION_ID, 1200, {FLOW.id: 1})
    record.open(datetime(2026, 10, 24, 9, 12, tzinfo=UTC))
    record.step("pod", "ready")
    record.image({"digest": "a" * 64, "flow": FLOW.id, "version": 1, "seed": 42})
    record.close()
    return folder / f"{SESSION_ID}.json"


# Each kind, and the production path that writes it from fixed inputs.
KINDS: dict[str, Callable[[Run, Schema, Vocabulary], Path]] = {
    "run": _frame,
    "error": _error,
    "caption": _caption,
    "wd14": _wd14,
    "tags": _tags,
    "sheet": _sheet,
    "sheet-empty": _sheet_empty,
    "draft": _draft,
    "draft-saved": _draft_saved,
    "approved": _approved,
    "prompt": _prompt,
    "render": _render,
    "edit": _edit,
    "placement": _placement,
    "session": _session,
}


def written(kind: str, tmp_path: Path, schema: Schema, vocabulary: Vocabulary) -> bytes:
    """Return the bytes today's writer produces for `kind`."""
    return KINDS[kind](_run(tmp_path), schema, vocabulary).read_bytes()


@pytest.mark.spec_exempt(
    "structural: the bytes each writer produces are pinned before the contract "
    "changes it"
)
@pytest.mark.parametrize("kind", sorted(KINDS))
def test_each_kind_is_written_byte_for_byte(
    kind: str, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    golden = (GOLDEN / f"{kind}.json").read_bytes()
    assert written(kind, tmp_path, schema, vocabulary) == golden


# --- the tripwire -------------------------------------------------------------


def json_writers(root: Path) -> set[str]:
    """Return every module under `root/isekai` that writes a run file by hand.

    A call to `write_atomically` counts unless the module is in `BYTE_WRITERS`.
    e.g. a module calling `write_json(...)` -> `isekai/pipeline/sheet.py`
    """
    found: set[str] = set()
    for name, tree in _modules(root):
        if name == CONTRACT:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            called = _called(node.func)
            if called == WRITER or (called == BYTE_WRITER and name not in BYTE_WRITERS):
                found.add(name)
    return found


def _modules(root: Path) -> Iterator[tuple[str, ast.Module]]:
    """Yield each module under `root/isekai`, by its repository path, parsed."""
    for path in sorted((root / "isekai").rglob("*.py")):
        name = path.relative_to(root).as_posix()
        yield name, ast.parse(path.read_text(), filename=str(path))


def _called(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


@pytest.mark.spec_exempt("structural: the scan reads the contract and the modules")
def test_the_scan_reads_the_contract() -> None:
    assert CONTRACT in {name for name, _ in _modules(REPO_ROOT)}


@pytest.mark.spec_exempt("structural: only the contract writes a run file")
def test_only_the_contract_writes_a_run_file() -> None:
    assert json_writers(REPO_ROOT) == set()


@pytest.mark.spec_exempt("structural: twin of test_only_the_contract_writes_a_run_file")
def test_the_check_catches_a_module_writing_json(tmp_path: Path) -> None:
    for name, text in {
        CONTRACT: "def write(path, kind, artifact):\n    write_json(path, artifact)\n",
        "isekai/pipeline/by_hand.py": "def f(run):\n    run.write_json(p, {})\n",
        "isekai/shared/direct.py": "def g():\n    write_json(p, {})\n",
        "isekai/pipeline/typed.py": "def h():\n    write(p, KIND, {})\n",
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    assert json_writers(tmp_path) == {
        "isekai/pipeline/by_hand.py",
        "isekai/shared/direct.py",
    }


@pytest.mark.spec_exempt("structural: twin of test_only_the_contract_writes_a_run_file")
def test_the_check_catches_a_byte_writer_outside_its_table(tmp_path: Path) -> None:
    table = next(iter(BYTE_WRITERS))
    for name, text in {
        CONTRACT: "def write(path, body):\n    write_atomically(path, body)\n",
        table: "def f(p, b):\n    write_atomically(p, b)\n",
        "isekai/pipeline/loose.py": "def g(p, b):\n    write_atomically(p, b)\n",
        "isekai/shared/dotted.py": "def h(p, b):\n    atomic.write_atomically(p, b)\n",
        "isekai/shared/reads.py": "def i(p):\n    return p.read_bytes()\n",
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    assert json_writers(tmp_path) == {
        "isekai/pipeline/loose.py",
        "isekai/shared/dotted.py",
    }


# --- the annotation -----------------------------------------------------------

# The contract's writers. `ty` checks an artifact key by key only when the caller
# annotated it, so the guard below makes the annotation a rule.
TYPED_WRITERS = ("write", "create", "replace")
_FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _annotated_target(node: ast.AST) -> str | None:
    """Return the name or `self.<name>` an annotated assignment binds, else None."""
    if not isinstance(node, ast.AnnAssign):
        return None
    target = node.target
    if isinstance(target, ast.Name):
        return target.id
    if (
        isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
        and target.value.id == "self"
    ):
        return f"self.{target.attr}"
    return None


def _class_attributes(tree: ast.Module) -> dict[int, set[str]]:
    """Map each method's id to the `self.<name>` attributes its class annotates."""
    inherited: dict[int, set[str]] = {}
    for cls in ast.walk(tree):
        if not isinstance(cls, ast.ClassDef):
            continue
        attributes = {
            target
            for node in ast.walk(cls)
            if (target := _annotated_target(node)) and target.startswith("self.")
        }
        for method in ast.walk(cls):
            if isinstance(method, _FUNCTIONS):
                inherited[id(method)] = attributes
    return inherited


def unannotated_writes(root: Path) -> set[str]:
    """Return each typed-writer call under `root/isekai` with an unannotated artifact.

    Annotated means a name bound by an annotated assignment in the same function, or
    a `self.<name>` that any method of the same class annotates.
    e.g. `write(p, KIND, {})` on line 3 of `isekai/x.py` -> `isekai/x.py:3`
    """
    found: set[str] = set()
    for name, tree in _modules(root):
        inherited = _class_attributes(tree)
        for scope in ast.walk(tree):
            if not isinstance(scope, _FUNCTIONS):
                continue
            annotated = {
                target
                for node in ast.walk(scope)
                if (target := _annotated_target(node))
            } | inherited.get(id(scope), set())
            for node in ast.walk(scope):
                if not (
                    isinstance(node, ast.Call)
                    and _called(node.func) in TYPED_WRITERS
                    and len(node.args) == 3
                ):
                    continue
                artifact = node.args[2]
                if not (
                    isinstance(artifact, (ast.Name, ast.Attribute))
                    and ast.unparse(artifact) in annotated
                ):
                    found.add(f"{name}:{node.lineno}")
    return found


@pytest.mark.spec_exempt("structural: every run file's writer annotates its artifact")
def test_every_write_gets_an_annotated_artifact() -> None:
    assert unannotated_writes(REPO_ROOT) == set()


@pytest.mark.spec_exempt(
    "structural: twin of test_every_write_gets_an_annotated_artifact"
)
def test_the_check_catches_a_bare_literal(tmp_path: Path) -> None:
    for name, text in {
        "isekai/pipeline/typed.py": (
            "def f(p):\n    frame: Frame = {}\n    write(p, KIND, frame)\n"
        ),
        "isekai/pipeline/bare.py": "def g(p):\n    write(p, KIND, {})\n",
        "isekai/pipeline/unannotated.py": (
            "def h(p):\n    frame = {}\n    write(p, KIND, frame)\n"
        ),
        "isekai/foundation/stream.py": "def i(sink):\n    sink.write(b'')\n",
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    assert unannotated_writes(tmp_path) == {
        "isekai/pipeline/bare.py:2",
        "isekai/pipeline/unannotated.py:3",
    }


@pytest.mark.spec_exempt(
    "structural: twin of test_every_write_gets_an_annotated_artifact"
)
def test_the_check_learns_a_classs_annotated_attribute(tmp_path: Path) -> None:
    path = tmp_path / "isekai/interface/session.py"
    path.parent.mkdir(parents=True)
    path.write_text(
        "class Record:\n"
        "    def __init__(self, p):\n"
        "        self._body: SessionRecord = {}\n"
        "        self._loose = {}\n"
        "    def start(self, p):\n"
        "        create(p, KIND, self._body)\n"
        "    def end(self, p):\n"
        "        replace(p, KIND, self._loose)\n"
        "        replace(p, KIND, {})\n"
    )
    assert unannotated_writes(tmp_path) == {
        "isekai/interface/session.py:8",
        "isekai/interface/session.py:9",
    }
