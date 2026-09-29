"""The living spec as the active changes' deltas leave it, and a tree to test that on.

Shared here rather than imported from one test module by another, which would
make that module undeletable -- the rule `tests/stages.py` is under.
"""

import re
from pathlib import Path

SECTION = re.compile(r"^## (.*)$", re.M)
REQUIREMENT = re.compile(r"^### Requirement: (.*)$", re.M)
_FROM = re.compile(r"^- FROM: `### Requirement: (.*)`$", re.M)
_TO = re.compile(r"^- TO: `### Requirement: (.*)`$", re.M)

# A capability's text before its first requirement, and each requirement's body.
Spec = tuple[str, dict[str, str]]


def split(heading: re.Pattern[str], text: str) -> dict[str, str]:
    """Return each heading's captured title, stripped, mapped to its body."""
    parts = heading.split(text)
    return {
        title.strip(): body
        for title, body in zip(parts[1::2], parts[2::2], strict=True)
    }


def effective(root: Path) -> dict[str, Spec]:
    """Return each capability's spec, as the active changes' deltas leave it.

    Each delta applies in OpenSpec's order: a RENAMED requirement moves to its new
    title, a REMOVED one goes, a MODIFIED one is replaced, an ADDED one is added.
    """
    specs: dict[str, Spec] = {}
    for path in sorted((root / "openspec" / "specs").glob("*/spec.md")):
        text = path.read_text()
        specs[path.parent.name] = (
            REQUIREMENT.split(text, maxsplit=1)[0],
            split(REQUIREMENT, text),
        )
    # The glob's depth leaves out `archive/<id>/`: an archived delta is folded in.
    for delta in sorted((root / "openspec" / "changes").glob("*/specs/*/spec.md")):
        _, reqs = specs.setdefault(delta.parent.name, ("", {}))
        sections = split(SECTION, delta.read_text())
        renamed = sections.get("RENAMED Requirements", "")
        for old, new in zip(_FROM.findall(renamed), _TO.findall(renamed), strict=True):
            reqs[new.strip()] = reqs.pop(old.strip(), "")
        for title in REQUIREMENT.findall(sections.get("REMOVED Requirements", "")):
            reqs.pop(title.strip(), None)
        for heading in ("MODIFIED Requirements", "ADDED Requirements"):
            reqs |= split(REQUIREMENT, sections.get(heading, ""))
    return specs


def write_tree(
    root: Path, living: str, delta: str | None = None, cap: str = "cap"
) -> Path:
    """Write one capability's living spec and, if given, an active delta for it."""
    spec = root / "openspec" / "specs" / cap / "spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(living)
    if delta is not None:
        path = root / "openspec" / "changes" / "0001-x" / "specs" / cap / "spec.md"
        path.parent.mkdir(parents=True)
        path.write_text(delta)
    return root
