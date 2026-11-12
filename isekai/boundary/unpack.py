"""A zip entry's members: unpacked by declared destination, each verified.

A manifest entry may declare `unpack`, the members to read out of its archive.
`provision.fetch` lands the archive like any file; this module then writes each
member to the destination the manifest declares, never to a name the archive
supplies. It sits beside `provision.py` because the pod image copies that file
and records its digest (D28), and the placement models never reach a pod.
"""

import argparse
import sys
import time
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from isekai.boundary import provision
from isekai.boundary.provision import (
    DEFAULT_MODELS_DIR,
    PINNED_SOURCE,
    WHITESPACE,
    DigestMismatch,
    Entry,
    EscapingDestination,
    Fetcher,
    HuggingFaceFetcher,
    Manifest,
    UnknownArtifact,
    UnpinnedArtifact,
    digest_of,
    resolve_dest,
    verify,
)

PLACEMENT_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "placement.json"
)

# The command that provisions the placement models, named once so every refusal
# over a missing file prints the same fix.
PLACEMENT_REMEDY = "uv run python -m isekai.boundary.unpack fetch config/placement.json"


class Member(TypedDict):
    """One file inside a zip entry: its name there, where it lands, its digest."""

    member: str
    dest: str
    sha256: str
    bytes: int


class ZipEntry(Entry):
    """An `Entry` that may declare the members to read out of its archive."""

    unpack: NotRequired[list[Member]]


class UnpackRefused(Exception):
    """A zip entry's member cannot be read out of its archive as declared."""


def _entries(manifest: Manifest) -> list[ZipEntry]:
    """Return the manifest's entries, each one that may declare members."""
    return cast(list[ZipEntry], manifest["entries"])


def _landing(declared: Entry | Member, models_dir: Path) -> Path:
    """Return `declared`'s path under `models_dir`, or raise `EscapingDestination`."""
    path = resolve_dest(
        {
            "dest": declared["dest"],
            "sha256": declared["sha256"],
            "bytes": declared["bytes"],
            "sources": [],
        },
        models_dir,
    )
    if path is None:
        raise EscapingDestination(
            f"{declared['dest']!r} does not resolve to a path under {models_dir}, "
            "so it is refused rather than written or loaded from"
        )
    return path


def decide_members(entry: ZipEntry, models_dir: Path) -> list[str]:
    """Return why each declared member's destination stops the run; empty if none does.

    A destination that escapes `models_dir`, or a file already there that does not
    hash to the member's digest, which is left exactly where it is.
    """
    reasons: list[str] = []
    for member in entry.get("unpack", []):
        try:
            target = _landing(member, models_dir)
        except EscapingDestination:
            reasons.append(
                f"destination {member['dest']!r} does not resolve inside {models_dir}"
            )
            continue
        if target.exists():
            try:
                verify(target, member["sha256"])
            except DigestMismatch as mismatch:
                reasons.append(f"{mismatch} — left on disk for inspection")
    return reasons


def unpack_members(entry: ZipEntry, archive: Path, models_dir: Path) -> None:
    """Write each absent member of `archive` to its declared destination, verified.

    The archive is verified first. A member is read by its declared name alone, at
    most its declared size plus one byte, into a `.partial` renamed only once its
    digest verifies. Raises `UnpackRefused` for a member the archive lacks or one
    past its size, `DigestMismatch` for bytes that do not verify, and
    `EscapingDestination` for a destination outside `models_dir`.
    """
    members = entry.get("unpack", [])
    if not members:
        return
    verify(archive, entry["sha256"])
    try:
        with zipfile.ZipFile(archive) as bundle:
            for member in members:
                _unpack_member(bundle, member, models_dir)
    except zipfile.BadZipFile as broken:
        raise UnpackRefused(f"{archive} is not a readable zip: {broken}") from broken


