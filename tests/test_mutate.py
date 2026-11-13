"""Tests of `tools/mutate.py`: what a mutant is, and what a run says of one.

Each operator makes its one edit; a range, a function body and a statement over
several lines limit where; a small repository of its own shows the run.
"""

import contextlib
import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

import pytest

from tools.mutate import (
    OPERATORS,
    TIMEOUT_FACTOR,
    copy_tree,
    main,
    mutant_timeout,
    pytest_args,
    run_tests,
    runner_args,
    sites,
    verdict,
)

CALC = """\
def add(a, b):
    return a + b


def label(n):
    return "big" if n >= 100 else "small"


def drain(n):
    while n > 0:
        n = n - 1
    return n
"""
ADD_LINE, LABEL_LINE, DRAIN_LINE = 2, 6, 11

CALC_TESTS = """\
from calc import add, drain, label


def test_add():
    assert add(2, 3) == 5


def test_label():
    assert label(5) == "small"
    assert label(500) == "big"


def test_drain():
    assert drain(3) == 0
"""
FAILING_TEST = """

def test_failing():
    assert add(1, 1) == 3
"""

ROWS = {
    "cmp": ("cmp", "x = a is not b", "x = a is b"),
    "bool": ("bool", "x = a and b", "x = a or b"),
    "not": ("not", "x = not a", "x = a"),
    "const": ("const", "x = 5", "x = (5 + 1)"),
    "raise": ("raise", "raise ValueError(a)", "pass"),
    "ret": ("ret", "return a", "return None"),
    "call": ("call", "print(a)", "pass"),
    "arith": ("arith", "x = a * b", "x = a // b"),
    "cmp_after_non_ascii": ("cmp", 'x = "ééé" not in a', 'x = "ééé" in a'),
}


def in_function(*lines: str) -> str:
    """Return a function `f` whose body is `lines`, one per line."""
    return "def f(a, b):\n" + "".join(f"    {line}\n" for line in lines)


@pytest.mark.spec_exempt("structural: each operator of the table makes its one edit")
@pytest.mark.parametrize("row", [*OPERATORS, "cmp_after_non_ascii"])
def test_each_operator_makes_its_one_edit(row: str) -> None:
    operator, line, new = ROWS[row]

    found = [m for m in sites(in_function(line), 2, 2) if m.operator == operator]

    assert [(m.line, m.old, m.new) for m in found] == [(2, f"    {line}", f"    {new}")]


@pytest.mark.spec_exempt("structural: a line range limits the sites to its lines")
def test_a_line_range_limits_the_sites() -> None:
    text = in_function("x = a == b", "y = a < b", "flag = True", "z = a > b")

    assert [m.line for m in sites(text, 3, 5)] == [3, 4, 5]
    assert [m.line for m in sites(text, 3, 3)] == [3]
    assert [m.new for m in sites(text, 4, 4)] == ["    flag = False"]
    assert sites(text, 6, 9) == []


@pytest.mark.spec_exempt("structural: only a function body is mutated")
def test_only_a_function_body_is_mutated() -> None:
    text = (
        "LIMIT = 1 + 2\n"
        "class Box:\n"
        "    size = 3 == 3\n"
        "@decorate(1 == 1)\n"
        "def f(a=4 + 4):\n"
        '    """A docstring that says 5 == 5."""\n'
        "    def inner():\n"
        "        return a < 6\n"
        "    return inner\n"
    )

    found = sites(text, 1, 9)

    assert [(m.line, m.operator) for m in found] == [
        (8, "ret"),
        (8, "cmp"),
        (8, "const"),
        (9, "ret"),
    ]


@pytest.mark.spec_exempt("structural: a statement over several lines is left alone")
def test_a_statement_over_several_lines_is_left_alone() -> None:
    text = in_function("x = (a ==", "     b)", "return (a +", "        b)")

    assert sites(text, 1, 6) == []


