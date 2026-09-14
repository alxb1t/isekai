"""Stage (2): the schema a sheet is shaped by, and the sheet itself.

A sheet is fields and nothing else. It carries no assembled prompt -- storing one
creates a footgun where a human edits the prompt block and a rebuild silently
overwrites it -- and this stage is never told which flow asked for it, which is
what lets one filled sheet serve every flow that shares a schema and a vocabulary.

**The schema is a versioned data file, not code.** It can be checked without
executing anything, and a second schema -- a photoreal flow's, say -- is a file
rather than a branch. It declares, in order, the sixteen fields, which seven are
scored, the per-field suffix convention, and the vocabulary it is written against
(design.md D8).

**Field names are slugs because they have to be.** The structured-output flag
becomes a tool input schema at the API, which enforces `^[a-zA-Z0-9_.-]{1,64}$` on
property keys; six of the sixteen names carried a space or a slash and the first
call hit a hard 400. Aliasing at the boundary was tried and is the cause of the
one caveat on the measured score -- the model read one set of names and was held
to another. One name everywhere removes the class of error.

Stdlib only.
"""

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from isekai.refusal import Refusal
from isekai.vocabulary import Vocabulary, map_phrase, normalise

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"

# The only schema document version this build reads. There is one schema version
# in existence, so there is no migration ladder and no second reader.
SCHEMA_VERSION = 1

# What the API enforces on a tool input schema's property keys. Held here rather
# than discovered at the boundary, because a name that fails it fails every call
# rather than one.
IDENTIFIER_SAFE = re.compile(r"^[a-zA-Z0-9_.-]{1,64}$")


@dataclass(frozen=True)
class Field:
    """One field of a sheet: its name, whether it is scored, and its suffix."""

    name: str
    scored: bool
    suffix: str | None


@dataclass(frozen=True)
class Schema:
    """A versioned field list, in prompt order, and the vocabulary it assumes."""

    name: str
    version: int
    vocabulary: Mapping[str, str]
    fields: tuple[Field, ...]

    @property
    def names(self) -> tuple[str, ...]:
        """Return the field names, in the one order a prompt is assembled in."""
        return tuple(field.name for field in self.fields)

    @property
    def scored(self) -> tuple[str, ...]:
        """Return the names of the fields a measurement is taken over."""
        return tuple(field.name for field in self.fields if field.scored)

    def field(self, name: str) -> Field:
        """Return the named field, or refuse naming what the schema does declare."""
        for field in self.fields:
            if field.name == name:
                return field
        raise Refusal(
            f"{name!r} is not a field of schema {self.name} v{self.version}; "
            f"this schema declares {', '.join(self.names)} -- correct the field "
            "name, or write a new schema version that declares it"
        )


def schema_path(name: str = "identity", version: int = SCHEMA_VERSION) -> Path:
    """Return the tracked path of one schema document."""
    return SCHEMAS_DIR / f"{name}.v{version}.json"


def load_schema(path: Path | None = None) -> Schema:
    """Read a schema document, refusing any version this build does not know.

    Nothing is interpreted before the version is checked: a best-effort read of a
    field list you do not know the shape of produces a sheet that looks filled and
    means nothing.
    """
    path = schema_path() if path is None else path
    document: Any = json.loads(path.read_text())
    declared = document.get("version")
    if declared != SCHEMA_VERSION:
        raise Refusal(
            f"{path.name}: declares schema version {declared!r} and this build "
            f"reads version {SCHEMA_VERSION}; upgrade isekai to a build that "
            f"reads version {declared!r}, or point the flow at a schema document "
            f"declaring version {SCHEMA_VERSION}"
        )
    fields = tuple(
        Field(str(entry["name"]), bool(entry["scored"]), entry["suffix"])
        for entry in document["fields"]
    )
    unsafe = [field.name for field in fields if not IDENTIFIER_SAFE.match(field.name)]
    if unsafe:
        raise Refusal(
            f"{path.name}: {', '.join(unsafe)} cannot be a structured-output "
            "property key, which must match "
            f"{IDENTIFIER_SAFE.pattern}; rename the field in the schema document "
            "and in the briefing that names it"
        )
    return Schema(
        name=str(document["schema"]),
        version=int(declared),
        vocabulary=dict(document["vocabulary"]),
        fields=fields,
    )


def fill(
    answers: Mapping[str, Sequence[str]],
    schema: Schema,
    vocabulary: Vocabulary,
) -> dict[str, list[str]]:
    """Map a model's free-text answers onto canonical tags, field by field.

    Every field the schema declares appears in the result, empty if the prose
    carried nothing for it -- an empty field is a real answer and is not a reason
    to reject a sheet. Nothing outside the vocabulary survives, because the
    cascade emits only tags it found there.
    """
    filled: dict[str, list[str]] = {}
    for field in schema.fields:
        tags: list[str] = []
        for phrase in answers.get(field.name, ()):
            for tag in map_phrase(phrase, vocabulary, field.suffix):
                if tag not in tags:
                    tags.append(tag)
        filled[field.name] = tags
    return filled


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
