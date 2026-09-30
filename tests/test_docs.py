"""The pins guide names files that exist.

`docs/pins.md` is an inventory: it names where each pin is declared and checked.
A file that moves and leaves the guide pointing at nothing is the drift the pins
exist to stop, so every repository path the guide names in backticks is held to
exist.
"""

import re
from pathlib import Path

import pytest

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
    "infra",
    "isekai",
    "tests",
    "tools",
)
ROOT_FILES = frozenset(
    {
        "Dockerfile",
        "Makefile",
        "start.sh",
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

    e.g. "boots `config/image.json` via `up.sh`" -> ["config/image.json"]
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


@pytest.mark.spec_exempt("structural: the twin of the pins guide's path check")
def test_the_check_reports_a_path_that_does_not_exist(tmp_path: Path) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "image.json").write_text("{}")

    text = "the pin lives in `config/image.json`, and was in `config/gone.json`"

    assert missing(text, tmp_path) == ["config/gone.json"]
