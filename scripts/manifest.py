#!/usr/bin/env python3
"""What every manifest deriver is made of: entry types, digest strategies, writer.

`scripts/models.json`, `scripts/eval_models.json` and `scripts/vocabulary.json`
are three manifests answering three questions -- what the graph needs on the pod,
what the scorer loads on the operator's machine, what the pipeline fills sheets
from -- and that separation is deliberate and stays (design.md D10). What they
share is *how* a manifest is derived, and that lives here.

Two derivers already shared these names by import, which makes an accidental
structure load-bearing the moment a third one arrives. Worse, the entry spec was
declared twice, under one name, with two different shapes; a third shape is how
that becomes a defect rather than an oddity. One definition, in a module, is the
fix.

**Both digest strategies are here because an artifact gets one or the other, not
because a deriver gets one or the other.** Hugging Face publishes a SHA-256 only
for LFS objects, so a small file stored as a plain git blob has to be fetched and
hashed -- and which route applies is stated per entry rather than sniffed, so a
file silently moving out of LFS is a loud failure rather than a quiet switch.

Operator tooling, not a package: nothing installs it, nothing imports it at
runtime, and it is not on `convert.py`'s import graph. `pyproject.toml` declares
`scripts/` a source root so the type checker and the suite see it the way a human
running it does.

**The refactor this module is verifiable for nothing.** Every deriver's output
must still be byte-identical on a re-run, which is the rule they were already
held to -- so any difference is this extraction's fault.
"""

import hashlib
import json
import urllib.request
from pathlib import Path
from typing import NamedTuple, TypedDict

# The agent string every derivation reaches upstream with. One value, so a
# publisher reading its logs sees one client rather than three.
USER_AGENT = "isekai-derive"

# Above this, a file is not a config and something is wrong with the spec. Every
# non-LFS file pinned anywhere here is a few hundred kilobytes at most; the cap
# exists so a mistake in a spec fails loudly instead of pulling a checkpoint
# through the hashing path.
BLOB_CAP_BYTES = 1 << 20


class ManifestEntry(TypedDict):
    """One emitted manifest entry: the shape `isekai.boundary.provision` reads."""

    dest: str
    sha256: str
    bytes: int
    sources: list[str]


class Manifest(TypedDict):
    """The emitted manifest."""

    pinned: str
    publishers: list[str]
    entries: list[ManifestEntry]


class Source(NamedTuple):
    """One Hugging Face file, addressed by an immutable revision."""

    repo: str
    revision: str
    path: str

    def url(self) -> str:
        """Return the `resolve/<sha>/` URL that serves exactly these bytes."""
        return f"https://huggingface.co/{self.repo}/resolve/{self.revision}/{self.path}"


class Spec(NamedTuple):
    """A destination, the ordered sources that fill it, and how to digest them.

    `expect_sha256` is for an artifact whose publisher is not the host: the
    publisher states a digest, every source is a mirror, and the derived digest is
    checked against the stated one. That check is what makes the mirrors
    interchangeable CDNs rather than trust roots.

    `lfs` says which digest route applies -- `published_digest` for an LFS object,
    which publishes its SHA-256 as its object id, and `blob_digest` for a plain
    git blob, which has to be fetched and hashed. Stated, never sniffed.

    Sources are ordered: the first is the primary and the rest are alternates,
    cross-checked against it by every deriver that declares more than one.
    """

    dest: str
    sources: tuple[Source, ...]
    expect_sha256: str | None = None
    lfs: bool = True


def published_digest(source: Source) -> tuple[str, int]:
    """Return the SHA-256 and size Hugging Face publishes for `source`.

    The digest is the LFS object id, which HF documents as the file's SHA-256. A
    path that is not stored in LFS has no such id, and this raises rather than
    falling back to the git blob sha1 -- a sha1 in a sha256 field would validate
    and verify nothing.
    """
    body = json.dumps({"paths": [source.path]}).encode()
    request = urllib.request.Request(
        f"https://huggingface.co/api/models/{source.repo}/paths-info/{source.revision}",
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.load(response)
    for item in payload:
        if item.get("path") != source.path:
            continue
        lfs = item.get("lfs")
        if not lfs or not lfs.get("oid"):
            raise SystemExit(f"{source.url()}: not an LFS object, no published SHA-256")
        return str(lfs["oid"]), int(item["size"])
    raise SystemExit(f"{source.url()}: not found at that revision")


def digest_of_url(url: str, cap: int) -> tuple[str, int]:
    """Return the SHA-256 and size of whatever `url` serves, refusing past `cap`.

    The cap is the caller's, and is required, because "how big may this be" is a
    statement about the artifact and not about the strategy. A file that overruns
    it is a mistake in a spec, and failing loudly is what stops a checkpoint
    arriving down a path meant for a config file.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=300) as response:
        body: bytes = response.read(cap + 1)
    if len(body) > cap:
        raise SystemExit(f"{url}: larger than {cap} bytes, which its spec declares")
    return hashlib.sha256(body).hexdigest(), len(body)


def blob_digest(source: Source) -> tuple[str, int]:
    """Return the SHA-256 and size of a non-LFS file, by fetching and hashing it.

    Capped, so this path can never be the one a checkpoint arrives through. The
    revision in the URL is what makes the result a pin rather than a snapshot of
    whatever `main` served today.
    """
    return digest_of_url(source.url(), BLOB_CAP_BYTES)


def digest_of(source: Source, lfs: bool) -> tuple[str, int]:
    """Return one source's SHA-256 and size, by the route its spec declares.

    The one place the two strategies are chosen between, which is what the module
    docstring claims: an artifact gets one route or the other, and stating the
    choice twice is how the two drift.
    """
    return published_digest(source) if lfs else blob_digest(source)


def entry_for(spec: Spec) -> ManifestEntry:
    """Derive one entry, cross-checking every alternate and any stated digest.

    An alternate that publishes different bytes is a failure, not a fallback: the
    whole point of an ordered source list is that any of them serves the artifact
    the digest names.
    """
    sha256, size = digest_of(spec.sources[0], spec.lfs)
    if spec.expect_sha256 is not None and sha256 != spec.expect_sha256:
        raise SystemExit(
            f"{spec.dest}: {spec.sources[0].url()} publishes {sha256}, "
            f"but the publisher states {spec.expect_sha256}"
        )
    for alternate in spec.sources[1:]:
        alt_sha, _ = published_digest(alternate) if spec.lfs else blob_digest(alternate)
        if alt_sha != sha256:
            raise SystemExit(
                f"{spec.dest}: alternate {alternate.url()} publishes {alt_sha}, "
                f"primary {spec.sources[0].url()} publishes {sha256}"
            )
    return {
        "dest": spec.dest,
        "sha256": sha256,
        "bytes": size,
        "sources": [source.url() for source in spec.sources],
    }


def write(manifest: Manifest, path: Path) -> None:
    """Write `manifest` to `path` and report what landed there.

    One writer for all three derivers, so the byte-for-byte format -- two-space
    indent, one trailing newline -- cannot drift between them. That format is what
    makes `git diff --exit-code` the re-derivation check.
    """
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    entries = manifest["entries"]
    total = sum(entry["bytes"] for entry in entries)
    print(f"wrote {path.name}: {len(entries)} entries, {total / 2**30:.1f} GiB")
