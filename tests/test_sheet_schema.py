"""The schema document, and what a sheet is allowed to be.

The tracked schema itself is read, not a fixture copy of it -- the same rule the
suite reads the shipped graph and the tracked manifests under. It is reached
through the flow that owns it, because there is no schema document outside a
flow directory.
"""

import ast
import json
from pathlib import Path

import pytest

from isekai.boundary.provision import VOCABULARY_MANIFEST_PATH
from isekai.foundation.flow import (
    IDENTIFIER_SAFE,
    SCHEMA_NAME,
    Schema,
    load_flow,
    load_schema,
    tracked_flows,
)
from isekai.foundation.refusal import Refusal
from isekai.shared.fields import validate
from isekai.shared.vocabulary import Vocabulary

SCHEMA_PATH = load_flow("summon-anime-wai").schema_path

# The sixteen, in the one order a prompt is assembled in, and the seven a
# measurement is taken over. Restated here so that reordering the schema document
# is a deliberate test edit, the way the committed prompts already are.
PROMPT_ORDER = (
    "count",
    "age_band",
    "skin_ancestry",
    "hair_colour",
    "hair_silhouette",
    "eye_colour",
    "eyebrows",
    "marks",
    "clothes",
    "accessories",
    "expression",
    "gaze",
    "pose",
    "framing",
    "body_shape",
    "background",
)
SCORED = (
    "hair_colour",
    "hair_silhouette",
    "eye_colour",
    "marks",
    "clothes",
    "gaze",
    "pose",
)


@pytest.mark.spec("sheet:schema:field-order-is-declared-once")
def test_the_schema_declares_the_sixteen_fields_in_prompt_order(
    schema: Schema,
) -> None:
    assert schema.names == PROMPT_ORDER


# A literal holding this many schema names is an ordering of them; a pair such as
# `("pose", "gaze")` is not.
ORDERING_THRESHOLD = 3
# Its literals are the field map's criteria, not an order.
ORDERING_CARVE_OUT = "tools/derive_field_map.py"


def field_name_literals(root: Path) -> list[str]:
    """Return each tuple, list, set or dict literal holding the names of the schema.

    A literal counts when it holds `ORDERING_THRESHOLD` or more distinct names.
    e.g. `("pose", "gaze", "count")` on line 3 of `isekai/x.py` -> `isekai/x.py:3`
    """
    found = []
    for tree in ("isekai", "evaluation", "tools"):
        for path in sorted((root / tree).rglob("*.py")):
            name = path.relative_to(root).as_posix()
            if name == ORDERING_CARVE_OUT:
                continue
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Dict):
                    items = [key for key in node.keys if key is not None]
                    items += node.values
                elif isinstance(node, ast.Tuple | ast.List | ast.Set):
                    items = node.elts
                else:
                    continue
                held = {
                    item.value
                    for item in items
                    if isinstance(item, ast.Constant) and item.value in PROMPT_ORDER
                }
                if len(held) >= ORDERING_THRESHOLD:
                    found.append(f"{name}:{node.lineno}")
    return found


