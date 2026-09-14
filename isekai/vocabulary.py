"""The canonical tag vocabulary, and the cascade that maps a phrase onto it.

**The artifact is a tag list; the cascade over it is ours.** The vocabulary --
8,106 general Danbooru tags with their post counts -- is provisioned from a
pinned, digested manifest and is swappable by pointing that manifest somewhere
else. The four-pass mapping is code and stays here, because the two outlive each
other in opposite directions: swap the sorting model and the mapper is still
needed, swap the vocabulary and it is useless (design.md D9).

**On this arm the mapping pass buys nothing measurable, and it still ships.**
Scoring the raw pre-mapping sheets gave the identical figure; it changed four
tags out of 130, none of which appeared in any reference. It ships because those
four were *outside the vocabulary* and it caught all four -- here it is a
validator -- and because on the open model the same pass is worth 0.033 to 0.482.
Stated so nobody later reads its presence as evidence it helped.

**No tag this module emits can be outside the vocabulary.** Every pass, the
curated table included, looks its result up before returning it, so an invented
tag that merely looks canonical -- the dangerous kind, because it passes every
later check on its way into the prompt -- cannot be produced at all.

Stdlib only: `csv`, `re`, `pathlib`.
"""

import csv
import io
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

# The destination the vocabulary manifest declares, and the models root the
# scorer already defaults to. One tree, two consumers, one provisioning rule.
VOCABULARY_DEST = "wd14/selected_tags.csv"
DEFAULT_MODELS_DIR = Path("models")

# The tagger's own category numbering. `0` is the general tags; `4` is character
# names and `9` is the rating meta-tags, and neither describes a person's
# appearance, so neither belongs in a sheet about one.
GENERAL_CATEGORY = "0"

# Danbooru writes `blue_eyes`; a prompt is read as `blue eyes`. One spelling
# reaches the rest of this module, and it is the prompt's.
_UNDERSCORES = re.compile(r"[_\s]+")

# A commit sha inside a pinned source URL, which is the vocabulary's revision.
_REVISION = re.compile(r"/resolve/(?P<revision>[0-9a-f]{40})/")

# A phrase asserting that something is *not* there. A positive prompt carries no
# negation, so an absence clause passed through becomes a presence instruction --
# a sheet stating that no tattoos were visible produced a render with tattoos.
# The clause is dropped whole rather than mapped, because every word left in it
# ("tattoos") is exactly the word that would be drawn.
_ABSENCE = re.compile(
    r"(?:^|\b)(?:no|not|none|never|without|absent|lacks|lacking|free of|"
    r"nothing|neither|unremarkable|n/a)\b"
)

# Curated spans: phrases a photograph's prose really carries and this vocabulary
# really has a tag for, where neither an exact match nor a suffix finds it. Each
# one is a recorded correction rather than a synonym dictionary's worth of
# guesses, and each is looked up in the vocabulary before it is emitted, so an
# entry that goes stale is inert rather than poisonous.
#
# **The `camera` entries are the load-bearing ones**, and they are here because
# the acceptance run caught them. A reader writes "looking at the camera" because
# that is English; `camera` is itself a canonical tag, meaning *a camera is in the
# picture*, so the exact-match pass would take it and the render would contain a
# camera. Naming the photographer's equipment instead of the subject's attribute
# is worse than an empty field, because what is named is what gets drawn. The
# briefing teaches the right register and this catches the cases where it does not
# take -- two defences, because one of them is a document nobody can test.
CURATED: Mapping[str, str] = {
    "chin length": "short hair",
    "shoulder length": "medium hair",
    "waist length": "very long hair",
    "buzz cut": "very short hair",
    "crew cut": "very short hair",
    "salt and pepper": "grey hair",
    "greying": "grey hair",
    "spectacles": "glasses",
    "eyeglasses": "glasses",
    "t shirt": "shirt",
    "button up": "collared shirt",
    "button down": "collared shirt",
    "stubble": "facial hair",
    "head and shoulders": "upper body",
    "eye contact": "looking at viewer",
    "looking at the camera": "looking at viewer",
    "looking at the lens": "looking at viewer",
    "looking into the lens": "looking at viewer",
    "straight at the camera": "looking at viewer",
    "three quarter view": "looking to the side",
    "profile view": "looking to the side",
    "one person": "solo",
    "one woman": "1girl",
    "one man": "1boy",
    "a woman": "1girl",
    "a man": "1boy",
    "two women": "2girls",
    "waist up": "cowboy shot",
    "neutral expression": "expressionless",
    "slight smile": "light smile",
}


def normalise(phrase: str) -> str:
    """Return the one spelling the rest of this module reads: lowercase, spaced."""
    return _UNDERSCORES.sub(" ", phrase.strip().lower()).strip()


