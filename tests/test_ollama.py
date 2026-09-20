"""The Ollama boundary: the request it sends, and what it makes of the answer.

Every test here drives an injected `Transport`, so the suite gains no socket and
no server. What is asserted is the classification table -- which answers are worth
another attempt, which will fail the same way every time, and which two are the
operator's one-command fix and must not spend an attempt at all.
"""

import http.client
import json
import urllib.error
import urllib.request
from collections.abc import Mapping

import pytest

from isekai.boundary.ollama import (
    GENERATE,
    HOST,
    TIMEOUT,
    OllamaFailure,
    ask,
    post,
)
from isekai.foundation.refusal import Refusal
from tests.transports import FakeTransport

BODY = {"model": "a-model", "prompt": "describe", "stream": False}
REMEDY = "ollama pull a-model"


# --- the request --------------------------------------------------------------


@pytest.mark.spec_exempt("the endpoint and the ceiling are constants, not behaviour")
def test_the_boundary_speaks_one_endpoint_at_one_ceiling() -> None:
    assert GENERATE == "/api/generate"
    assert HOST == "http://127.0.0.1:11434"
    assert TIMEOUT == 900


class RefusingConnection(http.client.HTTPConnection):
    """Stands in for the real connection and refuses, naming the host it was given.

    The only stand-in in this file that is not a `Transport`, because the thing
    under test is `post` itself -- which address urllib resolves the request to,
    below the seam every other test here drives. Nothing binds a socket: the
    connection refuses before it would open one, and the host it names is the
    assertion.
    """

    def request(
        self,
        method: str,
        url: str,
        body: object = None,
        headers: Mapping[str, object] | None = None,
        *,
        encode_chunked: bool = False,
    ) -> None:
        """Refuse, carrying the address this connection was constructed for."""
        raise ConnectionRefusedError(f"asked for {self.host}:{self.port}")


@pytest.mark.spec_exempt("structural: no environment may redirect a fixed address")
def test_no_proxy_in_the_environment_can_capture_the_photograph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A configured proxy must not stand between this call and the loopback host.

    urllib does **not** auto-bypass a proxy for loopback -- only an explicit
    `no_proxy` entry does -- and `urlopen`'s default opener builds its
    `ProxyHandler` from the environment. So an exported `http_proxy` would send
    every photograph, base64 in the body, to whatever it names: the one
    destination this module says it will not open, reached by a variable nobody
    chose.

    The second half is the falsification. Without it this test would pass on a
    machine that simply has no proxy set, which is every machine the suite
    usually runs on.
    """
    monkeypatch.setenv("http_proxy", "http://proxy.invalid:8080")
    monkeypatch.setenv("https_proxy", "http://proxy.invalid:8080")
    monkeypatch.setattr(http.client, "HTTPConnection", RefusingConnection)

    with pytest.raises(urllib.error.URLError) as refused:
        post(GENERATE, b"{}")

    assert str(refused.value.reason) == "asked for 127.0.0.1:11434"

    with pytest.raises(urllib.error.URLError) as captured:
        urllib.request.build_opener().open(
            urllib.request.Request(f"{HOST}{GENERATE}", data=b"{}"), timeout=TIMEOUT
        )

    assert str(captured.value.reason) == "asked for proxy.invalid:8080"


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
    transport = FakeTransport(
        payload={"error": 'model "a-model" not found'}, status=404
    )

    with pytest.raises(Refusal) as refused:
        ask(BODY, remedy=REMEDY, transport=transport)

    message = str(refused.value)
    assert "a-model" in message
    assert REMEDY in message


# --- transient: worth another attempt -----------------------------------------


@pytest.mark.spec_exempt("the failure-kind scenarios are bound at the adapters")
@pytest.mark.parametrize("status", [500, 502, 503])
def test_a_server_error_is_transient(status: int) -> None:
    transport = FakeTransport(payload={"error": "unable to load model"}, status=status)

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


@pytest.mark.spec_exempt("the failure-kind scenarios are bound at the adapters")
@pytest.mark.parametrize(
    "dropped",
    [
        http.client.RemoteDisconnected("Remote end closed connection"),
        http.client.IncompleteRead(b"partia", 94),
        ConnectionResetError(54, "Connection reset by peer"),
    ],
    ids=["remote-disconnected", "incomplete-read", "connection-reset"],
)
def test_a_connection_dropped_mid_answer_is_transient(dropped: BaseException) -> None:
    """The drop family must not escape, and must not be read as an absent host.

    urllib wraps only what the send raised, so nothing here is a `URLError`:
    uncaught, none of them is an `OllamaFailure`, a `CliFailure` or a `Refusal`,
    and one evicted model would take the whole batch down in a traceback with no
    error record written. Transient rather than a refusal, because the host did
    answer -- telling the operator to start `ollama serve` points away from the
    eviction that actually happened.
    """
    transport = FakeTransport(error=dropped)

    with pytest.raises(OllamaFailure) as failed:
        ask(BODY, remedy=REMEDY, transport=transport)

    assert failed.value.kind == "transient"
    assert type(dropped).__name__ in failed.value.detail


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
@pytest.mark.parametrize("answer", [b"{}", b'{"response": ""}', b'{"response": "   "}'])
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
    transport = FakeTransport(payload={"error": "invalid options"}, status=400)

    with pytest.raises(OllamaFailure) as failed:
        ask(BODY, remedy=REMEDY, transport=transport)

    assert failed.value.kind == "permanent"


@pytest.mark.spec_exempt("structural: a complete answer is not a failure")
def test_a_complete_answer_with_a_stop_reason_is_returned() -> None:
    transport = FakeTransport(payload={"response": "prose.", "done_reason": "stop"})

    assert ask(BODY, remedy=REMEDY, transport=transport) == "prose."
