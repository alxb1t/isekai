"""Resume: run every command twice, and assert nothing moved and nothing was called.

**This is the only assertion that can prove the state model works**, and it needs
no GPU and no network. There is no resume mode and no state machine here, so
there is nothing to corrupt and nothing to repair: a crashed process, a closed
laptop and a week-long pause are the same event, and the answer to all three is
the same invocation.

The doubles are what make the second half of the claim checkable. `FakeReader`
counts its calls and `FakeComfyClient` records every
submission, so "not one external call was made" is a number rather than a hope.
"""

import argparse
import io
import json
import random
import re
import urllib.error
from collections.abc import Sequence
from pathlib import Path

import pytest

from isekai.boundary.wd14 import LocalTagger
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import BUDGETS
from isekai.interface.cli import build_parser, dispatch
from isekai.interface.wiring import Wiring
from isekai.pipeline.caption import FakeReader
from isekai.pipeline.tagging import FakeTagger
from isekai.shared.vocabulary import Vocabulary, read_tags
from tests.conftest import CSV, snapshot
from tests.fakes import FakeComfyClient
from tests.images import jpeg_bytes
from tests.stages import FIELD_MAP, Always, FakeSession, fake_wd14
from tests.transports import FakeTransport

FLOW = "summon-anime-wai"

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
    return Wiring(
        reader=Always(FakeReader(prose="Brown hair, brown eyes, a collared shirt.")),
        tagger=fake_wd14(),
        hosted_tagger=Always(FakeTagger()),
        client=FakeComfyClient(),
        vocabulary=lambda: Vocabulary(
            "wd14/selected_tags.csv",
            "627aef95638667ddcaa3ac8ae625e88ea5b02f51",
            "298633d94d0031d2081c0893f29c82eab7f0df00b08483ba8f29d1e979441217",
            read_tags(CSV),
        ),
        field_map=lambda _: FIELD_MAP,
        runs_root=tmp_path / "runs",
        rng=random.Random(7),
        out=io.StringIO(),
        err=io.StringIO(),
    )


def _args(verb: str, *photos: str, **extra: object) -> argparse.Namespace:
    """Parse one invocation the way the command line does.

    Every stage verb requires `--flow`, so the helper supplies this suite's one
    flow unless the caller names its own.
    """
    selected = extra.pop("flow", FLOW if verb != "show" else None)
    flag = ["--flow", str(selected)] if selected is not None else []
    return build_parser().parse_args([verb, *photos, *flag, *_flags(extra)])


def _flags(extra: dict[str, object]) -> list[str]:
    """Render keyword arguments as the flags the parser reads."""
    rendered: list[str] = []
    for key, value in extra.items():
        flag = f"--{key.replace('_', '-')}"
        rendered.extend([flag] if value is True else [flag, str(value)])
    return rendered


def _calls(wired: Wiring) -> tuple[int, int, int, int]:
    """Return how many times each external double has been reached.

    Four now, not five. **The two taggers are counted separately and both are
    counted**, because they fail differently and one of them is not a network
    call at all: a second pass that re-opened the 467 MB graph would cost ~0.9 s
    per photograph while making no request, so an assertion that only counted
    requests would call that inert.

    **The sorter is gone rather than uncounted.** Stage ② reaches nothing to
    count -- it reads one artifact and routes it through a committed table -- so
    its inertness is the `wd14/` directory's, which the snapshot already covers.
    """
    resolve_reader = wired.reader
    resolve_wd14, resolve_hosted = wired.tagger, wired.hosted_tagger
    client = wired.client
    assert isinstance(resolve_reader, Always)
    assert isinstance(resolve_wd14, Always) and isinstance(resolve_hosted, Always)
    reader = resolve_reader.double
    local = resolve_wd14.double
    assert isinstance(local, LocalTagger)
    session = local.session
    hosted = resolve_hosted.double
    assert isinstance(reader, FakeReader)
    assert isinstance(session, FakeSession)
    assert isinstance(hosted, FakeTagger)
    assert isinstance(client, FakeComfyClient)
    return (
        len(reader.calls),
        session.calls,
        len(hosted.calls),
        len(client.submissions),
    )


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
    after_first = snapshot(wired.runs_root)
    calls = _calls(wired)

    assert _pass(wired, str(photo)) == 0

    assert snapshot(wired.runs_root) == after_first
    assert _calls(wired) == calls


