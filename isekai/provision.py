"""The manifest of model artifacts, and the checks that keep it honest.

`scripts/models.json` decides which bytes this repository renders with. Nothing
here downloads anything: the transfer is `wget` on the pod (design.md D3), and
what lives in Python is the part the offline suite can reach -- reading the
manifest, and deciding whether it says what a pin is supposed to say.

Not imported by `convert.py`. The runtime stays stdlib-only either way -- this
module is `json`, `re` and `pathlib` -- but the import graph stays narrow too.
"""

import json
import re
from pathlib import Path
from typing import Any, TypedDict

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "scripts" / "models.json"

# A lowercase SHA-256, in full. Anything else is not a digest of anything.
DIGEST = re.compile(r"^[0-9a-f]{64}$")

# A Hugging Face URL that addresses an immutable revision. `resolve/main/...` is
# the same URL on two different days, so it matches deliberately narrowly: the
# 40-hex commit, and nothing that merely looks like one.
PINNED_SOURCE = re.compile(
    r"^https://huggingface\.co/(?P<org>[^/]+)/[^/]+/resolve/[0-9a-f]{40}/.+$"
)

# The org of a source URL, whether or not the URL is pinned -- so a malformed
# source is reported once, by the pin check, rather than twice.
SOURCE_ORG = re.compile(r"^https://huggingface\.co/(?P<org>[^/]+)/")

ENTRY_KEYS = frozenset({"dest", "sha256", "bytes", "sources"})


class Entry(TypedDict):
    """One file: where it lands, what its bytes must hash to, where to get them."""

    dest: str
    sha256: str
    bytes: int
    sources: list[str]


class Manifest(TypedDict):
    """The whole tracked manifest."""

    pinned: str
    publishers: list[str]
    entries: list[Entry]


def load_manifest(path: Path = MANIFEST_PATH) -> Manifest:
    """Read and parse the tracked manifest."""
    parsed: Any = json.loads(path.read_text())
    return parsed


def entries_with_missing_keys(manifest: Manifest) -> list[str]:
    """Return the destinations of entries that do not declare every required key."""
    return [
        str(entry.get("dest", entry))
        for entry in manifest["entries"]
        if not ENTRY_KEYS <= set(entry)
    ]


def sources_on_a_mutable_ref(manifest: Manifest) -> list[str]:
    """Return every source URL that does not address an immutable revision."""
    return [
        source
        for entry in manifest["entries"]
        for source in entry["sources"]
        if not PINNED_SOURCE.match(source)
    ]


def entries_without_a_digest(manifest: Manifest) -> list[str]:
    """Return the destinations of entries whose digest is missing or malformed."""
    return [
        entry["dest"]
        for entry in manifest["entries"]
        if not DIGEST.match(str(entry.get("sha256", "")))
    ]


def mirror_entries_without_an_alternate(manifest: Manifest) -> list[str]:
    """Return the destinations of mirror-primary entries that declare no alternate.

    A digest makes the source interchangeable, so an alternate adds availability
    without adding trust (design.md D10) -- but only an entry whose primary is
    somebody's mirror actually needs one.
    """
    publishers = set(manifest["publishers"])
    missing: list[str] = []
    for entry in manifest["entries"]:
        primary = entry["sources"][0] if entry["sources"] else ""
        org = SOURCE_ORG.match(primary)
        if org is None or org.group("org") in publishers:
            continue
        if len(entry["sources"]) < 2:
            missing.append(entry["dest"])
    return missing
