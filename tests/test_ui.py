"""The app's server-side parts that need no server: the bundle and the invariant.

Nothing in this file needs a web framework; the endpoints are in
`tests/test_ui_api.py`, and the library is in `tests/test_ui_library.py`.
"""

import importlib.util
import os
import subprocess
import time
from pathlib import Path

import pytest

from isekai.foundation.refusal import Refusal
from isekai.interface.ui import bundle

# Every file in `ui/` that is neither `src/` nor an ignored root. `_is_fresh`
# watches them by exclusion rather than by name, so `tsconfig.json` -- which
# `vite` reads and which no allowlist here ever named -- is in this list.
_CONFIGS = ("vite.config.ts", "tsconfig.json", "package.json", "package-lock.json")

# --- the invariant that stands in for a structural guarantee ------------------


@pytest.mark.spec("ui:invariant:server-never-names-an-artifact")
def test_the_invariant_holds_no_module_of_the_surface_names_an_artifact() -> None:
    """A tripwire, and deliberately not a proof.

    `import artifact_name as name_it` walks straight past this, and a filename
    built by hand in an f-string is invisible to it. A check that overstated
    itself would be worse than none, so what it is worth is written down here
    rather than inferred from the fact that it exists.

    What it does buy is the one failure that matters: an approved artifact
    written around `approve()`'s `validate()` carries a tag outside the
    vocabulary into a prompt, and the first symptom is a render that looks wrong,
    minutes and money later. The same claim held by habit alone would go false
    with nothing to say so.
    """
    surface = Path(__file__).resolve().parent.parent / "isekai" / "interface" / "ui"
    forbidden = ("artifact_name(", "write_json(", "write(")

    named = {
        f"{path.name}: {name}"
        for path in sorted(surface.rglob("*.py"))
        for name in forbidden
        if name in path.read_text()
    }

    assert named == set(), (
        "the surface passes field values to pipeline functions, and they own the "
        "file's shape and its name"
    )


# --- the bundle: built when it is free, refused when it is not ----------------


@pytest.mark.spec("ui:bundle:a-missing-bundle-is-built")
def test_a_missing_bundle_is_built_before_the_surface_serves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "ui"
    (source / "node_modules").mkdir(parents=True)
    ran: list[list[str]] = []

    class _Build:
        """Stand in for `npm run build`, writing what vite would write."""

        returncode = 0

        def __init__(self, argv: list[str], **kwargs: object) -> None:
            ran.append(argv)
            (source / "dist" / "assets").mkdir(parents=True)
            (source / "dist" / "index.html").write_text("<!doctype html>")

        def communicate(self, timeout: float | None = None) -> tuple[str, str]:
            return "", ""

    monkeypatch.setattr(bundle.shutil, "which", lambda _: "/usr/local/bin/npm")
    monkeypatch.setattr(bundle.subprocess, "Popen", _Build)

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
    # third-party packages, so it is named rather than done.
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
    # node is one of this repository's two system dependencies, beside Ollama,
    # and its refusal takes the shape both are under.
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
        "`fastapi` pin in pyproject.toml's `dependencies`"
    )


# The manifest's own invariants -- that the server is declared, and declared
# once -- live in `tests/test_packaging.py`. They are not facts about the review
# surface, and split across two feature files they would carry two copies of one
# requirement-name parser.


# --- the bundle is rebuilt when the source moves under it ---------------------


@pytest.mark.spec_exempt("structural: when the on-demand build actually fires")
def test_a_bundle_older_than_its_source_is_rebuilt_rather_than_served(
    tmp_path: Path,
) -> None:
    # The defect this prevents: were `ensure_built` to return any non-empty
    # `dist/`, a bundle built from older source would go on being served while
    # the source sat rebuilt. Silent, and green -- `npm run typecheck` compiles
    # the source and the server reads the build.
    source = tmp_path / "ui"
    (source / "src").mkdir(parents=True)
    (source / "dist").mkdir()
    (source / "index.html").write_text("<!doctype html>")
    (source / "dist" / "index.html").write_text("built")
    component = source / "src" / "App.vue"
    component.write_text("old")
    os.utime(source / "dist" / "index.html", (2_000, 2_000))
    os.utime(component, (1_000, 1_000))
    os.utime(source / "index.html", (1_000, 1_000))

    assert bundle._is_fresh(source / "dist", source)

    # One source file edited after the build is the whole condition.
    os.utime(component, (3_000, 3_000))

    assert not bundle._is_fresh(source / "dist", source)


