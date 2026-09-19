"""Stage (1): a photograph in, descriptive prose out.

**The reader is told nothing about what happens next.** No schema, no field list,
no vocabulary, no flow identifier -- exactly one input, the photograph, and its
standing instructions. Pressing a reader into a schema is measured to make it
invent: told never to leave a field blank, one manufactured nineteen identity
marks across seven of ten subjects and its score fell from 0.518 to 0.307. A
caption written against one flow's schema also could not be reused when a second
flow arrives, and reuse is what makes adding a flow cheap.

**The reader is licensed to state absence**, and this stage does not strip it. A
positive prompt carries no negation, so a sentence saying no tattoos are visible
rendered tattoos -- and turning a licensed absence into an empty field is the
*next* stage's job. Naming where that happens is the point of allowing it here.

**No fallback reader.** A decline is a result to be recorded and surfaced, not
routed around: substituting a different implementation would write an artifact
whose provenance record is untrue, and the whole discipline of this pipeline is
that a producer names what actually made the artifact (design.md D6).

**Two implementations ship, and a flow says which.** `ClaudeReader` reaches a
model over the `claude` CLI, `OllamaReader` over HTTP to a runtime on this
machine, and they are not interchangeable: one spends money with a third party
and the other does not. The flow's manifest declares which, `interface/wiring.py`
resolves it, and a flow that declared one never reaches the other -- including
when the one it declared fails. Both adapters live here, beside the Protocol and
the double they share, rather than in `boundary/`: two implementations of one
Protocol in two different layers is the arrangement that avoids (design.md D5).

Stdlib only. The transports are behind `Reader`, and `FakeReader` is what keeps
the suite offline.
"""

import base64
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from isekai.boundary import ollama
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
from isekai.foundation.run import (
    CAPTIONS,
    Run,
    artifact_name,
    check_budget,
    envelope,
    latest,
    next_version,
    record_failure,
    write_json,
)

# The name this stage's budget is keyed by. Its directory inside a run is the
# run's to name, not the stage's -- `run.CAPTIONS`.
STAGE = "caption"

# The photograph's path goes *in the prompt*. A trailing positional after the
# prompt is silently ignored by the CLI's argument parser, which would leave the
# reader told to describe a photograph and never told where it is; `--add-dir` is
# what grants the read, and this line is what points at the file.
PHOTOGRAPH_LINE = "The photograph is the file at this path: {path}"

# What the open reader is sampled at. Pinned, and ported verbatim from the
# measurement: a reader whose output moves between runs cannot replace a
# transcript on the grounds of reproducibility, which was the whole argument for
# adopting it. The budget is this stage's alone -- prose runs longer than one
# word and shorter than sixteen fields (design.md D10).
READER_OPTIONS: Mapping[str, Any] = {
    "temperature": 0,
    "seed": 1,
    "num_predict": 1024,
}

# The one command that turns an absent reader into a present one. It is the
# adapter's rather than the boundary's because the two hosted models are not the
# same kind of name: this one is a machine-local alias built from a committed
# recipe, and the sorter's is a registry tag (design.md D3).
READER_REMEDY = "ollama create {model} -f scripts/joycaption.Modelfile"


@dataclass(frozen=True)
class Reading:
    """What a reader returned: the prose, and what actually produced it."""

    prose: str
    implementation: str
    models: tuple[str, ...] = ()
    pinned: bool = False


class Reader(Protocol):
    """The reader seam. One implementation ships; the double keeps the suite dry."""

    def read(self, photo: Path, briefing: str, workspace: Path) -> Reading:
        """Return prose describing `photo`, following `briefing`."""
        ...


@dataclass(frozen=True)
class FakeReader:
    """An offline stand-in that counts its calls.

    It is what makes the suite's idempotence assertion provable: showing that a
    completed stage makes no call needs something that counts calls.
    """

    prose: str = "A person, described in prose."
    implementation: str = "fake-reader"
    models: tuple[str, ...] = ("fake-model",)
    failure: CliFailure | None = None
    calls: list[tuple[Path, str]] = field(default_factory=list)

    def read(self, photo: Path, briefing: str, workspace: Path) -> Reading:
        """Record the call and return the prose it was constructed with."""
        self.calls.append((photo, briefing))
        if self.failure is not None:
            raise self.failure
        return Reading(self.prose, self.implementation, self.models)


