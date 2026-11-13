"""A render session's edits: what runs beside the renders, and what it leaves alone.

The session is `tests/test_render.py`'s, over the real `generate` and `edit --pending`
on a fake transport, or a stub of both where only a verb line is the point. An edit's
images are built here from flat colour, so what it must read is known before it runs.
"""

import fcntl
import io
import json
import random
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from isekai.boundary.comfy import TransportFailure
from isekai.foundation.artifacts import EDIT_FILE, SESSIONS, read
from isekai.foundation.edit import load_edit
from isekai.foundation.flow import Schema, Workflow, graph_digest, load_flow
from isekai.foundation.run import Run, approval_of, failures_alone, record_failure
from isekai.interface import render
from isekai.interface.cli import _dispatch_argv, build_parser, dispatch
from isekai.interface.compare_view import _renders
from isekai.interface.ui import library
from isekai.pipeline.edit import discard_edit, pending, request
from isekai.pipeline.generate import (
    discard_render,
    is_render,
    is_sidecar,
    rendered_seeds,
)
from isekai.shared.vocabulary import Vocabulary
from tests.fakes import RecordingComfyClient
from tests.stages import bare_wiring
from tests.test_render import (
    FLOW,
    LOCAL_PORT,
    Calls,
    FakeOpen,
    counted,
    log,
    real,
    session,
)

EDIT = load_edit("tattoo-wai")
SKIN = (200, 150, 120)
SIDE = 400
SAMPLED = (10, 200, 30)
CROP_SIDE = 1216
# The tattoo's square, as rows and columns of the 400 px render.
INKED = slice(80, 120)


def _png(pixels: "np.ndarray") -> bytes:
    """Return `pixels` encoded as a PNG."""
    body = io.BytesIO()
    Image.fromarray(pixels).save(body, "PNG")
    return body.getvalue()


def _pod(*, failing: bool = False) -> RecordingComfyClient:
    """Return a client whose pod answers a flat crop, and may reject an edit's graph.

    An edit's graph is the one holding the union ControlNet node; a render's graph
    is accepted either way, so a failing pod still lets a session render.
    """
    flat = np.full((CROP_SIDE, CROP_SIDE, 3), SAMPLED, dtype=np.uint8)

    class Pod(RecordingComfyClient):
        def submit(self, workflow: Workflow) -> str:
            held = {node["class_type"] for node in workflow.values()}
            if failing and "SetUnionControlNetType" in held:
                raise TransportFailure("permanent", "the endpoint rejected the graph")
            return super().submit(workflow)

    return Pod(view_bytes=_png(flat))


def _group(run: Run) -> Path:
    """Return the group `counted`'s approval renders into."""
    return run.path / FLOW / "outputs" / "002"


def _request(tmp_path: Path, run: Run, seed: int = 1, *, sampling: int = 5) -> Path:
    """Make render `seed` of `run` a real image and request an edit of it.

    Return the edit's record, pending beside the render.
    """
    render_pixels = np.full((SIDE, SIDE, 3), SKIN, dtype=np.uint8)
    composite = render_pixels.copy()
    composite[INKED, INKED] = (composite[INKED, INKED] * 0.5 + 0.5).astype(np.uint8)
    image = _group(run) / f"{seed}.png"
    image.write_bytes(_png(render_pixels))
    kept = tmp_path / f"composite-{seed}.png"
    kept.write_bytes(_png(composite))
    asked = request(
        EDIT, image, kept, overrides={}, seed=sampling, rng=random.Random(1)
    )
    return asked.record


def _marker(group: Path, names: Sequence[str], **held: object) -> None:
    """Write each of `names` in `group` as an edit's record holding `held`."""
    group.mkdir(parents=True, exist_ok=True)
    for name in names:
        (group / name).write_text(json.dumps({"schema": EDIT_FILE.schema, **held}))


