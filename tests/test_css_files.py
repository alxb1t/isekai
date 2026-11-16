"""Every file of `ui/src/css/` is imported by `ui/src/main.ts` once.

The rule is a function over a root directory, so a twin can run it on a small tree
built under `tmp_path`. It pins no rule of a sheet: `docs/decisions.md` D60.
"""

import re
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

IMPORT = re.compile(r"^import '\./css/([\w-]+\.css)'$", re.MULTILINE)


def css_faults(root: Path) -> list[str]:
    """Return the faults of the css imports, sorted.

    A fault is a file of `ui/src/css/` imported other than once, or an import
    naming a file that is missing.

    e.g. `["place.css imported 0 times"]`
    """
    source = root / "ui" / "src"
    imported = Counter(IMPORT.findall((source / "main.ts").read_text()))
    present = {path.name for path in (source / "css").glob("*.css")}
    faults = [
        f"{name} imported {imported[name]} times"
        for name in present
        if imported[name] != 1
    ]
    faults += [
        f"{name} imported but missing" for name in imported if name not in present
    ]
    return sorted(faults)


@pytest.mark.spec_exempt(
    "structural: every file of ui/src/css/ is imported by main.ts once"
)
def test_every_css_file_is_imported_by_main_once() -> None:
    assert list((REPO_ROOT / "ui" / "src" / "css").glob("*.css"))
    assert css_faults(REPO_ROOT) == []


def _tree(root: Path, main: str) -> None:
    source = root / "ui" / "src"
    (source / "css").mkdir(parents=True)
    for name in ("a.css", "b.css", "c.css"):
        (source / "css" / name).write_text("")
    (source / "main.ts").write_text(main)


CLEAN = "import './css/a.css'\nimport './css/b.css'\nimport './css/c.css'\n"


@pytest.mark.spec_exempt(
    "structural: twin of test_every_css_file_is_imported_by_main_once"
)
def test_the_check_catches_an_unimported_css_file(tmp_path: Path) -> None:
    clean = tmp_path / "clean"
    _tree(clean, CLEAN)
    assert css_faults(clean) == []

    removed = tmp_path / "removed"
    _tree(removed, "import './css/a.css'\nimport './css/c.css'\n")
    assert css_faults(removed) == ["b.css imported 0 times"]

    repeated = tmp_path / "repeated"
    _tree(repeated, CLEAN + "import './css/b.css'\n")
    assert css_faults(repeated) == ["b.css imported 2 times"]

    missing = tmp_path / "missing"
    _tree(missing, CLEAN + "import './css/gone.css'\n")
    assert css_faults(missing) == ["gone.css imported but missing"]
