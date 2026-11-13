"""Ceilings on the size of code and on what a test patches, each held by a ratchet.

A ratchet is a table of listed offenders and a row ceiling. An unlisted offender is
red, a row whose offender stopped offending is red, and a row count off its ceiling is
red. A listed offender may grow. A row is removed by the version that removes its
offender, and none is added: `docs/decisions.md` D56.

Each rule is a function over a root directory, so a twin can run it on a small tree
built under `tmp_path`.
"""

import ast
from collections.abc import Collection, Iterable, Iterator
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

FILE_LINES = 800
FUNCTION_LINES = 100
POSITIONAL = 6
UI_FILE_LINES = 600

# The top-level packages whose modules a patch can name.
PACKAGES = ("isekai", "evaluation")

# Those a patch is held to a name its module reads.
PATCH_PACKAGES = (*PACKAGES, "tools")


def ratchet_faults(
    measured: Collection[str], listed: Collection[str], rows: int
) -> list[str]:
    """Return the faults of a table, sorted.

    A fault is an unlisted offender, a stale row or a row count off its ceiling.

    e.g. `ratchet_faults({"a"}, {"a", "b"}, 2)` -> `["no longer offends b"]`
    """
    faults = [f"unlisted {key}" for key in set(measured) - set(listed)]
    faults += [f"no longer offends {key}" for key in set(listed) - set(measured)]
    if len(listed) != rows:
        faults.append(f"rows {len(listed)} listed, ceiling {rows}")
    return sorted(faults)


def _lines(path: Path) -> int:
    return len(path.read_text().splitlines())


