"""The browser bundle: built on demand, never committed, and refusing by name.

**The line is drawn at the network.** `vite build` is local and free, so a
missing `ui/dist/` is built without asking. `npm install` pulls arbitrary
third-party packages, so a missing `ui/node_modules/` refuses and names the
command -- a verb that fetched silently would be the surprise every other
network-touching default in this system avoids.

**node is this repository's second system dependency**, after the `claude`
binary, and the refusal copies `claude_cli.require_binary()`'s shape: say what is
absent, say what installs it, and say which part of the system needs it.

**The bundle is not tracked.** Vite emits content-hashed filenames, so committing
it would churn version control on every build for no reading a human does.
`ui/dist/` and `ui/node_modules/` are two of the repository's four ignored roots,
and they fail differently from the other two: losing this one costs a
deterministic rebuild, losing the other an `npm install` (design.md D12).

Stdlib only -- `subprocess` and `shutil`, the same two `claude_cli.py` uses.
"""

import shutil
import subprocess
from pathlib import Path

from isekai.foundation.refusal import Refusal
from isekai.interface.wiring import REPOSITORY

SOURCE = REPOSITORY / "ui"

DIST = SOURCE / "dist"

MODULES = SOURCE / "node_modules"

BINARY = "npm"


def ensure_built(source: Path = SOURCE) -> Path:
    """Return the built bundle's directory, building it first if it is absent.

    Called at startup, before a port is bound, so a missing toolchain is a
    message in the terminal the operator is already standing in rather than a
    blank page they have to diagnose.
    """
    dist = source / "dist"
    if dist.is_dir() and any(dist.iterdir()):
        return dist

    if shutil.which(BINARY) is None:
        raise Refusal(
            f"{BINARY!r} is not on PATH, and `isekai ui` is the only verb that "
            "needs it; install Node.js (https://nodejs.org), then run this "
            "command again -- every other verb in this pipeline is unaffected"
        )
    if not (source / "node_modules").is_dir():
        raise Refusal(
            f"{source.name}/node_modules/ is absent and the browser bundle "
            f"cannot be built without it; run `npm install` in {source.name}/ "
            "-- it is not done for you, because it fetches third-party packages"
        )

    built = subprocess.run(
        [BINARY, "run", "build"], cwd=source, capture_output=True, text=True
    )
    if built.returncode != 0:
        raise Refusal(
            f"building the browser bundle failed ({BINARY} run build exited "
            f"{built.returncode}); {built.stderr.strip() or built.stdout.strip()}"
        )
    if not dist.is_dir():
        raise Refusal(
            f"{BINARY} run build reported success and wrote no {dist.name}/; "
            f"check {source.name}/vite.config.ts for where it puts its output"
        )
    return dist
