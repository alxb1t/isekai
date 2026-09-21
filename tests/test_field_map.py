"""The authored tag-to-criterion table, its derived reverse index, and its checks.

Offline by construction, like `test_vocabulary.py`: every refusal test writes a
small table to `tmp_path` and holds it against the fixture vocabulary, so nothing
here needs the provisioned 308 KB list. The two tests that *do* read the
committed table skip when the vocabulary is absent -- that is the same dependency
every existing vocabulary test already carries, and it is what makes the pin
check worth having.
"""

import json
from pathlib import Path

import pytest

from isekai.foundation.refusal import Refusal
from isekai.shared.field_map import (
    FIELD_MAP_PATH,
    declared_fields,
    identity,
    load,
    parse,
)
from isekai.shared.vocabulary import Vocabulary, read_tags
from tests.conftest import CSV

# The fixture vocabulary's field names, as a table under test has to cover them.
# Two criteria, because the coverage check is about a declared name being absent
# and one name is enough to prove it while two prove the listing.
DECLARED = {"summon-v1": ("hair_colour", "hair_silhouette")}


@pytest.fixture
def vocabulary() -> Vocabulary:
    """Return a small vocabulary with the real one's shape and spelling."""
    return Vocabulary(
        name="wd14/selected_tags.csv",
        revision="f" * 40,
        digest="a" * 64,
        counts=read_tags(CSV),
    )


def table(
    tmp_path: Path,
    fields: dict[str, dict[str, list[str]]],
    excluded: list[str] | None = None,
    revision: int = 1,
) -> Path:
    """Write a table document to `tmp_path` and return its path."""
    path = tmp_path / "field_map.json"
    path.write_text(
        json.dumps(
            {
                "name": "scripts/field_map.json",
                "revision": revision,
                "fields": fields,
                "excluded": excluded or [],
            }
        )
    )
    return path


