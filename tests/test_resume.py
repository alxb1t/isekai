"""Resume: run every command twice, and assert nothing moved and nothing was called.

**This is the only assertion that can prove the state model works**, and it needs
no GPU and no network. There is no resume mode and no state machine here, so
there is nothing to corrupt and nothing to repair: a crashed process, a closed
laptop and a week-long pause are the same event, and the answer to all three is
the same invocation.

The doubles are what make the second half of the claim checkable. `FakeReader`
and `FakeSorter` count their calls and `FakeComfyClient` records every
submission, so "not one external call was made" is a number rather than a hope.
"""

import argparse
import io
import json
import random
from collections.abc import Sequence
from pathlib import Path

import pytest

from isekai.__main__ import Wiring, build_parser, dispatch
from isekai.caption import FakeReader
from isekai.refusal import Refusal
from isekai.run import BUDGETS
from isekai.sheet import FakeSorter, load_schema
from isekai.vocabulary import Vocabulary, read_tags
from tests.fakes import FakeComfyClient
from tests.images import jpeg_bytes
from tests.test_vocabulary import CSV

FLOW = "summon-v1"

# Every verb, in the order a run passes through them. `approve` follows `review`
# with no edit in between, which is a legitimate act: it renders the machine's
# raw sheet as the control the correction is measured against.
VERBS = ("caption", "sheet", "review", "approve", "generate", "show")


@pytest.fixture
def photo(tmp_path: Path) -> Path:
    """Write a photograph outside any run and return its path."""
    path = tmp_path / "ada.jpg"
    path.write_bytes(jpeg_bytes(1200, 900))
    return path


@pytest.fixture
def wired(tmp_path: Path) -> Wiring:
    """Return a wiring with every external thing replaced by a counting double."""
    from isekai.flow import load_flow

    return Wiring(
        reader=FakeReader(prose="Brown hair, brown eyes, a collared shirt."),
        sorter=FakeSorter(
            answers={
                "hair_colour": ["brown"],
                "eye_colour": ["brown"],
                "clothes": ["a crisp collared shirt"],
            }
        ),
        client=FakeComfyClient(),
        schema=load_schema(),
        vocabulary=Vocabulary(
            "wd14/selected_tags.csv",
            "627aef95638667ddcaa3ac8ae625e88ea5b02f51",
            "298633d94d0031d2081c0893f29c82eab7f0df00b08483ba8f29d1e979441217",
            read_tags(CSV),
        ),
        runs_root=tmp_path / "runs",
        present=list(load_flow(FLOW).models),
        rng=random.Random(7),
        out=io.StringIO(),
        err=io.StringIO(),
    )


def _args(verb: str, *photos: str, **extra: object) -> argparse.Namespace:
    """Parse one invocation the way the command line does."""
    return build_parser().parse_args([verb, *photos, *_flags(extra)])


def _flags(extra: dict[str, object]) -> list[str]:
    """Render keyword arguments as the flags the parser reads."""
    rendered: list[str] = []
    for key, value in extra.items():
        flag = f"--{key.replace('_', '-')}"
        rendered.extend([flag] if value is True else [flag, str(value)])
    return rendered


