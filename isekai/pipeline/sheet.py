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

**Two implementations ship, and the shape is required of both.** `ClaudeSorter`
puts `output_shape(schema)` behind `--json-schema`; `OllamaSorter` puts the same
object in `format`, which the runtime compiles into a grammar. The transport
differs and the constraint does not -- which is what keeps a malformed answer
*permanent* for either: the structure was required server-side rather than asked
for politely, so a second attempt would spend for nothing. Everything downstream
of the seam is shared and untouched by which one filled it: `answers_from` reads
the answer from the structured field or from the body, `fill` canonicalises
through the same cascade, and the vocabulary refuses a tag neither of them knows.

Stdlib only.
"""

import dataclasses
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from isekai.boundary import ollama
from isekai.boundary.claude_cli import (
    BASE_FLAGS,
    BINARY,
    CliFailure,
    Runner,
    invoke,
    spawn,
)
from isekai.foundation.flow import Schema
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    SHEETS,
    WD14,
    Run,
    artifact_name,
    check_budget,
    envelope,
    latest,
    next_version,
    read_artifact,
    write_json,
)
from isekai.shared.field_map import FieldMap, route
from isekai.shared.field_map import identity as field_map_identity
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

# What the sheet records as having filled it. The string the *tag* artifact's
# producer carries, because that is what the sheet's content now comes from --
# written out rather than imported from `tagging.py`, since no stage imports
# another.
TAGGER = "wd14"


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


# What the open sorter is sampled at, ported verbatim from the measurement.
# `repeat_penalty` is belt to the schema's braces and it is not decoration: at
# temperature 0 there is no sampling noise to break a loop, and one field came
# back with `"white robe"` forty times until the output budget ran out, which
# truncated the JSON mid-string. The budget is twice the reader's because sixteen
# fields of tags run longer than prose (design.md D1, D10).
SORTER_OPTIONS: Mapping[str, Any] = {
    "temperature": 0,
    "seed": 1,
    "num_predict": 2048,
    "repeat_penalty": 1.15,
}

# The one command that turns an absent sorter into a present one. A public
# registry tag, so it is a pull rather than a create -- the asymmetry with the
# reader's remedy is the whole reason the boundary takes one as an argument.
SORTER_REMEDY = "ollama pull {model}"


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


def sorter_prompt(prose: str, briefing: str) -> str:
    """Return the whole of what a sorter is told: its rules, then the prose.

    **Shared by both adapters rather than written once each**, for the same
    reason `output_shape` is: the two arms are only comparable if they differ in
    transport and in nothing else. Two copies of this line would let a heading or
    a `strip()` policy drift between them, which no test would catch and which
    would quietly invalidate any comparison drawn between the arms.
    """
    return f"{briefing.rstrip()}\n\n## The description to sort\n\n{prose.strip()}\n"


@dataclass(frozen=True)
class ClaudeSorter:
    """The `claude -p` adapter for this stage: no tools, and a required shape."""

    binary: str = BINARY
    runner: Runner = spawn
    implementation: str = "claude-cli"

    def argv(self, prose: str, schema: Schema, briefing: str) -> list[str]:
        """Return the exact argument vector this sorter is invoked with."""
        return [
            self.binary,
            "-p",
            sorter_prompt(prose, briefing),
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


@dataclass(frozen=True)
class OllamaSorter:
    """The Ollama adapter for this stage: the shape required, and thinking off.

    **`format` carries the same `output_shape(schema)` the Claude arm puts behind
    `--json-schema`.** Ollama compiles it into a llama.cpp grammar, so the sixteen
    keys are guaranteed present and the body is guaranteed to parse. That is what
    keeps a malformed answer classified as *permanent*: the structure was required
    server-side rather than asked for politely, so a response that does not carry
    it will not carry it on the next attempt either.

    **`think: false` is load-bearing and not an economy.** A hybrid reasoner draws
    its thinking tokens from the same `num_predict` budget as its answer, and on
    the first run they truncated the JSON mid-string on the third subject. Sorting
    is slot-filling against a closed vocabulary, not reasoning, so the budget
    belongs to the answer. A model with no thinking mode ignores the flag
    (design.md D1).
    """

    model: str
    transport: ollama.Transport = ollama.post
    implementation: str = "ollama"

    def body(self, prose: str, schema: Schema, briefing: str) -> dict[str, Any]:
        """Return the exact request this sorter is invoked with.

        A method rather than a local, so `format` is assertable against
        `output_shape(schema)` itself rather than against a copy of it.
        """
        return {
            "model": self.model,
            "prompt": sorter_prompt(prose, briefing),
            "format": output_shape(schema),
            "stream": False,
            "think": False,
            "options": dict(SORTER_OPTIONS),
        }

    def sort(self, prose: str, schema: Schema, briefing: str) -> Sorting:
        """Send the prose and read one list per field out of the answer.

        The answer arrives **as the response body**, not as a separate structured
        field, which is the path `answers_from` already falls back to. Nothing
        here parses it: the same function serves both implementations, so the
        cascade and the validation downstream cannot diverge between them.
        """
        try:
            answer = ollama.ask(
                self.body(prose, schema, briefing),
                remedy=SORTER_REMEDY.format(model=self.model),
                transport=self.transport,
            )
        except ollama.OllamaFailure as failed:
            raise CliFailure(failed.kind, failed.detail) from failed
        return Sorting(
            answers_from(None, answer, schema),
            self.implementation,
            (self.model,),
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
    schema: Schema,
    vocabulary: Vocabulary,
    field_map: FieldMap,
    *,
    new_version: bool = False,
) -> Path | None:
    """Route this flow's tag list into a sheet, under that flow.

    **The fill is told nothing about flows and reaches nothing at all.** It is
    handed a tag list, the schema, the vocabulary and the table, so the same code
    serves every flow without learning that flows exist; `flow` decides only which
    directory is read and written. A flow shares nothing, so the tag list read
    here is the one produced under this flow's own directory (design.md D5).

    **An absent tag list is a refusal, and that is the one rule this version
    narrows.** A sheet with every field empty is legal and therefore silent, so
    writing one when the tagger never ran would hide the only thing the operator
    needs told. The rule that a missing tag artifact is an absent aid still holds
    for the *hosted* tagger, which contributes nothing to a sheet; it cannot hold
    for the local one the sheet is filled from (design.md D21).

    Returns the artifact's path, or None when this flow already had a sheet.
    """
    directory = run.directory(flow, SHEETS)
    if latest(directory) is not None and not new_version:
        return None

    tagged = run.directory(flow, WD14)
    source = latest(tagged)
    if source is None:
        raise Refusal(
            f"{run.id}: there is no tag list to fill a sheet for {flow} from; run "
            f"`python -m isekai caption --flow {flow}` for this photograph first, "
            f"which writes {flow}/{WD14}/ beside the prose"
        )

    check_budget(STAGE, directory, next_version(directory), run.id)

    artifact = read_artifact(tagged / artifact_name(source))
    listed: Any = artifact["tags"]
    tags = [str(one["tag"]) for one in listed]

    fields = route(tags, field_map, schema)
    validate(fields, schema, vocabulary)

    path = directory / artifact_name(next_version(directory))
    write_json(
        path,
        envelope(
            STAGE,
            {
                # The producer of the *tags* is the producer of the sheet now, so
                # the pin it was verified against travels across rather than being
                # re-derived: these are the digests that session actually opened.
                "implementation": TAGGER,
                "models": list(artifact["producer"]["models"]),
                "pinned": bool(artifact["producer"]["pinned"]),
                "artifacts": dict(artifact["producer"]["artifacts"]),
                "from": source,
            },
            {
                "schema_document": {"name": schema.name},
                "vocabulary": vocabulary_identity(vocabulary),
                "field_map": field_map_identity(field_map),
                "fields": fields,
            },
        ),
    )
    return path