def _built_tree(tmp_path: Path) -> Path:
    """Return a `ui/` whose `dist/` is newer than every source beside it."""
    source = tmp_path / "ui"
    (source / "src").mkdir(parents=True)
    (source / "dist").mkdir()
    (source / "node_modules").mkdir()
    (source / "index.html").write_text("<!doctype html>")
    (source / "dist" / "index.html").write_text("built")
    (source / "src" / "App.vue").write_text("component")
    for name in _CONFIGS:
        (source / name).write_text("{}")
    for item in source.rglob("*"):
        os.utime(item, (1_000, 1_000))
    os.utime(source / "dist" / "index.html", (2_000, 2_000))
    return source


@pytest.mark.spec("ui:bundle:a-changed-build-input-makes-the-bundle-stale")
@pytest.mark.parametrize("name", _CONFIGS)
def test_a_build_config_edited_after_the_build_makes_the_bundle_stale(
    tmp_path: Path, name: str
) -> None:
    """The inputs outside `src/` that `_is_fresh` watches.

    A bumped dependency, an added vite plugin or a changed build script all
    change the emitted bundle and move nothing under `src/` -- so, unwatched,
    the operator would go on being served the previous build, silently, with a
    green gate. `tsconfig.json` is in this list because the watch is an
    exclusion rather than a list of build inputs: an allowlist naming the other
    three would miss it.
    """
    source = _built_tree(tmp_path)

    assert bundle._is_fresh(source / "dist", source)

    os.utime(source / name, (3_000, 3_000))

    assert not bundle._is_fresh(source / "dist", source)


@pytest.mark.spec("ui:bundle:a-fetched-tree-is-not-an-input")
def test_a_fetched_dependency_tree_is_not_source(tmp_path: Path) -> None:
    # The other half of the exclusion: `node_modules/` is fetched and `dist/` is
    # this function's own output, so neither may make the bundle look stale --
    # `npm install` alone would otherwise force a rebuild on every startup.
    source = _built_tree(tmp_path)
    (source / "node_modules" / "left-pad.js").write_text("module.exports = 1")
    os.utime(source / "node_modules" / "left-pad.js", (3_000, 3_000))

    assert bundle._is_fresh(source / "dist", source)


@pytest.mark.spec("ui:bundle:an-unfinished-build-is-stopped-and-named")
def test_a_build_that_does_not_finish_is_stopped_and_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The ceiling is applied, and it stops the build's whole process group.

    A real stand-in for `npm`, which starts a child the way `npm` starts `vite`:
    killing the parent alone would leave that child building unseen.
    """
    source = tmp_path / "ui"
    (source / "node_modules").mkdir(parents=True)
    child = tmp_path / "child.pid"
    npm = tmp_path / "npm"
    script = f"sleep 60 >/dev/null 2>&1 &\necho $! > {child}\nwait\n"
    npm.write_text(f"#!/bin/sh\n{script}")
    npm.chmod(0o755)
    monkeypatch.setattr(bundle, "BINARY", str(npm))
    # Long enough for the stand-in to start its child on a loaded machine.
    monkeypatch.setattr(bundle, "BUILD_TIMEOUT", 3)

    with pytest.raises(Refusal) as refused:
        bundle.ensure_built(source)

    assert "3 seconds" in str(refused.value)
    assert "by hand" in str(refused.value)
    assert _stops(int(child.read_text()))


def _stops(pid: int) -> bool:
    """Return whether process `pid` is gone, or a zombie, within a few seconds."""
    for _ in range(50):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        state = subprocess.run(
            ["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True
        ).stdout.strip()
        if state.startswith("Z") or not state:
            return True
        time.sleep(0.1)
    return False


@pytest.mark.spec_exempt("structural: when the on-demand build actually fires")
def test_an_absent_or_empty_bundle_is_still_not_fresh(tmp_path: Path) -> None:
    source = tmp_path / "ui"
    (source / "src").mkdir(parents=True)

    assert not bundle._is_fresh(source / "dist", source)

    (source / "dist").mkdir()

    assert not bundle._is_fresh(source / "dist", source)
