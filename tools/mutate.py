"""Say which mutants of some lines, or of some text edits, the named tests kill.

Run it from the repository root:

    uv run python -m tools.mutate <path>:<lo>[-<hi>] ...
        (--tests <file-or-node-id> ... | --all) [--timeout <seconds>]
    uv run python -m tools.mutate --edits <json> [--timeout <seconds>]

A mutant is one edit on one line of a function body. With `--edits` it is a text
edit in any tracked file, replayed against the tests its entry names, by pytest or,
with `"runner": "vitest"`, by vitest over files of `ui/src/`. The run
works in a copy of the tracked files, never the checkout, and exits 0 with no
survivor, 1 with one and 2 when it refuses. It imports the standard library alone.
"""

import argparse
import ast
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, NoReturn, cast

REPO_ROOT = Path(__file__).resolve().parent.parent

OPERATORS = ("cmp", "bool", "not", "const", "raise", "ret", "call", "arith")

LINKED = ("models",)

RUNNERS = ("pytest", "vitest")

VERDICTS = ("killed", "survived", "invalid", "timeout")

DEFAULT_TIMEOUT = 300

TIMEOUT_FACTOR = 3

BASELINE_SECONDS = 1800

TAIL_LINES = 20

TARGET = re.compile(r"(?P<path>.+):(?P<lo>\d+)(?:-(?P<hi>\d+))?")


@dataclass(frozen=True)
class Mutant:
    """One edit: `old` and `new` are the whole line, before and after."""

    path: str
    line: int
    operator: str
    old: str
    new: str


@dataclass(frozen=True)
class Edit:
    """One text edit of a replay: `find` becomes `replace` once in `path`."""

    finding: str
    path: str
    find: str
    replace: str
    tests: tuple[str, ...]
    runner: str
    line: int
    equivalent: str | None


class Refused(Exception):
    """A run that stops before any verdict, with the reason as its message."""


def parse_target(text: str) -> tuple[str, int, int]:
    """Return `(path, lo, hi)` of `<path>:<lo>[-<hi>]`, or raise `Refused`.

    e.g. "isekai/shared/chain.py:97" -> ("isekai/shared/chain.py", 97, 97)
    """
    found = TARGET.fullmatch(text)
    if found is None:
        raise Refused(f"{text!r} is not <path>:<lo>[-<hi>]")
    lo = int(found["lo"])
    hi = int(found["hi"]) if found["hi"] is not None else lo
    if lo > hi:
        raise Refused(f"{text!r} starts past its end")
    return found["path"], lo, hi


COMPARISON = re.compile(rb"\bis\s+not\b|\bnot\s+in\b|\bis\b|\bin\b|==|!=|<=|>=|<|>")
COMPARISON_SWAP = {
    b"==": b"!=",
    b"!=": b"==",
    b"<": b">=",
    b"<=": b">",
    b">": b"<=",
    b">=": b"<",
    b"in": b"not in",
    b"not in": b"in",
    b"is": b"is not",
    b"is not": b"is",
}
NEGATION = re.compile(rb"not\s*")
BOOLEAN = re.compile(rb"\band\b|\bor\b")
BOOLEAN_SWAP = {b"and": b"or", b"or": b"and"}
ARITHMETIC = re.compile(rb"//|\+|-|\*")
ARITHMETIC_SWAP = {b"+": b"-", b"-": b"+", b"*": b"//", b"//": b"*"}


def columns(node: ast.expr | ast.stmt) -> tuple[int, int]:
    """Return the byte columns where `node` starts and ends on its line."""
    return node.col_offset, node.end_col_offset or node.col_offset


def swap_between(
    line: bytes,
    left: ast.expr,
    right: ast.expr,
    pattern: re.Pattern[bytes],
    swap: dict[bytes, bytes],
) -> bytes | None:
    """Return `line` with the operator between two operands swapped, or None.

    e.g. b"a == b" -> b"a != b"
    """
    found = pattern.search(line, columns(left)[1], columns(right)[0])
    if found is None:
        return None
    word = b" ".join(found.group().split())
    return line[: found.start()] + swap[word] + line[found.end() :]


