"""The vocabulary object and the four-pass mapping cascade.

Offline by construction: every test builds its vocabulary from a CSV written to
`tmp_path`, so nothing here needs the provisioned artifact or the network. The
count that proves the real file parses -- 8,106 general tags -- is the task's
stated verification, run as a command against the provisioned tree; a test that
needed a gitignored 300 KB download would not run in CI at all.
"""

from pathlib import Path

import pytest

from isekai.vocabulary import (
    CURATED,
    Vocabulary,
    asserts_absence,
    identity,
    map_phrase,
    normalise,
    read_tags,
)

# A small stand-in with the same shape as the real list: general tags in
# category 0, character and meta tags in the categories the loader drops.
CSV = """tag_id,name,category,count
9999999,general,9,1000000
1,long_hair,0,3645082
2,short_hair,0,1904624
3,medium_hair,0,273659
4,very_long_hair,0,783428
5,wavy_hair,0,83362
6,brown_hair,0,1267072
7,blue_eyes,0,1490640
8,brown_eyes,0,747352
9,thick_eyebrows,0,77258
10,dark_skin,0,233165
11,simple_background,0,1420030
12,glasses,0,309385
13,smile,0,2365730
14,looking_at_viewer,0,2696730
15,jeans,0,200000
16,shirt,0,1382452
17,collared_shirt,0,321941
18,hair,0,50000
19,hatsune_miku,4,500000
"""


@pytest.fixture
def vocabulary() -> Vocabulary:
    """Return a small vocabulary with the real one's shape and spelling."""
    return Vocabulary(
        name="wd14/selected_tags.csv",
        revision="f" * 40,
        digest="a" * 64,
        counts=read_tags(CSV),
    )


@pytest.mark.spec_exempt("structural: the loader's parsing rules, not a scenario")
def test_only_general_tags_survive_the_read() -> None:
    tags = read_tags(CSV)

    assert "hatsune miku" not in tags
    assert "general" not in tags
    assert len(tags) == 18


@pytest.mark.spec_exempt("structural: one spelling reaches the rest of the module")
def test_underscores_become_spaces_on_the_way_in() -> None:
    assert read_tags(CSV)["long hair"] == 3645082
    assert normalise("Long_Hair  ") == "long hair"


@pytest.mark.spec_exempt("structural: the count and search helpers")
def test_count_is_the_post_count_and_zero_for_a_tag_that_is_not_there(
    vocabulary: Vocabulary,
) -> None:
    assert vocabulary.count("blue_eyes") == 1490640
    assert vocabulary.count("hazel eyes") == 0


@pytest.mark.spec_exempt("structural: the count and search helpers")
def test_search_returns_most_posted_first(vocabulary: Vocabulary) -> None:
    assert vocabulary.search("hair")[:4] == [
        "long hair",
        "short hair",
        "brown hair",
        "very long hair",
    ]


@pytest.mark.spec("sheet:output:sheet-names-its-vocabulary")
def test_the_vocabularys_identity_is_its_name_revision_and_digest(
    vocabulary: Vocabulary,
) -> None:
    assert identity(vocabulary) == {
        "name": "wd14/selected_tags.csv",
        "revision": "f" * 40,
        "sha256": "a" * 64,
    }


# --- the cascade --------------------------------------------------------------


@pytest.mark.spec("sheet:mapping:exact-match-wins-first")
def test_a_phrase_already_in_the_vocabulary_maps_to_itself(
    vocabulary: Vocabulary,
) -> None:
    assert map_phrase("blue eyes", vocabulary, "eyes") == ["blue eyes"]


@pytest.mark.spec("sheet:mapping:exact-match-wins-first")
def test_no_later_pass_alters_an_exact_match(vocabulary: Vocabulary) -> None:
    # `shirt` is exact, and `collared shirt` would win on containment if the
    # cascade ever got that far. It does not.
    assert map_phrase("shirt", vocabulary) == ["shirt"]


@pytest.mark.spec("sheet:mapping:suffix-completes-a-bare-value")
def test_a_fields_suffix_completes_a_bare_value(vocabulary: Vocabulary) -> None:
    assert map_phrase("brown", vocabulary, "hair") == ["brown hair"]
    assert map_phrase("brown", vocabulary, "eyes") == ["brown eyes"]


@pytest.mark.spec("sheet:mapping:suffix-completes-a-bare-value")
def test_the_suffix_comes_from_the_caller_and_not_from_the_field_name(
    vocabulary: Vocabulary,
) -> None:
    # The same phrase, two suffixes, two answers -- and the mapper was never told
    # a field name at all.
    assert map_phrase("brown", vocabulary, None) == []


@pytest.mark.spec("sheet:mapping:curated-pass-consumes-and-continues")
def test_a_curated_match_consumes_its_span_and_the_rest_continues(
    vocabulary: Vocabulary,
) -> None:
    assert map_phrase("shoulder length wavy", vocabulary, "hair") == [
        "medium hair",
        "wavy hair",
    ]


