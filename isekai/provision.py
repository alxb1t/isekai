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
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from http.client import HTTPMessage
from pathlib import Path
from typing import IO, Any, Literal, Protocol, TypedDict

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


class _KeepRedirect(urllib.request.HTTPRedirectHandler):
    """Stop urllib from following a redirect, so the 302's own headers survive."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> None:
        """Never produce a follow-up request."""
        return None


class HuggingFaceFetcher:
    """Reads the SHA-256 Hugging Face returns in `x-linked-etag` on a HEAD request.

    `resolve/<sha>/<path>` answers **302** and puts `x-linked-etag` on *that*
    response; the CDN it points at does not repeat it. Following the redirect
    therefore loses the header and every entry degrades to post-verification
    silently, so the redirect is deliberately not followed.

    Observed behaviour, not a documented contract, so every failure mode here --
    a missing header, a changed redirect shape, a network error -- returns None
    and the entry degrades to download-and-post-verify. It must never degrade to
    trust (design.md D10).
    """

    def published_digest(self, url: str) -> str | None:
        """Return the published SHA-256, or None if it cannot be read cheaply."""
        request = urllib.request.Request(url, method="HEAD")
        opener = urllib.request.build_opener(_KeepRedirect)
        try:
            with opener.open(request, timeout=30) as response:
                header = response.headers.get("x-linked-etag") or ""
        except urllib.error.HTTPError as redirected:
            header = redirected.headers.get("x-linked-etag") or ""
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


def plan(manifest: Manifest, models_dir: Path, fetcher: Fetcher) -> int:
    """Print one line per entry for the shell driver to act on; 0 if it may proceed.

    `SKIP<TAB><dest>` or `FETCH<TAB><dest><TAB><url>`. Every entry is decided
    before any line is printed, so an abort anywhere stops the run before a single
    byte is transferred rather than in the middle of a 6.9 GB download.
    """
    lines: list[str] = []
    aborts: list[str] = []
    for entry in manifest["entries"]:
        decision = decide(entry, models_dir, fetcher)
        if decision.action == "abort":
            aborts.append(decision.reason)
        elif decision.action == "skip":
            lines.append(f"SKIP\t{entry['dest']}")
        else:
            lines.append(f"FETCH\t{entry['dest']}\t{decision.url}")
    if aborts:
        for reason in aborts:
            print(f"ERROR: {reason}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


def _entry_for(manifest: Manifest, dest: str) -> Entry:
    """Return the manifest entry with this destination, or exit non-zero."""
    for entry in manifest["entries"]:
        if entry["dest"] == dest:
            return entry
    raise SystemExit(f"ERROR: {dest} is not declared in {MANIFEST_PATH}")


def main(argv: list[str]) -> int:
    """Run the two commands the shell driver uses: `plan` and `land`."""
    match argv:
        case ["plan", models_dir]:
            return plan(load_manifest(), Path(models_dir), HuggingFaceFetcher())
        case ["land", models_dir, dest, partial]:
            manifest = load_manifest()
            try:
                land(_entry_for(manifest, dest), Path(models_dir), Path(partial))
            except DigestMismatch as mismatch:
                print(f"ERROR: {mismatch}", file=sys.stderr)
                return 1
            print(f"saved (verified): {dest}")
            return 0
        case _:
            raise SystemExit(
                "usage: provision.py plan <models-dir>\n"
                "       provision.py land <models-dir> <dest> <partial>"
            )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


# What a model file is called, for the purpose of reading one out of the graph.
# A `.jpeg` on a LoadImage node is an input photograph, not an artifact to pin.
MODEL_SUFFIXES = (".safetensors", ".bin", ".onnx", ".pt", ".pth", ".ckpt")

# Node class -> the model files that node downloads for itself and exposes no
# field for. This is the half of the binding the graph cannot supply, and it is
# the gap this whole capability was found through: `LineArtPreprocessor` names no
# file and fetches two -- both of them, unconditionally, regardless of `coarse`.
#
# An empty tuple is a real answer, not a placeholder: `TilePreprocessor` fetches
# nothing at all, and `DWPreprocessor` names its two files in its own inputs, so
# the graph half already covers them. What matters is that the class is *here* --
# a preprocessor absent from this mapping fails the check rather than passing
# silently (design.md D6).
PREPROCESSOR_MODELS: dict[str, tuple[str, ...]] = {
    "TilePreprocessor": (),
    "DWPreprocessor": (),
    "LineArtPreprocessor": ("sk_model.pth", "sk_model2.pth"),
}


def graph_model_files(workflow: dict[str, Any]) -> list[str]:
    """Return every model filename the graph names in a node's inputs."""
    return [
        value
        for node in workflow.values()
        for value in node.get("inputs", {}).values()
        if isinstance(value, str) and value.endswith(MODEL_SUFFIXES)
    ]