@pytest.mark.spec("sheet:schema:field-order-is-declared-once")
def test_no_second_ordering_is_defined_anywhere_else() -> None:
    # The field list appears in the schema document and in this test, which pins
    # it. No module carries a list of field names at all.
    root = Path(__file__).resolve().parent.parent
    carriers = [
        path
        for path in (root / "isekai").rglob("*.py")
        if "hair_silhouette" in path.read_text()
    ]
    assert carriers == []
    assert field_name_literals(root) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_no_second_ordering_is_defined_anywhere_else"
)
def test_the_ordering_check_catches_a_literal_of_field_names(tmp_path: Path) -> None:
    for name, text in {
        "isekai/a.py": 'ORDER = ("count", "pose", "gaze")\n',
        "evaluation/b.py": 'BY = {"count": 1, "pose": 2, "gaze": 3}\n',
        "isekai/c.py": 'PAIR = ("pose", "gaze")\n',
        "tools/derive_field_map.py": 'CRITERIA = ("count", "pose", "gaze")\n',
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    assert field_name_literals(tmp_path) == ["isekai/a.py:1", "evaluation/b.py:1"]


@pytest.mark.spec("sheet:schema:field-order-is-declared-once")
def test_the_schema_declares_which_seven_fields_are_scored(schema: Schema) -> None:
    assert schema.scored == SCORED


@pytest.mark.spec("sheet:schema:field-names-are-identifier-safe")
def test_every_field_name_is_a_legal_structured_output_property_key(
    schema: Schema,
) -> None:
    for name in schema.names:
        assert IDENTIFIER_SAFE.match(name), name


@pytest.mark.spec("sheet:schema:field-names-are-identifier-safe")
def test_a_schema_carrying_a_name_the_api_would_reject_is_refused(
    tmp_path: Path,
) -> None:
    document = json.loads(SCHEMA_PATH.read_text())
    document["fields"][0]["name"] = "hair / silhouette"
    path = tmp_path / SCHEMA_NAME
    path.write_text(json.dumps(document))

    with pytest.raises(Refusal) as refused:
        load_schema(path)

    assert "hair / silhouette" in str(refused.value)
    assert IDENTIFIER_SAFE.pattern in str(refused.value)


@pytest.mark.spec("sheet:schema:field-names-are-identifier-safe")
def test_the_name_the_instructions_use_is_the_name_the_structure_enforces(
    schema: Schema,
) -> None:
    # No alias table exists, in either direction. There is one name per field.
    assert len(set(schema.names)) == len(schema.names)


@pytest.mark.spec("sheet:schema:schema-is-read-from-the-flow")
def test_every_tracked_flow_carries_its_own_schema_document() -> None:
    for name in tracked_flows():
        flow = load_flow(name)

        assert flow.schema_path == flow.path / SCHEMA_NAME
        assert flow.schema.names


@pytest.mark.spec("sheet:schema:schema-is-read-from-the-flow")
def test_no_schema_document_is_tracked_outside_a_flow_directory() -> None:
    root = Path(__file__).resolve().parent.parent
    flows = {load_flow(name).schema_path for name in tracked_flows()}

    stray = [
        path
        for path in root.rglob(SCHEMA_NAME)
        if path not in flows and ".venv" not in path.parts and ".data" not in path.parts
    ]

    assert stray == []


@pytest.mark.spec("sheet:schema:vocabulary-is-declared-by-the-flow")
def test_the_schema_document_declares_no_vocabulary_and_no_version() -> None:
    document = json.loads(SCHEMA_PATH.read_text())

    assert sorted(document) == ["fields", "name"]


@pytest.mark.spec("sheet:schema:vocabulary-is-declared-by-the-flow")
def test_the_vocabulary_a_fill_is_held_against_is_the_flows() -> None:
    manifest = json.loads(VOCABULARY_MANIFEST_PATH.read_text())
    entry = manifest["entries"][0]
    flow = load_flow("summon-anime-wai")

    assert flow.vocabulary["name"] == entry["dest"]
    assert flow.vocabulary["sha256"] == entry["sha256"]
    assert flow.vocabulary["revision"] in entry["sources"][0]


@pytest.mark.spec_exempt("structural: the field lookup's refusal")
def test_asking_for_a_field_the_schema_does_not_declare_is_refused(
    schema: Schema,
) -> None:
    with pytest.raises(Refusal) as refused:
        schema.field("hair_colour_but_wrong")

    assert "hair_colour" in str(refused.value)


# --- validating ---------------------------------------------------------------


@pytest.mark.spec("sheet:purity:no-tag-outside-the-vocabulary")
def test_a_sheet_carrying_a_tag_outside_the_vocabulary_is_refused(
    schema: Schema, vocabulary: Vocabulary
) -> None:
    sheet = {name: [] for name in schema.names}
    sheet["eye_colour"] = ["hazel eyes"]

    with pytest.raises(Refusal) as refused:
        validate(sheet, schema, vocabulary)

    message = str(refused.value)
    assert "hazel eyes" in message
    assert "prediction set" in message


@pytest.mark.spec("sheet:purity:an-excluded-tag-is-refused")
def test_a_sheet_carrying_an_excluded_tag_is_refused(
    schema: Schema, vocabulary: Vocabulary
) -> None:
    sheet = {name: [] for name in schema.names}
    sheet["accessories"] = ["glasses"]
    validate(sheet, schema, vocabulary)

    with pytest.raises(Refusal) as refused:
        validate(sheet, schema, vocabulary, excluded=frozenset({"glasses"}))

    message = str(refused.value)
    assert "'glasses' in accessories" in message
    assert "excluded list" in message
    assert "delete it from the draft" in message


@pytest.mark.spec("sheet:output:sheet-stores-fields-only")
def test_a_sheet_missing_a_field_is_refused_and_told_to_add_an_empty_one(
    schema: Schema, vocabulary: Vocabulary
) -> None:
    sheet = {name: [] for name in schema.names if name != "pose"}

    with pytest.raises(Refusal) as refused:
        validate(sheet, schema, vocabulary)

    assert "pose" in str(refused.value)
    assert "empty field is a legal answer" in str(refused.value)


@pytest.mark.spec("sheet:output:sheet-stores-fields-only")
def test_a_sheet_carrying_an_assembled_prompt_is_refused(
    schema: Schema, vocabulary: Vocabulary
) -> None:
    sheet: dict[str, list[str]] = {name: [] for name in schema.names}
    sheet["prompt"] = ["masterpiece, 1girl, brown hair"]

    with pytest.raises(Refusal) as refused:
        validate(sheet, schema, vocabulary)

    assert "prompt" in str(refused.value)
