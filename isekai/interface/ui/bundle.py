"""The browser bundle: built on demand, never committed, and refusing by name.

**The line is drawn at the network.** `vite build` is local and free, so a
missing `ui/dist/` is built without asking. `npm install` pulls arbitrary
third-party packages, so a missing `ui/node_modules/` refuses and names the
command -- a verb that fetched silently would be the surprise every other
network-touching default in this system avoids.

**node is one of this repository's two system dependencies**, beside Ollama, and
the refusal takes the shape both are under: say what is absent, say what installs
it, and say which part of the system needs it.

**The bundle is not tracked.** Vite emits content-hashed filenames, so committing
it would churn version control on every build for no reading a human does.
`ui/dist/` and `ui/node_modules/` are two of the repository's ignored roots,
and they fail differently from the other two: losing this one costs a
deterministic rebuild, losing the other an `npm install` (design.md D12).

Stdlib only -- `subprocess` and `shutil`, and nothing else reaches for either.
"""

import shutil
import subprocess
from pathlib import Path

from isekai.foundation.refusal import Refusal
from isekai.foundation.run import REPOSITORY

SOURCE = REPOSITORY / "ui"

BINARY = "npm"

# **What freshness is measured against: everything under `ui/` that is not one
# of the two ignored roots.** Stated as an exclusion rather than as a list of
# build inputs, because that list was wrong twice. It held `src/` and
# `index.html` alone until v0.22.1, so a bumped dependency, a plugin added to
# `vite.config.ts` or a changed build script left the previous bundle being
# served with a green gate -- `npm run typecheck` compiles the source and the
# server reads the build (v0.20 R6, v0.20 security/S2). Naming those three
# would have left out `tsconfig.json`, which `vite` reads and which sits in
# that directory today, and `postcss.config.js` or `public/` for whoever adds
# one next.
#
# The exclusion cannot go stale the same way: `dist/` is this function's own
# output and `node_modules/` is fetched, and both are ignored roots this
# repository already names as such. Everything else under `ui/` is tracked
# source, so the worst this rule can do is rebuild when a design note changes
# -- a few seconds, against a stale bundle nobody notices, which is the failure
# this entry was raised twice to stop.
NOT_SOURCE = frozenset({"dist", "node_modules"})

# The build is local, free and ordinarily a few seconds. A ceiling anyway,
# because `npm run build` can reach the network resolving a missing dependency
# and an `isekai ui` that hangs with no port bound and no output is
# indistinguishable from one that died (v0.20 R9').
BUILD_TIMEOUT = 300


def _newest(root: Path) -> float:
    """Return the newest mtime under `root`, or 0.0 where it holds no files."""
    return max(
        (item.stat().st_mtime for item in root.rglob("*") if item.is_file()),
        default=0.0,
    )


def _is_fresh(dist: Path, source: Path) -> bool:
    """Say whether the built bundle is newer than every source it is built from.

    **Presence is not freshness, and this is the whole of the defect it fixes.**
    The first version of this function returned any non-empty `dist/`, so an
    operator whose bundle was built by an earlier version went on being served
    that earlier version's page -- silently, with a green gate, because
    `npm run typecheck` compiles the *source* and the server reads the *build*.
    Nothing was wrong except that nothing had been rebuilt.

    It was unobservable until now for a reason that has just expired: v0.20 is
    the first version to change `ui/src/` since the bundle began being built on
    demand, so it is the first in which a stale `dist/` and a fresh checkout
    disagree. The rule about not going into files a version never touches does
    not apply to a gap the version itself makes reachable (design.md D28).

    Compared by mtime rather than by a content hash: `vite` emits
    content-hashed filenames, so a rebuild that changes nothing is cheap and a
    rebuild that changes something is exactly what is wanted. What counts as
    source is an exclusion rather than a list -- see `NOT_SOURCE`.
    """
    if not (dist.is_dir() and any(dist.iterdir())):
        return False
    # Pruned at the top level rather than filtered after the walk, because
    # `node_modules/` is thousands of files and this runs at every startup.
    return _newest(dist) >= max(
        (
            _newest(item) if item.is_dir() else item.stat().st_mtime
            for item in source.iterdir()
            if item.name not in NOT_SOURCE
        ),
        default=0.0,
    )


def ensure_built(source: Path = SOURCE) -> Path:
    """Return the built bundle's directory, building it first if it is absent.

    Called at startup, before a port is bound, so a missing toolchain is a
    message in the terminal the operator is already standing in rather than a
    blank page they have to diagnose.

    **Rebuilt when the source has moved under it**, not only when it is absent:
    see `_is_fresh`. A bundle that is present but older than the code it was
    built from is the one failure here that looks like success.
    """
    dist = source / "dist"
    if _is_fresh(dist, source):
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

    try:
        built = subprocess.run(
            [BINARY, "run", "build"],
            cwd=source,
            capture_output=True,
            text=True,
            timeout=BUILD_TIMEOUT,
        )
    except subprocess.TimeoutExpired as slow:
        raise Refusal(
            f"{BINARY} run build did not finish within {BUILD_TIMEOUT} seconds "
            f"and was stopped; run it in {source.name}/ by hand to see where it "
            "stops -- a build that reaches the network for a missing dependency "
            "is the usual cause"
        ) from slow
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