def unmapped_preprocessors(workflow: dict[str, Any]) -> list[str]:
    """Return preprocessor classes in the graph that `PREPROCESSOR_MODELS` omits.

    A preprocessor may fetch models with no field to name them, so an unmapped one
    is an unknown quantity, not a safe default.
    """
    return sorted(
        {
            node["class_type"]
            for node in workflow.values()
            if node["class_type"].endswith("Preprocessor")
            and node["class_type"] not in PREPROCESSOR_MODELS
        }
    )


def preprocessor_model_files(workflow: dict[str, Any]) -> list[str]:
    """Return the files the graph's preprocessors fetch without naming them."""
    return [
        filename
        for node in workflow.values()
        for filename in PREPROCESSOR_MODELS.get(node["class_type"], ())
    ]


def undeclared_files(filenames: list[str], manifest: Manifest) -> list[str]:
    """Return the filenames with no manifest entry, in order, without duplicates.

    A graph name is a path relative to its model folder, so it is matched against
    the tail of a destination -- `instantid/diffusion_pytorch_model.safetensors`
    is one entry and `openpose/diffusion_pytorch_model.safetensors` is another,
    and a bare basename match would confuse the two.
    """
    dests = [entry["dest"] for entry in manifest["entries"]]
    missing: list[str] = []
    for filename in filenames:
        if filename in missing:
            continue
        if not any(dest == filename or dest.endswith(f"/{filename}") for dest in dests):
            missing.append(filename)
    return missing


# ComfyUI's models root on the pod. Everything the manifest declares is a path
# relative to this, and `folder_paths` resolves every node's models from it.
MODELS_ROOT = "/opt/ComfyUI/models"

# Where the network volume mounts, and this project's slice of it. The volume is
# shared with another project under a different convention, so nothing here
# reaches outside `MODELS_NAMESPACE` (design.md D9).
VOLUME_MOUNT = "/runpod-volume"
MODELS_NAMESPACE = f"{VOLUME_MOUNT}/isekai"

# The preprocessor nodes whose checkpoints `comfyui_controlnet_aux` fetches into
# its own `ckpts` directory -- container disk, unless AUX_ANNOTATOR_CKPTS_PATH
# says otherwise (design.md D7).
ANNOTATOR_NODES = ("DWPreprocessor", "LineArtPreprocessor")


def annotator_files(workflow: dict[str, Any]) -> list[str]:
    """Return every checkpoint the graph's annotator nodes fetch for themselves.

    Both halves of the binding, for these nodes only: what `DWPreprocessor` names
    in its own inputs, and what `LineArtPreprocessor` fetches while naming nothing.
    """
    files: list[str] = []
    for node in workflow.values():
        if node["class_type"] not in ANNOTATOR_NODES:
            continue
        for value in node.get("inputs", {}).values():
            if isinstance(value, str) and value.endswith(MODEL_SUFFIXES):
                files.append(value)
        files.extend(PREPROCESSOR_MODELS.get(node["class_type"], ()))
    return files


def manifest_dest(filename: str, manifest: Manifest) -> str | None:
    """Return the destination the manifest declares for a graph filename."""
    for entry in manifest["entries"]:
        if entry["dest"] == filename or entry["dest"].endswith(f"/{filename}"):
            return entry["dest"]
    return None