def _key(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def long_files(root: Path) -> dict[str, int]:
    """Return each file under `isekai/` of more than `FILE_LINES` lines, with its lines.

    e.g. `{"isekai/interface/ui/app.py": 2954}`
    """
    sizes = {
        _key(root, path): _lines(path)
        for path in sorted((root / "isekai").rglob("*.py"))
    }
    return {key: size for key, size in sizes.items() if size > FILE_LINES}


def _functions(
    tree: ast.AST, scope: str = ""
) -> Iterator[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    """Yield each function of a tree by its dotted name, methods and nested ones too.

    e.g. `Box.method` for a method, `outer.inner` for a nested function
    """
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            name = f"{scope}{node.name}"
            yield name, node
            yield from _functions(node, f"{name}.")
        elif isinstance(node, ast.ClassDef):
            yield from _functions(node, f"{scope}{node.name}.")
        else:
            yield from _functions(node, scope)


def _functions_of(
    root: Path,
) -> Iterator[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    for path in sorted((root / "isekai").rglob("*.py")):
        key = _key(root, path)
        for name, node in _functions(ast.parse(path.read_text(), filename=key)):
            yield f"{key}::{name}", node


def long_functions(root: Path) -> dict[str, int]:
    """Return each function under `isekai/` past `FUNCTION_LINES` lines, with its lines.

    The lines run from the `def` to its last line, decorators out. A name defined twice,
    as a property's getter and setter are, counts its longest definition.
    e.g. `{"isekai/interface/ui/app.py::create_app": 1400}`
    """
    sizes: dict[str, int] = {}
    for key, node in _functions_of(root):
        size = (node.end_lineno or node.lineno) - node.lineno + 1
        # A property's getter and setter share a name: the longest definition counts.
        sizes[key] = max(size, sizes.get(key, 0))
    return {key: size for key, size in sizes.items() if size > FUNCTION_LINES}


def wide_functions(root: Path) -> dict[str, int]:
    """Return each function under `isekai/` past `POSITIONAL` positional parameters.

    A leading `self` or `cls` is dropped; `*args` and keyword-only ones are not counted.
    e.g. `{"isekai/pipeline/review.py::_write_draft": 8}`
    """
    widths: dict[str, int] = {}
    for key, node in _functions_of(root):
        names = [arg.arg for arg in node.args.posonlyargs + node.args.args]
        if names and names[0] in ("self", "cls"):
            names = names[1:]
        if len(names) > POSITIONAL:
            widths[key] = len(names)
    return widths


def big_ui_files(root: Path) -> dict[str, int]:
    """Return each `.vue`, `.ts` and `.css` file under `ui/src/` past `UI_FILE_LINES`.

    A name ending `.test.ts` is out. e.g. `{"ui/src/views/Review.vue": 912}`
    """
    sizes = {
        _key(root, path): _lines(path)
        for path in sorted((root / "ui" / "src").rglob("*"))
        if path.suffix in (".vue", ".ts", ".css") and not path.name.endswith(".test.ts")
    }
    return {key: size for key, size in sizes.items() if size > UI_FILE_LINES}


def _module_file(root: Path, dotted: str) -> Path | None:
    base = root.joinpath(*dotted.split("."))
    for candidate in (base.with_suffix(".py"), base / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def _top_names(path: Path) -> set[str]:
    """Return the names a module binds at its top level.

    A def, a class, an assignment or an import binds one.
    """
    names: set[str] = set()
    for node in ast.parse(path.read_text(), filename=str(path)).body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign | ast.AnnAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names.update(
                name.id
                for target in targets
                for name in ast.walk(target)
                if isinstance(name, ast.Name) and isinstance(name.ctx, ast.Store)
            )
        elif isinstance(node, ast.Import | ast.ImportFrom):
            names.update(
                (alias.asname or alias.name).split(".")[0] for alias in node.names
            )
    return names


def _bind(
    root: Path, node: ast.AST, packages: Collection[str], bound: dict[str, str]
) -> None:
    """Add to `bound` the module each name of one import statement stands for.

    Only a module of `packages` is bound, and a node that is no import binds nothing.
    e.g. `from isekai import x` -> `{"x": "isekai.x"}`
    e.g. `import isekai.x.y` -> `{"isekai": "isekai"}`
    """
    if isinstance(node, ast.Import):
        for alias in node.names:
            top = alias.name.split(".")[0]
            if top in packages:
                bound[alias.asname or top] = alias.name if alias.asname else top
    elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
        if node.module.split(".")[0] in packages:
            for alias in node.names:
                full = f"{node.module}.{alias.name}"
                if _module_file(root, full):
                    bound[alias.asname or alias.name] = full


def _bound_modules(
    root: Path, tree: ast.AST, packages: Collection[str]
) -> dict[str, str]:
    """Return the module each imported name stands for, anywhere in a file.

    A name imported twice stands for the last module in tree order; `_patches` scopes
    its names instead.
    e.g. `from isekai import x` -> `{"x": "isekai.x"}`
    """
    bound: dict[str, str] = {}
    for node in ast.walk(tree):
        _bind(root, node, packages, bound)
    return bound


def _chain(node: ast.expr) -> list[str] | None:
    """Return the names of a dotted chain, else None.

    e.g. `ui.library` -> `["ui", "library"]`
    """
    attributes: list[str] = []
    while isinstance(node, ast.Attribute):
        attributes.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    return [node.id, *reversed(attributes)]


def _text(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _setattr_target(
    node: ast.AST, bound: dict[str, str]
) -> tuple[int, str, str] | None:
    """Return the (line, dotted module path, name) an `x.setattr(...)` call patches.

    A node that is no such call, or whose target resolves to nothing, gives None.
    e.g. `setattr(ui.library, "run", f)` -> `(7, "isekai.interface.ui.library", "run")`
    """
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "setattr"
        and node.args
    ):
        return None
    first, rest = node.args[0], node.args[1:]
    if (dotted := _text(first)) is not None:
        module, _, name = dotted.rpartition(".")
        return node.lineno, module, name
    if (chain := _chain(first)) and chain[0] in bound and rest:
        if (name := _text(rest[0])) is not None:
            return node.lineno, ".".join([bound[chain[0]], *chain[1:]]), name
    return None


def _patches(
    root: Path,
    scope: ast.AST,
    packages: Collection[str],
    outer: dict[str, str] | None = None,
) -> Iterator[tuple[int, str, str]]:
    """Yield each `x.setattr(...)` patch of a scope, each bound by that scope's imports.

    A function's imports extend those of the scope around it. They reach no sibling
    function and not the module.
    e.g. a function that imports `ink as subject` patches `isekai.shared.ink`, whatever
    `subject` stands for in the function beside it
    """
    bound = dict(outer or {})
    nodes: list[ast.AST] = []
    functions: list[ast.AST] = []
    pending = list(ast.iter_child_nodes(scope))
    while pending:
        node = pending.pop()
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            functions.append(node)
            continue
        _bind(root, node, packages, bound)
        nodes.append(node)
        pending.extend(ast.iter_child_nodes(node))
    for node in nodes:
        if (patch := _setattr_target(node, bound)) is not None:
            yield patch
    for function in functions:
        yield from _patches(root, function, packages, bound)


def resolved_patches(
    root: Path, packages: Collection[str]
) -> list[tuple[str, int, str, str]]:
    """Return each patch of a module of `packages`, as (test path, line, module, name).

    A target that resolves to no module of the packages is left out.
    e.g. `("tests/test_x.py", 12, "isekai.boundary.ollama", "MODEL_RECORDS")`
    """
    found: list[tuple[str, int, str, str]] = []
    for path in sorted((root / "tests").rglob("*.py")):
        key = _key(root, path)
        tree = ast.parse(path.read_text(), filename=key)
        for line, module, name in sorted(_patches(root, tree, packages)):
            if module.split(".")[0] in packages and _module_file(root, module):
                found.append((key, line, module, name))
    return found


def patched_modules(root: Path) -> dict[str, int]:
    """Return each module whose own names a test patches, with its patches.

    A patch counts when the module binds the name at its top level.
    e.g. `{"isekai.interface.wiring": 5}`
    """
    counts: dict[str, int] = {}
    names: dict[Path, set[str]] = {}
    for _, _, module, name in resolved_patches(root, PACKAGES):
        file = _module_file(root, module)
        if file is None:
            continue
        if file not in names:
            names[file] = _top_names(file)
        if name in names[file]:
            counts[module] = counts.get(module, 0) + 1
    return dict(sorted(counts.items()))


def _dotted(root: Path, path: Path) -> str:
    parts = path.relative_to(root).with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


_FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)


def _locals(function: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda) -> set[str]:
    """Return the names a function binds for itself, its parameters and its stores.

    A nested function's own names are not counted, and a `global` name is not local.
    e.g. `def f(root): return root` -> `{"root"}`
    """
    arguments = function.args
    names = {
        argument.arg
        for argument in [
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
            *filter(None, [arguments.vararg, arguments.kwarg]),
        ]
    }
    declared: set[str] = set()
    pending: list[ast.AST] = (
        [function.body] if isinstance(function, ast.Lambda) else list(function.body)
    )
    while pending:
        node = pending.pop()
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.Global):
            declared.update(node.names)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
            continue
        elif isinstance(node, ast.Import | ast.ImportFrom):
            names.update(
                (alias.asname or alias.name).split(".")[0] for alias in node.names
            )
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
        pending.extend(ast.iter_child_nodes(node))
    return names - declared


def _bare_loads(nodes: Iterable[ast.AST], shadowed: frozenset[str]) -> set[str]:
    """Return the names loaded under `nodes` that no enclosing function binds itself.

    e.g. `def f(root): return root` loads nothing, `def f(): return root` loads `root`
    """
    loads: set[str] = set()
    for node in nodes:
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load) and node.id not in shadowed:
                loads.add(node.id)
        elif isinstance(node, _FUNCTIONS):
            outside = [
                *getattr(node, "decorator_list", []),
                *node.args.defaults,
                *filter(None, node.args.kw_defaults),
            ]
            body = [node.body] if isinstance(node.body, ast.expr) else node.body
            loads |= _bare_loads(outside, shadowed)
            loads |= _bare_loads(body, shadowed | _locals(node))
        else:
            loads |= _bare_loads(ast.iter_child_nodes(node), shadowed)
    return loads


def names_read(root: Path) -> dict[str, set[str]]:
    """Return, for each module under the patch packages, the names the product reads.

    A read is a load of a bare name no enclosing function binds for itself, in the
    module's own source; an attribute load through the module in any file; or an
    import of the name from the module inside a function. A store is not a read, a
    test is not product, and an import at module level is not a read: it copies the
    name when the importer loads, so a later patch of the source does not reach it.
    e.g. `{"isekai.boundary.ollama": {"MODEL_RECORDS", "OPENER"}}`
    """
    read: dict[str, set[str]] = {}
    for package in PATCH_PACKAGES:
        for path in sorted((root / package).rglob("*.py")):
            tree = ast.parse(path.read_text(), filename=_key(root, path))
            module = _dotted(root, path)
            bound = _bound_modules(root, tree, PATCH_PACKAGES)
            read.setdefault(module, set()).update(_bare_loads([tree], frozenset()))
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                    chain = _chain(node)
                    if chain and chain[0] in bound:
                        target = ".".join([bound[chain[0]], *chain[1:-1]])
                        read.setdefault(target, set()).add(chain[-1])
                elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    for inner in ast.walk(node):
                        if (
                            isinstance(inner, ast.ImportFrom)
                            and inner.level == 0
                            and inner.module
                        ):
                            read.setdefault(inner.module, set()).update(
                                alias.name for alias in inner.names
                            )
    return read


def unread_patches(root: Path) -> list[str]:
    """Return a line for each patch of a name its module's product never reads.

    A name read only in code that no longer runs the patched path still counts as
    read: this scan cannot see that.
    e.g. `["tests/test_x.py:9 patches isekai.m.gone, which nothing reads"]`
    """
    read = names_read(root)
    return [
        f"{path}:{line} patches {module}.{name}, which nothing reads"
        for path, line, module, name in resolved_patches(root, PATCH_PACKAGES)
        if name not in read.get(module, set())
    ]


# --- the tables: each row is `key: the measure when it was listed` -----------

LONG_FILES = {
    "isekai/foundation/run.py": 1045,
    "isekai/interface/cli.py": 1579,
    "isekai/interface/render.py": 1315,
    "isekai/interface/ui/app.py": 2351,
    "isekai/interface/ui/library.py": 881,
    "isekai/pipeline/importing.py": 841,
    "isekai/pipeline/review.py": 1278,
    "isekai/pipeline/tattoos.py": 1320,
}
FILE_ROWS = 8

LONG_FUNCTIONS = {
    "isekai/boundary/ollama.py::ask": 105,
    "isekai/foundation/flow.py::load_flow": 150,
    "isekai/interface/cli.py::build_parser": 368,
    "isekai/interface/cli.py::_per_item": 214,
    "isekai/interface/cli.py::_per_item.work": 154,
    "isekai/interface/render.py::_session": 119,
    "isekai/interface/render.py::_rendered": 118,
    "isekai/interface/ui/app.py::create_app": 1315,
    "isekai/pipeline/generate.py::render": 122,
    "isekai/pipeline/review.py::approve": 105,
}
FUNCTION_ROWS = 10

WIDE_FUNCTIONS = {
    "isekai/foundation/run.py::refusal_for": 9,
    "isekai/interface/drafting.py::draft_across": 7,
    "isekai/interface/render.py::Record.__init__": 7,
    "isekai/interface/render.py::_session": 9,
    "isekai/interface/render.py::_asked": 7,
    "isekai/interface/render.py::_rendered": 8,
    "isekai/interface/ui/app.py::create_app.read_compare": 8,
    "isekai/pipeline/review.py::_write_draft": 9,
    "isekai/pipeline/sheet.py::_from_tag_list": 8,
    "isekai/pipeline/tattoos.py::save_outline": 8,
    "isekai/pipeline/tattoos.py::ink_layer": 8,
    "isekai/pipeline/tattoos.py::ink_view": 8,
    "isekai/pipeline/tattoos.py::preview": 9,
    "isekai/pipeline/tattoos.py::composite": 8,
}
WIDE_ROWS = 14

BIG_UI_FILES = {
    "ui/src/app.css": 3044,
    "ui/src/views/Hub.vue": 671,
    "ui/src/views/Review.vue": 696,
}
UI_ROWS = 3

PATCHED_MODULES = {
    "evaluation.__main__": 5,
    "evaluation.eval_models": 2,
    "evaluation.face": 1,
    "evaluation.recall": 1,
    "isekai.boundary.ollama": 9,
    "isekai.boundary.provision": 7,
    "isekai.boundary.unpack": 3,
    "isekai.boundary.wd14": 4,
    "isekai.foundation.run": 1,
    "isekai.interface.cli": 2,
    "isekai.interface.render": 2,
    "isekai.interface.ui": 1,
    "isekai.interface.ui.app": 12,
    "isekai.interface.ui.bundle": 3,
    "isekai.interface.ui.events": 1,
    "isekai.interface.ui.library": 4,
    "isekai.interface.wiring": 13,
    "isekai.pipeline.edit": 3,
    "isekai.pipeline.generate": 1,
    "isekai.pipeline.importing": 8,
    "isekai.pipeline.review": 1,
    "isekai.pipeline.tattoos": 1,
    "isekai.shared.chain": 1,
    "isekai.shared.ink": 1,
}
PATCHED_ROWS = 24


# --- the rules, on this repository -------------------------------------------


@pytest.mark.spec_exempt("structural: a file under isekai/ past its ceiling is listed")
def test_no_long_file_is_unlisted() -> None:
    assert ratchet_faults(long_files(REPO_ROOT), LONG_FILES, FILE_ROWS) == []


@pytest.mark.spec_exempt(
    "structural: a function under isekai/ past its ceiling is listed"
)
def test_no_long_function_is_unlisted() -> None:
    faults = ratchet_faults(long_functions(REPO_ROOT), LONG_FUNCTIONS, FUNCTION_ROWS)
    assert faults == []


@pytest.mark.spec_exempt(
    "structural: a function under isekai/ past its parameter ceiling is listed"
)
def test_no_wide_function_is_unlisted() -> None:
    faults = ratchet_faults(wide_functions(REPO_ROOT), WIDE_FUNCTIONS, WIDE_ROWS)
    assert faults == []


@pytest.mark.spec_exempt("structural: a file under ui/src/ past its ceiling is listed")
def test_no_big_ui_file_is_unlisted() -> None:
    assert ratchet_faults(big_ui_files(REPO_ROOT), BIG_UI_FILES, UI_ROWS) == []


@pytest.mark.spec_exempt(
    "structural: a module whose own names a test patches is listed"
)
def test_no_patched_module_is_unlisted() -> None:
    faults = ratchet_faults(patched_modules(REPO_ROOT), PATCHED_MODULES, PATCHED_ROWS)
    assert faults == []


@pytest.mark.spec_exempt("structural: every patch names a name its module reads")
def test_every_patch_names_a_name_its_module_reads() -> None:
    assert resolved_patches(REPO_ROOT, PATCH_PACKAGES) != []
    assert unread_patches(REPO_ROOT) == []


# --- the twins: each rule, broken on purpose ----------------------------------


@pytest.mark.spec_exempt("structural: a ratchet reads each way a table goes wrong")
def test_the_ratchet_catches_each_way_a_table_goes_wrong() -> None:
    assert ratchet_faults({"a"}, {"a"}, 1) == []
    assert ratchet_faults({"a", "b"}, {"a"}, 1) == ["unlisted b"]
    assert ratchet_faults({"a"}, {"a", "b"}, 2) == ["no longer offends b"]
    assert ratchet_faults({"a"}, {"a"}, 2) == ["rows 1 listed, ceiling 2"]


@pytest.mark.spec_exempt("structural: twin of test_no_long_file_is_unlisted")
def test_the_check_catches_a_long_file(tmp_path: Path) -> None:
    (tmp_path / "isekai").mkdir()
    (tmp_path / "isekai" / "at.py").write_text("x = 1\n" * FILE_LINES)
    (tmp_path / "isekai" / "past.py").write_text("x = 1\n" * (FILE_LINES + 1))
    assert long_files(tmp_path) == {"isekai/past.py": FILE_LINES + 1}


def _def(header: str, lines: int, indent: str = "") -> str:
    """Return a `def` of `lines` lines in all, its header among them."""
    return f"{indent}{header}\n" + f"{indent}    pass\n" * (lines - 1)


def _isekai_module(root: Path, text: str) -> None:
    (root / "isekai").mkdir()
    (root / "isekai" / "m.py").write_text(text)


@pytest.mark.spec_exempt("structural: twin of test_no_long_function_is_unlisted")
def test_the_check_catches_a_long_function(tmp_path: Path) -> None:
    _isekai_module(
        tmp_path,
        "class Box:\n"
        + _def("def method(self):", FUNCTION_LINES + 1, "    ")
        + "def outer():\n"
        + _def("def inner():", FUNCTION_LINES + 1, "    ")
        + "@cache\n"
        + _def("def decorated():", FUNCTION_LINES)
        + "class Prop:\n"
        + "    @property\n"
        + _def("def value(self):", FUNCTION_LINES + 1, "    ")
        + "    @value.setter\n"
        + _def("def value(self, new):", 2, "    "),
    )
    assert long_functions(tmp_path) == {
        "isekai/m.py::Box.method": FUNCTION_LINES + 1,
        "isekai/m.py::Prop.value": FUNCTION_LINES + 1,
        "isekai/m.py::outer": FUNCTION_LINES + 2,
        "isekai/m.py::outer.inner": FUNCTION_LINES + 1,
    }


@pytest.mark.spec_exempt("structural: twin of test_no_wide_function_is_unlisted")
def test_the_check_catches_a_wide_function(tmp_path: Path) -> None:
    _isekai_module(
        tmp_path,
        "class Box:\n"
        "    def method(self, a, b, c, d, e, f):\n"
        "        pass\n"
        "def varied(a, b, c, d, e, f, *rest, g, h, i):\n"
        "    pass\n"
        "def pinned(a, b, c, /, d, e, f, g):\n"
        "    pass\n",
    )
    assert wide_functions(tmp_path) == {"isekai/m.py::pinned": POSITIONAL + 1}


@pytest.mark.spec_exempt("structural: twin of test_no_big_ui_file_is_unlisted")
def test_the_check_catches_a_big_ui_file(tmp_path: Path) -> None:
    source = tmp_path / "ui" / "src"
    source.mkdir(parents=True)
    past = "x\n" * (UI_FILE_LINES + 1)
    for name in ("View.vue", "app.css", "View.test.ts"):
        (source / name).write_text(past)
    (source / "at.ts").write_text("x\n" * UI_FILE_LINES)
    assert big_ui_files(tmp_path) == {
        "ui/src/View.vue": UI_FILE_LINES + 1,
        "ui/src/app.css": UI_FILE_LINES + 1,
    }


@pytest.mark.spec_exempt("structural: twin of test_no_patched_module_is_unlisted")
def test_the_check_catches_a_patched_module(tmp_path: Path) -> None:
    bound = "import os\nname = 1\ndef helper():\n    pass\n"
    for name, text in {
        "isekai/a.py": bound,
        "isekai/b/__init__.py": "",
        "isekai/b/c.py": bound,
        "isekai/b/f.py": bound,
        "isekai/b/h.py": bound,
        "isekai/d.py": bound,
        "isekai/g.py": bound,
        "evaluation/e.py": bound,
        "tests/test_patch.py": (
            "import isekai.a as alias\n"
            "import isekai.b.c\n"
            "import evaluation.e as ev\n"
            "from isekai import b, d\n"
            "from isekai.b import f\n"
            "def test_it(monkeypatch, other):\n"
            "    monkeypatch.setattr(alias, 'name', 1)\n"
            "    monkeypatch.setattr(alias, 'helper', 1)\n"
            "    monkeypatch.setattr(isekai.b.c, 'name', 1)\n"
            "    monkeypatch.setattr(d, 'name', 1)\n"
            "    monkeypatch.setattr(f, 'name', 1)\n"
            "    monkeypatch.setattr(b.h, 'name', 1)\n"
            "    monkeypatch.setattr(ev, 'name', 1)\n"
            "    monkeypatch.setattr('isekai.g.name', 1)\n"
            "    monkeypatch.setattr(alias, 'missing', 1)\n"
            "    monkeypatch.setattr(alias.os, 'getcwd', 1)\n"
            "    monkeypatch.setattr(other, 'name', 1)\n"
        ),
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    assert patched_modules(tmp_path) == {
        "evaluation.e": 1,
        "isekai.a": 2,
        "isekai.b.c": 1,
        "isekai.b.f": 1,
        "isekai.b.h": 1,
        "isekai.d": 1,
        "isekai.g": 1,
    }


@pytest.mark.spec_exempt("structural: twin of test_no_patched_module_is_unlisted")
def test_a_reused_local_alias_hides_no_patched_module(tmp_path: Path) -> None:
    for name, text in {
        "isekai/shared/fields.py": "def validate():\n    pass\n",
        "isekai/shared/ink.py": "def extract_ink():\n    pass\n",
        "tests/test_patch.py": (
            "from isekai.shared import fields\n"
            "def test_one(monkeypatch):\n"
            "    from isekai.shared import fields as subject\n"
            "    monkeypatch.setattr(subject, 'validate', 1)\n"
            "def test_two(monkeypatch):\n"
            "    from isekai.shared import ink as subject\n"
            "    monkeypatch.setattr(subject, 'extract_ink', 1)\n"
            "def test_three(monkeypatch):\n"
            "    monkeypatch.setattr(fields, 'validate', 1)\n"
            "def test_four(monkeypatch):\n"
            "    from isekai.shared import ink as fields\n"
            "    monkeypatch.setattr(fields, 'extract_ink', 1)\n"
        ),
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    assert patched_modules(tmp_path) == {
        "isekai.shared.fields": 2,
        "isekai.shared.ink": 2,
    }


def _patched_tree(root: Path) -> None:
    """Write a tree whose test patches four names of `isekai/m.py`, one only stored."""
    for name, text in {
        "isekai/m.py": (
            "loaded = 1\n"
            "attribute = 1\n"
            "imported = 1\n"
            "stored = 1\n"
            "shadowed = 1\n"
            "copied = 1\n"
            "def use():\n"
            "    return loaded\n"
            "def local(shadowed):\n"
            "    return shadowed\n"
        ),
        "isekai/n.py": (
            "from isekai import m\n"
            "from isekai.m import copied\n"
            "def read():\n"
            "    return m.attribute\n"
            "def pull():\n"
            "    from isekai.m import imported\n"
            "    return imported\n"
        ),
        "tests/test_patch.py": (
            "import isekai.m as m\n"
            "def test_it(monkeypatch):\n"
            "    monkeypatch.setattr(m, 'loaded', 1)\n"
            "    monkeypatch.setattr(m, 'attribute', 1)\n"
            "    monkeypatch.setattr(m, 'imported', 1)\n"
            "    monkeypatch.setattr(m, 'stored', 1)\n"
            "    monkeypatch.setattr(m, 'shadowed', 1)\n"
            "    monkeypatch.setattr(m, 'copied', 1)\n"
        ),
    }.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


@pytest.mark.spec_exempt(
    "structural: twin of test_every_patch_names_a_name_its_module_reads"
)
def test_the_check_catches_a_patch_of_a_name_nothing_reads(tmp_path: Path) -> None:
    for name, text in {
        "isekai/m.py": "stored = 1\n",
        "tests/test_patch.py": (
            "import isekai.m as m\n"
            "def test_it(monkeypatch):\n"
            "    monkeypatch.setattr(m, 'stored', 1)\n"
        ),
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    assert unread_patches(tmp_path) == [
        "tests/test_patch.py:3 patches isekai.m.stored, which nothing reads"
    ]


@pytest.mark.spec_exempt(
    "structural: a name is read by a load, an attribute or an import in a function, "
    "and by nothing else"
)
def test_a_name_is_read_by_a_load_an_attribute_or_an_import(tmp_path: Path) -> None:
    _patched_tree(tmp_path)

    assert names_read(tmp_path)["isekai.m"] == {"loaded", "attribute", "imported"}
    assert unread_patches(tmp_path) == [
        "tests/test_patch.py:6 patches isekai.m.stored, which nothing reads",
        "tests/test_patch.py:7 patches isekai.m.shadowed, which nothing reads",
        "tests/test_patch.py:8 patches isekai.m.copied, which nothing reads",
    ]
