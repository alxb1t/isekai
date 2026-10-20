"""Run one of `ui/`'s npm scripts for the gate, or refuse by name.

`npm run` needs the package directory, and a missing toolchain refuses by name
rather than exiting 127. The refusals copy `isekai/interface/ui/bundle.py`'s shape.
`npm install` is never run here: it fetches third-party packages, and nothing in
this repository restores `ui/node_modules/` silently.
"""

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def refusals(tool: str, what: str, needs: str) -> tuple[str, str]:
    """Return a tool's refusals: npm missing, then `ui/node_modules/` missing.

    e.g. ("test_ui", "browser unit tests", "vitest")
    """
    return (
        f"{tool}: 'npm' is not on PATH, and the gate's {what}\n"
        "  cannot run without it; install Node.js (https://nodejs.org), then run\n"
        "  this command again -- every other gate command is unaffected",
        f"{tool}: ui/node_modules/ is absent and {needs} cannot run without\n"
        "  it; run `npm install` in ui/ -- it is not done for you, because it\n"
        "  fetches third-party packages",
    )


def refusal(
    no_npm: str, no_modules: str, root: Path, which: Callable[[str], str | None]
) -> str | None:
    """Return why the script cannot run, or None when it can."""
    if which("npm") is None:
        return no_npm
    if not (root / "ui" / "node_modules").is_dir():
        return no_modules
    return None


def run(script: str, refused: str | None, root: Path) -> int:
    """Run `npm run <script>` in `ui/` and return its code, or 1 after a refusal."""
    if refused is not None:
        print(refused, file=sys.stderr)
        return 1
    return subprocess.run(
        ["npm", "run", script], cwd=root / "ui", check=False
    ).returncode