def replace_node(line: bytes, node: ast.expr | ast.stmt, new: bytes) -> bytes:
    """Return `line` with the columns of `node` replaced by `new`."""
    start, end = columns(node)
    return line[:start] + new + line[end:]


def edit_cmp(line: bytes, node: ast.Compare) -> bytes | None:
    """Return `line` with the one operator of a comparison flipped, or None."""
    if len(node.ops) != 1:
        return None
    return swap_between(
        line, node.left, node.comparators[0], COMPARISON, COMPARISON_SWAP
    )


def edit_bool(line: bytes, node: ast.BoolOp) -> bytes | None:
    """Return `line` with `and` and `or` swapped between two values, or None."""
    if len(node.values) != 2:
        return None
    return swap_between(line, node.values[0], node.values[1], BOOLEAN, BOOLEAN_SWAP)


def edit_not(line: bytes, node: ast.UnaryOp) -> bytes | None:
    """Return `line` with the `not` of a negation removed, or None."""
    if not isinstance(node.op, ast.Not):
        return None
    start = node.col_offset
    found = NEGATION.match(line, start)
    if found is None:
        return None
    return line[:start] + line[found.end() :]


def edit_const(line: bytes, node: ast.Constant) -> bytes | None:
    """Return `line` with a boolean flipped or a whole number raised by one, or None.

    e.g. b"n = 5" -> b"n = (5 + 1)"
    """
    if node.value is True:
        return replace_node(line, node, b"False")
    if node.value is False:
        return replace_node(line, node, b"True")
    if type(node.value) is int:
        start, end = columns(node)
        return replace_node(line, node, b"(" + line[start:end] + b" + 1)")
    return None


def is_text(node: ast.expr) -> bool:
    """Return whether `node` is a string, bytes or f-string."""
    if isinstance(node, ast.JoinedStr):
        return True
    return isinstance(node, ast.Constant) and isinstance(node.value, str | bytes)


def edit_arith(line: bytes, node: ast.BinOp) -> bytes | None:
    """Return `line` with `+` and `-`, or `*` and `//`, swapped, or None."""
    if not isinstance(node.op, ast.Add | ast.Sub | ast.Mult | ast.FloorDiv):
        return None
    if is_text(node.left) or is_text(node.right):
        return None
    return swap_between(line, node.left, node.right, ARITHMETIC, ARITHMETIC_SWAP)


def edit_raise(line: bytes, node: ast.Raise) -> bytes | None:
    """Return `line` with a `raise` statement replaced by `pass`."""
    return replace_node(line, node, b"pass")


def edit_ret(line: bytes, node: ast.Return) -> bytes | None:
    """Return `line` with a `return` of a value replaced by `return None`, or None."""
    if node.value is None:
        return None
    if isinstance(node.value, ast.Constant) and node.value.value is None:
        return None
    return replace_node(line, node, b"return None")


def edit_call(line: bytes, node: ast.Expr) -> bytes | None:
    """Return `line` with a statement that is one call replaced by `pass`, or None."""
    if not isinstance(node.value, ast.Call):
        return None
    return replace_node(line, node, b"pass")


def edits(node: ast.AST, line: bytes) -> Iterator[tuple[str, bytes | None]]:
    """Yield `(operator, new line)` for each operator that applies to `node`."""
    if isinstance(node, ast.Compare):
        yield "cmp", edit_cmp(line, node)
    elif isinstance(node, ast.BoolOp):
        yield "bool", edit_bool(line, node)
    elif isinstance(node, ast.UnaryOp):
        yield "not", edit_not(line, node)
    elif isinstance(node, ast.Constant):
        yield "const", edit_const(line, node)
    elif isinstance(node, ast.BinOp):
        yield "arith", edit_arith(line, node)
    elif isinstance(node, ast.Raise):
        yield "raise", edit_raise(line, node)
    elif isinstance(node, ast.Return):
        yield "ret", edit_ret(line, node)
    elif isinstance(node, ast.Expr):
        yield "call", edit_call(line, node)


