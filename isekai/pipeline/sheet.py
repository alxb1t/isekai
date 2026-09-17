"""Stage (2): prose in, a sheet of canonical tags out.

A sheet is fields and nothing else. It carries no assembled prompt -- storing one
creates a footgun where a human edits the prompt block and a rebuild silently
overwrites it. **The fill itself is told nothing about flows**: the sorter is
handed the prose, the schema and the briefing, so the same code serves every flow
without learning that flows exist, and the flow decides only which directory is
read and written.

**The schema is a data file, not code.** It can be checked without executing
anything, and a second schema -- a photoreal flow's, say -- is a file rather than
a branch. It declares, in order, the sixteen fields, which seven are scored and
the per-field suffix convention; it carries no version and no vocabulary, because
inside a frozen flow directory the digest proves the field list and the flow
declares the vocabulary. Its reader lives beside `Schema` in
`isekai/foundation/flow.py`.

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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from isekai.boundary.claude_cli import (
    BASE_FLAGS,
    BINARY,
    CliFailure,
    Runner,
    briefing_text,
    instructions_record,
    invoke,
    refusal_for,
    spawn,
)
from isekai.foundation.flow import Schema
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    CAPTIONS,
    SHEETS,
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
from isekai.shared.fields import validate
from isekai.shared.vocabulary import Vocabulary, map_phrase
from isekai.shared.vocabulary import identity as vocabulary_identity


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


# --- the stage: prose in, canonical fields out --------------------------------

# The name this stage's budget is keyed by. Its directory inside a run is the
# run's to name, not the stage's -- `run.SHEETS`.
STAGE = "sheet"


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
        result = invoke(self.argv(prose, schema, briefing), self.runner, self.binary)
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
            f"{schema.name} requires",
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


def sheet(
    run: Run,
    flow: str,
    sorter: Sorter,
    schema: Schema,
    vocabulary: Vocabulary,
    *,
    briefing_path: Path,
    new_version: bool = False,
) -> Path | None:
    """Sort this flow's caption into a sheet, under that flow.

    **The fill itself is told nothing about flows.** The sorter is handed the
    prose, the schema and the briefing, and nothing else, so the same code serves
    every flow without learning that flows exist; `flow` decides only which
    directory is read and written. A flow shares nothing, so the caption read here
    is the one produced under this flow's own instructions (design.md D5).

    Returns the artifact's path, or None when this flow already had a sheet.
    """
    directory = run.directory(flow, SHEETS)
    if latest(directory) is not None and not new_version:
        return None

    captions = run.directory(flow, CAPTIONS)
    source = latest(captions)
    if source is None:
        raise Refusal(
            f"{run.id}: there is no caption to sort for {flow}; run "
            f"`python -m isekai caption --flow {flow}` for this photograph first"
        )

    check_budget(STAGE, directory, next_version(directory), run.id)

    prose = str(read_artifact(captions / artifact_name(source))["prose"])
    briefing = briefing_text(briefing_path)
    try:
        sorted_answers = sorter.sort(prose, schema, briefing)
    except CliFailure as failed:
        record = record_failure(
            directory,
            next_version(directory),
            failed.kind,
            {"stage": STAGE, "detail": failed.detail, "envelope": failed.envelope},
        )
        raise refusal_for(
            "sorter", run.id, failed, record, f"{flow}/{SHEETS}/", STAGE
        ) from failed

    fields = fill(sorted_answers.answers, schema, vocabulary)
    validate(fields, schema, vocabulary)

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
                "schema_document": {"name": schema.name},
                "vocabulary": vocabulary_identity(vocabulary),
                "fields": fields,
            },
        ),
    )
    return path
