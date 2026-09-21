"""The Ollama host, offline: one hand-written double, shared by every caller.

Shared here rather than imported from one test module by another, which would
make that module undeletable -- the same rule `tests/images.py` and
`tests/stages.py` are under. The boundary's own tests drive it, and so do both
adapters', because what each of them asserts is the same thing: the request that
went out, and what the stage made of the answer that came back.

Separate from `tests/fakes.py`, which holds the doubles for the boundaries the
runtime reaches on the *rendering* path. This module is the hosted-model side,
and keeping the two apart is what lets the open arm's tests import nothing that
knows about a GPU.

Hand-written rather than mocked. The suite has no HTTP server, no bound socket
and no `unittest.mock`, and this is what keeps it that way while still making the
request body assertable -- the property `ClaudeReader.runner` gives `argv()`.
"""

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FakeTransport:
    """Answers what it was built to answer, and records every request it was sent.

    `payload` is the ordinary case; `raw` states bytes directly, for the bodies
    that are not valid JSON or not objects; `error` raises instead of answering,
    for the two rows that never reach a status at all.
    """

    payload: Mapping[str, object] | None = None
    status: int = 200
    raw: bytes | None = None
    error: BaseException | None = None
    sent: list[tuple[str, bytes]] = field(default_factory=list)

    def __call__(self, path: str, body: bytes) -> tuple[int, bytes]:
        """Record the request, then raise or answer as constructed."""
        self.sent.append((path, body))
        if self.error is not None:
            raise self.error
        if self.raw is not None:
            return self.status, self.raw
        answer = {"response": "prose."} if self.payload is None else self.payload
        return self.status, json.dumps(answer).encode()

    def bodies(self) -> list[dict[str, object]]:
        """Return every request body sent, parsed."""
        return [json.loads(body) for _, body in self.sent]


__all__: Sequence[str] = ("FakeTransport",)