def body_nodes(tree: ast.Module) -> Iterator[ast.expr | ast.stmt]:
    """Yield each node inside a function body once, nested functions included."""
    seen: set[int] = set()
    for function in ast.walk(tree):
        if not isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for statement in function.body:
            for node in ast.walk(statement):
                if id(node) in seen:
                    continue
                seen.add(id(node))
                if isinstance(node, ast.expr | ast.stmt):
                    yield node


def sites(text: str, lo: int, hi: int) -> list[Mutant]:
    """Return the mutants on lines `lo` to `hi` of `text`, in source order.

    A node is mutated inside a function body, when it starts and ends on one line.
    The `path` of each is empty: the caller knows the file.
    """
    lines = text.encode().split(b"\n")
    found: list[tuple[int, int, int, Mutant]] = []
    for node in body_nodes(ast.parse(text)):
        if node.end_lineno != node.lineno or not lo <= node.lineno <= hi:
            continue
        line = lines[node.lineno - 1]
        for operator, new in edits(node, line):
            if new is None or new == line:
                continue
            mutant = Mutant("", node.lineno, operator, line.decode(), new.decode())
            found.append(
                (node.lineno, node.col_offset, OPERATORS.index(operator), mutant)
            )
    return [mutant for *_, mutant in sorted(found, key=lambda site: site[:3])]


def tracked_files(root: Path) -> list[str]:
    """Return the paths `git ls-files` lists under `root`, or raise `Refused`."""
    try:
        listed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as failure:
        raise Refused(f"{root} is not a git repository") from failure
    return [os.fsdecode(path) for path in listed.stdout.split(b"\0") if path]


EDIT_KEYS = ("finding", "path", "find", "replace", "tests")
EDIT_OPTIONAL = ("why", "equivalent", "runner")
EDIT_TEXTS = ("finding", "path", "find", "replace", "why", "equivalent", "runner")


def load_edit(root: Path, tracked: set[str], number: int, item: object) -> Edit:
    """Return the `Edit` of the `number`th entry, or raise `Refused` naming it."""
    if not isinstance(item, dict):
        raise Refused(f"entry {number} is not an object")
    entry = cast("dict[str, Any]", item)
    name = entry.get("finding")
    label = name if isinstance(name, str) else f"entry {number}"
    missing = [key for key in EDIT_KEYS if key not in entry]
    if missing:
        raise Refused(f"{label}: missing {', '.join(missing)}")
    unknown = sorted(set(entry) - {*EDIT_KEYS, *EDIT_OPTIONAL})
    if unknown:
        raise Refused(f"{label}: unknown {', '.join(unknown)}")
    for key in EDIT_TEXTS:
        if key in entry and not isinstance(entry[key], str):
            raise Refused(f"{label}: {key} is not text")
    tests = entry["tests"]
    if not isinstance(tests, list) or not tests:
        raise Refused(f"{label}: tests is not a non-empty list")
    if not all(isinstance(test, str) for test in tests):
        raise Refused(f"{label}: tests holds a name that is not text")
    runner = entry.get("runner", "pytest")
    if runner not in RUNNERS:
        raise Refused(f"{label}: runner is not pytest or vitest")
    path, find = entry["path"], entry["find"]
    if path not in tracked:
        raise Refused(f"{label}: {path} is not tracked")
    try:
        text = (root / path).read_bytes().decode()
    except (OSError, ValueError) as failure:
        raise Refused(f"{label}: {path} cannot be read as text: {failure}") from failure
    found = text.count(find)
    if found != 1:
        raise Refused(f"{label}: find occurs {found} times in {path}, not once")
    return Edit(
        finding=entry["finding"],
        path=path,
        find=find,
        replace=entry["replace"],
        tests=tuple(tests),
        runner=runner,
        line=text.count("\n", 0, text.index(find)) + 1,
        equivalent=entry.get("equivalent"),
    )


def load_edits(root: Path, path: str) -> list[Edit]:
    """Return the edits of the JSON array at `path`, or raise `Refused`.

    `path` is read as given; the entries name tracked files of `root`.
    """
    try:
        entries = json.loads(Path(path).read_text())
    except (OSError, ValueError) as failure:
        raise Refused(f"{path} cannot be read as JSON: {failure}") from failure
    if not isinstance(entries, list):
        raise Refused(f"{path} is not a JSON array")
    tracked = set(tracked_files(root))
    return [
        load_edit(root, tracked, number, entry)
        for number, entry in enumerate(entries, 1)
    ]


