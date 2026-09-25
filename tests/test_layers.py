"""The layers of `docs/principles.md`, held by an AST scan of every import.

Each rule is a function over a root directory, so the twins can run it on a small
package built under `tmp_path`. Imports inside functions count: a lazy import is
still an edge. `tests/` is not scanned -- a component's own tests reach inside it.
Why and how: `0027` design D3.
"""

import ast
from collections.abc import Iterator
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Lowest first: a layer may import itself and the layers before it.
LAYERS = ("foundation", "shared", "boundary", "pipeline", "interface")

# Importers whose sub-package imports must go through the front door.
FRONT_DOOR_SCOPE = ("isekai", "probe", "scripts", "evaluate.py")

# The upward edges still to move, as (importer, imported module). Exact: an entry
# whose import is gone fails `test_the_allowlist_names_only_imports_that_exist`.
# Remove when the docs phase of `0027` deletes it.
ALLOWLIST = frozenset(
    {
        ("isekai/shared/vocabulary.py", "isekai.boundary.provision"),
        ("isekai/shared/vocabulary.py", "isekai.evaluation.eval_models"),
        ("isekai/boundary/wd14.py", "isekai.evaluation.eval_models"),
    }
)

Edge = tuple[str, str]


def _module_name(root: Path, path: Path) -> str:
    """Return the dotted name of a file under `root`.

    e.g. `isekai/interface/ui/__init__.py` -> `isekai.interface.ui`
    """
    parts = list(path.relative_to(root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _is_module(root: Path, name: str) -> bool:
    base = root.joinpath(*name.split("."))
    return base.with_suffix(".py").is_file() or (base / "__init__.py").is_file()


def _sources(root: Path, scope: tuple[str, ...]) -> Iterator[Path]:
    for entry in scope:
        path = root / entry
        if path.is_file():
            yield path
        elif path.is_dir():
            yield from sorted(path.rglob("*.py"))


def _imports(root: Path, path: Path) -> set[str]:
    """Return every `isekai` module a file imports, anywhere in its body.

    `from isekai.x import n` names `isekai.x.n` when that is a module, else `isekai.x`.
    """
    name = _module_name(root, path)
    package = name if path.name == "__init__.py" else name.rpartition(".")[0]
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                anchor = package.split(".")[: len(package.split(".")) - node.level + 1]
                base = ".".join([*anchor, base] if base else anchor)
            for alias in node.names:
                full = f"{base}.{alias.name}"
                found.add(full if _is_module(root, full) else base)
    return {module for module in found if module.split(".")[0] == "isekai"}


def _edges(root: Path, scope: tuple[str, ...] = ("isekai",)) -> Iterator[Edge]:
    for path in _sources(root, scope):
        importer = path.relative_to(root).as_posix()
        for module in sorted(_imports(root, path)):
            yield importer, module


def _layer(dotted: str) -> str | None:
    parts = dotted.split(".")
    return parts[1] if len(parts) > 1 and parts[1] in LAYERS else None


def _dotted(importer: str) -> str:
    return importer.removesuffix(".py").removesuffix("/__init__").replace("/", ".")


def upward_imports(root: Path) -> set[Edge]:
    """Return every import that names a layer above its importer's."""
    found: set[Edge] = set()
    for importer, module in _edges(root):
        low, high = _layer(_dotted(importer)), _layer(module)
        if low and high and LAYERS.index(high) > LAYERS.index(low):
            found.add((importer, module))
    return found


def evaluation_imports(root: Path) -> set[Edge]:
    """Return every import of `isekai.evaluation` from outside it."""
    return {
        (importer, module)
        for importer, module in _edges(root)
        if not importer.startswith("isekai/evaluation/")
        and (module + ".").startswith("isekai.evaluation.")
    }


def stage_imports(root: Path) -> set[Edge]:
    """Return every import of one pipeline module by another."""
    return {
        (importer, module)
        for importer, module in _edges(root)
        if importer.startswith("isekai/pipeline/")
        and module.startswith("isekai.pipeline.")
        and module != _dotted(importer)
    }


def layer_cycles(root: Path) -> list[list[str]]:
    """Return one path per import cycle among the modules of a single layer."""
    graph: dict[str, set[str]] = {}
    for importer, module in _edges(root):
        source = _dotted(importer)
        if _layer(source) and _layer(source) == _layer(module) and source != module:
            graph.setdefault(source, set()).add(module)
    cycles: list[list[str]] = []
    done: set[str] = set()

    def visit(node: str, path: list[str]) -> None:
        if node in path:
            cycles.append([*path[path.index(node) :], node])
            return
        if node in done:
            return
        for nxt in sorted(graph.get(node, ())):
            visit(nxt, [*path, node])
        done.add(node)

    for node in sorted(graph):
        visit(node, [])
    return cycles


def busy_inits(root: Path) -> list[str]:
    """Return each root or layer `__init__.py` that holds more than a docstring."""
    inits = [root / "isekai" / "__init__.py"]
    inits += [root / "isekai" / layer / "__init__.py" for layer in LAYERS]
    busy: list[str] = []
    for path in inits:
        if not path.is_file():
            continue
        body = ast.parse(path.read_text()).body
        docstring_only = (
            len(body) == 1
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        )
        if not docstring_only:
            busy.append(path.relative_to(root).as_posix())
    return busy


def past_front_doors(root: Path) -> set[Edge]:
    """Return every import of a module inside a layer's sub-package from outside it."""
    doors = {
        _module_name(root, init)
        for layer in LAYERS
        for init in (root / "isekai" / layer).glob("*/__init__.py")
    }
    found: set[Edge] = set()
    for importer, module in _edges(root, FRONT_DOOR_SCOPE):
        for door in doors:
            inside = importer.startswith(door.replace(".", "/") + "/")
            if module.startswith(door + ".") and not inside:
                found.add((importer, module))
    return found


# --- the rules, on this repository -------------------------------------------


@pytest.mark.spec_exempt("structural: imports point only down the layers")
def test_every_import_points_down() -> None:
    assert upward_imports(REPO_ROOT) - ALLOWLIST == set()


@pytest.mark.spec_exempt(
    "structural: evaluation measures isekai, and isekai never imports it"
)
def test_nothing_in_the_package_imports_evaluation() -> None:
    assert evaluation_imports(REPO_ROOT) - ALLOWLIST == set()


@pytest.mark.spec_exempt("structural: a stage reads files, never another stage")
def test_no_stage_imports_another() -> None:
    assert stage_imports(REPO_ROOT) == set()


@pytest.mark.spec_exempt(
    "structural: the modules of a layer import each other without a cycle"
)
def test_no_import_cycle_inside_a_layer() -> None:
    assert layer_cycles(REPO_ROOT) == []


@pytest.mark.spec_exempt("structural: a layer is a folder, not a front door")
def test_a_layer_init_holds_only_a_docstring() -> None:
    assert busy_inits(REPO_ROOT) == []


@pytest.mark.spec_exempt("structural: a sub-package is reached through its front door")
def test_a_subpackage_is_reached_only_through_its_front_door() -> None:
    assert past_front_doors(REPO_ROOT) == set()


@pytest.mark.spec_exempt("structural: the allowlist of upward edges is exact")
def test_the_allowlist_names_only_imports_that_exist() -> None:
    assert ALLOWLIST - set(_edges(REPO_ROOT)) == set()


# --- the twins: each rule, broken on purpose ----------------------------------


def _package(root: Path, files: dict[str, str]) -> Path:
    """Write `files` under `root`, beside a docstring `__init__.py` for every layer."""
    defaults = {"isekai/__init__.py": '"""Root."""\n'}
    defaults |= {f"isekai/{layer}/__init__.py": '"""Layer."""\n' for layer in LAYERS}
    for name, text in (defaults | files).items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


@pytest.mark.spec_exempt("structural: twin of test_every_import_points_down")
def test_the_check_catches_an_import_pointing_up(tmp_path: Path) -> None:
    root = _package(
        tmp_path,
        {
            "isekai/foundation/run.py": (
                "def f():\n    from isekai.pipeline.sheet import x\n"
            ),
            "isekai/pipeline/sheet.py": "x = 1\n",
        },
    )
    assert upward_imports(root) == {
        ("isekai/foundation/run.py", "isekai.pipeline.sheet")
    }


@pytest.mark.spec_exempt(
    "structural: twin of test_nothing_in_the_package_imports_evaluation"
)
def test_the_check_catches_an_import_of_evaluation(tmp_path: Path) -> None:
    root = _package(
        tmp_path,
        {
            "isekai/shared/image.py": "from isekai.evaluation import labels\n",
            "isekai/evaluation/__init__.py": "",
            "isekai/evaluation/labels.py": "",
        },
    )
    assert evaluation_imports(root) == {
        ("isekai/shared/image.py", "isekai.evaluation.labels")
    }


@pytest.mark.spec_exempt("structural: twin of test_no_stage_imports_another")
def test_the_check_catches_a_stage_importing_another(tmp_path: Path) -> None:
    root = _package(
        tmp_path,
        {
            "isekai/pipeline/generate.py": "from isekai.pipeline.review import state\n",
            "isekai/pipeline/review.py": "state = 1\n",
        },
    )
    assert stage_imports(root) == {
        ("isekai/pipeline/generate.py", "isekai.pipeline.review")
    }


@pytest.mark.spec_exempt("structural: twin of test_no_import_cycle_inside_a_layer")
def test_the_check_catches_a_cycle_inside_a_layer(tmp_path: Path) -> None:
    root = _package(
        tmp_path,
        {
            "isekai/shared/a.py": "from isekai.shared.b import y\nx = 1\n",
            "isekai/shared/b.py": (
                "def g():\n    from isekai.shared.a import x\ny = 1\n"
            ),
        },
    )
    assert layer_cycles(root) == [
        ["isekai.shared.a", "isekai.shared.b", "isekai.shared.a"]
    ]


@pytest.mark.spec_exempt("structural: twin of test_a_layer_init_holds_only_a_docstring")
def test_the_check_catches_code_in_a_layer_init(tmp_path: Path) -> None:
    root = _package(
        tmp_path,
        {
            "isekai/boundary/__init__.py": (
                '"""Layer."""\nfrom isekai.foundation import run\n'
            )
        },
    )
    assert busy_inits(root) == ["isekai/boundary/__init__.py"]


@pytest.mark.spec_exempt(
    "structural: twin of test_a_subpackage_is_reached_only_through_its_front_door"
)
def test_the_check_catches_an_import_past_a_front_door(tmp_path: Path) -> None:
    root = _package(
        tmp_path,
        {
            "isekai/interface/ui/__init__.py": (
                "from isekai.interface.ui.app import serve\n"
            ),
            "isekai/interface/ui/app.py": "serve = 1\n",
            "isekai/interface/cli.py": "from isekai.interface.ui import app\n",
            "probe/loader_probe.py": "from isekai.interface.ui.app import serve\n",
        },
    )
    assert past_front_doors(root) == {
        ("isekai/interface/cli.py", "isekai.interface.ui.app"),
        ("probe/loader_probe.py", "isekai.interface.ui.app"),
    }