@pytest.mark.spec("cli:resume:second-pass-is-inert")
def test_the_first_pass_actually_produced_something_to_be_inert_about(
    photo: Path, wired: Wiring
) -> None:
    # A resume assertion over an empty directory passes vacuously.
    _pass(wired, str(photo))
    files = snapshot(wired.runs_root)

    names = sorted(files)
    assert any(name.endswith(f"{FLOW}/captions/001.json") for name in names)
    assert any(name.endswith(f"{FLOW}/wd14/001.json") for name in names)
    assert any(name.endswith(f"{FLOW}/tags/001.json") for name in names)
    assert any(name.endswith(f"{FLOW}/sheets/001.json") for name in names)
    assert any(name.endswith(f"{FLOW}/review/001.approved.json") for name in names)
    assert any(name.endswith(f"{FLOW}/prompts/001.json") for name in names)
    assert any(".png" in name for name in names)
    assert _calls(wired) == (1, 1, 1, 1)


@pytest.mark.spec("cli:resume:second-pass-is-inert")
def test_resume_works_from_the_run_id_as_well_as_the_photograph(
    photo: Path, wired: Wiring
) -> None:
    _pass(wired, str(photo))
    after_first = snapshot(wired.runs_root)
    run_id = next(path.name for path in wired.runs_root.iterdir())

    assert _pass(wired, run_id) == 0
    assert snapshot(wired.runs_root) == after_first


# --- the explicit-version flag ------------------------------------------------


@pytest.mark.spec("cli:explicit-versions:repeat-invocation-is-a-no-op")
def test_a_repeat_invocation_writes_nothing_and_reports_completion(
    photo: Path, wired: Wiring
) -> None:
    dispatch(_args("caption", str(photo)), wired)
    before = snapshot(wired.runs_root)
    assert isinstance(wired.out, io.StringIO)
    wired.out.truncate(0), wired.out.seek(0)

    assert dispatch(_args("caption", str(photo)), wired) == 0

    assert snapshot(wired.runs_root) == before
    assert "already complete" in wired.out.getvalue()
    assert _calls(wired)[0] == 1


@pytest.mark.spec("cli:explicit-versions:flag-writes-the-next-version")
def test_the_explicit_flag_writes_the_next_version_and_leaves_the_last_alone(
    photo: Path, wired: Wiring
) -> None:
    dispatch(_args("caption", str(photo)), wired)
    run_id = next(path.name for path in wired.runs_root.iterdir())
    first = wired.runs_root / run_id / FLOW / "captions" / "001.json"
    frozen = first.read_bytes()

    assert dispatch(_args("caption", str(photo), new_version=True), wired) == 0

    assert (wired.runs_root / run_id / FLOW / "captions" / "002.json").exists()
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

    for directory in (f"{FLOW}/captions", f"{FLOW}/sheets", f"{FLOW}/review"):
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
    from isekai.foundation.flow import load_flow
    from isekai.foundation.run import open_run, read_artifact, record_failure
    from isekai.pipeline.caption import OllamaReader
    from isekai.pipeline.generate import photo_resolution, prompt_artifact
    from isekai.pipeline.review import approve, review
    from tests.stages import CAPTION_BRIEFING, caption, sheet

    photo = tmp_path / "bare.jpg"
    photo.write_bytes(jpeg_bytes(640, 480))
    bare = open_run(photo, wired.runs_root)
    flow = load_flow(FLOW)
    messages: list[str] = []
    # `reader` is an optional resolver on `Wiring` -- optional because a ③-only
    # front end composes one without it, and a resolver because the flow names the
    # model it runs. The narrowing below is an assertion about this fixture, not
    # about the code.
    resolve_reader = wired.reader
    assert resolve_reader is not None
    reader = resolve_reader(flow)

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
    schema = flow.schema
    collect(lambda: sheet(bare, schema, wired.vocabulary(), tags=None))
    collect(lambda: review(bare, FLOW))
    collect(lambda: approve(bare, FLOW, schema, wired.vocabulary()))
    collect(lambda: prompt_artifact(bare, flow, schema))
    collect(lambda: photo_resolution(_unreadable(tmp_path)))
    collect(lambda: load_flow("summon-v9"))
    collect(lambda: load_flow(FLOW, _incomplete_flow(tmp_path)))
    # An unreachable host rather than an absent binary: the surviving arm is
    # HTTP to a local port, so there is nothing on PATH to be missing.
    collect(
        lambda: OllamaReader(
            model="a-reader",
            transport=FakeTransport(error=urllib.error.URLError("Connection refused")),
        ).read(photo, "b", tmp_path)
    )

    directory = bare.directory(FLOW, "captions")
    for _ in range(BUDGETS["caption"]):
        record_failure(directory, 1, "transient", {})
    collect(lambda: caption(bare, reader, briefing_path=CAPTION_BRIEFING))
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