@dataclass(frozen=True)
class ClaudeReader:
    """The `claude -p` adapter: the photograph, the briefing, and `Read`."""

    binary: str = BINARY
    runner: Runner = spawn
    implementation: str = "claude-cli"

    def prompt(self, photo: Path, briefing: str) -> str:
        """Return the whole of what the reader is told: its briefing and the file."""
        return f"{briefing.rstrip()}\n\n{PHOTOGRAPH_LINE.format(path=photo)}\n"

    def argv(self, photo: Path, workspace: Path, briefing: str) -> list[str]:
        """Return the exact argument vector this reader is invoked with."""
        return [
            self.binary,
            "-p",
            self.prompt(photo, briefing),
            *BASE_FLAGS,
            "--tools",
            "Read",
            "--add-dir",
            str(workspace),
        ]

    def read(self, photo: Path, briefing: str, workspace: Path) -> Reading:
        """Invoke the CLI and read prose out of its envelope, or raise."""
        result = invoke(self.argv(photo, workspace, briefing), self.runner, self.binary)
        if not result.result:
            raise CliFailure(
                "permanent", "the envelope carries no prose the stage can read"
            )
        return Reading(result.result, self.implementation, result.models)


@dataclass(frozen=True)
class OllamaReader:
    """The Ollama adapter: the photograph's own bytes, the briefing, and no schema.

    **No schema, and that is measured rather than tidy.** Pressing a reader into a
    field list makes it invent -- told never to leave a field blank, one
    manufactured nineteen identity marks across seven of ten subjects and its
    score fell from 0.518 to 0.307. The sorter is where structure is required, and
    `format` is the field that requires it there.

    **The photograph goes as its own bytes, unresized.** The prototype's encoder
    downscaled through PIL, which is in the `eval` extra and cannot be imported
    from a module `isekai.__main__` reaches. So nothing is resampled, and nothing
    needs to be: the vision tower encodes at patch14-384 whatever it is handed
    (design.md D7).
    """

    model: str
    transport: ollama.Transport = ollama.post
    implementation: str = "ollama"

    def prompt(self, briefing: str) -> str:
        """Return the whole of what the reader is told.

        **The photograph's path is not in it.** The Claude adapter names a path
        because its reader opens the file itself with a `Read` tool; this one is
        handed the bytes, so a path would be an instruction it cannot act on and
        a detail about the operator's machine sent to a model for nothing.
        """
        return f"{briefing.rstrip()}\n"

    def body(self, photo: Path, briefing: str) -> dict[str, Any]:
        """Return the exact request this reader is invoked with.

        A method rather than a local, so the request is assertable without a call
        -- the property `ClaudeReader.argv()` has, for the same reason.
        """
        return {
            "model": self.model,
            "prompt": self.prompt(briefing),
            "images": [base64.b64encode(photo.read_bytes()).decode()],
            "stream": False,
            "options": dict(READER_OPTIONS),
        }

    def read(self, photo: Path, briefing: str, workspace: Path) -> Reading:
        """Send the photograph and return the prose, or raise.

        `workspace` is accepted and unused: it exists because the Claude adapter
        needs a directory to grant `--add-dir` over, and this reader reads the
        file itself. Keeping it in the signature is what keeps one `Reader`
        Protocol rather than two.
        """
        try:
            prose = ollama.ask(
                self.body(photo, briefing),
                remedy=READER_REMEDY.format(model=self.model),
                transport=self.transport,
            )
        except ollama.OllamaFailure as failed:
            raise CliFailure(failed.kind, failed.detail) from failed
        return Reading(prose, self.implementation, (self.model,))


def caption(
    run: Run,
    flow: str,
    reader: Reader,
    *,
    briefing_path: Path,
    new_version: bool = False,
) -> Path | None:
    """Read `run`'s photograph into prose, or do nothing because it is already read.

    **The caption belongs to the flow that asked for it.** The reader still gets
    the photograph and its standing instructions and nothing else -- `flow` never
    reaches it -- but the answer is written under that flow, because the briefing
    it was produced under is part of that flow's frozen directory. Two flows over
    one photograph read it twice, and a flow can no longer inherit a reading
    written to answer a different question (design.md D5).

    Returns the artifact's path when one is written, and None when the stage was
    already complete -- which is the whole of resume at this stage: no special
    mode and no state machine, just a command that does nothing the second time.
    """
    directory = run.directory(flow, CAPTIONS)
    if latest(directory) is not None and not new_version:
        return None

    version = next_version(directory)
    check_budget(STAGE, directory, version, run.id)

    briefing = briefing_text(briefing_path)
    try:
        reading = reader.read(run.photo, briefing, run.path)
    except CliFailure as failed:
        record = record_failure(
            directory,
            version,
            failed.kind,
            {"stage": STAGE, "detail": failed.detail, "envelope": failed.envelope},
        )
        raise refusal_for(
            "reader", run.id, failed, record, f"{flow}/{CAPTIONS}/", STAGE
        ) from failed

    path = directory / artifact_name(version)
    write_json(
        path,
        envelope(
            STAGE,
            {
                "implementation": reading.implementation,
                "models": list(reading.models),
                "pinned": reading.pinned,
                "briefing": instructions_record(briefing_path),
            },
            {"prose": reading.prose},
        ),
    )
    return path


__all__: Sequence[str] = (
    "ClaudeReader",
    "FakeReader",
    "OllamaReader",
    "Reader",
    "Reading",
    "caption",
)
