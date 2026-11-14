"""Run the gate's browser unit tests, `vitest run` over `ui/`, or refuse by name.

Run it from the repository root, as the `Makefile`'s `gate` does:

    uv run python -m tools.test_ui

One file, with vitest's own options after it:

    uv run python -m tools.test_ui ui/src/<name>.test.ts

The refusals and the run are `tools/npm_ui.py`'s.
"""

import shutil
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from tools import npm_ui

ROOT = npm_ui.ROOT

NO_NPM, NO_MODULES = npm_ui.refusals("test_ui", "browser unit tests", "vitest")


def refusal(
    root: Path = ROOT, which: Callable[[str], str | None] = shutil.which
) -> str | None:
    """Return why the tests cannot run, or None when they can."""
    return npm_ui.refusal(NO_NPM, NO_MODULES, root, which)


def in_ui(args: Sequence[str]) -> list[str]:
    """Return the arguments with a leading `ui/` removed from each.

    e.g. ["ui/src/a.test.ts", "-t", "x"] -> ["src/a.test.ts", "-t", "x"]
    """
    return [arg.removeprefix("ui/") for arg in args]


def main(root: Path = ROOT, args: Sequence[str] = ()) -> int:
    """Run `npm run test` in `ui/` and return its code, or 1 after a refusal."""
    return npm_ui.run("test", refusal(root, shutil.which), root, in_ui(args))


if __name__ == "__main__":
    sys.exit(main(args=sys.argv[1:]))
