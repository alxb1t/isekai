"""Hold a recorded shape against a declared one.

`faults` reads a declaration the way `tests.record.shape` writes an answer: keys and
type names, never a value. The cases below prove it on declarations of this file's own.
"""

import types
from typing import (
    Literal,
    TypedDict,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    is_typeddict,
)

import pytest

from isekai.foundation.artifacts import SessionRecord
from isekai.interface.ui.routes.hub import ROUTES as HUB
from isekai.interface.ui.routes.images import ROUTES as IMAGES
from isekai.interface.ui.routes.reviewing import ROUTES as REVIEWING
from isekai.interface.ui.routes.staging import ROUTES as STAGING
from isekai.interface.ui.routes.vocabulary import ROUTES as VOCABULARY
from isekai.interface.ui.shapes import ANSWERS, ServedSession
from tests.record import recorded

LEAVES = (str, int, float, bool)
TABLES = (HUB, STAGING, VOCABULARY, IMAGES, REVIEWING)


def _dot(at: str, key: str) -> str:
    return f"{at}.{key}" if at else key


def _seen(sampled: object) -> str:
    """Return how a refusal names `sampled`.

    e.g. "int" -> '"int"', {} -> "a map", [] -> "a list"
    """
    if isinstance(sampled, dict):
        return "a map"
    if isinstance(sampled, list):
        return "a list"
    return f'"{sampled}"'


def _fault(at: str, what: str) -> str:
    return f"{at or '.'}: {what}"


def _line(at: str, what: str) -> list[str]:
    return [_fault(at, what)]


def _record(declared: object, sampled: object, at: str) -> list[str]:
    if not isinstance(sampled, dict):
        return _line(at, f"{_seen(sampled)} is not a map")
    held = cast("dict[str, object]", sampled)
    fields = get_type_hints(declared)
    found = [
        _fault(_dot(at, key), "is not declared") for key in held if key not in fields
    ]
    found += [
        _fault(_dot(at, key), "is required and missing")
        for key in sorted(vars(declared)["__required_keys__"])
        if key not in held
    ]
    for key, field in fields.items():
        if key in held:
            found += faults(field, held[key], _dot(at, key))
    return found


def _map(held: object, sampled: object, at: str) -> list[str]:
    if not isinstance(sampled, dict):
        return _line(at, f"{_seen(sampled)} is not a map")
    found = [
        line for each in sampled.values() for line in faults(held, each, f"{at}.*")
    ]
    return list(dict.fromkeys(found))


def _list(held: object, sampled: object, at: str) -> list[str]:
    if not isinstance(sampled, list):
        return _line(at, f"{_seen(sampled)} is not a list")
    return faults(held, sampled[0], f"{at}[0]") if sampled else []


def _either(declared: object, sampled: object, at: str) -> list[str]:
    arms = [arm for arm in get_args(declared) if arm is not type(None)]
    if sampled == "null" and len(arms) < len(get_args(declared)):
        return []
    (arm,) = arms
    return faults(arm, sampled, at)


def _one_of(declared: object, sampled: object, at: str) -> list[str]:
    names = {type(value).__name__ for value in get_args(declared)}
    if isinstance(sampled, str) and sampled in names:
        return []
    return _line(at, f"{_seen(sampled)} is not a {'/'.join(sorted(names))}")


def faults(declared: object, sampled: object, at: str) -> list[str]:
    """Return a line for each way `sampled` breaks `declared`, `[]` when it fits.

    e.g. faults(list[str], ["int"], "ids") -> ['ids[0]: "int" is not a str']
    """
    origin = get_origin(declared)
    if is_typeddict(declared):
        return _record(declared, sampled, at)
    if origin is dict:
        return _map(get_args(declared)[1], sampled, at)
    if origin is list:
        return _list(get_args(declared)[0], sampled, at)
    if origin in (types.UnionType, Union):
        return _either(declared, sampled, at)
    if origin is Literal:
        return _one_of(declared, sampled, at)
    if isinstance(declared, type) and declared in LEAVES:
        if sampled == declared.__name__:
            return []
        return _line(at, f"{_seen(sampled)} is not a {declared.__name__}")
    raise TypeError(f"{at}: {declared!r} is no form of a declaration")


