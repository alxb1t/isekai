"""Run the gate's browser unit tests, `vitest run` over `ui/`, or refuse by name.

Run it from the repository root, as the `Makefile`'s `gate` does:

    uv run python -m tools.test_ui

The refusals and the run are `tools/npm_ui.py`'s.
"""

import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from tools import npm_ui

ROOT = npm_ui.ROOT

NO_NPM, NO_MODULES = npm_ui.refusals("test_ui", "browser unit tests", "vitest")


def refusal(
    root: Path = ROOT, which: Callable[[str], str | None] = shutil.which
) -> str | None:
    """Return why the tests cannot run, or None when they can."""
    return npm_ui.refusal(NO_NPM, NO_MODULES, root, which)


def main(root: Path = ROOT) -> int:
    """Run `npm run test` in `ui/` and return its code, or 1 after a refusal."""
    return npm_ui.run("test", refusal(root, shutil.which), root)


if __name__ == "__main__":
    sys.exit(main())
