"""The review surface's startup: what it refuses, and what it never writes down.

Every test here is stdlib-only and in the main suite, because `batch.py` imports
no web framework -- which is the whole reason the startup refusal order lives
there rather than in `app.py`. Nothing in this file needs the `ui` extra; the
endpoints that do are in `tests/test_ui_api.py`.
"""

import importlib.util
import io
import random
import subprocess
import tomllib
from pathlib import Path

import pytest

from isekai.foundation.flow import Schema
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import REVIEW, Run, open_run
from isekai.interface.ui import bundle
from isekai.interface.ui.batch import establish
from isekai.interface.wiring import Wiring
from isekai.pipeline.caption import FakeReader
from isekai.pipeline.review import approve, review
from isekai.pipeline.sheet import FakeSorter
from isekai.shared.vocabulary import Vocabulary
from tests.conftest import snapshot
from tests.images import jpeg_bytes
from tests.stages import caption, sheet

FLOW = "summon-v1"

# The bundle seam. `establish` takes it as an argument rather than reaching for
# `bundle.ensure_built`, so the suite never runs npm and never needs node.
BUNDLE = Path("ui/dist")


def _bundle() -> Path:
    """Stand in for a built browser bundle, without a toolchain in sight."""
    return BUNDLE


@pytest.fixture
def wired(tmp_path: Path, vocabulary: Vocabulary) -> Wiring:
    """Return a ③-only wiring: no reader, no sorter, no transport."""
    return Wiring(
        reader=None,
        sorter=None,
        client=None,
        vocabulary=lambda: vocabulary,
        runs_root=tmp_path / "runs",
        rng=random.Random(0),
        out=io.StringIO(),
        err=io.StringIO(),
    )


# A run id is a digest of the photograph, so two inputs need two photographs --
# identical bytes would collapse a "batch of three" into one run directory and
# quietly make every multi-input assertion here vacuous.
_SIZES = {"ada": (1200, 900), "grace": (1100, 900), "ida": (1000, 900)}


def _input(
    wired: Wiring,
    tmp_path: Path,
    name: str,
    schema: Schema,
    vocabulary: Vocabulary,
    *,
    with_sheet: bool = True,
) -> Run:
    """Open a run carrying a caption and, unless told otherwise, a filled sheet."""
    photo = tmp_path / f"{name}.jpg"
    photo.write_bytes(jpeg_bytes(*_SIZES[name]))
    made = open_run(photo, wired.runs_root)
    caption(made, FakeReader(prose="Dark brown hair, brown eyes."))
    if with_sheet:
        sheet(
            made,
            FakeSorter(answers={"hair_colour": ["dark brown"]}),
            schema,
            vocabulary,
        )
    return made


# --- the refusal order, all of it before a port is bound ----------------------


