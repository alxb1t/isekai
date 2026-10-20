"""Run the gate's browser unit tests, `vitest run` over `ui/`, or refuse by name.

Run it from the repository root, as the `Makefile`'s `gate` does:

    uv run python -m tools.test_ui

The shape is `tools/typecheck_ui.py`'s: `npm run` needs the package directory,
a missing toolchain refuses by name rather than exiting 127, and `npm install`
is never run here.
"""

import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NO_NPM = (
    "test_ui: 'npm' is not on PATH, and the gate's browser unit tests\n"
    "  cannot run without it; install Node.js (https://nodejs.org), then run\n"
    "  this command again -- every other gate command is unaffected"
)

NO_MODULES = (
    "test_ui: ui/node_modules/ is absent and vitest cannot run without\n"
    "  it; run `npm install` in ui/ -- it is not done for you, because it\n"
    "  fetches third-party packages"
)


def refusal(
    root: Path = ROOT, which: Callable[[str], str | None] = shutil.which
) -> str | None:
    """Return why the tests cannot run, or None when they can."""
    if which("npm") is None:
        return NO_NPM
    if not (root / "ui" / "node_modules").is_dir():
        return NO_MODULES
    return None


def main(root: Path = ROOT) -> int:
    """Run `npm run test` in `ui/` and return its code, or 1 after a refusal."""
    refused = refusal(root, shutil.which)
    if refused is not None:
        print(refused, file=sys.stderr)
        return 1
    return subprocess.run(
        ["npm", "run", "test"], cwd=root / "ui", check=False
    ).returncode


if __name__ == "__main__":
    sys.exit(main())
