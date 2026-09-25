"""The authored tag-to-criterion table, its derived reverse index, and its checks.

Offline by construction, like `test_vocabulary.py`: every refusal test writes a
small table to `tmp_path` and holds it against the fixture vocabulary, so nothing
here needs the provisioned 308 KB list. The tests that *do* read the committed
table need the vocabulary, through `require_vocabulary`, and it is what makes the
pin check worth having.
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
)
from isekai.shared.vocabulary import Vocabulary, read_tags
from tests.conftest import CSV, require_vocabulary

# The fixture vocabulary's field names, as a table under test has to cover them.
# Two criteria, because the coverage check is about a declared name being absent
# and one name is enough to prove it while two prove the listing.
DECLARED = {"summon-anime-wai": ("hair_colour", "hair_silhouette")}


@pytest.fixture
def provisioned() -> Vocabulary:
    """Return the provisioned vocabulary: the group sizes are its own."""
    from isekai.interface.wiring import load_vocabulary
    from isekai.shared.vocabulary import DEFAULT_MODELS_DIR, VOCABULARY_DEST

    require_vocabulary(DEFAULT_MODELS_DIR / VOCABULARY_DEST)
    return load_vocabulary()


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
    from isekai.foundation.flow import (
        FLOWS_DIR,
        SCHEMA_NAME,
        flow_path,
        load_schema,
        tracked_flows,
    )

    assert FLOWS_DIR not in FIELD_MAP_PATH.parents
    assert FIELD_MAP_PATH.parent.name == "scripts"

    # And no flow's schema document says which tags exist: a field entry carries
    # a name, a scored flag and a suffix, and never a tag list.
    for flow in tracked_flows():
        schema = load_schema(flow_path(flow) / SCHEMA_NAME)
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
def test_a_tag_claimed_as_primary_by_two_criteria_is_refused(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    path = table(
        tmp_path,
        {
            "hair_colour": {"primary": ["brown hair"], "also": []},
            "hair_silhouette": {"primary": ["brown hair"], "also": []},
        },
    )

    with pytest.raises(Refusal) as refused:
        load(vocabulary, path, DECLARED)

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
    tmp_path: Path, vocabulary: Vocabulary
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
        load(vocabulary, path, DECLARED)

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
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    path = table(tmp_path, {"hair_colour": {"primary": ["brown hair"], "also": []}})

    with pytest.raises(Refusal) as refused:
        load(vocabulary, path, DECLARED)

    assert "hair_silhouette" in str(refused.value)
    assert "summon-anime-wai" in str(refused.value)


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
def test_the_committed_table_resolves_in_the_provisioned_vocabulary(
    provisioned: Vocabulary,
) -> None:
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


# The seven seeds `notes/v0.19_improvements/ui.md:575` records for hair
# silhouette -- the only seed list that exists on disk anywhere, and the version's
# one verifiable number. `hime_cut` is ONE seed: splitting it yields a bare `cut`
# that pulls in the whole `cutout` family, a 32-tag error.
SEVEN = ("ponytail", "braid", "bun", "bangs", "twintails", "updo", "hime cut")

# The six the record's substring route adds and the matcher's rule does not.
# Every one is junk, and every one comes from the seed `bun`.
BUNNIES = (
    "playboy bunny",
    "reverse bunnysuit",
    "nontraditional playboy bunny",
    "setsubun",
    "male playboy bunny",
    "bunny day",
)


@pytest.mark.spec_exempt("structural: the authoring script's matcher, not a scenario")
def test_the_seven_recorded_seeds_reach_fifty_seven_beyond_the_suffix_group(
    provisioned: Vocabulary,
) -> None:
    from derive_field_map import by_suffix, expand

    hair = by_suffix("hair", provisioned)
    reached = expand(SEVEN, provisioned)
    substring = {
        tag for tag in provisioned.counts if any(seed in tag for seed in SEVEN)
    }

    assert len(hair) == 103
    assert len(reached) == 59
    assert len(reached - hair) == 57

    # The record's own route is substring, which 2.2's rule forbids. The whole
    # difference is the six bunnies, and `\bbun\b` matches none of them.
    assert len(substring - hair) == 63
    assert sorted((substring - reached) - hair) == sorted(BUNNIES)
    assert reached <= substring


@pytest.mark.spec_exempt("structural: the authoring script's matcher, not a scenario")
def test_a_bare_word_boundary_loses_the_plurals_the_inflections_keep(
    provisioned: Vocabulary,
) -> None:
    import re

    from derive_field_map import expand

    bare = {
        tag
        for tag in provisioned.counts
        if re.search(r"\b(?:" + "|".join(SEVEN) + r")\b", tag)
    }
    reached = expand(SEVEN, provisioned)

    assert len(bare) == 51
    assert sorted(reached - bare) == [
        "braided hair rings",
        "braiding hair",
        "low twin braids",
        "low-braided long hair",
        "multiple braids",
        "side braids",
        "tri braids",
        "twin braids",
    ]


@pytest.mark.spec_exempt("structural: the committed table against the operator's runs")
def test_every_approved_tag_is_reachable_in_the_field_it_was_approved_in(
    provisioned: Vocabulary,
) -> None:
    from collections import defaultdict

    from derive_field_map import APPROVED

    approved = sorted(Path().glob(APPROVED))
    if not approved:
        pytest.skip("the v0.20 runs are not on disk in this environment")

    filed: dict[str, set[str]] = defaultdict(set)
    for path in approved:
        for field, tags in json.loads(path.read_text())["fields"].items():
            for tag in tags:
                filed[tag].add(field)

    field_map = load(provisioned)
    unreachable = sorted(
        (tag, field)
        for tag, fields in filed.items()
        for field in fields
        if tag not in field_map.group(field)
    )

    assert len(filed) == 113
    assert unreachable == []


@pytest.mark.spec("model-provisioning:derivation:rerun-is-byte-identical")
def test_the_committed_table_re_derives_without_reading_the_gitignored_runs(
    provisioned: Vocabulary,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The byte-identical rule, and the reason the table can carry it at all.

    `derive_field_map` cannot join `tests/test_derivation.py`'s `DERIVERS`: that
    tuple is the roster of the shared *manifest* module, and `manifest.write`
    reads an `entries` key this artifact does not have. So the rule is asserted
    here instead, and it is asserted the strict way -- `filings()` is rigged to
    raise, so a derivation that reached back into `.data/` fails loudly rather
    than passing on this machine and nowhere else.
    """
    import sys

    import derive_field_map

    def refuse(root: Path = Path(".")) -> dict[str, object]:
        raise AssertionError("the derivation read the gitignored approved runs")

    written = tmp_path / "field_map.json"
    monkeypatch.setattr(derive_field_map, "filings", refuse)
    monkeypatch.setattr(derive_field_map, "FIELD_MAP_PATH", written)
    monkeypatch.setattr(sys, "argv", ["derive_field_map.py"])

    derive_field_map.main()

    assert written.read_bytes() == FIELD_MAP_PATH.read_bytes()


@pytest.mark.spec_exempt(
    "structural: the transcription against the sheets it came from"
)
def test_the_transcribed_filings_match_the_operator_s_approved_sheets(
    provisioned: Vocabulary,
) -> None:
    """`FILED` is authored, and this is what says it was authored faithfully.

    Environment-conditional for the same reason its neighbour above is: the runs
    are gitignored. The point of the transcription is that the *derivation* no
    longer needs them -- checking it does, where they happen to be present.
    """
    from derive_field_map import FILED, filings

    on_disk = filings()
    if not on_disk:
        pytest.skip("the v0.20 runs are not on disk in this environment")

    assert {tag: dict(counts) for tag, counts in on_disk.items()} == {
        tag: dict(counts) for tag, counts in FILED.items()
    }
