"""The bytes of every run file kind, and the one module that may write them.

A golden file per kind pins what today's writers produce, so moving the shapes
into one contract is proven to move no byte. The tripwire is an AST scan like
`tests/test_layers.py`'s. Why and how: `0028` design D8 and D9.
"""

import ast
from collections.abc import Callable
from pathlib import Path

import pytest

from isekai.foundation.artifacts import DRAFT_FILE, read
from isekai.foundation.flow import Schema, load_flow
from isekai.foundation.run import OUTPUTS, Run, open_run, record_failure
from isekai.pipeline.caption import FakeReader
from isekai.pipeline.generate import prompt_artifact, render
from isekai.pipeline.review import approve, review, save_draft
from isekai.pipeline.tagging import FakeTagger, caption_tags, caption_wd14
from isekai.shared.vocabulary import Vocabulary
from tests.fakes import FakeComfyClient
from tests.images import jpeg_bytes
from tests.stages import FLOW, caption, fake_tagger, sheet

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN = Path(__file__).resolve().parent / "golden"

# The module that owns every run file's shape, and so the one that writes them.
CONTRACT = "isekai/foundation/artifacts.py"

# The call that writes a run file by hand.
WRITER = "write_json"


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


def _caption(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    path = caption(run, FakeReader(prose="Brown hair, brown eyes."))
    assert path is not None
    return path


def _wd14(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    path = caption_wd14(run, FLOW.id, fake_tagger)
    assert path is not None
    return path


def _tags(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    path = caption_tags(run, FLOW.id, FakeTagger())
    assert path is not None
    return path


def _sheet(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    path = sheet(run, schema, vocabulary)
    assert path is not None
    return path


def _draft(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    _sheet(run, schema, vocabulary)
    path = review(run, FLOW.id)
    assert path is not None
    return path


def _approved(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    draft = _draft(run, schema, vocabulary)
    # An edit, so `save_draft`'s rewrite and `edited: true` are both pinned.
    fields = {name: list(tags) for name, tags in _fields(draft).items()}
    fields["expression"] = []
    save_draft(run, FLOW.id, fields)
    path, _ = approve(run, FLOW.id, schema, vocabulary)
    assert path is not None
    return path


def _fields(path: Path) -> dict[str, list[str]]:
    return read(path, DRAFT_FILE)["fields"]


def _prompt(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    _approved(run, schema, vocabulary)
    return prompt_artifact(run, load_flow(FLOW.id), schema)


def _render(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    _prompt(run, schema, vocabulary)
    (made,) = render(run, load_flow(FLOW.id), FakeComfyClient(), seeds=[42], poll=0)
    return made.provenance


# Each kind, and the production path that writes it from fixed inputs.
KINDS: dict[str, Callable[[Run, Schema, Vocabulary], Path]] = {
    "run": _frame,
    "error": _error,
    "caption": _caption,
    "wd14": _wd14,
    "tags": _tags,
    "sheet": _sheet,
    "draft": _draft,
    "approved": _approved,
    "prompt": _prompt,
    "render": _render,
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

    e.g. a module calling `write_json(...)` -> `isekai/pipeline/sheet.py`
    """
    found: set[str] = set()
    for path in sorted((root / "isekai").rglob("*.py")):
        name = path.relative_to(root).as_posix()
        if name == CONTRACT:
            continue
        for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
            if isinstance(node, ast.Call) and _called(node.func) == WRITER:
                found.add(name)
    return found


def _called(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


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
