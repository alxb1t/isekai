"""A flow that declares one implementation reaches no name from the other.

**The obvious form of this test passes vacuously**, and that is the whole reason
this module exists separately. Monkeypatching `shutil.which` to `None`, as
`tests/test_caption.py` does for the absent-binary refusal, only fires if
`require_binary` is *called* -- so a run that touches no Claude path is green for
the wrong reason, which is precisely the thing under test.

Instead both entry points of the Claude transport are replaced with functions that
raise, and the open flow is run through them. Non-vacuous, offline, and strictly
stronger than the PATH removal it stands in for: the operator's `claude`-off-PATH
run on a real machine remains the acceptance evidence, and this is its
CI-resident twin (design.md D11).
"""

from dataclasses import replace
from pathlib import Path

import pytest

from isekai.boundary import ollama
from isekai.foundation.flow import Flow, load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import CAPTIONS, SHEETS, Run, attempts, open_run, versions
from isekai.interface.wiring import reader_for, sorter_for
from isekai.pipeline.caption import OllamaReader, caption
from isekai.pipeline.sheet import OllamaSorter, sheet
from isekai.shared.vocabulary import Vocabulary
from tests.images import jpeg_bytes
from tests.transports import FakeTransport, sorted_answer

REACHED = "Claude was reached"

PROSE = "Dark brown hair past the shoulders, brown eyes, a white collared shirt."


@pytest.fixture
def sealed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every entry point of the Claude transport raise when it is touched.

    `spawn` is the only thing that starts the process and `require_binary` the
    only thing that looks for it, so between them nothing can reach the CLI
    without tripping one.
    """

    def reached(*args: object, **kwargs: object) -> object:
        raise AssertionError(REACHED)

    monkeypatch.setattr("isekai.boundary.claude_cli.spawn", reached)
    monkeypatch.setattr("isekai.boundary.claude_cli.require_binary", reached)


@pytest.fixture
def run(tmp_path: Path) -> Run:
    """Return a run with a photograph in it and nothing else."""
    photo = tmp_path / "aunt-ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    return open_run(photo, tmp_path / "runs")


def _offline[T](resolved: T, transport: ollama.Transport) -> T:
    """Return `resolved` with its transport replaced, if it has one to replace.

    **The resolution is exercised and the socket is not.** `reader_for` is what
    could wrongly hand back a Claude adapter, so it is called for real; the
    transport is then swapped at the seam the adapter declares for exactly this.
    Monkeypatching `ollama.post` does not work here and the failure is silent: a
    frozen dataclass captures the default in `__init__`, so a patched module
    attribute is never consulted and the call goes to the real host.
    """
    if isinstance(resolved, OllamaReader | OllamaSorter):
        return replace(resolved, transport=transport)
    return resolved


def _stage(flow: Flow, run: Run, vocabulary: Vocabulary, payload: bytes) -> None:
    """Run stages ① and ② of `flow`, resolving each seam the way the CLI does."""
    caption(
        run,
        flow.id,
        _offline(reader_for(flow), FakeTransport(payload={"response": PROSE})),
        briefing_path=flow.caption_briefing_path,
    )
    sheet(
        run,
        flow.id,
        _offline(sorter_for(flow), FakeTransport(raw=payload)),
        flow.schema,
        vocabulary,
        briefing_path=flow.sheet_briefing_path,
    )


@pytest.mark.spec("caption:selection:no-path-reaches-another-implementation")
def test_the_open_flow_captions_and_sorts_without_reaching_claude(
    sealed: None, run: Run, vocabulary: Vocabulary
) -> None:
    """Both stages complete with the Claude transport rigged to explode."""
    flow = load_flow("summon-open-v1")

    _stage(
        flow, run, vocabulary, sorted_answer(flow.schema, hair_colour=["dark brown"])
    )

    assert versions(run.directory(flow.id, CAPTIONS)) == [1]
    assert versions(run.directory(flow.id, SHEETS)) == [1]


@pytest.mark.spec("caption:selection:no-path-reaches-another-implementation")
def test_the_same_test_pointed_at_the_incumbent_flow_reaches_claude(
    sealed: None, run: Run, vocabulary: Vocabulary
) -> None:
    """The falsification, resident rather than performed once by hand.

    `summon-v1` declares no `hosted` block, so it resolves to the CLI arm and the
    sealed transport fires. Without this, the test above would stay green if the
    seal ever stopped sealing -- and would go on looking like a proof.
    """
    flow = load_flow("summon-v1")

    with pytest.raises(AssertionError, match=REACHED):
        _stage(flow, run, vocabulary, b"")


@pytest.mark.spec("caption:failure:decline-is-permanent")
def test_a_permanent_open_failure_reaches_no_other_implementation(
    sealed: None, run: Run
) -> None:
    """No fallback on the failure path, which is where a fallback would be added.

    A decline is a result to be recorded and surfaced, never routed around:
    substituting an implementation would write an artifact whose provenance record
    is untrue. The seal is what proves the substitution did not happen quietly.
    """
    flow = load_flow("summon-open-v1")
    resolved = reader_for(flow)
    assert isinstance(resolved, OllamaReader)
    truncated = replace(
        resolved,
        transport=FakeTransport(payload={"response": "", "done_reason": "length"}),
    )

    with pytest.raises(Refusal):
        caption(run, flow.id, truncated, briefing_path=flow.caption_briefing_path)

    directory = run.directory(flow.id, CAPTIONS)
    assert [one.kind for one in attempts(directory, 1)] == ["permanent"]
    assert versions(directory) == []
