"""Write `ui/src/wire.ts`, the page's half of the wire, from `shapes.py`.

Run it from the repository root:

    uv run python -m tools.derive_wire

The tool reads Python by `ast` and imports no `isekai` module. A form outside its
grammar is refused naming the class and the field, never guessed.
"""

import ast
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SHAPES = Path("isekai/interface/ui/shapes.py")
WIRE = Path("ui/src/wire.ts")

HEADER = "/* Written by `tools/derive_wire.py` from `isekai/interface/ui/shapes.py`. */"

LEAVES = {"str": "string", "int": "number", "float": "number", "bool": "boolean"}


class _NoForm(Exception):
    """Mark an annotation outside the grammar."""


def _named(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _flatten(node: ast.expr) -> list[ast.expr]:
    """Return the operands of a chain of `|`, left to right."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return [*_flatten(node.left), *_flatten(node.right)]
    return [node]


def _is_none(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _word(node: ast.expr) -> str:
    """Return a `Literal` word as TypeScript writes it.

    A quote, a backslash or a line break is refused.

    e.g. `"re-roll"` -> `'re-roll'`
    """
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and not any(mark in node.value for mark in "'\"\\\r\n")
    ):
        return f"'{node.value}'"
    raise _NoForm


def _has_fields(node: ast.ClassDef) -> bool:
    return any(isinstance(stmt, ast.AnnAssign) for stmt in node.body)


def _refused(owner: str, source: str) -> ValueError:
    return ValueError(f"{owner}: {source} is no form of the wire")


def _header(node: ast.ClassDef) -> str:
    parts = [ast.unparse(part) for part in [*node.bases, *node.keywords]]
    return f"class {node.name}({', '.join(parts)})" if parts else f"class {node.name}"


def _file(root: Path, dotted: str) -> Path | None:
    """Return the file a dotted module name stands for under `root`, if there is one.

    e.g. `isekai.pipeline.review` -> `isekai/pipeline/review.py`
    """
    base = Path(*dotted.split("."))
    for rel in (base.with_suffix(".py"), base / "__init__.py"):
        if (root / rel).is_file():
            return rel
    return None


class _Module:
    """One parsed module: its classes, its `Literal` aliases and its imports."""

    def __init__(self, root: Path, rel: Path) -> None:
        self.rel = rel
        stem = rel.parent.name if rel.stem == "__init__" else rel.stem
        self.name = stem[:1].upper() + stem[1:]
        self.tree = ast.parse((root / rel).read_text())
        self.classes: dict[str, ast.ClassDef] = {}
        self.aliases: dict[str, ast.Subscript] = {}
        self.imports: dict[str, tuple[Path, str | None]] = {}
        for node in self.tree.body:
            if isinstance(node, ast.ClassDef):
                self.classes[node.name] = node
            elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Subscript):
                if _named(node.value.value, "Literal"):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.aliases[target.id] = node.value
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                self._import(root, node.module, node)

    def _import(self, root: Path, dotted: str, node: ast.ImportFrom) -> None:
        home = _file(root, dotted)
        for item in node.names:
            module = _file(root, f"{dotted}.{item.name}")
            if module:
                self.imports[item.asname or item.name] = (module, None)
            elif home:
                self.imports[item.asname or item.name] = (home, item.name)


@dataclass(frozen=True)
class _Ref:
    module: _Module
    name: str
    is_alias: bool


class _Wire:
    """The file as it is built: its aliases, foreign classes and each name's origin."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.modules: dict[Path, _Module] = {}
        self.shapes = self.load(SHAPES)
        self.origins: dict[str, tuple[Path, str]] = {"Events": (SHAPES, "EVENTS")}
        self.aliases: dict[str, str] = {}
        self.foreign: dict[str, str] = {}

    def load(self, rel: Path) -> _Module:
        if rel not in self.modules:
            self.modules[rel] = _Module(self.root, rel)
        return self.modules[rel]

    def _local(self, module: _Module, name: str) -> _Ref | None:
        if name in module.classes:
            return _Ref(module, name, False)
        if name in module.aliases:
            return _Ref(module, name, True)
        return None

    def _lookup(self, module: _Module, name: str) -> _Ref | _Module | None:
        found = self._local(module, name)
        if found or name not in module.imports:
            return found
        rel, attr = module.imports[name]
        target = self.load(rel)
        return target if attr is None else self._local(target, attr)

    def resolve(self, module: _Module, node: ast.expr) -> _Ref:
        """Return the class or alias a name or `mod.Name` stands for in `module`."""
        found = None
        if isinstance(node, ast.Name):
            found = self._lookup(module, node.id)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            owner = self._lookup(module, node.value.id)
            found = (
                self._local(owner, node.attr) if isinstance(owner, _Module) else None
            )
        if not isinstance(found, _Ref):
            raise _NoForm
        return found

    def claim(self, wire: str, ref: _Ref) -> None:
        """Refuse a name that two declarations would write."""
        origin = (ref.module.rel, ref.name)
        first = self.origins.setdefault(wire, origin)
        if first != origin:
            raise ValueError(
                f"{wire}: written twice, by {first[0].as_posix()}"
                f" and {origin[0].as_posix()}"
            )

    def ref(self, ref: _Ref) -> str:
        """Return the name `ref` is written under, writing it first when it is new."""
        if ref.is_alias:
            wire = ref.module.name + ref.name
            self.claim(wire, ref)
            if wire not in self.aliases:
                self.aliases[wire] = ""
                self.aliases[wire] = self._alias(wire, ref)
            return wire
        self.claim(ref.name, ref)
        if ref.module is not self.shapes and ref.name not in self.foreign:
            self.foreign[ref.name] = ""
            self.foreign[ref.name] = self.cls(ref.module, ref.module.classes[ref.name])
        return ref.name

    def _alias(self, wire: str, ref: _Ref) -> str:
        node = ref.module.aliases[ref.name]
        items = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
        arms = []
        for item in items:
            try:
                if isinstance(item, ast.Name) and item.id in ref.module.aliases:
                    arms.append(self.ref(_Ref(ref.module, item.id, True)))
                else:
                    arms.append(_word(item))
            except _NoForm:
                raise _refused(ref.name, ast.unparse(item)) from None
        return f"export type {wire} = {' | '.join(arms)}"

    def arms(self, module: _Module, node: ast.expr) -> list[str]:
        """Return the arms of the union an annotation is written as."""
        operands = _flatten(node)
        if len(operands) > 1:
            if sum(not _is_none(operand) for operand in operands) > 1:
                raise _NoForm
            return [arm for operand in operands for arm in self.arms(module, operand)]
        if _is_none(node):
            return ["null"]
        if isinstance(node, ast.Name) and node.id in LEAVES:
            return [LEAVES[node.id]]
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            return self._subscript(module, node.value.id, node.slice)
        return [self.ref(self.resolve(module, node))]

    def _subscript(self, module: _Module, name: str, slice_: ast.expr) -> list[str]:
        if name == "Literal":
            items = slice_.elts if isinstance(slice_, ast.Tuple) else [slice_]
            return [_word(item) for item in items]
        if name == "list":
            inner = self.arms(module, slice_)
            return [f"({' | '.join(inner)})[]" if len(inner) > 1 else f"{inner[0]}[]"]
        if name == "dict" and isinstance(slice_, ast.Tuple) and len(slice_.elts) == 2:
            key, value = slice_.elts
            if _named(key, "str"):
                keys = "string"
            else:
                ref = self.resolve(module, key)
                if not ref.is_alias:
                    raise _NoForm
                keys = self.ref(ref)
            return [f"Record<{keys}, {' | '.join(self.arms(module, value))}>"]
        raise _NoForm

    def cls(self, module: _Module, node: ast.ClassDef) -> str:
        """Return the declaration of one `TypedDict` class."""
        extends = self._extends(module, node)
        fields = [stmt for stmt in node.body if isinstance(stmt, ast.AnnAssign)]
        if not _has_fields(node):
            if extends:
                raise _refused(node.name, _header(node))
            return f"export type {node.name} = Record<string, never>"
        lines = [self._field(module, node.name, stmt) for stmt in fields]
        base = f" extends {extends}" if extends else ""
        body = "".join(f"  {line}\n" for line in lines)
        return f"export interface {node.name}{base} {{\n{body}}}"

    def _extends(self, module: _Module, node: ast.ClassDef) -> str | None:
        bases = [base for base in node.bases if not _named(base, "TypedDict")]
        typed = len(bases) < len(node.bases)
        if node.keywords or len(bases) > 1 or not (bases or typed):
            raise _refused(node.name, _header(node))
        if not bases:
            return None
        try:
            ref = self.resolve(module, bases[0])
        except _NoForm:
            raise _refused(node.name, _header(node)) from None
        if ref.is_alias or not _has_fields(ref.module.classes[ref.name]):
            raise _refused(node.name, _header(node))
        return self.ref(ref)

    def _field(self, module: _Module, owner: str, stmt: ast.AnnAssign) -> str:
        annotation = stmt.annotation
        name = ast.unparse(stmt.target)
        optional = False
        try:
            if not isinstance(stmt.target, ast.Name):
                raise _NoForm
            optional = isinstance(annotation, ast.Subscript) and _named(
                annotation.value, "NotRequired"
            )
            if optional and isinstance(annotation, ast.Subscript):
                annotation = annotation.slice
            arms = self.arms(module, annotation)
        except _NoForm:
            raise _refused(f"{owner}.{name}", ast.unparse(stmt.annotation)) from None
        return f"{name}{'?' if optional else ''}: {' | '.join(arms)}"

    def events(self) -> str:
        """Return the `Events` interface, one line for each key of `EVENTS`."""
        table = next(
            (
                node.value
                for node in self.shapes.tree.body
                if isinstance(node, ast.AnnAssign) and _named(node.target, "EVENTS")
            ),
            None,
        )
        lines = []
        if isinstance(table, ast.Dict):
            for key, value in zip(table.keys, table.values):
                label = ast.unparse(key) if key else "**"
                try:
                    if not (
                        isinstance(key, ast.Constant) and isinstance(key.value, str)
                    ):
                        raise _NoForm
                    label = key.value
                    ref = self.resolve(self.shapes, value)
                    if ref.is_alias or not label.isidentifier():
                        raise _NoForm
                    lines.append(f"  {label}: {self.ref(ref)}\n")
                except _NoForm:
                    raise _refused(f"EVENTS.{label}", ast.unparse(value)) from None
        return f"export interface Events {{\n{''.join(lines)}}}"


def derive(root: Path) -> str:
    """Return the text of `ui/src/wire.ts` for the tree under `root`.

    The blocks are the aliases, the classes reached from other modules, the classes of
    `shapes.py` in source order, then `Events`, a blank line between each.
    """
    wire = _Wire(root)
    shapes = wire.shapes
    for node in shapes.tree.body:
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and _named(node.value.func, "TypedDict")
        ):
            raise _refused(ast.unparse(node.targets[0]), ast.unparse(node.value))
    for name in shapes.classes:
        wire.claim(name, _Ref(shapes, name, False))
    classes = [wire.cls(shapes, node) for node in shapes.classes.values()]
    events = wire.events()
    blocks = [HEADER]
    if wire.aliases:
        blocks.append("\n".join(wire.aliases[name] for name in sorted(wire.aliases)))
    blocks += [wire.foreign[name] for name in sorted(wire.foreign)]
    return "\n\n".join([*blocks, *classes, events]) + "\n"


def main() -> int:
    """Write `ui/src/wire.ts`, and return the process's exit status."""
    (REPO_ROOT / WIRE).write_text(derive(REPO_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