def build_repo(path: Path, *, failing: bool = False) -> Path:
    """Return `path`, a repository of `calc.py` and its tests, `models/` untracked."""
    (path / "tests").mkdir(parents=True)
    (path / "models").mkdir()
    (path / "calc.py").write_text(CALC)
    (path / "tests" / "test_calc.py").write_text(
        CALC_TESTS + (FAILING_TEST if failing else "")
    )
    (path / "models" / "weights.bin").write_bytes(b"w")
    subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(path), "add", "--", ".", ":!models"], check=True)
    return path


@pytest.fixture(scope="module")
def small_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_repo(tmp_path_factory.mktemp("small") / "repo")


@pytest.mark.spec_exempt(
    "structural: a copy is a repository of the tracked files that exist "
    "and links models alone"
)
def test_the_copy_holds_the_tracked_files_and_links_the_ignored_ones(
    tmp_path: Path,
) -> None:
    repo = build_repo(tmp_path / "repo")
    (repo / "calc.py").unlink()
    (repo / "ui" / "dist").mkdir(parents=True)
    (repo / "ui" / "dist" / "app.js").write_text("a")
    (repo / "ui" / "node_modules").mkdir()
    (repo / "ui" / "node_modules" / "m.js").write_text("m")
    copy = tmp_path / "copy"

    copy_tree(repo, copy)

    assert (copy / "tests" / "test_calc.py").read_text() == CALC_TESTS
    assert not (copy / "tests" / "test_calc.py").is_symlink()
    assert not (copy / "calc.py").exists()
    assert (copy / "models").is_symlink()
    assert (copy / "models" / "weights.bin").read_bytes() == b"w"
    assert not (copy / "ui").exists()
    listed = subprocess.run(
        ["git", "-C", str(copy), "ls-files"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout.split()
    assert "tests/test_calc.py" in listed
    assert not any(path.startswith("models") for path in listed)


@pytest.mark.spec_exempt("structural: --all runs the suite without the browser tests")
def test_all_runs_the_suite_without_the_browser_tests() -> None:
    everything = pytest_args([], True)
    chosen = pytest_args(["tests/test_a.py", "tests/test_b.py::test_c"], False)

    assert everything[-2:] == ["tests", "--ignore=tests/e2e"]
    assert chosen[-2:] == ["tests/test_a.py", "tests/test_b.py::test_c"]
    assert "--ignore=tests/e2e" not in chosen
    assert everything[:4] == chosen[:4] == ["-x", "-q", "-p", "no:cacheprovider"]


@pytest.mark.spec_exempt(
    "structural: a mutant that cannot run is invalid, and only exit 0 survives"
)
def test_a_mutant_that_cannot_run_is_invalid_not_a_survivor() -> None:
    assert verdict(0) == "survived"
    assert verdict(1) == "killed"
    assert [verdict(code) for code in (2, 3, 4, 5)] == ["invalid"] * 4
    assert verdict(None) == "timeout"


def run(
    capsys: pytest.CaptureFixture[str], repo: Path, *argv: str
) -> tuple[int, list[str], str]:
    """Return the status, the lines printed and the refusal of `main` over `repo`."""
    status = main(list(argv), root=repo)
    captured = capsys.readouterr()
    return status, captured.out.splitlines(), captured.err


@pytest.mark.spec_exempt("structural: a run refuses before it tries any mutant")
def test_a_red_baseline_refuses_before_any_mutant(
    tmp_path: Path, small_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    red = build_repo(tmp_path / "red", failing=True)
    on_add = f"calc.py:{ADD_LINE}"

    status, printed, refusal = run(capsys, red, on_add, "--tests", "tests/test_calc.py")
    assert (status, printed) == (2, [])
    assert "do not pass unmutated" in refusal
    assert "test_failing" in refusal

    status, printed, refusal = run(
        capsys, small_repo, "models/weights.bin:1", "--tests", "tests/test_calc.py"
    )
    assert (status, printed) == (2, [])
    assert "models/weights.bin is not tracked" in refusal

    status, printed, refusal = run(
        capsys, small_repo, "calc.py:1", "--tests", "tests/test_calc.py"
    )
    assert (status, printed) == (2, [])
    assert "calc.py:1 holds no mutant" in refusal


@pytest.mark.spec_exempt("structural: a surviving mutant is reported and exits one")
def test_a_surviving_mutant_is_reported_with_its_operator_and_exits_one(
    small_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status, printed, _ = run(
        capsys, small_repo, f"calc.py:{LABEL_LINE}", "--tests", "tests/test_calc.py"
    )

    assert status == 1
    assert printed[:3] == [
        'killed calc.py:6 ret: return "big" if n >= 100 else "small" -> return None',
        'killed calc.py:6 cmp: return "big" if n >= 100 else "small"'
        ' -> return "big" if n < 100 else "small"',
        'survived calc.py:6 const: return "big" if n >= 100 else "small"'
        ' -> return "big" if n >= (100 + 1) else "small"',
    ]
    assert printed[3:] == [
        "mutate: 2 killed, 1 survived, 0 invalid, 0 timeout",
        "survivor calc.py:6 const",
    ]
    assert (small_repo / "calc.py").read_text() == CALC
    assert (small_repo / "models" / "weights.bin").read_bytes() == b"w"


@pytest.mark.spec_exempt("structural: a run with no survivor exits zero")
def test_a_run_with_no_survivor_exits_zero(
    small_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status, printed, _ = run(
        capsys, small_repo, f"calc.py:{ADD_LINE}", "--tests", "tests/test_calc.py"
    )

    assert status == 0
    assert printed[-1] == "mutate: 2 killed, 0 survived, 0 invalid, 0 timeout"
    assert not any(line.startswith("survivor") for line in printed)


@pytest.mark.spec_exempt("structural: a mutant that hangs is timed out, not a survivor")
def test_a_mutant_that_hangs_is_timed_out(
    small_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status, printed, _ = run(
        capsys,
        small_repo,
        f"calc.py:{DRAIN_LINE}",
        "--tests",
        "tests/test_calc.py",
        "--timeout",
        "2",
    )

    assert status == 0
    assert "timeout calc.py:11 arith: n = n - 1 -> n = n + 1" in printed
    assert printed[-2:] == [
        "mutate: 1 killed, 0 survived, 0 invalid, 1 timeout",
        "timeout calc.py:11 arith",
    ]
    assert not any(line.startswith("survivor") for line in printed)


@pytest.mark.spec_exempt(
    "structural: a mutant's time limit is never below a multiple of the baseline's run"
)
def test_a_mutant_gets_a_multiple_of_the_baseline_time() -> None:
    assert mutant_timeout(0.1, 40.0) == 40.0 * TIMEOUT_FACTOR
    assert mutant_timeout(300, 1.0) == 300


@pytest.mark.spec_exempt(
    "structural: a survivor that outlasts --timeout is reported as one"
)
def test_a_survivor_that_outlasts_the_timeout_is_a_survivor(
    small_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status, printed, _ = run(
        capsys,
        small_repo,
        f"calc.py:{LABEL_LINE}",
        "--tests",
        "tests/test_calc.py",
        "--timeout",
        "0.1",
    )

    assert status == 1
    assert any(line.startswith("survived calc.py:6 const: ") for line in printed)
    assert not any(line.startswith("timeout") for line in printed)


@pytest.mark.spec_exempt(
    "structural: a timeout kills the processes the tests started, not pytest alone"
)
def test_a_timeout_kills_a_process_the_tests_started(tmp_path: Path) -> None:
    (tmp_path / "test_spawn.py").write_text(
        "import subprocess, sys, time\n"
        "from pathlib import Path\n"
        "\n"
        "def test_hang():\n"
        "    child = subprocess.Popen(\n"
        "        [sys.executable, '-c', 'import time; time.sleep(60)']\n"
        "    )\n"
        "    Path(__file__).with_name('child.pid').write_text(str(child.pid))\n"
        "    time.sleep(60)\n"
    )

    code, _ = run_tests(tmp_path, ["-q", "-p", "no:cacheprovider", "test_spawn.py"], 3)

    child = int((tmp_path / "child.pid").read_text())
    try:
        for _ in range(50):
            try:
                os.kill(child, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)
        else:
            pytest.fail("the process the test started outlived the timeout")
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.kill(child, signal.SIGKILL)
    assert code is None


@pytest.mark.spec_exempt("structural: one of --tests and --all is required")
def test_one_of_tests_and_all_is_required(
    small_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    on_add = f"calc.py:{ADD_LINE}"

    neither = run(capsys, small_repo, on_add)
    both = run(capsys, small_repo, on_add, "--tests", "tests/test_calc.py", "--all")

    assert neither[:2] == both[:2] == (2, [])
    assert "give one of --tests and --all" in neither[2]
    assert "give one of --tests and --all" in both[2]


NOTES_TESTS = """\
from pathlib import Path


def test_limit():
    text = (Path(__file__).parent.parent / "notes.txt").read_text()
    assert "limit = 10" in text
"""


def build_notes_repo(path: Path) -> Path:
    """Return `path`, a repository of `notes.txt` and a test that reads its limit."""
    (path / "tests").mkdir(parents=True)
    (path / "notes.txt").write_text("limit = 10\nremark: none\n")
    (path / "tests" / "test_notes.py").write_text(NOTES_TESTS)
    subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(path), "add", "--", "."], check=True)
    return path


UNLINKED_TESTS = """\
from pathlib import Path


def test_modules_are_not_linked():
    root = Path(__file__).parent.parent
    assert not (root / "ui" / "node_modules").exists()
"""


def fake_npm(bin_dir: Path) -> None:
    """Write an `npm` to `bin_dir` that passes while `ui/limit.txt` says `limit = 10`.

    It exits 3 for a file named from the repository's root, and fails without
    `node_modules` beside it.
    """
    npm = bin_dir / "npm"
    npm.write_text(
        "#!/bin/sh\n"
        'case "$*" in *" ui/"*) exit 3;; esac\n'
        'test -d node_modules && grep -q "limit = 10" limit.txt\n'
    )
    npm.chmod(0o755)


def build_vitest_repo(path: Path) -> Path:
    """Return `build_notes_repo(path)` plus a tracked `ui/limit.txt` and its modules."""
    build_notes_repo(path)
    (path / "ui").mkdir()
    (path / "ui" / "limit.txt").write_text("limit = 10\nremark: none\n")
    (path / "tests" / "test_unlinked.py").write_text(UNLINKED_TESTS)
    subprocess.run(
        ["git", "-C", str(path), "add", "--", "ui/limit.txt", "tests/test_unlinked.py"],
        check=True,
    )
    (path / "ui" / "node_modules").mkdir()
    (path / "ui" / "node_modules" / "m.js").write_text("m")
    return path


def entry(**given: object) -> dict[str, object]:
    """Return a valid edit of `calc.py`, each key of `given` set, None dropping it."""
    base: dict[str, object] = {
        "finding": "ED-X",
        "path": "calc.py",
        "find": "n >= 100",
        "replace": "n >= 101",
        "tests": ["tests/test_calc.py"],
    }
    return {key: value for key, value in {**base, **given}.items() if value is not None}


def edits_file(tmp_path: Path, *entries: dict[str, object]) -> str:
    """Write `entries` as a JSON array under `tmp_path` and return its path."""
    path = tmp_path / "edits.json"
    path.write_text(json.dumps(list(entries)))
    return str(path)


@pytest.mark.spec_exempt(
    "structural: an edit is replayed in any tracked file, with its own tests"
)
def test_an_edit_replays_in_any_file_and_a_survivor_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = build_notes_repo(tmp_path / "repo")
    edits = edits_file(
        tmp_path,
        entry(
            finding="ED-1",
            path="notes.txt",
            find="limit = 10",
            replace="limit = 11",
            tests=["tests/test_notes.py"],
        ),
        entry(
            finding="ED-2",
            path="notes.txt",
            find="remark: none",
            replace="remark: some",
            tests=["tests/test_notes.py"],
        ),
    )

    status, printed, _ = run(capsys, repo, "--edits", edits)

    assert status == 1
    assert printed == [
        "killed notes.txt:1 ED-1: limit = 10 -> limit = 11",
        "survived notes.txt:2 ED-2: remark: none -> remark: some",
        "mutate: 1 killed, 1 survived, 0 invalid, 0 timeout",
        "survivor notes.txt:2 ED-2",
    ]
    assert (repo / "notes.txt").read_text() == "limit = 10\nremark: none\n"


@pytest.mark.spec_exempt(
    "structural: an entry that cannot be replayed is refused before any mutant runs"
)
@pytest.mark.parametrize(
    ("given", "before", "expected"),
    [
        ({"find": "return"}, (), "ED-X"),
        ({"find": "no such text"}, (), "ED-X"),
        ({"path": "models/weights.bin"}, (), "ED-X"),
        ({"replace": None}, (), "ED-X"),
        ({"extra": "x"}, (), "ED-X"),
        ({"tests": []}, (), "ED-X"),
        ({}, ("calc.py:2",), "--edits takes no target, --tests or --all"),
        ({"runner": "jest"}, (), "ED-X"),
    ],
    ids=[
        "find twice",
        "find nowhere",
        "untracked path",
        "missing key",
        "unknown key",
        "empty tests",
        "edits beside a target",
        "unknown runner",
    ],
)
def test_an_entry_out_of_shape_or_whose_find_is_not_once_is_refused(
    given: dict[str, object],
    before: tuple[str, ...],
    expected: str,
    small_repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    edits = edits_file(tmp_path, entry(**given))

    status, printed, refusal = run(capsys, small_repo, *before, "--edits", edits)

    assert (status, printed) == (2, [])
    assert expected in refusal


@pytest.mark.spec_exempt("structural: an entry in no shape is named by its position")
def test_an_entry_without_a_finding_is_named_by_its_position(
    small_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    edits = edits_file(tmp_path, entry(), entry(finding=None, find="no such text"))

    status, printed, refusal = run(capsys, small_repo, "--edits", edits)

    assert (status, printed) == (2, [])
    assert "entry 2" in refusal


@pytest.mark.spec_exempt(
    "structural: an entry with equivalent is printed with its reason and not run"
)
def test_an_equivalent_entry_is_printed_and_not_run(
    small_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    edits = edits_file(
        tmp_path, entry(finding="ED-E", equivalent="no input tells 100 from 101")
    )

    status, printed, _ = run(capsys, small_repo, "--edits", edits)

    assert status == 0
    assert printed[0] == "equivalent calc.py:6 ED-E: no input tells 100 from 101"
    assert printed[-1] == "mutate: 0 killed, 0 survived, 0 invalid, 0 timeout"
    assert not any(line.startswith("survivor") for line in printed)


@pytest.mark.spec_exempt("structural: an edit that breaks a .py file is invalid")
def test_an_edit_that_breaks_python_is_invalid(
    small_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    edits = edits_file(
        tmp_path, entry(finding="ED-I", find="return a + b", replace="return a +")
    )

    status, printed, _ = run(capsys, small_repo, "--edits", edits)

    assert status == 0
    assert printed == [
        "invalid calc.py:2 ED-I: return a + b -> return a +",
        "mutate: 0 killed, 0 survived, 1 invalid, 0 timeout",
    ]


@pytest.mark.spec_exempt(
    "structural: a red baseline of any entry's tests refuses the run"
)
def test_a_red_baseline_of_one_entrys_tests_refuses_the_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    red = build_repo(tmp_path / "red", failing=True)
    edits = edits_file(
        tmp_path,
        entry(tests=["tests/test_calc.py::test_add"]),
        entry(finding="ED-Y", tests=["tests/test_calc.py::test_failing"]),
    )

    status, printed, refusal = run(capsys, red, "--edits", edits)

    assert (status, printed) == (2, [])
    assert "do not pass unmutated" in refusal


@pytest.mark.spec_exempt(
    "structural: a vitest entry is replayed with ui/node_modules linked for it alone"
)
def test_a_vitest_entry_replays_with_the_modules_linked_for_it_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = build_vitest_repo(tmp_path / "repo")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_npm(bin_dir)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    vitest = {"runner": "vitest", "tests": ["ui/src/limit.test.ts"]}
    edits = edits_file(
        tmp_path,
        entry(
            finding="ED-1",
            path="ui/limit.txt",
            find="limit = 10",
            replace="limit = 11",
            **vitest,
        ),
        entry(
            finding="ED-2",
            path="ui/limit.txt",
            find="remark: none",
            replace="remark: some",
            **vitest,
        ),
        entry(
            finding="ED-3",
            path="notes.txt",
            find="limit = 10",
            replace="limit = 11",
            tests=["tests/test_unlinked.py"],
        ),
    )

    status, printed, _ = run(capsys, repo, "--edits", edits)

    assert status == 1
    assert printed == [
        "killed ui/limit.txt:1 ED-1: limit = 10 -> limit = 11",
        "survived ui/limit.txt:2 ED-2: remark: none -> remark: some",
        "survived notes.txt:1 ED-3: limit = 10 -> limit = 11",
        "mutate: 1 killed, 2 survived, 0 invalid, 0 timeout",
        "survivor ui/limit.txt:2 ED-2",
        "survivor notes.txt:1 ED-3",
    ]
    assert (repo / "ui" / "limit.txt").read_text() == "limit = 10\nremark: none\n"
    assert (repo / "notes.txt").read_text() == "limit = 10\nremark: none\n"
    assert not (repo / "ui" / "node_modules").is_symlink()


@pytest.mark.spec_exempt(
    "structural: a vitest entry that cannot run is refused before any line prints"
)
@pytest.mark.parametrize("missing", ["modules", "npm"])
def test_a_vitest_entry_with_no_modules_or_no_npm_is_refused(
    missing: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = build_vitest_repo(tmp_path / "repo")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    if missing == "modules":
        shutil.rmtree(repo / "ui" / "node_modules")
        fake_npm(bin_dir)
        monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    else:
        git = shutil.which("git")
        assert git is not None
        (bin_dir / "git").symlink_to(git)
        monkeypatch.setenv("PATH", str(bin_dir))
    edits = edits_file(
        tmp_path,
        entry(
            finding="ED-1",
            path="ui/limit.txt",
            find="limit = 10",
            replace="limit = 11",
            runner="vitest",
            tests=["ui/src/limit.test.ts"],
        ),
    )

    status, printed, refusal = run(capsys, repo, "--edits", edits)

    assert (status, printed) == (2, [])
    assert ("ui/node_modules" if missing == "modules" else "npm on PATH") in refusal


@pytest.mark.spec_exempt("structural: vitest takes its files from the root of ui/")
def test_a_vitest_file_is_named_from_the_ui_root() -> None:
    assert runner_args("vitest", ["ui/src/a.test.ts"]) == ["src/a.test.ts"]
    assert runner_args("pytest", ["tests/test_a.py"]) == pytest_args(
        ["tests/test_a.py"], False
    )
