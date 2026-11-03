# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print how many tests pytest selects for the arguments given.

Run from the repository root: `tests_collected.py --ignore=tests/e2e`.
"""

import re
import subprocess
import sys

SUMMARY = re.compile(r"^(?:(\d+)(?:/\d+)?|no) tests? collected", re.MULTILINE)
NO_TESTS_EXIT = 5


def selected(output: str) -> int:
    """Return the selected count in pytest's collect summary.

    e.g. "3/5 tests collected (2 deselected) in 0.1s" -> 3
    """
    match = SUMMARY.search(output)
    if match is None:
        raise ValueError("pytest printed no `N tests collected` line")
    return int(match[1] or 0)


def main(argv: list[str] | None = None) -> int:
    """Print the selected count, or the reason it cannot be read."""
    args = sys.argv[1:] if argv is None else argv
    done = subprocess.run(
        ["uv", "run", "--frozen", "pytest", "--collect-only", "-q", *args],
        capture_output=True,
        text=True,
    )
    if done.returncode not in (0, NO_TESTS_EXIT):
        print(f"pytest exited {done.returncode}", file=sys.stderr)
        return 1
    try:
        count = selected(done.stdout)
    except ValueError as refusal:
        print(refusal, file=sys.stderr)
        return 1
    print(count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