def _unpack_member(bundle: zipfile.ZipFile, member: Member, models_dir: Path) -> None:
    """Write one member of `bundle` to its declared destination, or skip it if there."""
    target = _landing(member, models_dir)
    if target.exists():
        verify(target, member["sha256"])
        print(f"skip (present, verified): {target}")
        return
    partial = target.with_name(f"{target.name}.partial")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        source = bundle.open(member["member"])
    except KeyError as lacking:
        raise UnpackRefused(
            f"{member['member']} is not in the archive for {member['dest']}"
        ) from lacking
    allowed = member["bytes"] + 1
    read = 0
    with source, partial.open("wb") as handle:
        while read < allowed:
            chunk = source.read(min(1 << 20, allowed - read))
            if not chunk:
                break
            handle.write(chunk)
            read += len(chunk)
    if read > member["bytes"]:
        partial.unlink(missing_ok=True)
        raise UnpackRefused(
            f"{member['member']} holds more than its declared {member['bytes']} bytes"
        )
    actual = digest_of(partial)
    if actual != member["sha256"]:
        partial.unlink(missing_ok=True)
        raise DigestMismatch(
            f"SHA-256 mismatch for member {member['member']}: "
            f"expected {member['sha256']}, computed {actual}"
        )
    partial.replace(target)
    print(f"unpacked (verified): {target}")


def fetch(
    manifest: Manifest,
    models_dir: Path,
    fetcher: Fetcher,
    wait: Callable[[float], None] = time.sleep,
) -> int:
    """Land every entry and unpack every member under `models_dir`; 0 if all are there.

    Every member's destination is decided before a transfer, so a present file with
    other bytes stops the run with nothing asked for. The entries land through
    `provision.fetch`, and an archive's members are unpacked after it lands and after
    it is skipped, so a gone member needs no transfer.
    """
    aborts = [
        reason
        for entry in _entries(manifest)
        for reason in decide_members(entry, models_dir)
    ]
    if aborts:
        for reason in aborts:
            print(f"ERROR: {reason}", file=sys.stderr)
        return 1
    landed = provision.fetch(manifest, models_dir, fetcher, wait)
    if landed != 0:
        return landed
    for entry in _entries(manifest):
        try:
            unpack_members(entry, _landing(entry, models_dir), models_dir)
        except (DigestMismatch, UnpackRefused, EscapingDestination) as refused:
            print(f"ERROR: {refused}", file=sys.stderr)
            return 1
    return 0


def member_for(manifest: Manifest, dest: str) -> tuple[ZipEntry, Member]:
    """Return the zip entry and the member declaring `dest`, or raise `UnknownArtifact`.

    e.g. "sam2/encoder.onnx" -> (the archive's entry, the member landing there)
    """
    for entry in _entries(manifest):
        for member in entry.get("unpack", []):
            if member["dest"] == dest:
                return entry, member
    raise UnknownArtifact(f"{dest} is not a member declared in the manifest searched")


def resolve_member(dest: str, models_dir: Path, manifest: Manifest) -> Path:
    """Return the verified path to one unpacked member, or raise rather than load it.

    `provision.resolve`'s refusals, for a member: the archive's sources must be
    pinned, the destination must resolve inside `models_dir`, and the file must hash
    to the member's own digest.
    """
    entry, member = member_for(manifest, dest)
    for source in entry["sources"]:
        if WHITESPACE.search(source) or not PINNED_SOURCE.match(source):
            raise UnpinnedArtifact(
                f"{dest}: {source!r} is not a pinned revision, so the digest "
                "beside it verifies nothing in particular"
            )
    path = _landing(member, models_dir)
    verify(path, member["sha256"])
    return path


def _parser() -> argparse.ArgumentParser:
    """Return the parser for `fetch`."""
    parser = argparse.ArgumentParser(prog="unpack.py")
    verbs = parser.add_subparsers(dest="verb", required=True)
    fetch_verb = verbs.add_parser(
        "fetch", help="land a manifest's files and unpack its archives, verified"
    )
    fetch_verb.add_argument(
        "--models-dir",
        type=Path,
        default=DEFAULT_MODELS_DIR,
        help="where the files land (default: the repository's models/)",
    )
    fetch_verb.add_argument(
        "manifest", nargs="?", help="default: config/placement.json"
    )
    return parser


def main(argv: list[str]) -> int:
    """Run `fetch`: `unpack.py fetch [--models-dir DIR] [manifest]`."""
    args = _parser().parse_args(argv)
    source = PLACEMENT_MANIFEST_PATH if args.manifest is None else Path(args.manifest)
    return fetch(provision.load_manifest(source), args.models_dir, HuggingFaceFetcher())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
