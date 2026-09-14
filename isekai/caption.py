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

Stdlib only. The network is behind `Reader`, and `FakeReader` is what keeps the
suite offline.
"""

import hashlib
import json
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from isekai.refusal import Refusal
from isekai.run import (
    Kind,
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

# The stage's own directory inside a run, and the name the budget is keyed by.
STAGE = "caption"
DIRECTORY = "captions"

# The invocation, and three of its flags are load-bearing (design.md D6):
#
#   --safe-mode ................ by default the CLI discovers a CLAUDE.md from the
#       working directory. Run from this repository, the reader would get sixteen
#       kilobytes about this repository injected into the context that is supposed
#       to describe a photograph. The minimal-mode flag was rejected: it forces
#       API-key authentication and defeats the point of using the CLI at all.
#   --tools Read ............... the reader needs to open the photograph and needs
#       nothing else. A stage that can run shell commands is not a stage.
#   --permission-prompts none .. without it a misconfigured stage waits for a
#       human forever.
#
# The output is always the JSON envelope, never plain text, because the envelope
# is what carries the error status, the stop reason and which models actually ran.
BASE_FLAGS: tuple[str, ...] = (
    "--safe-mode",
    "--strict-mcp-config",
    "--no-session-persistence",
    "--permission-prompts",
    "none",
    "--output-format",
    "json",
)

# What the envelope has to say for a failure to be worth another attempt. A rate
# limit, a server error or a timeout will pass; anything else -- a decline, a
# denied permission, a response that is not prose -- will fail the same way every
# time, so retrying it spends for nothing.
TRANSIENT_MARKERS: tuple[str, ...] = (
    "rate_limit",
    "rate limit",
    "overloaded",
    "timeout",
    "timed out",
    "api_error",
    "server error",
    "internal server",
    "503",
    "502",
    "500",
)


@dataclass(frozen=True)
class Reading:
    """What a reader returned: the prose, and what actually produced it."""

    prose: str
    implementation: str
    models: tuple[str, ...] = ()
    pinned: bool = False


class ReaderFailure(Exception):
    """The reader did not produce prose, and the kind says whether to try again."""

    def __init__(
        self, kind: Kind, detail: str, envelope: Mapping[str, Any] | None = None
    ) -> None:
        """Carry the kind and the detail the error record is written from."""
        super().__init__(detail)
        self.kind = kind
        self.detail = detail
        self.envelope = dict(envelope or {})


class Reader(Protocol):
    """The one network boundary of this stage, and the only thing faked in it."""

    def read(self, photo: Path, briefing: str, workspace: Path) -> Reading:
        """Return prose describing `photo`, following `briefing`."""
        ...


class Runner(Protocol):
    """How a reader's process is started. Faked so the argument vector is testable."""

    def __call__(self, argv: Sequence[str]) -> tuple[int, str, str]:
        """Run `argv` and return its exit status, standard output and error."""
        ...


def _spawn(argv: Sequence[str]) -> tuple[int, str, str]:
    """Run `argv` to completion, capturing both streams."""
    done = subprocess.run(list(argv), capture_output=True, text=True)
    return done.returncode, done.stdout, done.stderr


@dataclass(frozen=True)
class FakeReader:
    """An offline stand-in that counts its calls.

    It is what makes the suite's idempotence assertion provable: showing that a
    completed stage makes no call needs something that counts calls.
    """

    prose: str = "A person, described in prose."
    implementation: str = "fake-reader"
    models: tuple[str, ...] = ("fake-model",)
    failure: ReaderFailure | None = None
    calls: list[tuple[Path, str]] = field(default_factory=list)

    def read(self, photo: Path, briefing: str, workspace: Path) -> Reading:
        """Record the call and return the prose it was constructed with."""
        self.calls.append((photo, briefing))
        if self.failure is not None:
            raise self.failure
        return Reading(self.prose, self.implementation, self.models)


@dataclass(frozen=True)
class ClaudeReader:
    """The `claude -p` adapter: one locked-down invocation, one JSON envelope."""

    binary: str = "claude"
    runner: Runner = _spawn
    implementation: str = "claude-cli"

    def argv(self, photo: Path, workspace: Path, briefing: str) -> list[str]:
        """Return the exact argument vector this reader is invoked with."""
        return [
            self.binary,
            "-p",
            briefing,
            *BASE_FLAGS,
            "--tools",
            "Read",
            "--add-dir",
            str(workspace),
            "--",
            str(photo),
        ]

    def read(self, photo: Path, briefing: str, workspace: Path) -> Reading:
        """Invoke the CLI and read prose out of its envelope, or raise."""
        if shutil.which(self.binary) is None:
            raise Refusal(
                f"{self.binary!r} is not on PATH, and stages 1 and 2 are the two "
                "that need it; install the Claude Code CLI and sign in "
                "(`npm install -g @anthropic-ai/claude-code`, then `claude`), "
                "then run this command again"
            )
        status, out, err = self.runner(self.argv(photo, workspace, briefing))
        return _reading(status, out, err, self.implementation)


