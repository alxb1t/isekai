"""The pins guide names files that exist.

`docs/pins.md` is an inventory: it names where each pin is declared and checked.
A file that moves and leaves the guide pointing at nothing is the drift the pins
exist to stop, so every repository path the guide names in backticks is held to
exist.

Each layer README's *Imported by* table is a copy of the import graph, so the
deriver's output for it is held equal to the file.
"""

import re
from pathlib import Path

import pytest

from tools.derive_imported_by import HEADING, TABLES, derive

REPO_ROOT = Path(__file__).resolve().parent.parent
GUIDE = REPO_ROOT / "docs" / "pins.md"

# A backtick span the guide uses as a repository path: under a tracked top-level
# directory, or a tracked file at the root. e.g. `config/image.json`, `Dockerfile`;
# not `ghcr.io/…` or `sha256:…`.
ROOTS = (
    ".github",
    "config",
    "docs",
    "evaluation",
    "flows",
    "image",
    "isekai",
    "tests",
    "tools",
)
ROOT_FILES = frozenset(
    {
        "Dockerfile",
        "Makefile",
        "gpunit.toml",
        "pyproject.toml",
        "uv.lock",
        "CHANGELOG.md",
        "README.md",
        ".gitignore",
    }
)
SPAN = re.compile(r"`([^`\s]+)`")


def named_paths(text: str) -> list[str]:
    """Return every repository path `text` names in backticks, in order.

    e.g. "boots `config/image.json` via `isekai render`" -> ["config/image.json"]
    """
    return [
        span
        for span in SPAN.findall(text)
        if span in ROOT_FILES or span.split("/", 1)[0] in ROOTS and "/" in span
    ]


def missing(text: str, root: Path) -> list[str]:
    """Return the paths `text` names that do not exist under `root`."""
    return [path for path in named_paths(text) if not (root / path).exists()]


@pytest.mark.spec_exempt("structural: the pins guide names files that exist")
def test_every_path_the_pins_guide_names_exists() -> None:
    text = GUIDE.read_text()

    assert named_paths(text), "the guide names no repository path at all"
    assert missing(text, REPO_ROOT) == []


@pytest.mark.spec_exempt("structural: the pins guide's path check")
def test_the_check_reports_a_path_that_does_not_exist(tmp_path: Path) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "image.json").write_text("{}")

    text = "the pin lives in `config/image.json`, and was in `config/gone.json`"

    assert missing(text, tmp_path) == ["config/gone.json"]


@pytest.mark.spec_exempt("structural: an imported-by table is what the deriver writes")
@pytest.mark.parametrize("readme", TABLES, ids=str)
def test_every_imported_by_table_is_the_one_the_deriver_writes(readme: Path) -> None:
    assert derive(REPO_ROOT, readme) == (REPO_ROOT / readme).read_text()


@pytest.mark.spec_exempt("structural: every imported-by table is derived")
def test_every_readme_with_an_imported_by_table_is_derived() -> None:
    held = sorted(
        readme.relative_to(REPO_ROOT)
        for top in ("isekai", "evaluation")
        for readme in (REPO_ROOT / top).rglob("README.md")
        if HEADING in readme.read_text().split("\n")
    )

    assert held, "no README holds an imported-by table"
    assert [readme for readme in held if readme not in TABLES] == []


GPU_README = """# `boundary/`

## Imported by

An old note.

| file | inside `isekai/` | outside |
|---|---|---|
| `{row}` | {inside} | — |

> A note under the table.
"""


def _graph(root: Path, readme: str) -> Path:
    """Write a small tree: `gpu.py` imported by the interface, and a README."""
    files = {
        "isekai/__init__.py": "",
        "isekai/boundary/__init__.py": "",
        "isekai/boundary/gpu.py": "x = 1\n",
        "isekai/interface/__init__.py": "",
        "isekai/interface/cli.py": "from isekai.boundary import gpu\n",
        "evaluation/__init__.py": "",
        "tools/__init__.py": "",
        "isekai/boundary/README.md": readme,
    }
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


@pytest.mark.spec_exempt(
    "structural: twin of test_every_imported_by_table_is_the_one_the_deriver_writes"
)
def test_the_deriver_catches_a_stale_table(tmp_path: Path) -> None:
    stale = GPU_README.format(row="gpu.py", inside="—")
    root = _graph(tmp_path, stale)
    readme = Path("isekai/boundary/README.md")

    derived = derive(root, readme)

    assert derived != stale
    assert "| `gpu.py` | `interface/cli.py` | — |" in derived
    assert "An old note." not in derived
    assert "> A note under the table." in derived
    (root / readme).write_text(derived)
    assert derive(root, readme) == derived


@pytest.mark.spec_exempt(
    "structural: twin of test_every_imported_by_table_is_the_one_the_deriver_writes"
)
def test_the_deriver_refuses_a_row_naming_no_module(tmp_path: Path) -> None:
    root = _graph(tmp_path, GPU_README.format(row="gone.py", inside="—"))

    with pytest.raises(ValueError, match="names no module"):
        derive(root, Path("isekai/boundary/README.md"))
