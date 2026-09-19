"""The Ollama boundary: the request it sends, and what it makes of the answer.

Every test here drives an injected `Transport`, so the suite gains no socket and
no server. What is asserted is the classification table -- which answers are worth
another attempt, which will fail the same way every time, and which two are the
operator's one-command fix and must not spend an attempt at all.
"""

import json
import urllib.error
from collections.abc import Mapping
from dataclasses import dataclass, field

import pytest

from isekai.boundary.ollama import (
    GENERATE,
    HOST,
    TIMEOUT,
    OllamaFailure,
    ask,
)
from isekai.foundation.refusal import Refusal

BODY = {"model": "a-model", "prompt": "describe", "stream": False}
REMEDY = "ollama pull a-model"

# A body with no answer in it. Spelled as bytes rather than as an empty mapping
# because `FakeTransport.payload` defaults to `None` meaning "the ordinary
# answer", and a second sentinel to say "an empty object, and I mean it" would be
# one more thing to get wrong than `raw` already handles.
EMPTY_OBJECT = b"{}"


@dataclass(frozen=True)
class FakeTransport:
    """The host, offline: it answers what it was built to answer, and counts calls.

    Hand-written rather than mocked, as every double in this suite is, and it is
    what makes the request body assertable without a socket -- the property
    `ClaudeReader.runner` gives `argv()`.
    """

    status: int = 200
    payload: Mapping[str, object] | None = None
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


# --- the request --------------------------------------------------------------


@pytest.mark.spec_exempt("the endpoint and the ceiling are constants, not behaviour")
def test_the_boundary_speaks_one_endpoint_at_one_ceiling() -> None:
    assert GENERATE == "/api/generate"
    assert HOST == "http://127.0.0.1:11434"
    assert TIMEOUT == 900


@pytest.mark.spec_exempt("structural: the body reaches the transport unaltered")
def test_the_body_is_sent_to_the_generate_endpoint_as_json() -> None:
    transport = FakeTransport()

    ask(BODY, remedy=REMEDY, transport=transport)

    path, sent = transport.sent[0]
    assert path == GENERATE
    assert json.loads(sent) == BODY


@pytest.mark.spec_exempt("structural: the answer comes back from the body")
def test_the_models_own_answer_is_what_comes_back() -> None:
    transport = FakeTransport(payload={"response": "a person, described."})

    assert ask(BODY, remedy=REMEDY, transport=transport) == "a person, described."


# --- the two that refuse rather than spending an attempt ----------------------


@pytest.mark.spec_exempt("the reachability scenarios are bound at the adapters")
def test_nothing_listening_refuses_naming_the_command_that_starts_it() -> None:
    transport = FakeTransport(error=urllib.error.URLError("Connection refused"))

    with pytest.raises(Refusal) as refused:
        ask(BODY, remedy=REMEDY, transport=transport)

    message = str(refused.value)
    assert HOST in message
    assert "ollama serve" in message


@pytest.mark.spec_exempt("the reachability scenarios are bound at the adapters")
def test_an_absent_model_refuses_naming_the_callers_own_remedy() -> None:
    transport = FakeTransport(404, {"error": 'model "a-model" not found'})

    with pytest.raises(Refusal) as refused:
        ask(BODY, remedy=REMEDY, transport=transport)

    message = str(refused.value)
    assert "a-model" in message
    assert REMEDY in message


@pytest.mark.spec_exempt("the reachability scenarios are bound at the adapters")
@pytest.mark.parametrize("error", [urllib.error.URLError("refused"), None])
def test_neither_no_attempt_case_raises_the_retryable_failure(
    error: BaseException | None,
) -> None:
    """Both are `Refusal`, which is what keeps them out of the retry budget.

    A retry budget counts models tried and failed. Neither of these is that, and
    spending an attempt on one leaves a run whose error records have to be deleted
    by hand before it can resume.
    """
    transport = FakeTransport(error=error) if error is not None else FakeTransport(404)

    with pytest.raises(Refusal):
        ask(BODY, remedy=REMEDY, transport=transport)


# --- transient: worth another attempt -----------------------------------------


