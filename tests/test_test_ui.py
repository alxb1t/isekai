import shutil
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


@pytest.mark.spec_exempt("structural: the browser tests' refusals")
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


@pytest.mark.spec_exempt("structural: a file is run in ui/ after the double dash")
def test_a_file_is_run_in_ui_after_the_double_dash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _ui(tmp_path, modules=True)
    ran: list[tuple[list[str], Path]] = []

    def run(command: list[str], cwd: Path, check: bool) -> SimpleNamespace:
        ran.append((command, cwd))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(test_ui.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(subprocess, "run", run)
    assert test_ui.main(root, ["ui/src/cancel.test.ts", "-t", "a name"]) == 0
    assert test_ui.main(root, ["src/cancel.test.ts"]) == 0
    assert ran == [
        (
            ["npm", "run", "test", "--", "src/cancel.test.ts", "-t", "a name"],
            root / "ui",
        ),
        (["npm", "run", "test", "--", "src/cancel.test.ts"], root / "ui"),
    ]


@pytest.mark.spec_exempt(
    "structural: vitest started at the repository root is refused and writes nothing"
)
def test_vitest_beside_the_root_config_refuses_and_writes_nothing(
    tmp_path: Path,
) -> None:
    if refusal() is not None:
        pytest.skip("no ui toolchain: the gate's own vitest run refuses first")
    start = tmp_path / "start"
    start.mkdir()
    shutil.copy(test_ui.ROOT / "vitest.config.mjs", start)
    vitest = test_ui.ROOT / "ui" / "node_modules" / ".bin" / "vitest"
    done = subprocess.run(
        [str(vitest), "run"], cwd=start, capture_output=True, text=True, check=False
    )
    assert done.returncode != 0
    assert "python -m tools.test_ui" in done.stdout + done.stderr
    assert [entry.name for entry in start.iterdir()] == ["vitest.config.mjs"]


@pytest.mark.spec_exempt("structural: a refusal runs nothing and exits 1")
def test_a_refusal_runs_nothing_and_exits_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _ui(tmp_path, modules=False)
    monkeypatch.setattr(test_ui.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("ran npm"))
    assert test_ui.main(root) == 1
    assert capsys.readouterr().err.strip() == NO_MODULES
