"""The import graph of `isekai` and `evaluation`, read by an AST scan.

The layer guards and the importer tables read the same graph. Imports inside
functions count: a lazy import is still an edge. Stdlib only.
"""

import ast
from collections.abc import Iterator
from functools import cache
from importlib.util import resolve_name
from pathlib import Path

# The top-level packages whose imports the graph reads.
PACKAGES = ("isekai", "evaluation")

Edge = tuple[str, str]


def module_name(root: Path, path: Path) -> str:
    """Return the dotted name of a file under `root`.

    e.g. `isekai/interface/ui/__init__.py` -> `isekai.interface.ui`
    """
    parts = list(path.relative_to(root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def is_module(root: Path, name: str) -> bool:
    """Return whether the dotted `name` is a module or a package under `root`."""
    base = root.joinpath(*name.split("."))
    return base.with_suffix(".py").is_file() or (base / "__init__.py").is_file()


def sources(root: Path, scope: tuple[str, ...]) -> Iterator[Path]:
    """Yield every Python file under `scope`, failing on an entry that is not there.

    A missing entry would narrow the check with no failure.
    """
    for entry in scope:
        path = root / entry
        if path.is_file():
            yield path
        elif path.is_dir():
            yield from sorted(path.rglob("*.py"))
        else:
            raise FileNotFoundError(f"scope path {entry!r} does not exist under {root}")


def imports(root: Path, path: Path) -> set[str]:
    """Return every `isekai` or `evaluation` module a file imports, anywhere in it.

    `from isekai.x import n` names `isekai.x.n` when that is a module, else `isekai.x`.
    """
    name = module_name(root, path)
    package = name if path.name == "__init__.py" else name.rpartition(".")[0]
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = resolve_name("." * node.level + (node.module or ""), package)
            for alias in node.names:
                full = f"{base}.{alias.name}"
                found.add(full if is_module(root, full) else base)
    return {module for module in found if module.split(".")[0] in PACKAGES}


@cache
def edges(root: Path, scope: tuple[str, ...] = ("isekai",)) -> tuple[Edge, ...]:
    """Return every (importer, imported) pair under `scope`, both as dotted names."""
    return tuple(
        (module_name(root, path), module)
        for path in sources(root, scope)
        for module in sorted(imports(root, path))
    )