class Leaf(TypedDict):
    """Every leaf type."""

    name: str
    count: int
    ratio: float
    ready: bool


class Nothing(TypedDict):
    """A declaration with no field."""


class Holding(TypedDict):
    """Every form a declaration is written in."""

    leaf: Leaf
    names: list[str]
    leaves: list[Leaf]
    by_name: dict[str, Leaf]
    maybe: Leaf | None
    maybe_name: str | None
    mode: Literal["a", "b"]
    nothing: Nothing


LEAF: dict[str, object] = {
    "name": "str",
    "count": "int",
    "ratio": "float",
    "ready": "bool",
}
HELD: dict[str, object] = {
    "leaf": LEAF,
    "names": [],
    "leaves": [LEAF],
    "by_name": {"x": LEAF, "y": LEAF},
    "maybe": "null",
    "maybe_name": "str",
    "mode": "str",
    "nothing": {},
}


@pytest.mark.spec_exempt(
    "structural: the walker takes each form a declaration is written in"
)
def test_the_walker_accepts_what_a_declaration_allows() -> None:
    assert faults(Holding, HELD, "") == []
    other = {
        **HELD,
        "names": ["str"],
        "by_name": {},
        "maybe": LEAF,
        "maybe_name": "null",
    }
    assert faults(Holding, other, "") == []


@pytest.mark.spec_exempt(
    "structural: twin of test_the_walker_accepts_what_a_declaration_allows"
)
def test_the_walker_refuses_an_undeclared_key() -> None:
    sampled = {**HELD, "by_name": {"x": {**LEAF, "extra": "int"}}}
    assert faults(Holding, sampled, "") == ["by_name.*.extra: is not declared"]


@pytest.mark.spec_exempt(
    "structural: twin of test_the_walker_accepts_what_a_declaration_allows"
)
def test_the_walker_refuses_a_missing_required_key() -> None:
    sampled = {key: value for key, value in HELD.items() if key != "names"}
    assert faults(Holding, sampled, "") == ["names: is required and missing"]


@pytest.mark.spec_exempt(
    "structural: twin of test_the_walker_accepts_what_a_declaration_allows"
)
def test_the_walker_refuses_a_wrong_leaf() -> None:
    sampled = {**HELD, "leaves": [{**LEAF, "ratio": "int"}]}
    assert faults(Holding, sampled, "") == ['leaves[0].ratio: "int" is not a float']


def _routes() -> dict[str, dict[str, object]]:
    return cast("dict[str, dict[str, object]]", recorded("routes"))


@pytest.mark.spec_exempt(
    "structural: each answer of ANSWERS fits the shape the record holds for its key"
)
def test_every_answer_fits_the_record() -> None:
    entries = _routes()
    for key, declared in ANSWERS.items():
        assert key in entries, key
        assert "shape" in entries[key], key
        assert faults(declared, entries[key]["shape"], "") == [], key


@pytest.mark.spec_exempt(
    "structural: each route of the tables with a recorded shape has a row in ANSWERS"
)
def test_every_recorded_shape_of_the_tables_has_a_row() -> None:
    entries = _routes()
    keys = [f"{route.method} {route.path}" for table in TABLES for route in table]
    shaped = [key for key in keys if "shape" in entries.get(key, {})]
    assert [key for key in shaped if key not in ANSWERS] == []


@pytest.mark.spec_exempt(
    "structural: the served session is the session record with a nullable outcome"
)
def test_the_served_session_is_the_record_with_a_nullable_outcome() -> None:
    served, record = get_type_hints(ServedSession), get_type_hints(SessionRecord)
    assert served.pop("outcome") == str | None
    assert record.pop("outcome") is str
    assert served == record
    assert list(served) == list(record)
    assert ServedSession.__required_keys__ == SessionRecord.__required_keys__
    assert ServedSession.__optional_keys__ == SessionRecord.__optional_keys__
