"""Tests of `tools/mutate.py`: what a mutant is, and what a run says of one.

Each operator makes its one edit; a range, a function body and a statement over
several lines limit where; a small repository of its own shows the run.
"""

import contextlib
import os
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
