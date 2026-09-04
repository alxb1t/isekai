"""The manifest of model artifacts, and the checks that keep it honest.

`scripts/models.json` decides which bytes this repository renders with, and this
module owns every *decision* taken about it: whether the manifest says what a pin
is supposed to say, and, for each entry, whether to skip it, abort the run or
fetch it. The bytes move through `wget` on the pod (design.md D3, D14); the only
network call here is the cheap pre-flight HEAD behind the `Fetcher` seam, which a
fake replaces so the whole suite stays offline.

Not imported by `convert.py`. The runtime stays stdlib-only either way -- this
module is `json`, `re` and `pathlib` -- but the import graph stays narrow too.
"""

import hashlib
import json
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol, TypedDict

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


class DigestMismatch(Exception):
    """Bytes on disk do not hash to the digest the manifest declares for them."""


class Fetcher(Protocol):
    """The pre-flight seam: what a source says it would serve, before it serves it.

    The bytes themselves do not move through here. `wget` in the shell moves them
    and the shell hands the result back to `land` (design.md D14), so what passes
    through this seam is the cheap question a ranged request can answer: does the
    source's *published* digest already disagree with the manifest? A fake answers
    it from a dict, which is what keeps the suite offline.
    """

    def published_digest(self, url: str) -> str | None:
        """Return the SHA-256 the source publishes, or None if it publishes none."""
        ...


class HuggingFaceFetcher:
    """Reads the SHA-256 Hugging Face returns in `x-linked-etag` on a HEAD request.

    Observed behaviour, not a documented contract, so every failure mode here —
    a missing header, a redirect that drops it, a network error — returns None
    and the entry degrades to download-and-post-verify. It must never degrade to
    trust (design.md D10).
    """

    def published_digest(self, url: str) -> str | None:
        """Return the published SHA-256, or None if it cannot be read cheaply."""
        request = urllib.request.Request(url, method="HEAD")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                header = response.headers.get("x-linked-etag") or ""
        except OSError:
            return None
        candidate = header.strip().strip('"')
        return candidate if DIGEST.match(candidate) else None


@dataclass(frozen=True)
class Decision:
    """What provisioning should do about one manifest entry.

    `skip` — present and verified. `abort` — stop the run and let a human look;
    nothing is deleted. `fetch` — transfer `url`, then hand the result to `land`.
    """

    action: Literal["skip", "abort", "fetch"]
    url: str | None
    reason: str


def digest_of(path: Path) -> str:
    """Return the SHA-256 of a file, read in chunks so a 6.9 GB model fits in RAM."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(path: Path, expected: str) -> None:
    """Raise `DigestMismatch` unless `path` hashes to `expected`.

    The message names all three of the file, the expected digest and the computed
    one, because a mismatch is read by a human deciding whether a pin is stale or
    a mirror has been swapped, and two of the three do not answer that.
    """
    actual = digest_of(path)
    if actual != expected:
        raise DigestMismatch(
            f"SHA-256 mismatch for {path}: expected {expected}, computed {actual}"
        )


def decide(entry: Entry, models_dir: Path, fetcher: Fetcher) -> Decision:
    """Decide what to do about one entry: skip it, abort the run, or fetch it.

    A file already at the destination is *hashed*, never taken on its name — that
    is the whole point of a manifest, and skip-if-present is what would otherwise
    leave a warm volume permanently unchecked (design.md D4). A present file that
    fails is left exactly where it is: the volume is shared, and a file this run
    did not write is not this run's to remove.
    """
    dest = models_dir / entry["dest"]
    if dest.exists():
        actual = digest_of(dest)
        if actual == entry["sha256"]:
            return Decision("skip", None, f"present and verified: {entry['dest']}")
        return Decision(
            "abort",
            None,
            f"SHA-256 mismatch for {entry['dest']}: expected {entry['sha256']}, "
            f"computed {actual} — left on disk for inspection",
        )

    rejected: list[str] = []
    for url in entry["sources"]:
        published = fetcher.published_digest(url)
        if published is not None and published != entry["sha256"]:
            rejected.append(f"{url} publishes {published}")
            continue
        return Decision("fetch", url, f"absent: {entry['dest']}")

    return Decision(
        "abort",
        None,
        f"every source for {entry['dest']} was rejected before transfer "
        f"(expected {entry['sha256']}): " + "; ".join(rejected),
    )


def land(entry: Entry, models_dir: Path, partial: Path) -> None:
    """Verify a just-transferred file and only then move it to its destination.

    Raises `DigestMismatch` and removes `partial` if the bytes are wrong, so an
    interrupted or tampered transfer never occupies the final name and the next
    run sees the file as absent rather than as present-and-trusted.
    """
    try:
        verify(partial, entry["sha256"])
    except DigestMismatch:
        partial.unlink(missing_ok=True)
        raise
    dest = models_dir / entry["dest"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial.replace(dest)