def _reading(status: int, out: str, err: str, implementation: str) -> Reading:
    """Turn one invocation's result into prose, or into a classified failure."""
    try:
        parsed: Any = json.loads(out)
    except ValueError:
        raise ReaderFailure(
            classify_text(f"{status} {err}"),
            f"the reader returned no JSON envelope (exit {status}): "
            f"{(err or out).strip()[:400]}",
        ) from None
    if not isinstance(parsed, dict):
        raise ReaderFailure("permanent", "the envelope is not an object")
    kind = classify(parsed, status)
    if kind is not None:
        raise ReaderFailure(kind, _detail(parsed), parsed)
    prose = parsed.get("result")
    if not isinstance(prose, str) or not prose.strip():
        raise ReaderFailure(
            "permanent",
            "the envelope carries no prose the stage can read",
            parsed,
        )
    return Reading(prose.strip(), implementation, models_that_ran(parsed))


def classify_text(text: str) -> Kind:
    """Say whether a failure described by `text` is worth another attempt."""
    lowered = text.lower()
    return (
        "transient"
        if any(marker in lowered for marker in TRANSIENT_MARKERS)
        else "permanent"
    )


def classify(parsed: Mapping[str, Any], status: int = 0) -> Kind | None:
    """Classify an envelope: None when it succeeded, otherwise its failure kind.

    Measured rather than assumed: a rate limit, a server error or a timeout is
    transient, and any other error status, a declined request, a denied permission
    or a response that does not match the required structure is permanent.
    """
    declined = str(parsed.get("stop_reason", "")).lower() in {"refusal", "declined"}
    if declined:
        return "permanent"
    if not parsed.get("is_error") and status == 0:
        return None
    return classify_text(
        " ".join(
            str(parsed.get(key, ""))
            for key in ("subtype", "error", "result", "stop_reason")
        )
    )


def _detail(parsed: Mapping[str, Any]) -> str:
    """Return the one line of a failed envelope worth putting in an error record."""
    for key in ("error", "result", "subtype"):
        value = parsed.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:400]
    return "the reader failed and the envelope says nothing about why"


def models_that_ran(parsed: Mapping[str, Any]) -> tuple[str, ...]:
    """Return every model the envelope says actually ran, not the one asked for.

    A probe showed two in a single envelope -- the model requested, and a smaller
    one doing the CLI's own internal work. The record names what ran.
    """
    usage = parsed.get("modelUsage")
    if isinstance(usage, dict):
        return tuple(sorted(str(name) for name in usage))
    model = parsed.get("model")
    return (str(model),) if isinstance(model, str) and model else ()


def briefing_text(path: Path = BRIEFING_PATH) -> str:
    """Return the reader's standing instructions."""
    return path.read_text()


def briefing_record(path: Path = BRIEFING_PATH) -> dict[str, str]:
    """Return the path and digest of the instruction text, for the producer.

    This is the variable the evidence says matters most: one change to a reader's
    instructions moved its score from 0.518 to 0.307 and manufactured nineteen
    identity marks. An artifact whose provenance names the model but not the
    instructions cannot explain its own result (design.md D7).
    """
    root = Path(__file__).resolve().parent.parent
    resolved = path.resolve()
    inside = resolved.is_relative_to(root)
    return {
        "path": str(resolved.relative_to(root)) if inside else resolved.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


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
    directory = run.path / DIRECTORY
    if latest(directory) is not None and not new_version:
        return None

    version = next_version(directory)
    check_budget(STAGE, directory, version, run.id)

    briefing = briefing_text(briefing_path)
    try:
        reading = reader.read(run.photo, briefing, run.path)
    except ReaderFailure as failed:
        record = record_failure(
            directory,
            version,
            failed.kind,
            {"stage": STAGE, "detail": failed.detail, "envelope": failed.envelope},
        )
        raise Refusal(
            f"{run.id}: the reader failed ({failed.kind}) -- {failed.detail}; "
            f"see {record.name} in {DIRECTORY}/, and run `python -m isekai "
            f"caption` again once what it names is fixed"
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
                "briefing": briefing_record(briefing_path),
            },
            {"prose": reading.prose},
        ),
    )
    return path
