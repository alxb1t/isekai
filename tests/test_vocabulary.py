"""The vocabulary object: what a tag is, whether it exists, and how strong it is.

**The four-pass cascade this module used to carry is gone**, and with it sixteen
of this file's tests. Nothing maps free text onto a tag any more: the sheet's
input is a list the tagger already emitted, so every tag arrives canonical and
the only question left about one is whether the list contains it.

Offline by construction: every test builds its vocabulary from a CSV written in
`tests/conftest.py`, so nothing here needs the provisioned artifact or the
network. The two that read the provisioned file skip when it is absent.
"""

from pathlib import Path

import pytest

from isekai.shared.vocabulary import (
    Vocabulary,
    identity,
    normalise,
    read_tags,
)
from tests.conftest import CSV


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


@pytest.mark.spec_exempt("structural: the loader against the provisioned file")
def test_the_provisioned_vocabulary_carries_its_pin(tmp_path: Path) -> None:
    from isekai.shared.vocabulary import DEFAULT_MODELS_DIR, VOCABULARY_DEST, load

    if not (DEFAULT_MODELS_DIR / VOCABULARY_DEST).exists():
        pytest.skip("the vocabulary is not provisioned in this environment")
    provisioned = load()

    assert len(provisioned) == 8106
    assert len(provisioned.revision) == 40
    assert len(provisioned.digest) == 64
