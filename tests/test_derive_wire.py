"""The page's wire is what `tools.derive_wire` writes from `shapes.py`."""

from pathlib import Path

import pytest
from _pytest.mark import ParameterSet

from tools.derive_wire import derive

SHAPES = "isekai/interface/ui/shapes.py"
PRELUDE = "from typing import Any, Literal, NotRequired, TypedDict\n\n"
HEADER = "/* Written by `tools/derive_wire.py` from `isekai/interface/ui/shapes.py`. */"
NO_EVENTS = "export interface Events {\n}"


def _tree(root: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


def _text(*blocks: str) -> str:
    return "\n\n".join([HEADER, *blocks, NO_EVENTS]) + "\n"


@pytest.mark.spec_exempt("structural: the tool writes each leaf and None")
def test_the_leaves_and_none_are_written(tmp_path: Path) -> None:
    shapes = PRELUDE + (
        "class Leaves(TypedDict):\n"
        "    a: str\n"
        "    b: int\n"
        "    c: float\n"
        "    d: bool\n"
        "    e: None\n"
    )
    root = _tree(tmp_path, {SHAPES: shapes})
    assert derive(root) == _text(
        "export interface Leaves {\n"
        "  a: string\n"
        "  b: number\n"
        "  c: number\n"
        "  d: boolean\n"
        "  e: null\n"
        "}"
    )


@pytest.mark.spec_exempt("structural: the tool writes a list as an array")
def test_a_list_is_an_array(tmp_path: Path) -> None:
    shapes = PRELUDE + (
        "class Bag(TypedDict):\n"
        "    names: list[str]\n"
        "    either: list[Literal['a', 'b']]\n"
        "    maybe: list[str | None]\n"
    )
    root = _tree(tmp_path, {SHAPES: shapes})
    assert derive(root) == _text(
        "export interface Bag {\n"
        "  names: string[]\n"
        "  either: ('a' | 'b')[]\n"
        "  maybe: (string | null)[]\n"
        "}"
    )


@pytest.mark.spec_exempt("structural: the tool writes a map by str as a record")
def test_a_map_by_str_is_a_record_of_strings(tmp_path: Path) -> None:
    shapes = PRELUDE + (
        "class Table(TypedDict):\n"
        "    counts: dict[str, int]\n"
        "    lists: dict[str, list[str]]\n"
        "    maybe: dict[str, int | None]\n"
    )
    root = _tree(tmp_path, {SHAPES: shapes})
    assert derive(root) == _text(
        "export interface Table {\n"
        "  counts: Record<string, number>\n"
        "  lists: Record<string, string[]>\n"
        "  maybe: Record<string, number | null>\n"
        "}"
    )


@pytest.mark.spec_exempt("structural: the tool writes a map by an alias as a record")
def test_a_map_by_an_alias_is_a_record_by_it(tmp_path: Path) -> None:
    files = {
        SHAPES: PRELUDE
        + "from isekai.pipeline import tattoos\n\n"
        + "class Table(TypedDict):\n    by: dict[tattoos.Kind, int]\n",
        "isekai/pipeline/tattoos.py": "Kind = Literal['image', 'cut']\n",
    }
    root = _tree(tmp_path, files)
    assert derive(root) == _text(
        "export type TattoosKind = 'image' | 'cut'",
        "export interface Table {\n  by: Record<TattoosKind, number>\n}",
    )


@pytest.mark.spec_exempt("structural: the tool writes NotRequired as an optional field")
def test_not_required_is_an_optional_field(tmp_path: Path) -> None:
    shapes = PRELUDE + (
        "class Maybe(TypedDict):\n"
        "    a: NotRequired[str]\n"
        "    b: NotRequired[list[str]]\n"
        "    c: int\n"
    )
    root = _tree(tmp_path, {SHAPES: shapes})
    assert derive(root) == _text(
        "export interface Maybe {\n  a?: string\n  b?: string[]\n  c: number\n}"
    )


@pytest.mark.spec_exempt("structural: the tool writes an inline Literal as its words")
def test_an_inline_literal_is_a_union_of_its_words(tmp_path: Path) -> None:
    shapes = PRELUDE + (
        "class Pick(TypedDict):\n"
        "    kind: Literal['revision', 're-roll'] | None\n"
        "    state: Literal['baked']\n"
    )
    root = _tree(tmp_path, {SHAPES: shapes})
    assert derive(root) == _text(
        "export interface Pick {\n"
        "  kind: 'revision' | 're-roll' | null\n"
        "  state: 'baked'\n"
        "}"
    )


@pytest.mark.spec_exempt("structural: an alias is named by its module and its name")
def test_an_alias_imported_through_its_module_is_named_by_both(tmp_path: Path) -> None:
    files = {
        SHAPES: PRELUDE
        + "from isekai.interface.ui import library\n\n"
        + "class Cell(TypedDict):\n    stage: library.Stage | None\n",
        "isekai/interface/ui/library.py": "Stage = Literal['assigned', 'tagged']\n",
    }
    root = _tree(tmp_path, files)
    assert derive(root) == _text(
        "export type LibraryStage = 'assigned' | 'tagged'",
        "export interface Cell {\n  stage: LibraryStage | null\n}",
    )


@pytest.mark.spec_exempt("structural: an alias imported by name takes its module's")
def test_an_alias_imported_by_its_own_name_is_named_by_its_module(
    tmp_path: Path,
) -> None:
    files = {
        SHAPES: PRELUDE
        + "from isekai.pipeline.review import Status\n\n"
        + "class Cell(TypedDict):\n    status: Status\n",
        "isekai/pipeline/review.py": "Status = Literal['draft', 'approved']\n",
    }
    root = _tree(tmp_path, files)
    assert derive(root) == _text(
        "export type ReviewStatus = 'draft' | 'approved'",
        "export interface Cell {\n  status: ReviewStatus\n}",
    )


@pytest.mark.spec_exempt("structural: an alias that nests another names it")
def test_an_alias_that_nests_another_names_it(tmp_path: Path) -> None:
    files = {
        SHAPES: PRELUDE
        + "from isekai.pipeline import importing\n\n"
        + "class File(TypedDict):\n    state: importing.Upload\n",
        "isekai/pipeline/importing.py": (
            "State = Literal['ready', 'skipped']\nUpload = Literal[State, 'waiting']\n"
        ),
    }
    root = _tree(tmp_path, files)
    assert derive(root) == _text(
        "export type ImportingState = 'ready' | 'skipped'\n"
        "export type ImportingUpload = ImportingState | 'waiting'",
        "export interface File {\n  state: ImportingUpload\n}",
    )


@pytest.mark.spec_exempt("structural: a base in the module is extended")
def test_a_base_in_the_module_is_extended(tmp_path: Path) -> None:
    shapes = PRELUDE + (
        "class Base(TypedDict):\n    a: str\n\n\nclass Child(Base):\n    b: int\n"
    )
    root = _tree(tmp_path, {SHAPES: shapes})
    assert derive(root) == _text(
        "export interface Base {\n  a: string\n}",
        "export interface Child extends Base {\n  b: number\n}",
    )


@pytest.mark.spec_exempt("structural: a base of another module is written, extended")
def test_a_base_in_another_module_is_written_and_extended(tmp_path: Path) -> None:
    files = {
        SHAPES: PRELUDE
        + "from isekai.foundation import artifacts\n\n"
        + "class Running(artifacts.Record):\n    collection: str\n",
        "isekai/foundation/artifacts.py": (
            "from typing import TypedDict\n\n\n"
            "class Block(TypedDict):\n    name: str\n\n\n"
            "class Record(TypedDict):\n    schema: Block\n"
        ),
    }
    root = _tree(tmp_path, files)
    assert derive(root) == _text(
        "export interface Block {\n  name: string\n}",
        "export interface Record {\n  schema: Block\n}",
        "export interface Running extends Record {\n  collection: string\n}",
    )


@pytest.mark.spec_exempt("structural: a class with no field is a record of nothing")
def test_an_empty_class_is_a_record_of_nothing(tmp_path: Path) -> None:
    shapes = PRELUDE + 'class Empty(TypedDict):\n    """An answer with no key."""\n'
    root = _tree(tmp_path, {SHAPES: shapes})
    assert derive(root) == _text("export type Empty = Record<string, never>")


@pytest.mark.spec_exempt("structural: the events map follows EVENTS in its order")
def test_the_events_map_follows_events(tmp_path: Path) -> None:
    shapes = PRELUDE + (
        "class A(TypedDict):\n    x: int\n\n\n"
        "class B(TypedDict):\n    y: int\n\n\n"
        "EVENTS: dict[str, Any] = {'second': B, 'first': A}\n"
    )
    root = _tree(tmp_path, {SHAPES: shapes})
    assert (
        derive(root)
        == "\n\n".join(
            [
                HEADER,
                "export interface A {\n  x: number\n}",
                "export interface B {\n  y: number\n}",
                "export interface Events {\n  second: B\n  first: A\n}",
            ]
        )
        + "\n"
    )


def _refusal(
    name: str, body: str, message: str, extra: dict[str, str] | None = None
) -> ParameterSet:
    files = {SHAPES: PRELUDE + body, **(extra or {})}
    return pytest.param(files, message, id=name)


ARTIFACTS_BLOCK = {
    "isekai/foundation/artifacts.py": "class Block(TypedDict):\n    name: str\n"
}


@pytest.mark.spec_exempt("structural: a form outside the grammar is refused by name")
@pytest.mark.parametrize(
    ("files", "message"),
    [
        _refusal(
            "a union of arms that are not None",
            "class Bad(TypedDict):\n    a: int | str\n",
            "Bad.a: int | str is no form of the wire",
        ),
        _refusal(
            "a tuple",
            "class Bad(TypedDict):\n    a: tuple[int, int]\n",
            "Bad.a: tuple[int, int] is no form of the wire",
        ),
        _refusal(
            "a name that is no class or alias",
            "class Bad(TypedDict):\n    a: Missing\n",
            "Bad.a: Missing is no form of the wire",
        ),
        _refusal(
            "an annotation that is a string",
            'class Bad(TypedDict):\n    a: "int"\n',
            "Bad.a: 'int' is no form of the wire",
        ),
        _refusal(
            "a literal word holding a quote",
            'class Bad(TypedDict):\n    a: Literal["it\'s"]\n',
            'Bad.a: Literal["it\'s"] is no form of the wire',
        ),
        _refusal(
            "a map by a key that is no str or alias",
            "class Bad(TypedDict):\n    a: dict[int, str]\n",
            "Bad.a: dict[int, str] is no form of the wire",
        ),
        _refusal(
            "a field that is not a plain name",
            "class Bad(TypedDict):\n    a.b: int\n",
            "Bad.a.b: int is no form of the wire",
        ),
        _refusal(
            "a class with a keyword",
            "class Bad(TypedDict, total=False):\n    a: int\n",
            "Bad: class Bad(TypedDict, total=False) is no form of the wire",
        ),
        _refusal(
            "a functional TypedDict",
            "Bad = TypedDict('Bad', {'a': int})\n",
            "Bad: TypedDict('Bad', {'a': int}) is no form of the wire",
        ),
        _refusal(
            "an empty class with a base",
            "class Base(TypedDict):\n    a: int\n\n\n"
            "class Bad(Base):\n    '''No field.'''\n",
            "Bad: class Bad(Base) is no form of the wire",
        ),
        _refusal(
            "a class that is no TypedDict",
            "class Bad:\n    a: int\n",
            "Bad: class Bad is no form of the wire",
        ),
        _refusal(
            "a name written twice",
            "from isekai.foundation import artifacts\n\n"
            "class Block(TypedDict):\n    a: int\n\n\n"
            "class Bad(TypedDict):\n    b: artifacts.Block\n",
            "Block: written twice, by isekai/interface/ui/shapes.py"
            " and isekai/foundation/artifacts.py",
            ARTIFACTS_BLOCK,
        ),
        _refusal(
            "an event valued by no class",
            "EVENTS: dict[str, Any] = {'a': int}\n",
            "EVENTS.a: int is no form of the wire",
        ),
        _refusal(
            "an event named by no identifier",
            "class Bad(TypedDict):\n    a: int\n\n\n"
            "EVENTS: dict[str, Any] = {'a-b': Bad}\n",
            "EVENTS.a-b: Bad is no form of the wire",
        ),
    ],
)
def test_a_form_outside_the_grammar_is_refused_naming_the_class_and_the_field(
    tmp_path: Path, files: dict[str, str], message: str
) -> None:
    root = _tree(tmp_path, files)
    with pytest.raises(ValueError) as refused:
        derive(root)
    assert str(refused.value) == message