def _snapshot(directory: Path) -> dict[str, bytes]:
    """Return every file under `directory`, by relative name, with its bytes."""
    return {
        str(path.relative_to(directory)): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def _calls(wired: Wiring) -> tuple[int, int, int]:
    """Return how many times each external double has been reached."""
    reader, sorter, client = wired.reader, wired.sorter, wired.client
    assert isinstance(reader, FakeReader)
    assert isinstance(sorter, FakeSorter)
    assert isinstance(client, FakeComfyClient)
    return len(reader.calls), len(sorter.calls), len(client.submissions)


def _pass(wired: Wiring, target: str) -> int:
    """Run every verb once over one target, and return the worst exit status."""
    worst = 0
    for verb in VERBS:
        worst = max(worst, dispatch(_args(verb, target), wired))
    return worst


# --- the whole of resume ------------------------------------------------------


@pytest.mark.spec("cli:resume:second-pass-is-inert")
def test_a_second_full_pass_changes_nothing_and_calls_nothing(
    photo: Path, wired: Wiring
) -> None:
    assert _pass(wired, str(photo)) == 0
    after_first = _snapshot(wired.runs_root)
    calls = _calls(wired)

    assert _pass(wired, str(photo)) == 0

    assert _snapshot(wired.runs_root) == after_first
    assert _calls(wired) == calls


@pytest.mark.spec("cli:resume:second-pass-is-inert")
def test_the_first_pass_actually_produced_something_to_be_inert_about(
    photo: Path, wired: Wiring
) -> None:
    # A resume assertion over an empty directory passes vacuously.
    _pass(wired, str(photo))
    files = _snapshot(wired.runs_root)

    names = sorted(files)
    assert any(name.endswith("captions/001.json") for name in names)
    assert any(name.endswith(f"sheets/{FLOW}/001.json") for name in names)
    assert any(name.endswith(f"review/{FLOW}/001.approved.json") for name in names)
    assert any(name.endswith(f"prompts/{FLOW}/001.json") for name in names)
    assert any(".png" in name for name in names)
    assert _calls(wired) == (1, 1, 1)


@pytest.mark.spec("cli:resume:second-pass-is-inert")
def test_resume_works_from_the_run_id_as_well_as_the_photograph(
    photo: Path, wired: Wiring
) -> None:
    _pass(wired, str(photo))
    after_first = _snapshot(wired.runs_root)
    run_id = next(path.name for path in wired.runs_root.iterdir())

    assert _pass(wired, run_id) == 0
    assert _snapshot(wired.runs_root) == after_first


# --- the explicit-version flag ------------------------------------------------


@pytest.mark.spec("cli:explicit-versions:repeat-invocation-is-a-no-op")
def test_a_repeat_invocation_writes_nothing_and_reports_completion(
    photo: Path, wired: Wiring
) -> None:
    dispatch(_args("caption", str(photo)), wired)
    before = _snapshot(wired.runs_root)
    assert isinstance(wired.out, io.StringIO)
    wired.out.truncate(0), wired.out.seek(0)

    assert dispatch(_args("caption", str(photo)), wired) == 0

    assert _snapshot(wired.runs_root) == before
    assert "already complete" in wired.out.getvalue()
    assert _calls(wired)[0] == 1


@pytest.mark.spec("cli:explicit-versions:flag-writes-the-next-version")
def test_the_explicit_flag_writes_the_next_version_and_leaves_the_last_alone(
    photo: Path, wired: Wiring
) -> None:
    dispatch(_args("caption", str(photo)), wired)
    run_id = next(path.name for path in wired.runs_root.iterdir())
    first = wired.runs_root / run_id / "captions" / "001.json"
    frozen = first.read_bytes()

    assert dispatch(_args("caption", str(photo), new_version=True), wired) == 0

    assert (wired.runs_root / run_id / "captions" / "002.json").exists()
    assert first.read_bytes() == frozen
    assert _calls(wired)[0] == 2


@pytest.mark.spec("run-directory:idempotence:new-version-must-be-asked-for")
def test_without_the_flag_no_next_version_appears_for_any_stage(
    photo: Path, wired: Wiring
) -> None:
    _pass(wired, str(photo))
    run_id = next(path.name for path in wired.runs_root.iterdir())
    run = wired.runs_root / run_id

    _pass(wired, str(photo))

    for directory in ("captions", f"sheets/{FLOW}", f"review/{FLOW}"):
        numbered = sorted(p.name for p in (run / directory).iterdir())
        assert len(numbered) == 1, (directory, numbered)


@pytest.mark.spec("run-directory:idempotence:rerun-is-a-no-op")
def test_no_external_call_is_made_on_a_pass_that_changes_nothing(
    photo: Path, wired: Wiring
) -> None:
    _pass(wired, str(photo))
    calls = _calls(wired)

    for _ in range(3):
        _pass(wired, str(photo))

    assert _calls(wired) == calls


# --- refusals -----------------------------------------------------------------


def _every_refusal(wired: Wiring, tmp_path: Path) -> list[str]:
    """Provoke one refusal from each stage that has one, and return the messages."""
    from isekai.caption import ClaudeReader, caption
    from isekai.flow import load_flow
    from isekai.generate import preflight, prompt_artifact
    from isekai.review import approve, review
    from isekai.run import open_run, read_artifact, record_failure
    from isekai.sheet import load_schema, sheet

    photo = tmp_path / "bare.jpg"
    photo.write_bytes(jpeg_bytes(640, 480))
    bare = open_run(photo, wired.runs_root)
    flow = load_flow(FLOW)
    messages: list[str] = []

    def collect(work: object) -> None:
        try:
            work()  # ty: ignore[call-non-callable]
        except Refusal as refused:
            messages.append(str(refused))
        else:
            raise AssertionError("that was supposed to refuse")

    collect(lambda: open_run(tmp_path / "missing.jpg", wired.runs_root))
    collect(lambda: open_run(_unreadable(tmp_path), wired.runs_root))
    collect(lambda: read_artifact(_future_artifact(tmp_path)))
    collect(lambda: sheet(bare, wired.sorter, wired.schema, wired.vocabulary, [FLOW]))
    collect(lambda: review(bare, FLOW))
    collect(lambda: approve(bare, FLOW, wired.schema, wired.vocabulary))
    collect(lambda: prompt_artifact(bare, flow, wired.schema))
    collect(lambda: preflight(flow, []))
    collect(lambda: load_flow("summon-v9"))
    collect(lambda: load_schema(_future_schema(tmp_path)))
    collect(lambda: ClaudeReader(binary="not-a-real-binary").read(photo, "b", tmp_path))

    directory = bare.directory("captions")
    for _ in range(BUDGETS["caption"]):
        record_failure(directory, 1, "transient", {})
    collect(lambda: caption(bare, wired.reader))
    return messages


def _unreadable(tmp_path: Path) -> Path:
    """Return a file whose bytes this build cannot read as a photograph."""
    path = tmp_path / "notes.txt"
    path.write_bytes(b"this is not a photograph at all")
    return path


def _future_artifact(tmp_path: Path) -> Path:
    """Return an artifact declaring a schema version this build does not know."""
    path = tmp_path / "001.json"
    path.write_text(json.dumps({"schema": {"name": "caption", "version": 99}}))
    return path


def _future_schema(tmp_path: Path) -> Path:
    """Return a schema document declaring a version this build does not read."""
    path = tmp_path / "identity.v99.json"
    path.write_text(json.dumps({"schema": "identity", "version": 99, "fields": []}))
    return path


# The verbs and paths a refusal is allowed to send an operator to. A remedy this
# build cannot perform is worse than no remedy, because it sends somebody looking
# for something that is not there.
AVAILABLE: Sequence[str] = (
    "python -m isekai caption",
    "python -m isekai sheet",
    "python -m isekai review",
    "python -m isekai approve",
    "python -m isekai generate",
    "python -m isekai show",
    "scripts/download_models.sh",
    "npm install -g @anthropic-ai/claude-code",
    "upgrade isekai",
    "convert the photograph",
    "check the path",
    "delete",
    "rename",
    "add the field",
    "correct the field",
    "replace it with a tag",
    "remove the entry",
    "use lowercase",
    "add the graph",
    "add it to",
    "give the path",
    "point the",
    "point at",
    "the flows this build carries",
    "read the record",
    "change `hires_scale`",
    "check the pod's",
    "drop whichever",
)


@pytest.mark.spec("cli:refusals:refusal-names-the-remedy")
def test_every_refusal_names_an_action_this_build_can_perform(
    wired: Wiring, tmp_path: Path
) -> None:
    unhelpful = [
        message
        for message in _every_refusal(wired, tmp_path)
        if not any(remedy in message for remedy in AVAILABLE)
    ]
    assert unhelpful == []


@pytest.mark.spec("cli:refusals:refusal-names-the-remedy")
def test_no_refusal_offers_a_command_this_build_does_not_have(
    wired: Wiring, tmp_path: Path
) -> None:
    # The migration verb is the one that would be most natural to promise and is
    # deliberately absent: only schema version 1 exists, so its dispatch table
    # would have no entries.
    for message in _every_refusal(wired, tmp_path):
        assert "isekai migrate" not in message
        assert "isekai repair" not in message
        assert "isekai reset" not in message


@pytest.mark.spec("cli:refusals:refusal-exits-non-zero")
def test_a_refusal_exits_non_zero_and_writes_its_reason_to_the_error_stream(
    wired: Wiring, tmp_path: Path
) -> None:
    assert isinstance(wired.err, io.StringIO)

    status = dispatch(_args("caption", str(tmp_path / "nothing-here.jpg")), wired)

    assert status == 1
    assert "refused:" in wired.err.getvalue()
    assert "nothing-here.jpg" in wired.err.getvalue()
    assert isinstance(wired.out, io.StringIO)
    assert "nothing-here.jpg" not in wired.out.getvalue()


@pytest.mark.spec("run-directory:budget:one-failure-does-not-halt-the-batch")
def test_one_bad_identifier_does_not_stop_the_rest_of_a_batch(
    photo: Path, wired: Wiring
) -> None:
    status = dispatch(
        _args("caption", str(photo.parent / "missing.jpg"), str(photo)), wired
    )

    assert status == 1
    assert _calls(wired)[0] == 1
    assert len(list(wired.runs_root.iterdir())) == 1