@pytest.mark.spec("edit:session:a-pending-edit-runs-beside-the-renders")
def test_edit_render_a_pending_edit_runs_after_the_render_in_the_same_pod(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = counted(tmp_path, schema, vocabulary, "ada", 1)
    root = tmp_path / "b" / "runs"
    record = _request(tmp_path, run)
    pod, opener = _pod(), FakeOpen()

    status = session(
        root,
        generate=_dispatch_argv,
        wiring=real(root, vocabulary),
        client=pod,
        opener=opener,
    )

    group = _group(run)
    told = log(root)
    assert status == 0, told
    assert opener.opened == 1
    assert len(rendered_seeds(group, ".png")) == 2
    assert (group / "1.edit-1.png").is_file()
    assert told.index(f"{run.id}: rendered") < told.index(
        f"{run.id}: edited {FLOW}/1.edit-1.png"
    )
    # The render's graph went first, the edit's last.
    classes = [
        {node["class_type"] for node in graph.values()} for graph in pod.submissions
    ]
    assert "SetUnionControlNetType" not in classes[0]
    assert "SetUnionControlNetType" in classes[-1]
    body = read(record, EDIT_FILE)
    assert body["graph_sha256"] == graph_digest(pod.submissions[-1])
    assert body["runtime"]["comfyui_version"]
    assert isinstance(body["duration"], float)


@pytest.mark.spec("edit:session:a-changed-source-refuses-before-the-pod")
def test_edit_render_a_changed_source_refuses_before_anything_is_rented(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = counted(tmp_path, schema, vocabulary, "ada", 1)
    root = tmp_path / "b" / "runs"
    _request(tmp_path, run)
    (_group(run) / "1.png").write_bytes(_png(np.full((SIDE, SIDE, 3), 90, np.uint8)))
    pod, opener = _pod(), FakeOpen()

    status = session(
        root,
        generate=_dispatch_argv,
        wiring=real(root, vocabulary),
        client=pod,
        opener=opener,
    )

    assert status == 1
    assert (opener.opened, pod.submissions, pod.uploads) == (0, [], [])
    assert "refused: 1.edit-1.json: its source 1.png has changed" in log(root)
    assert len(rendered_seeds(_group(run), ".png")) == 1


@pytest.mark.spec("edit:session:a-session-may-hold-edits-alone")
def test_edit_render_a_session_may_hold_edits_alone(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = counted(tmp_path, schema, vocabulary, "ada", 2)
    root = tmp_path / "b" / "runs"
    record = _request(tmp_path, run)
    pod, opener = _pod(), FakeOpen()

    status = session(
        root,
        generate=_dispatch_argv,
        wiring=real(root, vocabulary),
        client=pod,
        opener=opener,
    )

    assert status == 0, log(root)
    assert opener.opened == 1
    assert len(pod.submissions) == 1
    assert (_group(run) / "1.edit-1.png").is_file()
    assert len(rendered_seeds(_group(run), ".png")) == 2
    assert "duration" in read(record, EDIT_FILE)
    # The session's own record is a render's: it plans no image for the edit.
    (opened,) = (root.parent / SESSIONS).glob("*.json")
    ended = json.loads(opened.read_text())
    assert ended["planned"] == []
    assert (ended["outcome"], ended["message"]) == ("done", None)


@pytest.mark.spec("edit:session:a-flow-taken-out-takes-its-edits-out")
def test_edit_render_a_flow_taken_out_leaves_its_edit_pending(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = counted(tmp_path, schema, vocabulary, "ada", 2)
    root = tmp_path / "b" / "runs"
    record = _request(tmp_path, run)
    opener = FakeOpen()

    status = session(
        root,
        without=[root / run.id / FLOW],
        generate=_dispatch_argv,
        wiring=real(root, vocabulary),
        client=_pod(),
        opener=opener,
    )

    assert status == 0
    assert opener.opened == 0
    assert pending(_group(run)) == [record]
    assert "nothing is short of its count; nothing was rented" in log(root)


@pytest.mark.spec("edit:session:a-flow-taken-out-takes-its-edits-out")
def test_edit_render_the_cells_are_each_run_and_flow_less_what_is_taken_out(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    kept = counted(tmp_path, schema, vocabulary, "ada", 2)
    taken = counted(tmp_path, schema, vocabulary, "beatrix", 2)
    root = tmp_path / "b" / "runs"
    for run in (kept, taken):
        _marker(_group(run), ["1.edit-1.json"])
    calls = Calls()

    status = session(root, without=[root / taken.id / FLOW], generate=calls)

    assert status == 0, log(root)
    cell = f"{kept.id}/{FLOW}"
    server = f"http://127.0.0.1:{LOCAL_PORT}"
    assert calls.lines == [
        ["edit", "--pending", cell, "--runs", str(root)],
        ["edit", "--progress", "json", "--pending", cell]
        + ["--server", server, "--runs", str(root)],
    ]
    assert [line[0] for line in calls.rendered()] == ["edit"]


@pytest.mark.spec("edit:session:a-request-runs-no-edit")
def test_edit_render_a_request_runs_no_edit(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = counted(tmp_path, schema, vocabulary, "ada", 1)
    root = tmp_path / "b" / "runs"
    _marker(_group(run), ["1.edit-1.json"])
    calls = Calls()

    assert session(root, f"{FLOW}=1", generate=calls) == 0

    assert {line[0] for line in calls.lines} == {"generate"}
    assert pending(_group(run)) == [_group(run) / "1.edit-1.json"]


@pytest.mark.spec("edit:session:a-failed-sampling-leaves-the-request-pending")
def test_edit_render_a_rejected_graph_fails_the_session_and_leaves_the_edit_pending(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = counted(tmp_path, schema, vocabulary, "ada", 2)
    root = tmp_path / "b" / "runs"
    record = _request(tmp_path, run)

    status = session(
        root,
        generate=_dispatch_argv,
        wiring=real(root, vocabulary),
        client=_pod(failing=True),
    )

    told = log(root)
    assert status == 1
    assert "the sampling failed (permanent) -- the endpoint rejected the graph" in told
    assert f"python -m isekai discard {_group(run) / '1.edit-1.png'}" in told
    assert not (_group(run) / "1.edit-1.png").exists()
    assert pending(_group(run)) == [record]
    (held,) = (root.parent / SESSIONS).glob("*.json")
    ended = json.loads(held.read_text())
    assert (ended["outcome"], ended["message"]) == (
        "failed",
        "a flow failed; the collection's log names it",
    )


# --- the listings --------------------------------------------------------------


def _with_an_edit(group: Path, seed: int) -> None:
    """Write an edit's image, record and composite for `seed` into `group`."""
    _marker(group, [f"{seed}.edit-1.json"], source=f"{seed}.png")
    for suffix in (".png", ".composite.png"):
        (group / f"{seed}.edit-1{suffix}").write_bytes(b"x")


@pytest.mark.spec("edit:listing:the-listings-skip-an-edit")
def test_edit_listing_the_seeds_and_the_predicates_read_the_render_alone(
    tmp_path: Path,
) -> None:
    group = tmp_path / "outputs" / "001"
    group.mkdir(parents=True)
    (group / "42.png").write_bytes(b"png")
    (group / "42.render.json").write_text("{}")
    _with_an_edit(group, 42)

    assert rendered_seeds(group, ".png") == [42]
    assert not any(is_render(path, ".png") for path in group.glob("*.edit-*")), (
        "an edit's image is no render"
    )
    assert [path.name for path in group.iterdir() if is_sidecar(path)] == [
        "42.render.json"
    ]


@pytest.mark.spec("edit:listing:the-listings-skip-an-edit")
def test_edit_listing_a_cell_and_the_evaluator_list_the_render_alone(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = counted(tmp_path, schema, vocabulary, "ada", 1)
    root = tmp_path / "b" / "runs"
    group = _group(run)
    _with_an_edit(group, 1)
    flow = load_flow(FLOW)

    cell = library.stage(run, flow)

    assert cell.renders == 1
    assert [(image.version, image.seed) for image in cell.images] == [(2, 1)]
    assert cell.newest is not None and cell.newest.seed == 1
    figures = _renders(run, FLOW, flow, root.parent)
    assert len(figures) == 1
    assert "edit-1" not in figures[0]


@pytest.mark.spec_exempt("structural: the group listing is what the discard tests")
def test_edit_group_a_group_holding_an_edits_file_is_no_group_of_failure_records(
    tmp_path: Path,
) -> None:
    group = tmp_path / "outputs" / "001"
    group.mkdir(parents=True)
    record_failure(group, 1, "permanent", {"stage": "render", "seed": 7, "detail": "x"})
    failure = next(group.iterdir())

    assert failures_alone(group) == [failure]

    (group / "7.edit-1.json").write_text("{}")

    assert failures_alone(group) is None


# --- the discard ---------------------------------------------------------------


def _chain(group: Path) -> None:
    """Write edits 1 and 3 of seed 42 from the render, and 2 from the first edit."""
    group.mkdir(parents=True, exist_ok=True)
    (group / "42.png").write_bytes(b"png")
    for number, source in ((1, "42.png"), (2, "42.edit-1.png"), (3, "42.png")):
        _marker(group, [f"42.edit-{number}.json"], source=source)
        (group / f"42.edit-{number}.composite.png").write_bytes(b"x")
    for number in (1, 2):
        (group / f"42.edit-{number}.png").write_bytes(b"x")


@pytest.mark.spec("edit:discard:a-render-takes-its-edits")
def test_edit_discard_a_render_takes_every_edit_of_its_seed_and_no_other(
    tmp_path: Path,
) -> None:
    group = tmp_path / "runs" / "0123456789ab_a" / FLOW / "outputs" / "001"
    (group.parents[2] / "run.json").parent.mkdir(parents=True, exist_ok=True)
    (group.parents[2] / "run.json").write_text("{}")
    _chain(group)
    (group / "7.png").write_bytes(b"png")
    _with_an_edit(group, 7)

    deleted = discard_render(group / "42.png")

    assert sorted(path.name for path in deleted) == [
        "42.edit-1.composite.png",
        "42.edit-1.json",
        "42.edit-1.png",
        "42.edit-2.composite.png",
        "42.edit-2.json",
        "42.edit-2.png",
        "42.edit-3.composite.png",
        "42.edit-3.json",
        "42.png",
    ]
    assert sorted(path.name for path in group.iterdir()) == [
        "7.edit-1.composite.png",
        "7.edit-1.json",
        "7.edit-1.png",
        "7.png",
    ]


@pytest.mark.spec("edit:discard:an-edit-takes-its-chain")
def test_edit_discard_an_edit_takes_the_edits_made_from_it_and_the_render_stays(
    tmp_path: Path,
) -> None:
    group = tmp_path / "runs" / "0123456789ab_a" / FLOW / "outputs" / "001"
    group.parents[2].mkdir(parents=True)
    (group.parents[2] / "run.json").write_text("{}")
    _chain(group)

    deleted = discard_edit(group / "42.edit-1.png")

    assert sorted(path.name for path in deleted) == [
        "42.edit-1.composite.png",
        "42.edit-1.json",
        "42.edit-1.png",
        "42.edit-2.composite.png",
        "42.edit-2.json",
        "42.edit-2.png",
    ]
    assert sorted(path.name for path in group.iterdir()) == [
        "42.edit-3.composite.png",
        "42.edit-3.json",
        "42.png",
    ]


@pytest.mark.spec("edit:discard:an-edit-takes-its-chain")
def test_edit_discard_a_pending_edit_is_named_by_the_path_its_image_will_have(
    tmp_path: Path,
) -> None:
    group = tmp_path / "runs" / "0123456789ab_a" / FLOW / "outputs" / "001"
    group.parents[2].mkdir(parents=True)
    (group.parents[2] / "run.json").write_text("{}")
    _chain(group)

    deleted = discard_edit(group / "42.edit-3.png")

    assert sorted(path.name for path in deleted) == [
        "42.edit-3.composite.png",
        "42.edit-3.json",
    ]
    assert (group / "42.edit-1.png").is_file()


@pytest.mark.spec("edit:discard:an-edit-takes-its-chain")
def test_edit_discard_an_unreadable_record_in_the_chain_deletes_nothing(
    tmp_path: Path,
) -> None:
    group = tmp_path / "runs" / "0123456789ab_a" / FLOW / "outputs" / "001"
    group.parents[2].mkdir(parents=True)
    (group.parents[2] / "run.json").write_text("{}")
    _chain(group)
    (group / "42.edit-2.json").write_text("{ not json")
    before = sorted(path.name for path in group.iterdir())

    with pytest.raises(Exception, match="42.edit-2.json"):
        discard_edit(group / "42.edit-1.png")

    assert sorted(path.name for path in group.iterdir()) == before


def _discard(wired_path: Path, image: Path) -> tuple[int, str, str]:
    """Run `discard` on `image`; return its exit and streams."""
    wired = bare_wiring(runs_root=wired_path)
    args = build_parser().parse_args(["discard", str(image)])
    assert isinstance(wired.out, io.StringIO)
    assert isinstance(wired.err, io.StringIO)
    return dispatch(args, wired), wired.out.getvalue(), wired.err.getvalue()


@pytest.mark.spec("cli:discard:an-edits-path-discards-the-edit")
def test_edit_discard_the_verb_deletes_an_edit_and_keeps_the_render_and_approval(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = counted(tmp_path, schema, vocabulary, "ada", 1)
    group = _group(run)
    _with_an_edit(group, 1)
    before = sorted(path.name for path in group.iterdir() if "edit" not in path.name)

    code, out, err = _discard(tmp_path, group / "1.edit-1.png")

    where = f"{run.id}/{FLOW}/outputs/002"
    assert (code, err) == (0, "")
    assert out.splitlines() == [
        f"discard deleted {where}/1.edit-1.png",
        f"discard deleted {where}/1.edit-1.json",
        f"discard deleted {where}/1.edit-1.composite.png",
    ]
    assert sorted(path.name for path in group.iterdir()) == before
    assert approval_of(run, FLOW, 2).is_file()


@pytest.mark.spec("cli:discard:a-render-takes-its-edits-with-it")
@pytest.mark.spec("edit:discard:the-last-render-with-an-edit-takes-its-approval")
def test_edit_discard_the_last_render_with_an_edit_takes_the_group_and_the_approval(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = counted(tmp_path, schema, vocabulary, "ada", 1)
    group = _group(run)
    _with_an_edit(group, 1)

    code, out, err = _discard(tmp_path, group / "1.png")

    where = f"{run.id}/{FLOW}/outputs/002"
    assert (code, err) == (0, "")
    printed = out.splitlines()
    for name in ("1.edit-1.png", "1.edit-1.json", "1.edit-1.composite.png"):
        assert f"discard deleted {where}/{name}" in printed
    assert f"discard deleted {where}" in printed
    assert not group.exists()
    assert not approval_of(run, FLOW, 2).exists()


@pytest.mark.spec("edit:discard:a-running-session-refuses-it")
def test_edit_discard_a_running_session_refuses_an_edits_path(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = counted(tmp_path, schema, vocabulary, "ada", 1)
    (tmp_path / "b" / "sources").mkdir()
    group = _group(run)
    _with_an_edit(group, 1)
    record = tmp_path / "b" / SESSIONS / "20261024T091200Z"
    record.parent.mkdir()
    record.with_suffix(".json").write_text("{}")

    with record.with_suffix(".lock").open("w") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        code, out, err = _discard(tmp_path, group / "1.edit-1.png")

    assert (code, out) == (1, "")
    assert "A render session is running" in err
    assert (group / "1.edit-1.png").is_file()


@pytest.mark.spec("cli:discard:a-path-naming-no-render-is-refused")
@pytest.mark.parametrize("name", ["1.edit-1.json", "1.edit-0.png", "01.edit-1.png"])
def test_edit_discard_a_path_that_is_no_render_and_no_edit_names_both_forms(
    name: str, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = counted(tmp_path, schema, vocabulary, "ada", 1)
    group = _group(run)
    (group / name).write_bytes(b"x")
    before = sorted(path.name for path in group.iterdir())

    code, out, err = _discard(tmp_path, group / name)

    assert (code, out) == (1, "")
    assert err.startswith(f"refused: {group / name}: ")
    assert "<run>/<flow>/outputs/<NNN>/<seed>.png" in err
    assert "<run>/<flow>/outputs/<NNN>/<seed>.edit-<k>.png" in err
    assert sorted(path.name for path in group.iterdir()) == before


@pytest.mark.spec_exempt(
    "structural: the quote and the session agree on the edits' cells"
)
def test_edit_render_the_discard_of_an_edit_leaves_the_session_nothing_to_run(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = counted(tmp_path, schema, vocabulary, "ada", 2)
    root = tmp_path / "b" / "runs"
    _marker(_group(run), ["1.edit-1.json"], source="1.png")
    (_group(run) / "1.edit-1.composite.png").write_bytes(b"x")
    assert render.edits_of(root, [run.id], {FLOW}, []).cells == (f"{run.id}/{FLOW}",)

    _discard(tmp_path, _group(run) / "1.edit-1.png")

    assert render.edits_of(root, [run.id], {FLOW}, []).cells == ()
