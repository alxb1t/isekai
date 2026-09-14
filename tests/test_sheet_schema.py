"""The schema document, and what a sheet is allowed to be.

The tracked schema itself is read, not a fixture copy of it -- the same rule the
suite reads the shipped graph and the tracked manifests under.
"""

import json
from pathlib import Path

import pytest

from isekai.refusal import Refusal
from isekai.sheet import (
    IDENTIFIER_SAFE,
    SCHEMA_VERSION,
    Schema,
    fill,
    load_schema,
    schema_path,
    validate,
)
from isekai.vocabulary import Vocabulary, read_tags
from tests.test_vocabulary import CSV

# D8's sixteen, in the one order a prompt is assembled in, and the seven a
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


@pytest.fixture
def schema() -> Schema:
    """Return the tracked identity schema."""
    return load_schema()


@pytest.fixture
def vocabulary() -> Vocabulary:
    """Return the small offline vocabulary the mapping tests use."""
    return Vocabulary("wd14/selected_tags.csv", "f" * 40, "a" * 64, read_tags(CSV))


@pytest.mark.spec("sheet:schema:field-order-is-declared-once")
def test_the_schema_declares_the_sixteen_fields_in_prompt_order(
    schema: Schema,
) -> None:
    assert schema.names == PROMPT_ORDER


@pytest.mark.spec("sheet:schema:field-order-is-declared-once")
def test_no_second_ordering_is_defined_anywhere_else() -> None:
    # The field list appears in the schema document and in this test, which pins
    # it. No module carries a list of field names at all.
    root = Path(__file__).resolve().parent.parent
    carriers = [
        path
        for path in (root / "isekai").glob("*.py")
        if "hair_silhouette" in path.read_text()
    ]
    assert carriers == []


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
    document = json.loads(schema_path().read_text())
    document["fields"][0]["name"] = "hair / silhouette"
    path = tmp_path / "identity.v1.json"
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


@pytest.mark.spec("sheet:schema:unknown-version-is-refused")
def test_a_schema_from_a_version_this_build_does_not_know_is_refused(
    tmp_path: Path,
) -> None:
    path = tmp_path / "identity.v2.json"
    path.write_text(json.dumps({"schema": "identity", "version": 2, "fields": []}))

    with pytest.raises(Refusal) as refused:
        load_schema(path)

    message = str(refused.value)
    assert "identity.v2.json" in message
    assert "2" in message and str(SCHEMA_VERSION) in message


@pytest.mark.spec("sheet:schema:unknown-version-is-refused")
def test_no_field_of_an_unknown_schema_version_is_interpreted(
    tmp_path: Path,
) -> None:
    path = tmp_path / "identity.v9.json"
    path.write_text(
        json.dumps({"schema": "identity", "version": 9, "fields": [{"name": "unread"}]})
    )

    with pytest.raises(Refusal) as refused:
        load_schema(path)

    assert "unread" not in str(refused.value)


@pytest.mark.spec_exempt("structural: the schema's own declared vocabulary")
def test_the_schema_declares_the_vocabulary_it_is_written_against(
    schema: Schema,
) -> None:
    manifest = json.loads(
        (
            Path(__file__).resolve().parent.parent / "scripts" / "vocabulary.json"
        ).read_text()
    )
    entry = manifest["entries"][0]

    assert schema.vocabulary["name"] == entry["dest"]
    assert schema.vocabulary["sha256"] == entry["sha256"]
    assert schema.vocabulary["revision"] in entry["sources"][0]


@pytest.mark.spec_exempt("structural: the field lookup's refusal")
def test_asking_for_a_field_the_schema_does_not_declare_is_refused(
    schema: Schema,
) -> None:
    with pytest.raises(Refusal) as refused:
        schema.field("hair_colour_but_wrong")

    assert "hair_colour" in str(refused.value)


# --- filling and validating ---------------------------------------------------


@pytest.mark.spec("sheet:output:sheet-stores-fields-only")
def test_a_filled_sheet_carries_one_entry_per_schema_field(
    schema: Schema, vocabulary: Vocabulary
) -> None:
    filled = fill({"hair_colour": ["brown"]}, schema, vocabulary)

    assert tuple(filled) == schema.names
    assert "prompt" not in filled
    assert "positive" not in filled


@pytest.mark.spec("sheet:output:empty-field-is-legal")
def test_a_field_the_prose_carried_nothing_for_is_present_and_empty(
    schema: Schema, vocabulary: Vocabulary
) -> None:
    filled = fill({"hair_colour": ["brown"]}, schema, vocabulary)

    assert filled["hair_colour"] == ["brown hair"]
    assert filled["marks"] == []
    validate(filled, schema, vocabulary)


@pytest.mark.spec("sheet:purity:absence-clause-is-dropped")
def test_an_absence_clause_leaves_its_field_empty_rather_than_negated(
    schema: Schema, vocabulary: Vocabulary
) -> None:
    filled = fill({"accessories": ["no glasses"]}, schema, vocabulary)

    assert filled["accessories"] == []


@pytest.mark.spec("sheet:purity:no-tag-outside-the-vocabulary")
def test_every_tag_a_fill_produces_is_in_the_vocabulary(
    schema: Schema, vocabulary: Vocabulary
) -> None:
    filled = fill(
        {
            "hair_colour": ["brown"],
            "eye_colour": ["hazel"],
            "clothes": ["a crisp collared shirt", "tucked into jeans"],
            "expression": ["an air of quiet competence"],
        },
        schema,
        vocabulary,
    )

    for tags in filled.values():
        for tag in tags:
            assert tag in vocabulary
    assert filled["eye_colour"] == []
    assert filled["expression"] == []


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