def asserts_absence(phrase: str) -> bool:
    """Say whether `phrase` claims an attribute is missing rather than present."""
    return _ABSENCE.search(normalise(phrase)) is not None


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

    def search(self, term: str) -> list[str]:
        """Return every tag containing `term`, most-posted first, then alphabetical.

        Popularity is the ranking because the vocabulary is a frequency table:
        among tags that fit a phrase equally well, the one the base model has seen
        most is the one it can actually draw.
        """
        needle = normalise(term)
        return sorted(
            (tag for tag in self.counts if needle in tag),
            key=lambda tag: (-self.counts[tag], tag),
        )

    @cached_property
    def words(self) -> Mapping[str, frozenset[str]]:
        """Return each tag's words, for the containment pass to test against."""
        return {tag: frozenset(tag.split()) for tag in self.counts}

    def contained_in(
        self, words: Iterable[str], suffix: Iterable[str] = ()
    ) -> list[str]:
        """Return every tag all of whose words appear in `words`, best first.

        *Every* word, with no threshold. Scoring by overlap ratio let a tag win
        while containing a word the phrase never had; requiring the whole tag
        removes that class of error without a number anybody has to tune. The
        longest tag wins, because it is the most specific thing the phrase
        actually said, and the post count breaks ties.

        `suffix` lets a field's convention complete a bare value here as well as
        in the pass above -- "wavy" in a hair field can reach "wavy hair". A
        candidate must still use at least one word the phrase itself carried, so
        the suffix can complete a value but can never be the whole of one.
        """
        phrase = frozenset(words)
        available = phrase | frozenset(suffix)
        return sorted(
            (
                tag
                for tag, needed in self.words.items()
                if needed <= available and needed & phrase
            ),
            key=lambda tag: (-len(self.words[tag]), -self.counts[tag], tag),
        )


def read_tags(body: str) -> dict[str, int]:
    """Parse the tagger's `selected_tags.csv` into general tags and their counts."""
    rows = csv.DictReader(io.StringIO(body))
    return {
        normalise(row["name"]): int(row["count"])
        for row in rows
        if row.get("category") == GENERAL_CATEGORY
    }


def load(models_dir: Path = DEFAULT_MODELS_DIR) -> Vocabulary:
    """Read the provisioned vocabulary, verifying its bytes against the manifest.

    The digest check is the reason the pin is worth anything: the manifest is the
    only evidence the file on disk is the list the sheets were written against.
    Provisioning goes through the scorer's resolver rather than a second copy of
    it -- the repository keeps one enforcement site for the containment and digest
    rules, not one per consumer.
    """
    from isekai.eval_models import resolve
    from isekai.provision import load_vocabulary_manifest

    manifest = load_vocabulary_manifest()
    path = resolve(VOCABULARY_DEST, models_dir, manifest)
    entry = next(e for e in manifest["entries"] if e["dest"] == VOCABULARY_DEST)
    match = _REVISION.search(entry["sources"][0])
    return Vocabulary(
        name=VOCABULARY_DEST,
        revision=match.group("revision") if match else "",
        digest=entry["sha256"],
        counts=read_tags(path.read_text()),
    )


def identity(vocabulary: Vocabulary) -> dict[str, str]:
    """Return the record a sheet carries to say which vocabulary filled it."""
    return {
        "name": vocabulary.name,
        "revision": vocabulary.revision,
        "sha256": vocabulary.digest,
    }


def map_phrase(
    phrase: str,
    vocabulary: Vocabulary,
    suffix: str | None = None,
    curated: Mapping[str, str] = CURATED,
) -> list[str]:
    """Map one free-text phrase onto canonical tags, by a fixed four-pass cascade.

    Exact match, then the field's suffix convention, then a curated pass that
    consumes the span it matched and carries on, then containment over whatever
    words are left. Each rule in that order is a recorded correction, and the
    order is what makes the result reproducible rather than a matter of which
    rule happened to fire.

    `suffix` is the field's, passed in from the schema rather than looked up by
    field name here. That is the whole reason this function is independent of the
    field list: expecting hair-colour values to end in "hair" is a statement about
    a particular tag list paired with a particular field, and it belongs with the
    schema that pairs them (design.md D8).

    An empty list is a real answer. Nothing is substituted for a phrase that maps
    to nothing, because a nearest neighbour is a tag nobody said.
    """
    text = normalise(phrase)
    if not text or asserts_absence(text):
        return []

    if text in vocabulary:
        return [text]

    if suffix:
        completed = f"{text} {normalise(suffix)}"
        if completed in vocabulary:
            return [completed]

    found, words = _curated_pass(text.split(), vocabulary, curated)

    remaining = vocabulary.contained_in(
        words, normalise(suffix).split() if suffix else ()
    )
    if remaining:
        found.append(remaining[0])

    return _in_order(found)


def _curated_pass(
    words: list[str],
    vocabulary: Vocabulary,
    curated: Mapping[str, str],
) -> tuple[list[str], list[str]]:
    """Emit every curated span present, consuming each one and continuing.

    Returning on the first hit lost concepts from multi-concept phrases, so this
    keeps going over what is left. Longest span first, so a specific curated
    phrase is never pre-empted by a shorter one nested inside it.
    """
    spans = sorted(curated, key=lambda span: -len(normalise(span).split()))
    found: list[str] = []
    for span in spans:
        needle = normalise(span).split()
        tag = normalise(curated[span])
        if tag not in vocabulary:
            continue
        while (at := _index_of(words, needle)) is not None:
            found.append(tag)
            words = words[:at] + words[at + len(needle) :]
    return found, words


def _index_of(words: Sequence[str], needle: Sequence[str]) -> int | None:
    """Return where `needle` appears contiguously in `words`, or None."""
    if not needle:
        return None
    for start in range(len(words) - len(needle) + 1):
        if list(words[start : start + len(needle)]) == list(needle):
            return start
    return None


def _in_order(tags: Iterable[str]) -> list[str]:
    """Return `tags` with duplicates dropped, keeping the order they were found."""
    seen: dict[str, None] = {}
    for tag in tags:
        seen.setdefault(tag, None)
    return list(seen)
