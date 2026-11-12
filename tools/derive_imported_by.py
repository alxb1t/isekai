"""Write the `## Imported by` table of each layer README from the import graph.

Run it from the repository root:

    uv run python -m tools.derive_imported_by

A row keeps its first cell, the file or package the row is about; the other two
cells are written. The graph is the one the layer guards read, over `isekai`,
`evaluation` and `tools`, so no test is named.
"""

import re
from pathlib import Path

from tools.import_graph import edges, module_name

REPO_ROOT = Path(__file__).resolve().parent.parent

SCOPE = ("isekai", "evaluation", "tools")

TABLES = (
    Path("isekai/foundation/README.md"),
    Path("isekai/shared/README.md"),
    Path("isekai/boundary/README.md"),
    Path("isekai/pipeline/README.md"),
    Path("isekai/interface/README.md"),
    Path("evaluation/README.md"),
)

HEADING = "## Imported by"

NOTE = (
    "**Derived.** `uv run python -m tools.derive_imported_by` writes this table from "
    "the import graph of `tools/import_graph.py`, the one the layer guards read, and "
    "a test re-derives it. It names importers in `isekai/`, `evaluation/` and "
    "`tools/`, never a test."
)

ROW = re.compile(r"^\| `([^`]+)` \|")


def _file_of(root: Path, dotted: str) -> Path:
    """Return the file a dotted module name stands for, relative to `root`.

    e.g. `isekai.interface.ui` -> `isekai/interface/ui/__init__.py`
    """
    base = root.joinpath(*dotted.split("."))
    module = base.with_suffix(".py")
    return (module if module.is_file() else base / "__init__.py").relative_to(root)


def _target(root: Path, readme: Path, cell: str) -> str:
    """Return the dotted name a row's first cell names, refusing a row with none.

    e.g. `comfy/` in `isekai/boundary/README.md` -> `isekai.boundary.comfy`
    """
    path = root / readme.parent / cell
    found = path / "__init__.py" if cell.endswith("/") else path
    if not found.is_file():
        raise ValueError(f"{readme}: row `{cell}` names no module")
    return module_name(root, found)


def _importers(root: Path, target: str, package: bool) -> list[Path]:
    """Return the files that import `target`, or anything under it when a package."""
    found = {
        importer
        for importer, module in edges(root, SCOPE)
        if (module == target or (package and module.startswith(target + ".")))
        and importer != target
        and not (package and importer.startswith(target + "."))
    }
    return sorted(_file_of(root, importer) for importer in found)


def _cell(shown: list[str]) -> str:
    return ", ".join(f"`{name}`" for name in shown) or "—"


def _within_readme(path: Path, readme: Path) -> str:
    """Return `path` under the README's directory when it is there, else its package."""
    base = (
        readme.parent if path.is_relative_to(readme.parent) else Path(readme.parts[0])
    )
    return path.relative_to(base).as_posix()


def _row(root: Path, readme: Path, line: str) -> str:
    match = ROW.match(line)
    if not match:
        raise ValueError(f"{readme}: row {line!r} names no file")
    cell = match[1]
    target = _target(root, readme, cell)
    files = _importers(root, target, cell.endswith("/"))
    inside = [_within_readme(p, readme) for p in files if p.parts[0] == readme.parts[0]]
    outside = [p.as_posix() for p in files if p.parts[0] != readme.parts[0]]
    return f"| `{cell}` | {_cell(inside)} | {_cell(outside)} |"


def derive(root: Path, readme: Path) -> str:
    """Return the text of `readme` with its `## Imported by` table re-derived.

    The lines between the heading and the table's header row become `NOTE`; the
    header row stays as it stands.
    """
    lines = (root / readme).read_text().split("\n")
    heading = lines.index(HEADING)
    header = next(
        i for i in range(heading, len(lines)) if lines[i].startswith("| file |")
    )
    end = header + 2
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    rows = [_row(root, readme, line) for line in lines[header + 2 : end]]
    return "\n".join(
        [*lines[: heading + 1], "", NOTE, "", *lines[header : header + 2], *rows]
        + lines[end:]
    )


def main() -> int:
    """Write each table in `TABLES`, and return the process's exit status."""
    for readme in TABLES:
        (REPO_ROOT / readme).write_text(derive(REPO_ROOT, readme))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