@pytest.mark.spec_exempt("the failure-kind scenarios are bound at the adapters")
@pytest.mark.parametrize("status", [500, 502, 503])
def test_a_server_error_is_transient(status: int) -> None:
    transport = FakeTransport(status, {"error": "unable to load model"})

    with pytest.raises(OllamaFailure) as failed:
        ask(BODY, remedy=REMEDY, transport=transport)

    assert failed.value.kind == "transient"
    assert str(status) in failed.value.detail


@pytest.mark.spec_exempt("the failure-kind scenarios are bound at the adapters")
def test_a_timeout_is_transient() -> None:
    transport = FakeTransport(error=TimeoutError("timed out"))

    with pytest.raises(OllamaFailure) as failed:
        ask(BODY, remedy=REMEDY, transport=transport)

    assert failed.value.kind == "transient"
    assert str(TIMEOUT) in failed.value.detail


@pytest.mark.spec_exempt("the failure-kind scenarios are bound at the adapters")
def test_a_timeout_wrapped_in_a_url_error_is_still_transient() -> None:
    """The wrapped form must not be read as an unreachable host.

    `URLError` is the refusal row and `TimeoutError` the transient one, and urllib
    delivers a timeout as either depending on where it expired. Read the wrapped
    one as the parent class and the operator is told to start a server that is
    already running, while a retryable failure is spent as a refusal.
    """
    transport = FakeTransport(error=urllib.error.URLError(TimeoutError("timed out")))

    with pytest.raises(OllamaFailure) as failed:
        ask(BODY, remedy=REMEDY, transport=transport)

    assert failed.value.kind == "transient"


# --- permanent: it will fail the same way every time --------------------------


@pytest.mark.spec_exempt("the failure-kind scenarios are bound at the adapters")
def test_a_body_that_is_not_json_is_permanent() -> None:
    transport = FakeTransport(raw=b"<html>gateway</html>")

    with pytest.raises(OllamaFailure) as failed:
        ask(BODY, remedy=REMEDY, transport=transport)

    assert failed.value.kind == "permanent"


@pytest.mark.spec_exempt("the failure-kind scenarios are bound at the adapters")
def test_a_body_that_is_not_an_object_is_permanent() -> None:
    transport = FakeTransport(raw=b"[1, 2, 3]")

    with pytest.raises(OllamaFailure) as failed:
        ask(BODY, remedy=REMEDY, transport=transport)

    assert failed.value.kind == "permanent"


@pytest.mark.spec_exempt("the failure-kind scenarios are bound at the adapters")
@pytest.mark.parametrize(
    "answer", [EMPTY_OBJECT, b'{"response": ""}', b'{"response": "   "}']
)
def test_an_answerless_body_is_permanent(answer: bytes) -> None:
    transport = FakeTransport(raw=answer)

    with pytest.raises(OllamaFailure) as failed:
        ask(BODY, remedy=REMEDY, transport=transport)

    assert failed.value.kind == "permanent"


@pytest.mark.spec_exempt("the failure-kind scenarios are bound at the adapters")
def test_truncation_is_permanent_and_the_detail_says_so() -> None:
    """`done_reason` is in the detail, because without it two failures look alike.

    A truncated answer and a malformed one are indistinguishable from the outside
    and only one of them is fixed by raising the output budget.
    """
    transport = FakeTransport(
        payload={"response": '{"hair": "blo', "done_reason": "length"}
    )

    with pytest.raises(OllamaFailure) as failed:
        ask(BODY, remedy=REMEDY, transport=transport)

    assert failed.value.kind == "permanent"
    assert "length" in failed.value.detail


@pytest.mark.spec_exempt("the failure-kind scenarios are bound at the adapters")
def test_a_status_that_is_neither_ok_nor_a_server_error_is_permanent() -> None:
    transport = FakeTransport(400, {"error": "invalid options"})

    with pytest.raises(OllamaFailure) as failed:
        ask(BODY, remedy=REMEDY, transport=transport)

    assert failed.value.kind == "permanent"


@pytest.mark.spec_exempt("structural: a complete answer is not a failure")
def test_a_complete_answer_with_a_stop_reason_is_returned() -> None:
    transport = FakeTransport(payload={"response": "prose.", "done_reason": "stop"})

    assert ask(BODY, remedy=REMEDY, transport=transport) == "prose."