@pytest.mark.spec("field-map:table:the-reverse-index-is-derived")
def test_the_reverse_index_is_computed_from_the_authored_direction(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    document = {
        "hair_colour": {"primary": ["brown hair"], "also": []},
        "hair_silhouette": {"primary": ["long hair"], "also": []},
    }
    path = table(tmp_path, document)

    field_map = load(vocabulary, path, DECLARED)

    # The document declares `field -> tags` and nothing else; a `tag -> field`
    # answer therefore cannot have been read, only computed.
    assert json.loads(path.read_text())["fields"] == document
    assert field_map.primary_of("brown hair") == "hair_colour"
    assert field_map.primary_of("long hair") == "hair_silhouette"


@pytest.mark.spec("field-map:table:it-is-not-read-from-a-flow")
def test_the_table_lives_outside_every_flow_directory() -> None:
    from isekai.foundation.flow import FLOWS_DIR, load_schema, tracked_flows

    assert FLOWS_DIR not in FIELD_MAP_PATH.parents
    assert FIELD_MAP_PATH.parent.name == "scripts"

    # And no flow's schema document says which tags exist: a field entry carries
    # a name, a scored flag and a suffix, and never a tag list.
    for flow in tracked_flows():
        schema = load_schema(FLOWS_DIR / flow / "schema.json")
        for field in schema.fields:
            assert not hasattr(field, "tags")


@pytest.mark.spec("field-map:table:it-names-its-own-revision")
def test_the_table_reports_a_name_a_revision_and_a_digest_of_its_bytes(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    import hashlib

    path = table(
        tmp_path,
        {
            "hair_colour": {"primary": ["brown hair"], "also": []},
            "hair_silhouette": {"primary": [], "also": []},
        },
        revision=7,
    )

    field_map = load(vocabulary, path, DECLARED)

    assert field_map.name == "scripts/field_map.json"
    assert field_map.revision == 7
    assert field_map.digest == hashlib.sha256(path.read_bytes()).hexdigest()
    assert identity(field_map) == {
        "name": "scripts/field_map.json",
        "revision": 7,
        "sha256": field_map.digest,
    }


@pytest.mark.spec("field-map:integrity:a-tag-outside-the-vocabulary-is-refused")
def test_a_tag_the_vocabulary_does_not_carry_is_refused(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    path = table(
        tmp_path,
        {
            "hair_colour": {"primary": ["brown hair", "chartreuse hair"], "also": []},
            "hair_silhouette": {"primary": [], "also": []},
        },
    )

    with pytest.raises(Refusal) as refused:
        load(vocabulary, path, DECLARED)

    assert "chartreuse hair" in str(refused.value)
    assert "brown hair" not in str(refused.value)


@pytest.mark.spec("field-map:membership:every-tag-has-exactly-one-primary")
def test_a_tag_claimed_as_primary_by_two_criteria_is_refused(tmp_path: Path) -> None:
    path = table(
        tmp_path,
        {
            "hair_colour": {"primary": ["brown hair"], "also": []},
            "hair_silhouette": {"primary": ["brown hair"], "also": []},
        },
    )

    with pytest.raises(Refusal) as refused:
        parse(path.read_text(), DECLARED)

    assert "brown hair" in str(refused.value)
    assert "hair_colour" in str(refused.value)
    assert "hair_silhouette" in str(refused.value)


@pytest.mark.spec("field-map:membership:a-tag-may-be-browsed-under-several")
def test_a_tag_is_browsable_under_several_criteria_and_routes_to_one(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    path = table(
        tmp_path,
        {
            "hair_colour": {"primary": ["brown hair"], "also": ["long hair"]},
            "hair_silhouette": {"primary": ["long hair"], "also": ["brown hair"]},
        },
    )

    field_map = load(vocabulary, path, DECLARED)

    assert set(field_map.group("hair_colour")) == {"brown hair", "long hair"}
    assert set(field_map.group("hair_silhouette")) == {"brown hair", "long hair"}
    assert field_map.primary_of("long hair") == "hair_silhouette"
    assert field_map.primary_of("brown hair") == "hair_colour"


@pytest.mark.spec("field-map:excluded:no-tag-is-in-both")
def test_a_tag_in_both_a_group_and_the_excluded_list_is_refused(
    tmp_path: Path,
) -> None:
    path = table(
        tmp_path,
        {
            "hair_colour": {"primary": ["brown hair"], "also": []},
            "hair_silhouette": {"primary": ["long hair"], "also": []},
        },
        excluded=["long hair"],
    )

    with pytest.raises(Refusal) as refused:
        parse(path.read_text(), DECLARED)

    assert "long hair" in str(refused.value)


@pytest.mark.spec("field-map:excluded:a-tag-in-neither-is-dropped")
def test_a_tag_in_no_group_and_not_excluded_routes_nowhere_and_is_not_refused(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    path = table(
        tmp_path,
        {
            "hair_colour": {"primary": ["brown hair"], "also": []},
            "hair_silhouette": {"primary": [], "also": []},
        },
    )

    field_map = load(vocabulary, path, DECLARED)

    assert "glasses" in vocabulary
    assert field_map.primary_of("glasses") is None
    assert "glasses" not in field_map.excluded


@pytest.mark.spec("field-map:coverage:every-declared-field-has-an-entry")
def test_a_criterion_a_tracked_flow_declares_with_no_entry_is_refused(
    tmp_path: Path,
) -> None:
    path = table(tmp_path, {"hair_colour": {"primary": ["brown hair"], "also": []}})

    with pytest.raises(Refusal) as refused:
        parse(path.read_text(), DECLARED)

    assert "hair_silhouette" in str(refused.value)
    assert "summon-v1" in str(refused.value)


@pytest.mark.spec("field-map:coverage:an-empty-group-is-legal")
def test_an_empty_group_loads_and_is_reported_as_empty(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    path = table(
        tmp_path,
        {
            "hair_colour": {"primary": ["brown hair"], "also": []},
            "hair_silhouette": {"primary": [], "also": []},
        },
    )

    field_map = load(vocabulary, path, DECLARED)

    assert "hair_silhouette" in field_map.fields
    assert field_map.group("hair_silhouette") == ()


@pytest.mark.spec("field-map:integrity:the-check-runs-against-the-pin")
def test_the_committed_table_resolves_in_the_provisioned_vocabulary() -> None:
    from isekai.shared.vocabulary import DEFAULT_MODELS_DIR, VOCABULARY_DEST
    from isekai.shared.vocabulary import load as load_vocabulary

    if not (DEFAULT_MODELS_DIR / VOCABULARY_DEST).exists():
        pytest.skip("the vocabulary is not provisioned in this environment")
    provisioned = load_vocabulary()

    # `load` raises all four checks, so reaching a `FieldMap` at all is the
    # assertion; the revision is named so a moved pin is visible in the failure.
    field_map = load(provisioned)

    assert provisioned.revision == "627aef95638667ddcaa3ac8ae625e88ea5b02f51"
    assert len(provisioned) == 8106
    assert set(field_map.fields) >= {
        name for names in declared_fields().values() for name in names
    }


@pytest.mark.spec_exempt("structural: the committed table's own shape, not a scenario")
def test_the_committed_table_covers_every_declared_criterion() -> None:
    document = json.loads(FIELD_MAP_PATH.read_text())
    declared = {name for names in declared_fields().values() for name in names}

    assert len(declared) == 21
    assert set(document["fields"]) == declared
