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

import dataclasses
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from isekai import caption as caption_module
from isekai.claude_cli import (
    BASE_FLAGS,
    BINARY,
    CliFailure,
    Runner,
    instructions_record,
    invoke,
    require_binary,
    spawn,
)
from isekai.refusal import Refusal
from isekai.run import (
    Run,
    artifact_name,
    check_budget,
    envelope,
    latest,
    next_version,
    read_artifact,
    record_failure,
    write_json,
)
from isekai.vocabulary import Vocabulary, map_phrase, normalise
from isekai.vocabulary import identity as vocabulary_identity

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


# --- the stage: prose in, canonical fields out --------------------------------

BRIEFING_PATH = SCHEMAS_DIR / "identity.v1.briefing.md"

# The stage's own directory inside a run, and the name its budget is keyed by.
STAGE = "sheet"
DIRECTORY = "sheets"


@dataclass(frozen=True)
class Sorting:
    """What a sorter returned: free-text answers per field, and what produced them."""

    answers: Mapping[str, Sequence[str]]
    implementation: str
    models: tuple[str, ...] = ()
    pinned: bool = False


class Sorter(Protocol):
    """The sorting seam. One implementation ships; the double keeps the suite dry."""

    def sort(self, prose: str, schema: Schema, briefing: str) -> Sorting:
        """Return one list of free-text phrases per field the schema declares."""
        ...


@dataclass(frozen=True)
class FakeSorter:
    """An offline stand-in that counts its calls and answers from a canned table."""

    answers: Mapping[str, Sequence[str]] = dataclasses.field(default_factory=dict)
    implementation: str = "fake-sorter"
    models: tuple[str, ...] = ("fake-model",)
    failure: CliFailure | None = None
    calls: list[str] = dataclasses.field(default_factory=list)

    def sort(self, prose: str, schema: Schema, briefing: str) -> Sorting:
        """Record the call and return the answers it was constructed with."""
        self.calls.append(prose)
        if self.failure is not None:
            raise self.failure
        return Sorting(
            {name: list(self.answers.get(name, ())) for name in schema.names},
            self.implementation,
            self.models,
        )


def output_shape(schema: Schema) -> dict[str, Any]:
    """Return the JSON Schema the model's answer is held to: the fields, exactly.

    This constrains the *shape* of the answer and not its wording. Constraining
    generation to the vocabulary was measured and rejected: token-prefix masking
    lands on the nearest tag sharing a prefix rather than the one the model meant,
    which turns a visible failure into an invisible one -- a phrase meaning
    "tucked into jeans" became a valid, unrelated tag that passes every guard and
    gets rendered. Generating freely and mapping afterwards scored 0.482 against
    0.316 for the constrained arm.
    """
    return {
        "type": "object",
        "properties": {
            name: {"type": "array", "items": {"type": "string"}}
            for name in schema.names
        },
        "required": list(schema.names),
        "additionalProperties": False,
    }


@dataclass(frozen=True)
class ClaudeSorter:
    """The `claude -p` adapter for this stage: no tools, and a required shape."""

    binary: str = BINARY
    runner: Runner = spawn
    implementation: str = "claude-cli"

    def prompt(self, prose: str, briefing: str) -> str:
        """Return the whole of what the sorter is told: its rules, then the prose."""
        return f"{briefing.rstrip()}\n\n## The description to sort\n\n{prose.strip()}\n"

    def argv(self, prose: str, schema: Schema, briefing: str) -> list[str]:
        """Return the exact argument vector this sorter is invoked with."""
        return [
            self.binary,
            "-p",
            self.prompt(prose, briefing),
            *BASE_FLAGS,
            "--tools",
            "",
            "--json-schema",
            json.dumps(output_shape(schema)),
        ]

    def sort(self, prose: str, schema: Schema, briefing: str) -> Sorting:
        """Invoke the CLI and read one list per field out of its envelope."""
        require_binary(self.binary)
        result = invoke(self.argv(prose, schema, briefing), self.runner)
        return Sorting(
            answers_from(result.structured, result.result, schema),
            self.implementation,
            result.models,
        )