@pytest.mark.spec("sheet:mapping:curated-pass-consumes-and-continues")
def test_a_curated_entry_whose_tag_is_not_in_the_vocabulary_is_inert(
    vocabulary: Vocabulary,
) -> None:
    assert map_phrase("beehive", vocabulary, "hair", {"beehive": "not a tag"}) == []


@pytest.mark.spec("sheet:mapping:containment-requires-every-word")
def test_a_candidate_containing_a_word_the_phrase_lacks_is_not_emitted(
    vocabulary: Vocabulary,
) -> None:
    # "collared shirt" needs "collared", which "tucked in shirt" does not carry.
    assert map_phrase("tucked in shirt", vocabulary) == ["shirt"]


@pytest.mark.spec("sheet:mapping:containment-requires-every-word")
def test_a_candidate_whose_every_word_appears_may_be_emitted(
    vocabulary: Vocabulary,
) -> None:
    assert map_phrase("a crisp collared shirt", vocabulary) == ["collared shirt"]


@pytest.mark.spec("sheet:mapping:containment-requires-every-word")
def test_the_suffix_can_complete_a_value_but_never_be_the_whole_of_one(
    vocabulary: Vocabulary,
) -> None:
    # `hair` is a tag in its own right, and a hair field must not collapse an
    # unmappable phrase into it.
    assert map_phrase("wavy", vocabulary, "hair") == ["wavy hair"]
    assert map_phrase("frizzy", vocabulary, "hair") == []


@pytest.mark.spec("sheet:mapping:no-match-emits-nothing")
def test_a_phrase_that_maps_to_nothing_emits_nothing(
    vocabulary: Vocabulary,
) -> None:
    assert map_phrase("an air of quiet competence", vocabulary) == []


@pytest.mark.spec("sheet:mapping:no-match-emits-nothing")
def test_the_mapper_does_not_substitute_a_nearest_neighbour(
    vocabulary: Vocabulary,
) -> None:
    # "hazel" shares no word with any tag; the nearest neighbour would be a
    # colour nobody said.
    assert map_phrase("hazel", vocabulary, "eyes") == []


@pytest.mark.spec("sheet:purity:absence-clause-is-dropped")
@pytest.mark.parametrize(
    "phrase",
    [
        "no glasses",
        "not wearing glasses",
        "none visible",
        "without glasses",
        "no visible marks",
        "nothing in her hair",
    ],
)
def test_an_absence_clause_produces_nothing(
    vocabulary: Vocabulary, phrase: str
) -> None:
    assert asserts_absence(phrase)
    assert map_phrase(phrase, vocabulary) == []


@pytest.mark.spec("sheet:purity:absence-clause-is-dropped")
def test_a_positive_phrase_is_not_mistaken_for_an_absence_clause(
    vocabulary: Vocabulary,
) -> None:
    assert not asserts_absence("wearing glasses")
    assert map_phrase("wearing glasses", vocabulary) == ["glasses"]


@pytest.mark.spec("sheet:purity:no-tag-outside-the-vocabulary")
def test_no_pass_of_the_cascade_can_emit_a_tag_the_vocabulary_lacks(
    vocabulary: Vocabulary,
) -> None:
    phrases = [
        "blue eyes",
        "brown",
        "shoulder length wavy",
        "a crisp collared shirt",
        "an air of quiet competence",
        "hazel",
    ]
    for phrase in phrases:
        for tag in map_phrase(phrase, vocabulary, "hair"):
            assert tag in vocabulary


@pytest.mark.spec_exempt("structural: the curated table's own shape")
def test_every_curated_span_and_tag_is_written_in_the_normal_spelling() -> None:
    for span, tag in CURATED.items():
        assert span == normalise(span)
        assert tag == normalise(tag)
        assert span != tag


@pytest.mark.spec_exempt(
    "structural: the provisioned artifact is gitignored, so this asserts the "
    "curated table against it only where it is present"
)
def test_every_curated_tag_is_in_the_provisioned_vocabulary() -> None:
    from isekai.vocabulary import DEFAULT_MODELS_DIR, VOCABULARY_DEST, load

    if not (DEFAULT_MODELS_DIR / VOCABULARY_DEST).exists():
        pytest.skip("the vocabulary is not provisioned in this environment")
    provisioned = load()

    dead = [tag for tag in CURATED.values() if tag not in provisioned]
    assert dead == []


@pytest.mark.spec_exempt("structural: the loader against the provisioned file")
def test_the_provisioned_vocabulary_carries_its_pin(tmp_path: Path) -> None:
    from isekai.vocabulary import DEFAULT_MODELS_DIR, VOCABULARY_DEST, load

    if not (DEFAULT_MODELS_DIR / VOCABULARY_DEST).exists():
        pytest.skip("the vocabulary is not provisioned in this environment")
    provisioned = load()

    assert len(provisioned) == 8106
    assert len(provisioned.revision) == 40
    assert len(provisioned.digest) == 64
