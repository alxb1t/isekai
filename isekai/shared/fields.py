"""What a filled field map is allowed to be, held against a schema and a vocabulary.

Takes a field map, a schema and a vocabulary and returns an answer -- it reads no
run, no flow and no score, which is what puts it here rather than in a stage.

It lives in `shared/` rather than in `foundation/` beside `Schema` because it
depends on a `Vocabulary`, and `shared/vocabulary.py` already imports
`foundation/refusal.py`; a vocabulary-dependent function in `foundation` would
make the two groups import each other in both directions. `shared` already
imports `foundation`, so this adds no new direction (design.md D8).

Stdlib only.
"""

from collections.abc import Mapping, Sequence

from isekai.foundation.flow import Schema
from isekai.foundation.refusal import Refusal
from isekai.shared.vocabulary import Vocabulary, normalise


def validate(
    fields: Mapping[str, Sequence[str]],
    schema: Schema,
    vocabulary: Vocabulary,
) -> None:
    """Refuse a sheet that is not exactly the schema's fields of canonical tags.

    Three ways a sheet can be wrong, and each names what to do about it: a field
    the schema declares is missing, a key the schema does not declare is present,
    or a tag is not in the vocabulary's prediction set. An empty field is none of
    those.
    """
    missing = [name for name in schema.names if name not in fields]
    if missing:
        raise Refusal(
            f"the sheet is missing {', '.join(missing)}; add the field with an "
            "empty list -- an empty field is a legal answer, a missing one is not"
        )
    extra = [name for name in fields if name not in schema.names]
    if extra:
        raise Refusal(
            f"the sheet carries {', '.join(sorted(extra))}, which schema "
            f"{schema.name} v{schema.version} does not declare; remove "
            "the entry, or write a schema version that declares it"
        )
    outside = [
        (name, tag)
        for name in schema.names
        for tag in fields[name]
        if tag not in vocabulary
    ]
    if outside:
        listed = ", ".join(f"{tag!r} in {name}" for name, tag in outside)
        raise Refusal(
            f"{listed}: not in {vocabulary.name}'s prediction set, so the base "
            "model was never trained to draw it; replace it with a tag the "
            "vocabulary carries, or delete it"
        )
    unspelled = [
        (name, tag)
        for name in schema.names
        for tag in fields[name]
        if tag != normalise(tag)
    ]
    if unspelled:
        listed = ", ".join(f"{tag!r} in {name}" for name, tag in unspelled)
        raise Refusal(
            f"{listed}: not written in the vocabulary's own spelling; use "
            "lowercase words separated by single spaces"
        )
