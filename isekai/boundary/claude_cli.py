"""The `claude -p` boundary: one locked-down invocation, one JSON envelope.

**The second network boundary in this repository, and the only one the pipeline
has.** Stages (1) and (2) both reach a hosted model through the CLI, so the
invocation, the envelope and the failure classification live here once rather
than twice -- the same discipline `ComfyTransport` is under, for the same reason:
one seam, one fake, one place a flag can be wrong.

**Why the CLI and not an API.** The runtime declares `dependencies = []`, so an
SDK is not available; the choice was raw HTTP or the CLI. The CLI needs no key
handling and no per-token budget, and it is closer to what was actually measured
-- the reading score this design is built on came from an agent session with
tools, not from a bare completion call (design.md D6).

**Three flags are load-bearing**, and each is here because leaving it out breaks
something specific:

- `--safe-mode`. By default the CLI discovers a `CLAUDE.md` from the working
  directory. Run from this repository, a stage would get sixteen kilobytes about
  *this repository* injected into the context that is supposed to describe a
  photograph. The minimal-mode flag was rejected: it forces API-key
  authentication and defeats the point of using the CLI.
- `--tools`. The reader needs `Read` and nothing else; the sorter needs nothing
  at all. A stage that can run shell commands is not a stage.
- `--permission-prompts none`. Without it a misconfigured stage waits for a
  human forever.

**The output is always the JSON envelope, never plain text**, because the
envelope is what carries the error status, the stop reason, the permission
denials and which models actually ran.

**There is no fallback model.** A fallback would render the artifact on a
different model than the one asked for, and the whole provenance discipline is
that a producer names what actually produced it.

Stdlib only.
"""

import json
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from isekai.foundation.refusal import Refusal
from isekai.foundation.run import Kind, StageFailure

# The binary every stage resolves on PATH. New for this repository: tooling has
# always resolved binaries, the runtime never has. It is bounded -- the open,
# digest-pinned readers a later version brings remove it.
BINARY = "claude"

# The flags every stage passes, whatever it is doing.
BASE_FLAGS: tuple[str, ...] = (
    "--safe-mode",
    "--strict-mcp-config",
    "--no-session-persistence",
    "--permission-prompts",
    "none",
    "--output-format",
    "json",
)

# What an envelope has to say for a failure to be worth another attempt. A rate
# limit, a server error or a timeout will pass; anything else -- a decline, a
# denied permission, a response that does not match the required structure --
# will fail the same way every time, so retrying it spends for nothing.
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

# Stop reasons that mean the model declined rather than failed.
DECLINED: frozenset[str] = frozenset({"refusal", "declined"})


class Runner(Protocol):
    """How a process is started. Faked, so the argument vector itself is testable."""

    def __call__(self, argv: Sequence[str]) -> tuple[int, str, str]:
        """Run `argv` and return its exit status, standard output and error."""
        ...


def spawn(argv: Sequence[str]) -> tuple[int, str, str]:
    """Run `argv` to completion, capturing both streams."""
    done = subprocess.run(list(argv), capture_output=True, text=True)
    return done.returncode, done.stdout, done.stderr


def require_binary(binary: str = BINARY) -> None:
    """Refuse, naming what to install, when the CLI is not on this machine.

    The posture the evaluator already takes for an absent optional dependency:
    state the command that would fix it. It matters more here, because this is the
    first thing a fresh clone touches.
    """
    if shutil.which(binary) is None:
        raise Refusal(
            f"{binary!r} is not on PATH, and stages 1 and 2 are the two that "
            "need it; install the Claude Code CLI and sign in "
            "(`npm install -g @anthropic-ai/claude-code`, then `claude`), then "
            "run this command again"
        )


@dataclass(frozen=True)
class Envelope:
    """One parsed `--output-format json` result, and what actually produced it."""

    result: str
    structured: Any
    models: tuple[str, ...]


def invoke(
    argv: Sequence[str], runner: Runner = spawn, binary: str = BINARY
) -> Envelope:
    """Run one locked-down invocation and return its envelope, or raise.

    The binary check is here rather than at each call site: every caller in the
    repository ran it immediately before invoking, which makes it part of
    invoking rather than a thing to remember.
    """
    require_binary(binary)
    status, out, err = runner(argv)
    try:
        parsed: Any = json.loads(out)
    except ValueError:
        raise StageFailure(
            classify_text(f"{status} {err}"),
            f"the CLI returned no JSON envelope (exit {status}): "
            f"{(err or out).strip()[:400]}",
        ) from None
    if not isinstance(parsed, dict):
        raise StageFailure("permanent", "the envelope is not an object")
    kind = classify(parsed, status)
    if kind is not None:
        raise StageFailure(kind, detail(parsed), parsed)
    return Envelope(
        result=str(parsed.get("result", "")).strip(),
        structured=parsed.get("structured_output"),
        models=models_that_ran(parsed),
    )


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

    Measured rather than assumed. A rate limit, a server error or a timeout is
    transient. A decline, a denied permission, any other error status and a
    response that does not match the required structure are permanent, because
    each will come back the same way on the next attempt.
    """
    if str(parsed.get("stop_reason", "")).lower() in DECLINED:
        return "permanent"
    if parsed.get("permission_denials"):
        return "permanent"
    if (
        not parsed.get("is_error")
        and not parsed.get("api_error_status")
        and status == 0
    ):
        return None
    return classify_text(
        " ".join(
            str(parsed.get(key, ""))
            for key in ("api_error_status", "subtype", "error", "result", "stop_reason")
        )
    )


def detail(parsed: Mapping[str, Any]) -> str:
    """Return the one line of a failed envelope worth putting in an error record."""
    for key in ("api_error_status", "error", "result", "subtype"):
        value = parsed.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:400]
    return "the CLI failed and the envelope says nothing about why"


def models_that_ran(parsed: Mapping[str, Any]) -> tuple[str, ...]:
    """Return every model the envelope says actually ran, not the one asked for.

    A probe of this invocation returned two in a single envelope -- the model
    requested, and a smaller one doing the CLI's own internal work. The record
    names what ran (design.md D7).
    """
    usage = parsed.get("modelUsage")
    if isinstance(usage, dict):
        return tuple(sorted(str(name) for name in usage))
    model = parsed.get("model")
    return (str(model),) if isinstance(model, str) and model else ()
