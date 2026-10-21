import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import test_ui
from tools.test_ui import NO_MODULES, NO_NPM, refusal


def _ui(root: Path, *, modules: bool) -> Path:
    (root / "ui").mkdir()
    if modules:
        (root / "ui" / "node_modules").mkdir()
    return root


@pytest.mark.spec_exempt("structural: the gate's browser tests refuse without npm")
def test_no_npm_is_refused_naming_what_installs_it(tmp_path: Path) -> None:
    root = _ui(tmp_path, modules=True)
    assert refusal(root, which=lambda name: None) == NO_NPM


@pytest.mark.spec_exempt(
    "structural: the gate's browser tests refuse without ui/node_modules/"
)
def test_absent_node_modules_is_refused_naming_npm_install(tmp_path: Path) -> None:
    root = _ui(tmp_path, modules=False)
    assert refusal(root, which=lambda name: f"/bin/{name}") == NO_MODULES
    assert "run `npm install` in ui/" in NO_MODULES


@pytest.mark.spec_exempt("structural: twin of the browser tests' refusals")
def test_a_ready_tree_is_not_refused(tmp_path: Path) -> None:
    root = _ui(tmp_path, modules=True)
    assert refusal(root, which=lambda name: f"/bin/{name}") is None


@pytest.mark.spec_exempt("structural: the browser tests run in ui/ and keep the code")
def test_the_tests_run_in_ui_and_return_their_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _ui(tmp_path, modules=True)
    ran: list[tuple[list[str], Path]] = []

    def run(command: list[str], cwd: Path, check: bool) -> SimpleNamespace:
        ran.append((command, cwd))
        return SimpleNamespace(returncode=3)

    monkeypatch.setattr(test_ui.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(subprocess, "run", run)
    assert test_ui.main(root) == 3
    assert ran == [(["npm", "run", "test"], root / "ui")]


@pytest.mark.spec_exempt("structural: a refusal runs nothing and exits 1")
def test_a_refusal_runs_nothing_and_exits_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _ui(tmp_path, modules=False)
    monkeypatch.setattr(test_ui.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("ran npm"))
    assert test_ui.main(root) == 1
    assert capsys.readouterr().err.strip() == NO_MODULES
