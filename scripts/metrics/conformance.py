# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print how far a change's branch departs from the method, by one measure.

Run from the repository root: `conformance.py trailer|minions|amends`. The
collector sets `MF_METRICS_CHANGE`, `MF_METRICS_BASE` and `MF_METRICS_HEAD`.
"""

import os
import subprocess
import sys
from pathlib import Path

MEASURES = ("trailer", "minions", "amends")
RECORD = "\x1e"
FIELD = "\x1f"


def git(root: Path, *args: str) -> str:
    """Return the output of a git command run in `root`."""
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    ).stdout


def commits_without_trailer(root: Path, change: str, base: str, head: str) -> int:
    """Return the commits in base..head whose `Change` trailer is not `change`.

    e.g. two commits, one trailed `Change: 0092-x` and one trailed nothing -> 1
    """
    log = git(
        root,
        "log",
        f"--format={RECORD}%H{FIELD}%(trailers:key=Change,valueonly,separator=%x1f)",
        f"{base}..{head}",
    )
    missing = 0
    for record in filter(None, log.split(RECORD)):
        _, _, trailers = record.partition(FIELD)
        if change not in [value.strip() for value in trailers.split(FIELD)]:
            missing += 1
    return missing


def minions_files_tracked(root: Path) -> int:
    """Return the tracked files under `.minions`."""
    return len(git(root, "ls-files", ".minions").splitlines())


def amends(root: Path, change: str, base: str, head: str) -> int:
    """Return the commits in base..head that amend the change directory."""
    subjects = git(root, "log", "--format=%s", f"{base}..{head}").splitlines()
    return subjects.count(f"docs({change}): amend the change directory")


def main(argv: list[str] | None = None) -> int:
    """Print the measure named in `argv`, or the reason it cannot be read."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1 or args[0] not in MEASURES:
        print(f"usage: conformance.py {'|'.join(MEASURES)}", file=sys.stderr)
        return 1
    root = Path.cwd()
    try:
        if args[0] == "minions":
            print(minions_files_tracked(root))
            return 0
        change = os.environ["MF_METRICS_CHANGE"]
        base = os.environ["MF_METRICS_BASE"]
        head = os.environ["MF_METRICS_HEAD"]
        measure = commits_without_trailer if args[0] == "trailer" else amends
        print(measure(root, change, base, head))
    except KeyError as missing:
        print(f"{missing.args[0]} is not set", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as refusal:
        print(f"git failed: {refusal.stderr.strip()}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