def answers_from(structured: object, text: str, schema: Schema) -> dict[str, list[str]]:
    """Read the model's answer, refusing anything that is not the schema's fields.

    A structural mismatch is *permanent*: the structure was stated in the request,
    so a response that does not carry it will not carry it on the next attempt
    either, and another attempt would spend for nothing.
    """
    parsed: Any = structured
    if not isinstance(parsed, dict):
        try:
            parsed = json.loads(text)
        except ValueError:
            parsed = None
    if not isinstance(parsed, dict):
        raise CliFailure(
            "permanent", "the response is not an object carrying the schema's fields"
        )
    missing = [name for name in schema.names if name not in parsed]
    if missing:
        raise CliFailure(
            "permanent",
            f"the response does not carry {', '.join(missing)}, which schema "
            f"{schema.name} v{schema.version} requires",
        )
    # A bare string is tolerated as a one-phrase answer, because a model that
    # returns `"brown"` where `["brown"]` was asked for said something usable and
    # refusing it would spend an attempt on punctuation.
    answers: dict[str, list[str]] = {}
    for name in schema.names:
        given: Any = parsed[name]
        listed = given if isinstance(given, list) else [given]
        answers[name] = [
            str(phrase).strip()
            for phrase in listed
            if isinstance(phrase, str) and phrase.strip()
        ]
    return answers


def briefing_text(path: Path = BRIEFING_PATH) -> str:
    """Return the sorter's standing instructions."""
    return path.read_text()


def sheet(
    run: Run,
    sorter: Sorter,
    schema: Schema,
    vocabulary: Vocabulary,
    flows: Sequence[str],
    *,
    new_version: bool = False,
    briefing_path: Path = BRIEFING_PATH,
) -> list[Path]:
    """Sort `run`'s caption into a sheet, and write it to every flow given.

    **One fill, many destinations.** The stage is never told which flow asked --
    it is handed the schema, the vocabulary and the caption, and nothing else --
    so flows declaring the same pair start from identical sheets and diverge only
    when a human edits them. Filling once and copying is what makes adding a flow
    cheap, and it follows from the stage's ignorance rather than from a check.

    Returns the paths written, empty when every flow already had a sheet.
    """
    wanted = [
        flow
        for flow in flows
        if latest(run.directory(DIRECTORY, flow)) is None or new_version
    ]
    if not wanted:
        return []

    captions = run.directory(caption_module.DIRECTORY)
    source = latest(captions)
    if source is None:
        raise Refusal(
            f"{run.id}: there is no caption to sort; run "
            "`python -m isekai caption` for this photograph first"
        )

    first = run.directory(DIRECTORY, wanted[0])
    check_budget(STAGE, first, next_version(first), run.id)

    prose = str(read_artifact(captions / artifact_name(source))["prose"])
    briefing = briefing_text(briefing_path)
    try:
        sorted_answers = sorter.sort(prose, schema, briefing)
    except CliFailure as failed:
        record = record_failure(
            first,
            next_version(first),
            failed.kind,
            {"stage": STAGE, "detail": failed.detail, "envelope": failed.envelope},
        )
        raise Refusal(
            f"{run.id}: the sorter failed ({failed.kind}) -- {failed.detail}; "
            f"see {record.name} in {DIRECTORY}/{wanted[0]}/, and run "
            "`python -m isekai sheet` again once what it names is fixed"
        ) from failed

    fields = fill(sorted_answers.answers, schema, vocabulary)
    validate(fields, schema, vocabulary)

    written: list[Path] = []
    for flow in wanted:
        directory = run.directory(DIRECTORY, flow)
        path = directory / artifact_name(next_version(directory))
        write_json(
            path,
            envelope(
                STAGE,
                {
                    "implementation": sorted_answers.implementation,
                    "models": list(sorted_answers.models),
                    "pinned": sorted_answers.pinned,
                    "briefing": instructions_record(briefing_path),
                    "from": source,
                },
                {
                    "schema_document": {
                        "name": schema.name,
                        "version": schema.version,
                    },
                    "vocabulary": vocabulary_identity(vocabulary),
                    "fields": fields,
                },
            ),
        )
        written.append(path)
    return written