def _incomplete_flow(tmp_path: Path) -> Path:
    """Return a flows root holding a flow whose directory is missing a file."""
    from isekai.foundation.flow import MANIFEST_NAME, SIBLINGS, load_flow

    source = load_flow(FLOW).path
    root = tmp_path / "incomplete" / FLOW
    root.mkdir(parents=True)
    (root / MANIFEST_NAME).write_bytes((source / MANIFEST_NAME).read_bytes())
    for name in SIBLINGS[1:]:
        (root / name).write_bytes((source / name).read_bytes())
    return tmp_path / "incomplete"


# The verbs and paths a refusal is allowed to send an operator to. A remedy this
# build cannot perform is worse than no remedy, because it sends somebody looking
# for something that is not there.
# **Every stage verb carries `--flow`**, because every stage verb has required it
# since v0.16. The bare forms this list held until v0.22.1 were the only reason
# `cli:refusals:refusal-names-the-remedy` passed while four refusals printed a
# command argparse refuses -- the scenario text was stronger than the fixture
# bound to it (design.md D10). `show` is the one verb with no `--flow` to carry.
AVAILABLE: Sequence[str] = (
    "python -m isekai caption --flow ",
    "python -m isekai sheet --flow ",
    "python -m isekai review --flow ",
    "python -m isekai approve --flow ",
    "python -m isekai generate --flow ",
    "python -m isekai show",
    "scripts/download_models.sh",
    # The two Ollama remedies, which replaced the `npm install -g` one that told
    # an operator to install a CLI this build no longer reaches.
    "ollama serve",
    "ollama create",
    "npm install",
    "upgrade isekai",
    "convert the photograph",
    "re-export the photograph",
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


@pytest.mark.spec("cli:refusals:refusal-names-the-remedy")
def test_every_command_a_refusal_prints_is_one_this_build_accepts(
    wired: Wiring, tmp_path: Path
) -> None:
    """The remedy is copy-pasteable, which is the only thing that makes it one.

    Not *a command exists with that name* -- `AVAILABLE` above already says
    that, and said it while four refusals printed a stage verb without the
    `--flow` v0.16 made required. This parses what is printed, with the parser
    that ships, so a remedy an operator pastes back cannot be a usage error
    (v0.16 R5, design.md D10).
    """
    from isekai.interface.cli import build_parser

    printed = [
        command
        for message in _every_refusal(wired, tmp_path)
        for command in re.findall(r"`python -m isekai ([^`]+)`", message)
    ]
    # A positive count, so a refactor that stops printing commands at all does
    # not turn this test green by emptying it.
    assert printed

    for command in printed:
        words = command.split()
        # `show` reads a run directory and takes no flow; every other verb does,
        # required, so a bare one would be refused by the parser below.
        expected = [] if words[0] == "show" else ["--flow"]
        assert [word for word in words if word == "--flow"][:1] == expected
        build_parser().parse_args([*words, "an-identifier"])


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


@pytest.mark.spec_exempt("structural: the runs root is a flag, not a fixed path")
def test_the_runs_root_is_a_flag_defaulting_to_the_gitignored_data_root(
    tmp_path: Path,
) -> None:
    from isekai.foundation.run import RUNS_ROOT

    assert build_parser().parse_args(["show"]).runs == RUNS_ROOT
    assert build_parser().parse_args(["show", "--runs", str(tmp_path)]).runs == tmp_path
    # Wherever it points by default, it is inside the one ignored root.
    assert RUNS_ROOT.parent.name == ".data"


# --- assembly happens for the whole batch before any endpoint is acquired ------


def _approved_run(wired: Wiring, tmp_path: Path, name: str) -> str:
    """Carry one photograph all the way to an approved sheet, and return its id."""
    photo = tmp_path / f"{name}.jpg"
    # Distinct bytes per name -- identical bytes are the same run, by design.
    photo.write_bytes(jpeg_bytes(1200, 904 + 8 * (sum(map(ord, name)) % 40)))
    for verb in ("caption", "sheet", "review", "approve"):
        assert dispatch(_args(verb, str(photo)), wired) == 0
    from isekai.foundation.run import open_run

    return open_run(photo, wired.runs_root).id


@pytest.mark.spec("image-generation:assembly:bad-sheet-fails-before-the-session")
def test_every_prompt_is_assembled_before_the_first_render_is_submitted(
    wired: Wiring, tmp_path: Path
) -> None:
    # The acceptance run caught this: dispatching per-item assembled one prompt
    # and then immediately reached for the endpoint, so a malformed third sheet
    # would have been found after a machine was already rented.
    ids = [_approved_run(wired, tmp_path, name) for name in ("one", "two", "three")]
    assert isinstance(wired.client, FakeComfyClient)

    seen: list[str] = []
    real_upload = wired.client.upload_image

    def watched(path: str) -> str:
        seen.append("upload")
        return real_upload(path)

    wired.client.upload_image = watched  # ty: ignore[invalid-assignment]
    assert isinstance(wired.out, io.StringIO)
    wired.out.truncate(0), wired.out.seek(0)

    assert dispatch(_args("generate", *ids), wired) == 0

    lines = wired.out.getvalue().splitlines()
    assembled = [i for i, line in enumerate(lines) if "assembled" in line]
    rendered = [i for i, line in enumerate(lines) if "rendered" in line]
    assert len(assembled) == 3
    assert max(assembled) < min(rendered)
    assert len(seen) == 3


@pytest.mark.spec("image-generation:assembly:assembly-is-local-and-free")
def test_generate_without_a_server_assembles_everything_and_contacts_nothing(
    wired: Wiring, tmp_path: Path
) -> None:
    ids = [_approved_run(wired, tmp_path, name) for name in ("one", "two")]
    wired.client = None
    assert isinstance(wired.out, io.StringIO)
    wired.out.truncate(0), wired.out.seek(0)

    assert dispatch(_args("generate", *ids), wired) == 0

    assert wired.out.getvalue().count("assembled") == 2
    assert "rendered" not in wired.out.getvalue()
    for run_id in ids:
        assert (wired.runs_root / run_id / FLOW / "prompts" / "001.json").exists()


@pytest.mark.spec("cli:generate-signature:count-defaults-to-one")
def test_the_server_flag_has_no_default_so_rendering_is_always_asked_for() -> None:
    assert build_parser().parse_args(["generate", "--flow", FLOW]).server is None


@pytest.mark.spec("cli:refusals:refusal-names-the-remedy")
def test_an_unreachable_endpoint_refuses_naming_the_tunnel_rather_than_a_socket(
    wired: Wiring, tmp_path: Path
) -> None:
    import urllib.error

    run_id = _approved_run(wired, tmp_path, "one")

    class Dead:
        def upload_image(self, path: str) -> str:
            raise urllib.error.URLError(
                ConnectionRefusedError(61, "Connection refused")
            )

        def submit(self, workflow: object) -> str:
            raise AssertionError("nothing should be submitted")

        def history(self, prompt_id: str) -> dict[str, object]:
            raise AssertionError("nothing should be polled")

        def view(self, image: object) -> bytes:
            raise AssertionError("nothing should be downloaded")

    wired.client = Dead()
    assert isinstance(wired.err, io.StringIO)

    assert dispatch(_args("generate", run_id), wired) == 1

    message = wired.err.getvalue()
    assert "could not be reached" in message
    assert "infra/up.sh" in message
    assert "--server" in message
    assert "Traceback" not in message
    # The assembly still happened before the endpoint was reached at all.
    assert (wired.runs_root / run_id / FLOW / "prompts" / "001.json").exists()


# --- resume asks the flow what it produces ------------------------------------


@pytest.mark.spec("run-directory:listings:resume-does-not-assume-an-image-format")
def test_the_completed_output_check_is_not_tied_to_one_format(tmp_path: Path) -> None:
    from isekai.foundation.flow import load_flow
    from isekai.pipeline.generate import rendered_seeds

    flow = load_flow(FLOW)
    directory = tmp_path / "outputs"
    directory.mkdir()
    (directory / f"42{flow.output_suffix}").write_bytes(b"a render")
    (directory / "42.json").write_text("{}")
    # A form no flow here produces: the predicate takes the flow's word for what
    # counts, so this is not one of its outputs.
    (directory / "43.webm").write_bytes(b"not this flow's output")

    assert rendered_seeds(directory, flow.output_suffix) == [42]
    assert rendered_seeds(directory, ".webm") == [43]


@pytest.mark.spec("run-directory:listings:resume-does-not-assume-an-image-format")
def test_no_image_format_is_named_in_the_resume_predicate() -> None:
    import inspect

    from isekai.pipeline.generate import rendered_seeds

    source = inspect.getsource(rendered_seeds)

    for form in (".png", ".jpg", ".jpeg", ".webp"):
        assert form not in source, form
