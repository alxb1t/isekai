# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Print one count of what the repository pins, specifies or decides.

Run from the repository root: `counts.py pinned|scenarios|decisions`.
"""

import ast
import re
import sys
from pathlib import Path

MEASURES = ("pinned", "scenarios", "decisions")
SCENARIO = re.compile(r"^#### Scenario:", re.MULTILINE)
DECISION = re.compile(r"^### D\d+ ·", re.MULTILINE)


def pinned(root: Path) -> int:
    """Return the flows `PINNED` in `tests/test_flow.py` holds a digest for."""
    tree = ast.parse((root / "tests" / "test_flow.py").read_text("utf-8"))
    for node in tree.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "PINNED"
            and isinstance(node.value, ast.Dict)
        ):
            return len(node.value.keys)
    raise ValueError("tests/test_flow.py holds no `PINNED` dict")


def scenarios(root: Path) -> int:
    """Return the scenarios across the living specs."""
    specs = (root / "openspec" / "specs").glob("*/spec.md")
    return sum(len(SCENARIO.findall(path.read_text("utf-8"))) for path in specs)


def decisions(root: Path) -> int:
    """Return the decisions `docs/decisions.md` has a heading for."""
    return len(DECISION.findall((root / "docs" / "decisions.md").read_text("utf-8")))


def main(argv: list[str] | None = None) -> int:
    """Print the count `argv` names, or the reason it cannot be read."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1 or args[0] not in MEASURES:
        print(f"usage: counts.py {'|'.join(MEASURES)}", file=sys.stderr)
        return 1
    measure = {"pinned": pinned, "scenarios": scenarios, "decisions": decisions}
    try:
        print(measure[args[0]](Path.cwd()))
    except (OSError, ValueError) as refusal:
        print(f"{args[0]} unreadable: {refusal}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
