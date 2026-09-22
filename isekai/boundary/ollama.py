"""The Ollama boundary: one POST to a local runtime, and what its answer means.

**The second network boundary, and since v0.22 the only one the pipeline has.**
Stage (1)'s reader and its hosted tagger both reach their model through this
module, so the request, the classification and the two refusals live here once
rather than twice -- the same discipline `ComfyTransport` is already under.

**There was a second transport beside this one**, `claude_cli.py`, and an
isolation law keeping a flow that declared one arm from reaching a name from the
other. v0.22 deleted it, so the law has nothing left to separate. Nothing in the
gate would catch a second transport being reintroduced; what makes one visible is
that there is no registry to add an entry to -- a second reader is a second
adapter, in review (design.md D18, D27).

**`/api/generate`, not the OpenAI-compatible endpoint**, and the two missing
fields are why. `think: false` is load-bearing because a hybrid reasoner draws its
thinking tokens from the same budget as its answer -- they truncated the sorter's
JSON mid-string on the third subject -- and `repeat_penalty` because at
temperature 0 there is no sampling noise to break a loop, and one field came back
with `"white robe"` forty times until the budget ran out. The compatible endpoint
expresses neither, so using it would re-measure the two known failure modes of the
model this repository is adopting (design.md D1).

**The address is a module constant and cannot be configured.** Not a flag, not an
environment variable: the runtime reads no environment at all, a fixed local
address is what `interface/ui/` and `interface/cli.py` already do, and an operator
-controlled destination for a photograph is a security surface this version
declines to open. `--server`'s deliberate no-default exists because rendering
costs money; a free loopback call does not inherit that reason (design.md D4).
**Which is why the opener is built by hand**: `urlopen`'s default carries a proxy
read from the environment, and urllib bypasses loopback for no address it was not
explicitly told to -- so `http_proxy` alone would have made the photograph's
destination configurable after all, by a variable nobody chose.

**There is no adapter in this file.** `OllamaReader` and `OllamaTagger` live
beside their twins in `pipeline/`, because two implementations of one Protocol in
two different layers is the thing that arrangement avoids.

Stdlib only.
"""

import http.client
import json
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from isekai.foundation.refusal import Refusal
from isekai.foundation.run import Kind

# Where the runtime listens. Fixed, and see the module docstring for why there is
# no way to say otherwise.
HOST = "http://127.0.0.1:11434"

# The one endpoint this repository speaks. Named rather than inlined so the two
# adapters and their tests agree on it by construction.
GENERATE = "/api/generate"

# The opener every request goes through, and the empty mapping is the whole point
# of it. `urllib.request.urlopen` uses a default opener whose `ProxyHandler` is
# built from `getproxies()`, and urllib does **not** auto-bypass loopback -- only
# an explicit `no_proxy` entry does. So on a machine with `http_proxy` exported,
# the default opener addresses `127.0.0.1:11434` to the proxy instead, and a
# photograph base64-encoded into the body goes with it. `ProxyHandler({})` reads
# no environment at all, which is what makes `HOST` reachable by no configuration
# rather than merely undocumented (design.md D4).
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

# One ceiling, for both stages, and it is a ceiling on a hang rather than a
# budget. The prototype used 300 for the reader and 900 for the sorter because it
# ran many reader calls in a row and only the first was a cold load. This pipeline
# alternates the two stages and **the two models do not co-reside in 16 GiB**, so
# every transition evicts the other and the next call is cold either way. Two
# numbers would be a knob with no measurement behind it (design.md D10).
TIMEOUT = 900

# The host's own answer to "truncated or malformed". Without it the two are
# indistinguishable and only one of them is fixed by raising the output budget.
TRUNCATED = "length"


class OllamaFailure(Exception):
    """The host answered and a stage cannot use it; the kind says what comes next.

    Deliberately not `run.StageFailure`, which is the *stage's* vocabulary and
    would make a boundary depend on one, and deliberately not a third vocabulary
    either: it carries the same `Kind` the run directory already records, so an
    adapter translates it in one line and the stage that catches it is unchanged.
    """

    def __init__(self, kind: Kind, detail: str) -> None:
        """Carry the kind and the detail an error record is written from."""
        super().__init__(detail)
        self.kind = kind
        self.detail = detail


class Transport(Protocol):
    """How a request is sent. Faked, so the request body itself is testable.

    The same shape `ComfyTransport` is under, for the same reason: it is what
    makes the request body assertable without a socket, and the suite has none.
    """

    def __call__(self, path: str, body: bytes) -> tuple[int, bytes]:
        """POST `body` to `path` and return the status and the response bytes."""
        ...


