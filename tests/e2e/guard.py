"""What a browser test fails on: the faults a context saw, as one pure function."""

from collections.abc import Sequence
from dataclasses import dataclass, field

FAILED_LOAD = "Failed to load resource"


@dataclass(frozen=True)
class Refused:
    """A 4xx a test expects: its status, and what the request's path starts with."""

    status: int
    path: str


@dataclass
class Seen:
    """What a context saw: page errors, console messages, and responses."""

    errors: list[str] = field(default_factory=list)
    consoles: list[tuple[str, str]] = field(default_factory=list)
    responses: list[tuple[int, str]] = field(default_factory=list)


def answered(refusal: Refused, status: int, path: str) -> bool:
    """Return whether a response of `status` at `path` is the one `refusal` declares."""
    return status == refusal.status and path.startswith(refusal.path)


def faults(seen: Seen, expected: Sequence[Refused]) -> list[str]:
    """Return each fault a browser test must fail on, one line each, in order seen."""
    found = [f"page error: {text}" for text in seen.errors]
    found += [
        f"console {kind}: {text}"
        for kind, text in seen.consoles
        if kind == "error" and not text.startswith(FAILED_LOAD)
    ]
    for status, path in seen.responses:
        if status >= 500:
            found.append(f"server error: {status} {path}")
        elif status >= 400 and not any(answered(one, status, path) for one in expected):
            found.append(f"undeclared refusal: {status} {path}")
    found += [
        f"declared refusal never answered: {one.status} {one.path}"
        for one in expected
        if not any(answered(one, status, path) for status, path in seen.responses)
    ]
    return found