def copy_tree(root: Path, into: Path) -> None:
    """Copy each tracked file of `root` that exists into `into` as a git repository.

    A file is copied by content, so a mutant never writes through a link into `root`.
    The copy is then made a git repository and `models` is linked, so a test that
    writes under `models/` writes through the link and is a test to isolate.
    """
    for name in tracked_files(root):
        source = root / name
        if source.is_file():
            (into / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, into / name)
    try:
        subprocess.run(
            ["git", "-C", str(into), "init", "-q"], capture_output=True, check=True
        )
        subprocess.run(
            ["git", "-C", str(into), "add", "-A", "-f"],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as failure:
        raise Refused(f"{into} cannot be made a git repository") from failure
    for name in LINKED:
        source = root / name
        if source.is_dir() and not (into / name).exists():
            (into / name).parent.mkdir(parents=True, exist_ok=True)
            (into / name).symlink_to(source)


@contextmanager
def linked_modules(copy: Path, root: Path) -> Iterator[None]:
    """Link `root`'s `ui/node_modules` into `copy` for the block, then unlink it."""
    link = copy / "ui" / "node_modules"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(root / "ui" / "node_modules")
    try:
        yield
    finally:
        link.unlink()


def pytest_args(tests: Sequence[str], everything: bool) -> list[str]:
    """Return the arguments after `python -m pytest` for one run of the tests.

    `everything` runs `tests/` but the browser's, else the files or node ids given.
    """
    chosen = ["tests", "--ignore=tests/e2e"] if everything else list(tests)
    return ["-x", "-q", "-p", "no:cacheprovider", *chosen]


def runner_args(runner: str, tests: Sequence[str]) -> list[str]:
    """Return the arguments after the runner's command for one run of `tests`.

    Vitest matches a filter against the path from `ui/`, so `ui/` is removed.
    e.g. `runner_args("vitest", ["ui/src/a.test.ts"])` -> ["src/a.test.ts"]
    """
    if runner == "pytest":
        return pytest_args(tests, False)
    return [test.removeprefix("ui/") for test in tests]


def run_tests(
    copy: Path, args: Sequence[str], timeout: float, runner: str = "pytest"
) -> tuple[int | None, str]:
    """Return the runner's `(exit code, output)` in `copy`, the code None on a timeout.

    The runner runs in its own session, and a timeout kills the whole group, so a
    process a test started does not outlive the verdict.
    """
    if runner == "vitest":
        command, where = ["npm", "run", "test", "--", *args], copy / "ui"
    else:
        command, where = [sys.executable, "-m", "pytest", *args], copy
    with subprocess.Popen(
        command,
        cwd=where,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    ) as process:
        try:
            output, _ = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            return None, ""
    return process.returncode, output


def mutant_timeout(timeout: float, baseline: float) -> float:
    """Return the seconds one mutant may run: `timeout`, or more for a slow suite.

    A survivor runs every test, as the unmutated baseline did, so no limit is
    shorter than a multiple of the baseline's own time.
    e.g. `mutant_timeout(300, 1.0)` -> 300, `mutant_timeout(0.1, 40.0)` -> 120.0
    """
    return max(timeout, TIMEOUT_FACTOR * baseline)


def verdict(code: int | None) -> str:
    """Return the verdict of a pytest exit code, None being a timeout.

    e.g. 0 -> "survived", 1 -> "killed", 2 -> "invalid"
    """
    if code is None:
        return "timeout"
    return {0: "survived", 1: "killed"}.get(code, "invalid")


def try_bytes(
    copy: Path,
    name: str,
    mutated: bytes,
    args: Sequence[str],
    timeout: float,
    runner: str = "pytest",
) -> str:
    """Return the verdict of `name` holding `mutated` in `copy`, then restore it.

    A `.py` file that does not parse is `invalid`, and no test runs.
    """
    target = copy / name
    original = target.read_bytes()
    if target.suffix == ".py":
        try:
            ast.parse(mutated)
        except (SyntaxError, ValueError):
            return "invalid"
    target.write_bytes(mutated)
    try:
        code, _ = run_tests(copy, args, timeout, runner)
    finally:
        target.write_bytes(original)
    return verdict(code)


def try_mutant(copy: Path, mutant: Mutant, args: Sequence[str], timeout: float) -> str:
    """Return the verdict of `mutant` in `copy`, the file restored after the run."""
    lines = (copy / mutant.path).read_bytes().split(b"\n")
    lines[mutant.line - 1] = mutant.new.encode()
    return try_bytes(copy, mutant.path, b"\n".join(lines), args, timeout)


def try_edit(copy: Path, edit: Edit, args: Sequence[str], timeout: float) -> str:
    """Return the verdict of `edit` in `copy`, the file restored after the run."""
    original = (copy / edit.path).read_bytes()
    mutated = original.replace(edit.find.encode(), edit.replace.encode(), 1)
    return try_bytes(copy, edit.path, mutated, args, timeout, edit.runner)


def verdict_line(mutant: Mutant, result: str) -> str:
    """Return the line that says what became of `mutant`."""
    edit = f"{mutant.old.strip()} -> {mutant.new.strip()}"
    return f"{result} {mutant.path}:{mutant.line} {mutant.operator}: {edit}"


def report(results: Sequence[tuple[Mutant, str]]) -> None:
    """Print the count of each verdict, then each survivor and each timeout."""
    tally = [sum(result == name for _, result in results) for name in VERDICTS]
    killed, survived, invalid, timeout = tally
    print(
        f"mutate: {killed} killed, {survived} survived, "
        f"{invalid} invalid, {timeout} timeout"
    )
    for mutant, result in results:
        if result == "survived":
            print(f"survivor {mutant.path}:{mutant.line} {mutant.operator}")
    for mutant, result in results:
        if result == "timeout":
            print(f"timeout {mutant.path}:{mutant.line} {mutant.operator}")


class Parser(argparse.ArgumentParser):
    """An argument parser whose errors are a `Refused`, not an exit."""

    def error(self, message: str) -> NoReturn:
        """Raise `Refused` with `message`."""
        raise Refused(message)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Return the command line's targets, tests, `everything` flag, edits, timeout."""
    parser = Parser(prog="python -m tools.mutate", allow_abbrev=False)
    parser.add_argument("targets", nargs="*", metavar="path:lo[-hi]")
    parser.add_argument("--tests", nargs="+", default=[], metavar="TEST")
    parser.add_argument("--all", action="store_true", dest="everything")
    parser.add_argument("--edits", metavar="JSON")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    return parser.parse_args(argv)


def collect(root: Path, targets: Sequence[str]) -> list[Mutant]:
    """Return the mutants of each target, or raise `Refused` for one that has none."""
    tracked = set(tracked_files(root))
    mutants: list[Mutant] = []
    for target in targets:
        path, lo, hi = parse_target(target)
        if path not in tracked:
            raise Refused(f"{path} is not tracked")
        try:
            found = sites((root / path).read_text(), lo, hi)
        except (OSError, SyntaxError, ValueError) as failure:
            raise Refused(f"{path} cannot be read as Python: {failure}") from failure
        if not found:
            raise Refused(f"{target} holds no mutant")
        mutants += [replace(mutant, path=path) for mutant in found]
    return mutants


def baseline_limit(
    copy: Path, args: Sequence[str], timeout: float, runner: str = "pytest"
) -> float:
    """Return the seconds a mutant of `args` may run, or raise `Refused` if red.

    The tests run unmutated in `copy`; the limit is `mutant_timeout` of that run.
    """
    started = time.monotonic()
    code, output = run_tests(copy, args, BASELINE_SECONDS, runner)
    timeout = mutant_timeout(timeout, time.monotonic() - started)
    if code != 0:
        tail = "\n".join(output.splitlines()[-TAIL_LINES:])
        raise Refused(
            f"the tests do not pass unmutated in a copy (exit {code}), "
            "so no mutant is tried; a test that reads the git history or an "
            f"untracked file fails in a copy\n{tail}"
        )
    return timeout


def run_mutants(
    root: Path, mutants: Sequence[Mutant], args: Sequence[str], timeout: float
) -> list[tuple[Mutant, str]]:
    """Return each mutant with its verdict, tried alone in a copy of `root`.

    The tests run unmutated first, and a baseline that is not green is a `Refused`.
    A mutant's limit is `timeout`, or a multiple of that baseline's time if more.
    """
    with tempfile.TemporaryDirectory() as scratch:
        copy = Path(scratch) / "repo"
        copy_tree(root, copy)
        timeout = baseline_limit(copy, args, timeout)
        results: list[tuple[Mutant, str]] = []
        for mutant in mutants:
            result = try_mutant(copy, mutant, args, timeout)
            print(verdict_line(mutant, result), flush=True)
            results.append((mutant, result))
    return results


def first_line(text: str) -> str:
    """Return the first line of `text`, empty for empty text."""
    return text.split("\n", 1)[0]


def run_edits(
    root: Path, edits: Sequence[Edit], timeout: float
) -> list[tuple[Mutant, str]]:
    """Return each edit that is run with its verdict, tried alone in one copy.

    The tests of each distinct list run unmutated first, and a baseline that is not
    green is a `Refused` before any line prints. An edit with `equivalent` is
    printed with its reason and is not run. A vitest entry is refused, before the copy
    is made, when `ui/node_modules` or `npm` is missing; its tests run with the modules
    linked into the copy.
    """
    if any(e.runner == "vitest" for e in edits):
        if not (root / "ui" / "node_modules").is_dir():
            raise Refused(
                "a vitest entry needs ui/node_modules: run npm ci --prefix ui"
            )
        if shutil.which("npm") is None:
            raise Refused("a vitest entry needs npm on PATH")
    with tempfile.TemporaryDirectory() as scratch:
        copy = Path(scratch) / "repo"
        copy_tree(root, copy)
        limits: dict[tuple[str, tuple[str, ...]], float] = {}
        lists = dict.fromkeys(
            (e.runner, e.tests) for e in edits if e.equivalent is None
        )
        for runner, tests in lists:
            with linked_modules(copy, root) if runner == "vitest" else nullcontext():
                limits[runner, tests] = baseline_limit(
                    copy, runner_args(runner, tests), timeout, runner
                )
        results: list[tuple[Mutant, str]] = []
        for edit in edits:
            if edit.equivalent is not None:
                print(
                    f"equivalent {edit.path}:{edit.line} {edit.finding}: "
                    f"{edit.equivalent}",
                    flush=True,
                )
                continue
            mutant = Mutant(
                edit.path,
                edit.line,
                edit.finding,
                first_line(edit.find),
                first_line(edit.replace),
            )
            args = runner_args(edit.runner, edit.tests)
            with (
                linked_modules(copy, root) if edit.runner == "vitest" else nullcontext()
            ):
                result = try_edit(copy, edit, args, limits[edit.runner, edit.tests])
            print(verdict_line(mutant, result), flush=True)
            results.append((mutant, result))
    return results


def main(argv: Sequence[str] | None = None, *, root: Path = REPO_ROOT) -> int:
    """Run the mutants named; return the exit status, 0, 1 or 2."""
    try:
        args = parse_args(sys.argv[1:] if argv is None else argv)
        if args.edits is not None:
            if args.targets or args.tests or args.everything:
                raise Refused("--edits takes no target, --tests or --all")
            results = run_edits(root, load_edits(root, args.edits), args.timeout)
        else:
            if not args.targets:
                raise Refused("give a target or --edits")
            if bool(args.tests) == args.everything:
                raise Refused("give one of --tests and --all")
            mutants = collect(root, args.targets)
            chosen = pytest_args(args.tests, args.everything)
            results = run_mutants(root, mutants, chosen, args.timeout)
    except Refused as refusal:
        print(f"mutate: refused: {refusal}", file=sys.stderr)
        return 2
    report(results)
    return 1 if any(result == "survived" for _, result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