def post(path: str, body: bytes) -> tuple[int, bytes]:
    """POST `body` to `HOST` at `path`, returning the status and the bytes.

    **`HTTPError` is caught first because it is a subclass of `URLError`**, and
    the two mean opposite things here: one is a host that answered with a status
    worth reading, the other is no host at all. Catching the parent first labels
    every 404 and every 502 as "did not answer", which is exactly the bug the
    prototype's single handler had (design.md D9).

    A status is a return value rather than an exception, so a fake transport
    states one the same way a real host does.

    **`OPENER`, not `urlopen`**, so no proxy the environment happens to name can
    stand between this call and the loopback address above.
    """
    request = urllib.request.Request(
        f"{HOST}{path}", data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with OPENER.open(request, timeout=TIMEOUT) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as answered:
        return answered.code, answered.read()


def ask(
    body: Mapping[str, Any],
    *,
    remedy: str,
    transport: Transport = post,
) -> str:
    """Return the model's own answer to `body`, or refuse, or raise.

    `remedy` is the one command that fixes an absent model, and the caller supplies
    it rather than this module holding one: which command fixes an absent model
    depends on how that model was named, and a boundary that knew that would know
    the flow. Both callers here build a machine-local alias with `ollama create`;
    a registry tag fetched by `ollama pull` is the other shape, and the manifest
    still names one.

    **A missing model and a missing host refuse rather than spending an attempt.**
    A retry budget counts models tried and failed, and neither of those is that;
    both are the operator's one-command fix, and spending an attempt on one leaves
    a run whose error records have to be deleted by hand before it resumes. It is
    the posture this repository already takes for an absent system dependency,
    applied to a **port and a model name** rather than to a `PATH` entry, which is
    the shape a hosted model needs and a binary check cannot give (design.md D9).

    **A connection that drops mid-answer is transient, and catching it is not
    optional.** urllib wraps only what the send raised; anything `getresponse()`
    or `read()` raises comes out as an `http.client` exception or a bare socket
    error, neither of which is a `URLError`. Uncaught, it is not an
    `OllamaFailure`, so no adapter translates it, not a `StageFailure`, so no
    stage records it, and not a `Refusal`, so `run.across()` does not collect it -- one
    evicted model would end the whole batch in a traceback with nothing written
    down. The host being OOM-killed between two models that do not co-reside is
    the designed-in condition, not an exotic one.
    """
    model = str(body["model"])
    # Serialised into a local and the mapping dropped before the call: a
    # photograph goes on this wire base64-encoded, so `body` can hold tens of
    # megabytes and the request another copy of them -- for as long as the call
    # runs, which this module caps at `TIMEOUT`. Nothing below reads `body`.
    request = json.dumps(body).encode()
    del body
    try:
        status, payload = transport(GENERATE, request)
    except (OSError, http.client.HTTPException) as failed:
        # The whole surface a socket presents, in the order the three answers
        # differ. `OSError` covers `TimeoutError`, `URLError` and the reset
        # family; `HTTPException` covers what a truncated response raises, which
        # is not an `OSError` at all.
        #
        # **A timeout can arrive raw or wrapped in a `URLError`**, and the first
        # two branches are opposite answers: one waits again, the other tells the
        # operator to start a server. Read the wrapped form as its parent class
        # and a retryable failure is spent as a refusal.
        expired = isinstance(failed, TimeoutError) or isinstance(
            getattr(failed, "reason", None), TimeoutError
        )
        if expired:
            raise OllamaFailure(
                "transient", f"{model} did not answer within {TIMEOUT}s"
            ) from failed
        if isinstance(failed, urllib.error.URLError):
            # urllib wraps what the *send* raised, so this is a connection that
            # was never made: no host, refused port, unresolvable name.
            raise Refusal(
                f"nothing is listening at {HOST}, and stages 1 and 2 of this flow "
                "are the two that need it; start the runtime (`ollama serve`), "
                "then run this command again"
            ) from failed
        # Everything left reached a host and lost it. Transient rather than a
        # refusal: telling the operator to start a server that answered and then
        # died points away from the eviction that actually happened.
        raise OllamaFailure(
            "transient",
            f"{HOST} dropped the connection while {model} was answering "
            f"({type(failed).__name__})",
        ) from failed

    if status == 404:
        raise Refusal(
            f"{HOST} does not carry the model {model!r} this flow declares; "
            f"create it (`{remedy}`), then run this command again"
        )
    if status >= 500:
        raise OllamaFailure("transient", f"{HOST} answered {status} for {model}")
    if status != 200:
        raise OllamaFailure("permanent", f"{HOST} answered {status} for {model}")

    try:
        answered: Any = json.loads(payload)
    except json.JSONDecodeError:
        raise OllamaFailure(
            "permanent", f"{model} returned a body that is not JSON"
        ) from None
    if not isinstance(answered, Mapping):
        raise OllamaFailure(
            "permanent", f"{model} returned a body that is not an object"
        )

    reason = answered.get("done_reason")
    if reason == TRUNCATED:
        raise OllamaFailure(
            "permanent",
            f"{model} stopped at the output budget (done_reason {TRUNCATED!r}); "
            "the answer is truncated rather than malformed",
        )
    answer = answered.get("response")
    if not isinstance(answer, str) or not answer.strip():
        raise OllamaFailure(
            "permanent",
            f"{model} returned no answer the stage can read (done_reason {reason!r})",
        )
    return answer


__all__: Sequence[str] = (
    "GENERATE",
    "HOST",
    "OPENER",
    "TIMEOUT",
    "OllamaFailure",
    "Transport",
    "ask",
    "post",
)
