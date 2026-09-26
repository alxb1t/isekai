"""The canonical tag vocabulary: a pinned tag list and its post counts.

The list -- general Danbooru tags -- is provisioned from a pinned, digested
manifest and is swappable by pointing that manifest somewhere else.

This file holds `normalise()`, the one spelling every lookup reads;
`Vocabulary`, the list with its counts and the one ranking rule; `read_tags()`,
which parses the tagger's `selected_tags.csv`; `load()`, which reads a verified
list with its manifest entry; and `identity()`, the record a sheet carries to say
which list filled it.

**No invented tag reaches a sheet, and that holds by construction elsewhere.**
WD14's labels are the vocabulary, and `shared/field_map.py` is a table over it.

Stdlib only.
"""

import csv
import io
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from isekai.foundation.artifacts import VocabularyRecord

# The destination the vocabulary manifest declares, and the models root the
# scorer already defaults to. One tree, two consumers, one provisioning rule.
VOCABULARY_DEST = "wd14/selected_tags.csv"
DEFAULT_MODELS_DIR = Path("models")

# The one command that provisions anything in this repository, pointed at the
# manifest that declares this file. Named here because `interface/wiring.py` and
# `boundary/wd14.py`, which loads the tagger the list is the output layer of, both
# refuse over it, and a literal in each could name different commands for one fix.
VOCABULARY_REMEDY = "bash scripts/download_models.sh scripts/vocabulary.json"

# The tagger's own category numbering. `0` is the general tags; `4` is character
# names and `9` is the rating meta-tags, and neither describes a person's
# appearance, so neither belongs in a sheet about one.
GENERAL_CATEGORY = "0"

# Danbooru writes `blue_eyes`; a prompt is read as `blue eyes`. One spelling
# reaches the rest of this module, and it is the prompt's.
_UNDERSCORES = re.compile(r"[_\s]+")

# A commit sha inside a pinned source URL, which is the vocabulary's revision.
_REVISION = re.compile(r"/resolve/(?P<revision>[0-9a-f]{40})/")


def normalise(phrase: str) -> str:
    """Return the one spelling the rest of this module reads: lowercase, spaced."""
    return _UNDERSCORES.sub(" ", phrase.strip().lower()).strip()


@dataclass(frozen=True)
class Vocabulary:
    """A tag list with its post counts, and the pin that says which list it is."""

    name: str
    revision: str
    digest: str
    counts: Mapping[str, int]

    def __contains__(self, tag: str) -> bool:
        """Say whether `tag` is canonical, under the one normalised spelling."""
        return normalise(tag) in self.counts

    def __len__(self) -> int:
        """Return how many tags the vocabulary carries."""
        return len(self.counts)

    def count(self, tag: str) -> int:
        """Return `tag`'s post count, or zero if it is not in the vocabulary.

        Zero rather than a refusal: the count ranks candidates, and a tag that is
        not there simply loses to every tag that is.
        """
        return self.counts.get(normalise(tag), 0)

    def rank(self, tags: Iterable[str]) -> list[str]:
        """Return `tags` most-posted first, then alphabetical.

        **The one ranking rule, and there is no second one.** Popularity, because
        the vocabulary is a frequency table: among tags that fit equally well, the
        one the base model has seen most is the one it can actually draw. Every
        tag surface in this repository sorts through here, so a tie-break that
        moved would move all of them together rather than desynchronising the
        cheatsheet from the autocomplete.
        """
        return sorted(tags, key=lambda tag: (-self.counts.get(tag, 0), tag))

    def search(self, term: str) -> list[str]:
        """Return every tag containing `term`, ranked."""
        needle = normalise(term)
        return self.rank(tag for tag in self.counts if needle in tag)


def read_tags(body: str) -> dict[str, int]:
    """Parse the tagger's `selected_tags.csv` into general tags and their counts."""
    rows = csv.DictReader(io.StringIO(body))
    return {
        normalise(row["name"]): int(row["count"])
        for row in rows
        if row.get("category") == GENERAL_CATEGORY
    }


def load(path: Path, entry: Mapping[str, Any]) -> Vocabulary:
    """Return the vocabulary at `path`, named by its manifest `entry`.

    It only reads: the bytes are verified against `entry` before this is called,
    by `interface/wiring.py`'s `load_vocabulary`, so `shared` reaches no boundary.
    """
    match = _REVISION.search(entry["sources"][0])
    return Vocabulary(
        name=VOCABULARY_DEST,
        revision=match.group("revision") if match else "",
        digest=entry["sha256"],
        counts=read_tags(path.read_text()),
    )


def identity(vocabulary: Vocabulary) -> VocabularyRecord:
    """Return the record a sheet carries to say which vocabulary filled it."""
    return {
        "name": vocabulary.name,
        "revision": vocabulary.revision,
        "sha256": vocabulary.digest,
    }
