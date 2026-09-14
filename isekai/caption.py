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

Stdlib only. The network is behind `Reader`; `isekai.claude_cli` is the one
implementation of it, and `FakeReader` is what keeps the suite offline.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from isekai.claude_cli import (
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
from isekai.run import (
    Run,
    artifact_name,
    check_budget,
    envelope,
    latest,
    next_version,
    record_failure,
    write_json,
)

BRIEFINGS_DIR = Path(__file__).resolve().parent.parent / "briefings"
BRIEFING_PATH = BRIEFINGS_DIR / "caption.md"

# The stage's own directory inside a run, and the name its budget is keyed by.
STAGE = "caption"
DIRECTORY = "captions"

# The photograph's path goes *in the prompt*. A trailing positional after the
# prompt is silently ignored by the CLI's argument parser, which would leave the
# reader told to describe a photograph and never told where it is; `--add-dir` is
# what grants the read, and this line is what points at the file.
PHOTOGRAPH_LINE = "The photograph is the file at this path: {path}"


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


def caption(
    run: Run,
    reader: Reader,
    *,
    new_version: bool = False,
    briefing_path: Path = BRIEFING_PATH,
) -> Path | None:
    """Read `run`'s photograph into prose, or do nothing because it is already read.

    Returns the artifact's path when one is written, and None when the stage was
    already complete -- which is the whole of resume at this stage: no special
    mode and no state machine, just a command that does nothing the second time.
    """
    directory = run.directory(DIRECTORY)
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
            "reader", run.id, failed, record, f"{DIRECTORY}/", STAGE
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
    "BRIEFING_PATH",
    "ClaudeReader",
    "FakeReader",
    "Reader",
    "Reading",
    "caption",
)