@pytest.mark.spec("ui:startup:untracked-flow-is-refused")
def test_a_flow_this_build_does_not_track_is_refused_naming_the_ones_it_does(
    wired: Wiring, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    made = _input(wired, tmp_path, "ada", schema, vocabulary)

    with pytest.raises(Refusal) as refused:
        establish(wired, "summon-v9", [made.id], bundle=_bundle)

    assert FLOW in str(refused.value)


@pytest.mark.spec("ui:startup:input-without-a-sheet-is-refused")
def test_an_input_with_no_sheet_is_refused_by_name_and_told_what_to_run(
    wired: Wiring, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    bare = _input(wired, tmp_path, "ada", schema, vocabulary, with_sheet=False)

    with pytest.raises(Refusal) as refused:
        establish(wired, FLOW, [bare.id], bundle=_bundle)

    message = str(refused.value)
    assert bare.id in message
    # The remedy has to be a command this build can actually run -- which is why
    # `review.py`'s was repaired in the same version: startup calls `review()`
    # once per input, so this is the surface's likeliest message.
    assert f"python -m isekai sheet --flow {FLOW}" in message


@pytest.mark.spec("ui:startup:refusals-are-reported-together")
def test_every_input_that_cannot_be_prepared_is_named_in_one_refusal(
    wired: Wiring, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    first = _input(wired, tmp_path, "ada", schema, vocabulary, with_sheet=False)
    ready = _input(wired, tmp_path, "grace", schema, vocabulary)
    second = _input(wired, tmp_path, "ida", schema, vocabulary, with_sheet=False)

    with pytest.raises(Refusal) as refused:
        establish(wired, FLOW, [first.id, ready.id, second.id], bundle=_bundle)

    message = str(refused.value)
    # Ten photographs with two missing sheets must name both and start nothing,
    # rather than making the operator find them one restart at a time.
    assert first.id in message
    assert second.id in message


@pytest.mark.spec("ui:startup:refusals-are-reported-together")
def test_an_identifier_that_is_not_a_run_is_refused_without_creating_one(
    wired: Wiring, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    _input(wired, tmp_path, "ada", schema, vocabulary)
    before = snapshot(wired.runs_root)

    with pytest.raises(Refusal) as refused:
        establish(wired, FLOW, ["not-a-run-at-all"], bundle=_bundle)

    assert "not-a-run-at-all" in str(refused.value)
    assert snapshot(wired.runs_root) == before


@pytest.mark.spec("ui:startup:a-draft-is-opened-for-each-input")
def test_starting_the_surface_takes_a_draft_and_starting_again_takes_no_second(
    wired: Wiring, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    made = _input(wired, tmp_path, "ada", schema, vocabulary)
    directory = made.directory(FLOW, REVIEW)
    assert not directory.exists()

    batch = establish(wired, FLOW, [made.id], bundle=_bundle)

    assert (directory / "001.draft.json").is_file()
    assert batch.draft_path(batch.inputs[0]) == directory / "001.draft.json"

    establish(wired, FLOW, [made.id], bundle=_bundle)

    assert [path.name for path in sorted(directory.iterdir())] == ["001.draft.json"]


# --- the batch is the argument list, and it is never written down -------------


@pytest.mark.spec("ui:batch:no-batch-artifact-is-written")
def test_establishing_a_batch_writes_nothing_that_describes_the_batch(
    wired: Wiring, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    first = _input(wired, tmp_path, "ada", schema, vocabulary)
    second = _input(wired, tmp_path, "grace", schema, vocabulary)

    establish(wired, FLOW, [first.id, second.id], bundle=_bundle)

    written = set(snapshot(wired.runs_root))
    # The only thing startup writes is a draft per input, inside that input's own
    # run. Nothing anywhere says the two belong together (design.md D3).
    assert {name for name in written if "draft" in name} == {
        f"{first.id}/{FLOW}/{REVIEW}/001.draft.json",
        f"{second.id}/{FLOW}/{REVIEW}/001.draft.json",
    }
    assert not any(
        "batch" in name or "session" in name or "surface" in name for name in written
    )


@pytest.mark.spec("ui:batch:approved-count-comes-from-disk")
def test_the_approved_count_follows_the_directory_not_the_batch_in_memory(
    wired: Wiring, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    first = _input(wired, tmp_path, "ada", schema, vocabulary)
    second = _input(wired, tmp_path, "grace", schema, vocabulary)
    batch = establish(wired, FLOW, [first.id, second.id], bundle=_bundle)

    assert batch.approved_count == 0

    # Approved by the verb, beside the running surface. A cached count would go
    # stale here; a directory cannot.
    approve(first, FLOW, schema, vocabulary)

    assert batch.approved_count == 1
    assert batch.approved_path(batch.find(first.id)) is not None
    assert batch.approved_path(batch.find(second.id)) is None


@pytest.mark.spec("ui:batch:no-batch-artifact-is-written")
def test_an_input_outside_the_batch_is_refused_by_name(
    wired: Wiring, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    held = _input(wired, tmp_path, "ada", schema, vocabulary)
    outside = _input(wired, tmp_path, "grace", schema, vocabulary)
    review(outside, FLOW)
    batch = establish(wired, FLOW, [held.id], bundle=_bundle)

    with pytest.raises(Refusal) as refused:
        batch.find(outside.id)

    assert held.id in str(refused.value)


# --- the invariant that replaced a structural guarantee -----------------------


@pytest.mark.spec("ui:invariant:server-never-names-an-artifact")
def test_the_invariant_holds_no_module_of_the_surface_names_an_artifact() -> None:
    """A tripwire, and deliberately not a proof.

    `import artifact_name as name_it` walks straight past this, and a filename
    built by hand in an f-string is invisible to it. A check that overstated
    itself would be worse than none, so what it is worth is written down here
    rather than inferred from the fact that it exists (design.md D11).

    What it does buy is the one failure that matters: an approved artifact
    written around `approve()`'s `validate()` carries a tag outside the
    vocabulary into a prompt, and the first symptom is a render that looks wrong,
    minutes and money later. The same claim held by habit alone in this
    repository was false six times before two releases closed it.
    """
    surface = Path(__file__).resolve().parent.parent / "isekai" / "interface" / "ui"
    forbidden = ("envelope(", "artifact_name(", "write_json(")

    named = {
        f"{path.name}: {name}"
        for path in sorted(surface.rglob("*.py"))
        for name in forbidden
        if name in path.read_text()
    }

    assert named == set(), (
        "the surface passes field values to pipeline functions, and they own the "
        "envelope and the filename"
    )


# --- the bundle: built when it is free, refused when it is not ----------------


@pytest.mark.spec("ui:bundle:a-missing-bundle-is-built")
def test_a_missing_bundle_is_built_before_the_surface_serves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "ui"
    (source / "node_modules").mkdir(parents=True)
    ran: list[list[str]] = []

    def _build(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        """Stand in for `npm run build`, writing what vite would write."""
        ran.append(argv)
        (source / "dist" / "assets").mkdir(parents=True)
        (source / "dist" / "index.html").write_text("<!doctype html>")
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(bundle.shutil, "which", lambda _: "/usr/local/bin/npm")
    monkeypatch.setattr(bundle.subprocess, "run", _build)

    built = bundle.ensure_built(source)

    assert built == source / "dist"
    assert ran == [["npm", "run", "build"]]

    # A second start does not rebuild: the build is free, but it is not instant,
    # and the surface is opened many times a session.
    assert bundle.ensure_built(source) == built
    assert len(ran) == 1


@pytest.mark.spec("ui:bundle:missing-dependencies-refuse-by-name")
def test_absent_fetched_dependencies_refuse_and_name_the_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "ui"
    source.mkdir()
    monkeypatch.setattr(bundle.shutil, "which", lambda _: "/usr/local/bin/npm")

    with pytest.raises(Refusal) as refused:
        bundle.ensure_built(source)

    # A build is local and free and may run implicitly; fetching pulls arbitrary
    # third-party packages, so it is named rather than done (design.md D12).
    assert "npm install" in str(refused.value)
    assert not (source / "dist").exists()


@pytest.mark.spec("ui:bundle:missing-dependencies-refuse-by-name")
def test_an_absent_toolchain_refuses_naming_what_to_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "ui"
    (source / "node_modules").mkdir(parents=True)
    monkeypatch.setattr(bundle.shutil, "which", lambda _: None)

    with pytest.raises(Refusal) as refused:
        bundle.ensure_built(source)

    message = str(refused.value)
    # node is this repository's second system dependency, after the `claude`
    # binary, and the refusal copies `require_binary()`'s shape.
    assert "nodejs.org" in message
    assert "isekai ui" in message


@pytest.mark.spec_exempt("structural: it proves the gate runs the API tests")
def test_the_gate_installs_the_web_framework_the_api_tests_need() -> None:
    # `tests/test_ui_api.py` opens with an `importorskip`, and four `ui`
    # scenarios are bound there and nowhere else. If FastAPI is absent from the
    # environment the gate syncs, that module skips and those four are proved by
    # a test that never runs. So the presence of the framework is itself
    # asserted, here, where its absence is a failure rather than a skip.
    assert importlib.util.find_spec("fastapi") is not None, (
        "FastAPI is absent, so tests/test_ui_api.py will skip and the four `ui` "
        "scenarios bound only there will be proved by nothing -- restore the "
        "`fastapi` pin in pyproject.toml's `dev` dependency group"
    )


@pytest.mark.spec_exempt("structural: it holds two pin lists equal, not a behaviour")
def test_the_extra_and_the_dev_group_pin_the_server_identically() -> None:
    # The `ui` extra is what an operator installs to serve the surface; the
    # `dev` group is what the gate installs to test it. They name the same two
    # packages, so a bump to one that missed the other would have the suite
    # proving a version nobody runs.
    root = Path(__file__).resolve().parent.parent
    config = tomllib.loads((root / "pyproject.toml").read_text())
    extra = set(config["project"]["optional-dependencies"]["ui"])
    dev = set(config["dependency-groups"]["dev"])

    assert extra <= dev, f"the `dev` group is missing {sorted(extra - dev)}"
