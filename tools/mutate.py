"""Say which mutants of some lines the named tests kill.

Run it from the repository root:

    uv run python -m tools.mutate <path>:<lo>[-<hi>] ...
        (--tests <file-or-node-id> ... | --all) [--timeout <seconds>]

A mutant is one edit on one line of a function body. The run works in a copy of
the tracked files, never the checkout, and exits 0 with no survivor, 1 with one
and 2 when it refuses. It imports the standard library alone.
"""

import argparse
import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import NoReturn

REPO_ROOT = Path(__file__).resolve().parent.parent

OPERATORS = ("cmp", "bool", "not", "const", "raise", "ret", "call", "arith")

LINKED = ("models", "ui/node_modules", "ui/dist")

VERDICTS = ("killed", "survived", "invalid", "timeout")

DEFAULT_TIMEOUT = 300

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


def copy_tree(root: Path, into: Path) -> None:
    """Copy each tracked file of `root` that exists into `into`, and link `LINKED`.

    A file is copied by content, so a mutant never writes through a link into `root`.
    """
    for name in tracked_files(root):
        source = root / name
        if source.is_file():
            (into / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, into / name)
    for name in LINKED:
        source = root / name
        if source.is_dir() and not (into / name).exists():
            (into / name).parent.mkdir(parents=True, exist_ok=True)
            (into / name).symlink_to(source)


def pytest_args(tests: Sequence[str], everything: bool) -> list[str]:
    """Return the arguments after `python -m pytest` for one run of the tests.

    `everything` runs `tests/` but the browser's, else the files or node ids given.
    """
    chosen = ["tests", "--ignore=tests/e2e"] if everything else list(tests)
    return ["-x", "-q", "-p", "no:cacheprovider", *chosen]


def run_tests(
    copy: Path, args: Sequence[str], timeout: float
) -> tuple[int | None, str]:
    """Return pytest's `(exit code, output)` in `copy`, the code None on a timeout."""
    try:
        done = subprocess.run(
            [sys.executable, "-m", "pytest", *args],
            cwd=copy,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, ""
    return done.returncode, done.stdout + done.stderr


def verdict(code: int | None) -> str:
    """Return the verdict of a pytest exit code, None being a timeout.

    e.g. 0 -> "survived", 1 -> "killed", 2 -> "invalid"
    """
    if code is None:
        return "timeout"
    return {0: "survived", 1: "killed"}.get(code, "invalid")


def try_mutant(copy: Path, mutant: Mutant, args: Sequence[str], timeout: float) -> str:
    """Return the verdict of `mutant` in `copy`, the file restored after the run."""
    target = copy / mutant.path
    original = target.read_bytes()
    lines = original.split(b"\n")
    lines[mutant.line - 1] = mutant.new.encode()
    mutated = b"\n".join(lines)
    try:
        ast.parse(mutated)
    except (SyntaxError, ValueError):
        return "invalid"
    target.write_bytes(mutated)
    try:
        code, _ = run_tests(copy, args, timeout)
    finally:
        target.write_bytes(original)
    return verdict(code)


def verdict_line(mutant: Mutant, result: str) -> str:
    """Return the line that says what became of `mutant`."""
    edit = f"{mutant.old.strip()} -> {mutant.new.strip()}"
    return f"{result} {mutant.path}:{mutant.line} {mutant.operator}: {edit}"


def report(results: Sequence[tuple[Mutant, str]]) -> None:
    """Print the count of each verdict, then each survivor."""
    tally = [sum(result == name for _, result in results) for name in VERDICTS]
    killed, survived, invalid, timeout = tally
    print(
        f"mutate: {killed} killed, {survived} survived, "
        f"{invalid} invalid, {timeout} timeout"
    )
    for mutant, result in results:
        if result == "survived":
            print(f"survivor {mutant.path}:{mutant.line} {mutant.operator}")


class Parser(argparse.ArgumentParser):
    """An argument parser whose errors are a `Refused`, not an exit."""

    def error(self, message: str) -> NoReturn:
        """Raise `Refused` with `message`."""
        raise Refused(message)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Return the command line's targets, tests, `everything` flag and timeout."""
    parser = Parser(prog="python -m tools.mutate", allow_abbrev=False)
    parser.add_argument("targets", nargs="+", metavar="path:lo[-hi]")
    parser.add_argument("--tests", nargs="+", default=[], metavar="TEST")
    parser.add_argument("--all", action="store_true", dest="everything")
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


def run_mutants(
    root: Path, mutants: Sequence[Mutant], args: Sequence[str], timeout: float
) -> list[tuple[Mutant, str]]:
    """Return each mutant with its verdict, tried alone in a copy of `root`.

    The tests run unmutated first, and a baseline that is not green is a `Refused`.
    """
    with tempfile.TemporaryDirectory() as scratch:
        copy = Path(scratch) / "repo"
        copy_tree(root, copy)
        code, output = run_tests(copy, args, BASELINE_SECONDS)
        if code != 0:
            tail = "\n".join(output.splitlines()[-TAIL_LINES:])
            raise Refused(
                f"the tests do not pass unmutated in a copy (exit {code}), "
                "so no mutant is tried; a test that reads the git history or an "
                f"untracked file fails in a copy\n{tail}"
            )
        results: list[tuple[Mutant, str]] = []
        for mutant in mutants:
            result = try_mutant(copy, mutant, args, timeout)
            print(verdict_line(mutant, result), flush=True)
            results.append((mutant, result))
    return results


def main(argv: Sequence[str] | None = None, *, root: Path = REPO_ROOT) -> int:
    """Run the mutants of the lines named; return the exit status, 0, 1 or 2."""
    try:
        args = parse_args(sys.argv[1:] if argv is None else argv)
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
