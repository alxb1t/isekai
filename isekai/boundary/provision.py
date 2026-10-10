"""The manifest of model artifacts, and the checks that keep it honest.

`config/models.json` decides which bytes this repository renders with, and this
module owns every *decision* taken about it: whether the manifest says what a pin is
supposed to say, and, for each entry, whether to skip it, abort the run or fetch it.
`fetch` carries those decisions out, on the laptop and on the pod alike. Every
network call -- the pre-flight HEAD and the transfer -- goes through the `Fetcher`
seam, which a fake replaces so the whole suite stays offline.

On `python -m isekai`'s import graph through `ollama.py`, which reads the
reader's manifest; it imports only the standard library.
"""

import argparse
import hashlib
import json
import posixpath
import re
import shutil
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from http.client import HTTPMessage
from pathlib import Path, PurePosixPath
from typing import IO, Any, Literal, NotRequired, Protocol, TypedDict

MANIFEST_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "models.json"

# The third manifest: the tag list the sorting stage fills a sheet from. A sibling
# of the other two rather than a section of either -- one file per question, and
# this one answers what the pipeline's vocabulary is. The path is declared here,
# beside the graph's, because the checks that keep a manifest honest are this
# module's and all three are held to them.
VOCABULARY_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "vocabulary.json"
)

# The fourth: the reader's model and projector files, keyed by the alias a flow
# names, so the files behind an alias can be checked before it answers (D6).
READER_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "reader.json"
)

# Where `fetch` lands files when told nowhere else: the repository's own models
# root, anchored so it resolves from any working directory.
DEFAULT_MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"

# A lowercase SHA-256, in full. Anything else is not a digest of anything.
DIGEST = re.compile(r"^[0-9a-f]{64}$")

# A Hugging Face URL that addresses an immutable revision. `resolve/main/...` is
# the same URL on two different days, so it matches deliberately narrowly: the
# 40-hex commit, and nothing that merely looks like one.
PINNED_SOURCE = re.compile(
    r"^https://huggingface\.co/[^/]+/[^/]+/resolve/[0-9a-f]{40}/.+$"
)

# The org of a source URL, whether or not the URL is pinned -- so a malformed
# source is reported once, by the pin check, rather than twice.
SOURCE_ORG = re.compile(r"^https://huggingface\.co/(?P<org>[^/]+)/")

# Any whitespace at all. `PINNED_SOURCE` ends in `.+$`, and neither `.` nor `$`
# rules out a newline in the middle of a value: a source carrying one would pass
# the pin check and then arrive at the transfer as two arguments.
WHITESPACE = re.compile(r"\s")


class Entry(TypedDict):
    """One file: where it lands, what its bytes must hash to, where to get them."""

    dest: str
    sha256: str
    bytes: int
    sources: list[str]


class ReaderModel(TypedDict):
    """Which entries a local model is built from, each by its `dest`."""

    model: str
    projector: str


class Manifest(TypedDict):
    """The whole tracked manifest; `aliases` is the reader's alone."""

    pinned: str
    publishers: list[str]
    entries: list[Entry]
    aliases: NotRequired[dict[str, ReaderModel]]


# Derived from the type rather than restated, so a field added to `Entry` is
# shape-checked at runtime too -- a second hand-written list would keep passing.
ENTRY_KEYS = frozenset(Entry.__required_keys__)


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
    without adding trust -- but only an entry whose primary is somebody's mirror
    actually needs one.
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
    """The network seam: what a source says it would serve, and the bytes it serves.

    `published_digest` is the cheap question a HEAD request can answer: does the
    source's *published* digest already disagree with the manifest? `get` moves the
    bytes, which `land` then verifies. A fake answers both from dicts, which is
    what keeps the suite offline.
    """

    def published_digest(self, url: str) -> str | None:
        """Return the SHA-256 the source publishes, or None if it publishes none."""
        ...

    def get(self, url: str, into: Path) -> None:
        """Write the bytes the source serves to `into`; raise `OSError` on failure."""
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

    Observed behaviour, not a documented contract, so every failure mode here -- a
    missing header, a changed redirect shape, a network error -- returns None and
    the entry degrades to download-and-post-verify. It must never degrade to trust.
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

    def get(self, url: str, into: Path) -> None:
        """Stream the file, following the redirect to the CDN, into `into`."""
        with urllib.request.urlopen(url, timeout=60) as response:
            with into.open("wb") as handle:
                shutil.copyfileobj(response, handle, 1 << 20)


@dataclass(frozen=True)
class Decision:
    """What provisioning should do about one manifest entry.

    `skip` — present and verified. `abort` — stop the run and let a human look;
    nothing is deleted. `fetch` — transfer from `urls`, in order, until one of
    them yields bytes that verify, then hand the result to `land`.

    `urls` is the whole ordered list rather than a single winner because that is
    what makes the ordered fallback real: the pre-flight can only reject a
    source that answers, and the failure the alternates exist for — a mirror that
    has gone away — is one the pre-flight collapses to "publishes no digest".

    `target` is the resolved destination, carried rather than recomputed: deciding
    required resolving it, so the decision is what should hold it. It is None
    exactly when the action is `abort`, which is the only case in which no
    destination was arrived at.
    """

    action: Literal["skip", "abort", "fetch"]
    urls: tuple[str, ...]
    reason: str
    target: Path | None = None


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


def resolve_dest(entry: Entry, models_dir: Path) -> Path | None:
    """Return the destination resolved under `models_dir`, or None if it escapes.

    The one place a manifest destination is joined onto the filesystem, so the
    containment rule has exactly one site to be enforced at. The digest offers no
    protection here: whoever supplies the destination supplies the digest beside it,
    and a second project shares the volume this tree lives on.

    Lexical on purpose — `normpath` rather than `resolve` — because `MODELS_ROOT`
    on the pod IS a symlink onto the namespace, so resolving would report the
    target through a path `fetch` was never handed.
    """
    dest = entry["dest"]
    # Whitespace is refused as `sources` refuses it: no pinned file name carries
    # any, and a `\n` would split the log line that names the destination.
    if not dest or dest.startswith("~") or "\\" in dest or WHITESPACE.search(dest):
        return None
    normalized = PurePosixPath(posixpath.normpath(dest))
    # `normpath` cannot turn a relative path absolute, so one test covers both
    # a leading slash and anything that normalises to one; `..` first is the
    # only way a relative path climbs out. The empty `parts` is `"."` — the
    # models root itself rather than a file under it, which is equally not a
    # path this may land on, and which indexing `parts[0]` crashed on.
    if normalized.is_absolute() or normalized.parts[:1] in ((), ("..",)):
        return None
    return models_dir / normalized


class UnknownArtifact(Exception):
    """A caller asked for a destination the manifest it searched does not declare."""


class UnpinnedArtifact(Exception):
    """A manifest entry names a source that does not address an immutable revision."""


class EscapingDestination(Exception):
    """A manifest entry's destination does not land under the models root."""


def entry_for(manifest: Manifest, dest: str) -> Entry:
    """Return the entry declaring `dest`, or raise `UnknownArtifact`.

    The lookup the scorer and the vocabulary's callers go through to reach a
    model, so a typo in an artifact name is a named failure rather than a `None`
    that surfaces three frames later as a missing file.
    """
    for entry in manifest["entries"]:
        if entry["dest"] == dest:
            return entry
    raise UnknownArtifact(f"{dest} is not declared in the manifest searched")


def resolve(dest: str, models_dir: Path, manifest: Manifest) -> Path:
    """Return the verified path to one artifact, or raise rather than score from it.

    Three refusals, in the order a bad manifest would trip them: an artifact the
    manifest does not declare, an entry whose sources are not pinned revisions,
    and bytes on disk that do not hash to the pin. The last one raises
    `DigestMismatch` from `isekai.boundary.provision`, whose message names the file, the
    expected digest and the computed one -- all three, because a mismatch is read
    by a human deciding whether a pin is stale or a file has been swapped.

    The pin check runs even though this function fetches nothing. The manifest is
    the only reason to believe the bytes on disk are the right ones, and an entry
    pointing at `resolve/main/` says nothing about which bytes those were.

    A fourth refusal sits under the third: the join onto `models_dir` goes through
    `isekai.boundary.provision.resolve_dest`, which is the repository's **single**
    site for the containment rule. Every caller here passes a literal today, so this
    is not an exploit path being closed -- it is the invariant keeping one
    enforcement site rather than two, so a destination that climbs out of the models
    root is refused here exactly as it is on the pod.
    """
    entry = entry_for(manifest, dest)
    for source in entry["sources"]:
        if WHITESPACE.search(source) or not PINNED_SOURCE.match(source):
            raise UnpinnedArtifact(
                f"{dest}: {source!r} is not a pinned revision, so the digest "
                "beside it verifies nothing in particular"
            )
    path = resolve_dest(entry, models_dir)
    if path is None:
        raise EscapingDestination(
            f"{dest!r} does not resolve to a path under {models_dir}, so it is "
            "refused rather than loaded from"
        )
    verify(path, entry["sha256"])
    return path


def decide(entry: Entry, models_dir: Path, fetcher: Fetcher) -> Decision:
    """Decide what to do about one entry: skip it, abort the run, or fetch it.

    A file already at the destination is *hashed*, never taken on its name — that is
    the whole point of a manifest, and skip-if-present is what would otherwise leave
    a warm volume permanently unchecked. A present file that fails is left exactly
    where it is: the volume is shared, and a file this run did not write is not this
    run's to remove.

    An absent file is offered *every* source that survives the pre-flight, in the
    manifest's order, so `fetch` can walk them. Only a source that positively
    disagrees is dropped; a source that publishes nothing is kept, because the
    pre-flight is an optimisation and never a substitute for hashing the bytes that
    landed.
    """
    dest = resolve_dest(entry, models_dir)
    if dest is None:
        return Decision(
            "abort",
            (),
            f"destination {entry['dest']!r} does not resolve inside {models_dir}",
        )

    if dest.exists():
        try:
            verify(dest, entry["sha256"])
        except DigestMismatch as mismatch:
            return Decision("abort", (), f"{mismatch} — left on disk for inspection")
        return Decision("skip", (), f"present and verified: {entry['dest']}", dest)

    if not entry["sources"]:
        return Decision("abort", (), f"no source is declared for {entry['dest']}")

    rejected: list[str] = []
    offered: list[str] = []
    for url in entry["sources"]:
        if WHITESPACE.search(url) or not PINNED_SOURCE.match(url):
            rejected.append(f"{url} is not a pinned URL free of whitespace")
            continue
        published = fetcher.published_digest(url)
        if published is not None and published != entry["sha256"]:
            rejected.append(f"{url} publishes {published}")
            continue
        offered.append(url)

    if offered:
        return Decision("fetch", tuple(offered), f"absent: {entry['dest']}", dest)

    return Decision(
        "abort",
        (),
        f"every source for {entry['dest']} was rejected before transfer "
        f"(expected {entry['sha256']}): " + "; ".join(rejected),
    )


def land(entry: Entry, dest: Path, partial: Path) -> None:
    """Verify a just-transferred file and only then move it to `dest`.

    Raises `DigestMismatch` and removes `partial` if the bytes are wrong, so an
    interrupted or tampered transfer never occupies the final name and the next
    run sees the file as absent rather than as present-and-trusted.

    Takes the destination rather than deriving one, so `resolve_dest` really is the
    single site the containment rule is enforced at instead of being the single site
    plus everywhere that calls it again.
    """
    try:
        verify(partial, entry["sha256"])
    except DigestMismatch:
        partial.unlink(missing_ok=True)
        raise
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial.replace(dest)


def fetch(manifest: Manifest, models_dir: Path, fetcher: Fetcher) -> int:
    """Land every entry the manifest declares under `models_dir`; 0 if all are there.

    Every entry is decided before a byte moves, so an abort anywhere stops the run
    before a 6.9 GB download rather than in the middle of one. Each fetched entry
    walks its sources in order: a failed transfer or bytes that do not verify move
    to the next, and only exhausting them all fails the run.
    """
    decisions = [
        (entry, decide(entry, models_dir, fetcher)) for entry in manifest["entries"]
    ]
    aborts = [
        decision.reason for _, decision in decisions if decision.action == "abort"
    ]
    if aborts:
        for reason in aborts:
            print(f"ERROR: {reason}", file=sys.stderr)
        return 1
    for entry, decision in decisions:
        target = decision.target
        assert target is not None  # only an abort carries no target
        if decision.action == "skip":
            print(f"skip (present, verified): {target}")
        elif not _transfer(entry, target, decision.urls, fetcher):
            print(f"ERROR: every source for {target} failed", file=sys.stderr)
            return 1
    print(f"models ready under {models_dir}")
    return 0


def _transfer(
    entry: Entry, target: Path, urls: tuple[str, ...], fetcher: Fetcher
) -> bool:
    """Land `entry` at `target` from the first of `urls` that serves verified bytes."""
    partial = target.with_name(f"{target.name}.partial")
    target.parent.mkdir(parents=True, exist_ok=True)
    for url in urls:
        print(f"downloading: {url}")
        try:
            fetcher.get(url, partial)
        except OSError as failed:
            partial.unlink(missing_ok=True)
            print(f"WARNING: transfer failed from {url}: {failed}", file=sys.stderr)
            continue
        try:
            land(entry, target, partial)
        except DigestMismatch:
            print(f"WARNING: bytes served by {url} did not verify", file=sys.stderr)
            continue
        print(f"saved (verified): {target}")
        return True
    return False


def manifest_argument(given: str | None) -> Path:
    """Return the manifest a `fetch` invocation names, defaulting to the graph's.

    **Which manifest, not which policy.** Every manifest this repository keeps is
    held to the same pins, the same digests and the same containment rule, so the
    provisioner takes the file as an argument rather than growing a verb per
    consumer. It is what makes the vocabulary a *provisioned* artifact rather than
    one that is merely verified: `uv run python -m isekai.boundary.provision fetch
    config/vocabulary.json` fetches it through this exact path.
    """
    return MANIFEST_PATH if given is None else Path(given)


def _parser() -> argparse.ArgumentParser:
    """Return the parser for `fetch`."""
    parser = argparse.ArgumentParser(prog="provision.py")
    verbs = parser.add_subparsers(dest="verb", required=True)
    fetch_verb = verbs.add_parser("fetch", help="land a manifest's files, verified")
    fetch_verb.add_argument(
        "--models-dir",
        type=Path,
        default=DEFAULT_MODELS_DIR,
        help="where the files land (default: the repository's models/)",
    )
    fetch_verb.add_argument("manifest", nargs="?", help="default: config/models.json")
    return parser


def main(argv: list[str]) -> int:
    """Run `fetch`: `provision.py fetch [--models-dir DIR] [manifest]`."""
    args = _parser().parse_args(argv)
    source = manifest_argument(args.manifest)
    return fetch(load_manifest(source), args.models_dir, HuggingFaceFetcher())


# What a model file is called, for the purpose of reading one out of the graph.
# A `.jpeg` on a LoadImage node is an input photograph, not an artifact to pin.
MODEL_SUFFIXES = (".safetensors", ".bin", ".onnx", ".pt", ".pth", ".ckpt")

# Every node class the shipped graph uses -> the model files that class downloads
# for itself and exposes no field for. This is the half of the binding the graph
# cannot supply, and it is the gap this whole capability was found through:
# `LineArtPreprocessor` names no file and fetches two -- both of them,
# unconditionally, regardless of `coarse`.
#
# Membership is **by name, over every class in the graph**, not by a
# `*Preprocessor` suffix. A suffix rule binds the nodes that happen to be spelled
# that way and silently passes the ones that are not:
# `InstantIDFaceAnalysis` fetches the whole antelopev2 pack and matches no
# pattern at all. So a class in the graph that is absent from this mapping fails
# the check, and adding a node forces the question to be answered once.
#
# An empty tuple is a real answer, not a placeholder: `TilePreprocessor` fetches
# nothing at all, and `DWPreprocessor` names its two files in its own inputs, so
# the graph half already covers them.
SELF_FETCHING_MODELS: dict[str, tuple[str, ...]] = {
    # Nodes that fetch models nothing in the graph names.
    "InstantIDFaceAnalysis": (
        "1k3d68.onnx",
        "2d106det.onnx",
        "genderage.onnx",
        "glintr100.onnx",
        "scrfd_10g_bnkps.onnx",
    ),
    "LineArtPreprocessor": ("sk_model.pth", "sk_model2.pth"),
    # Nodes that fetch nothing, or name in their own inputs everything they load.
    "ApplyInstantIDAdvanced": (),
    "CLIPSetLastLayer": (),
    "CLIPTextEncode": (),
    "CheckpointLoaderSimple": (),
    "ControlNetApplyAdvanced": (),
    "ControlNetLoader": (),
    "DWPreprocessor": (),
    "EmptyLatentImage": (),
    "ImageScale": (),
    "ImageUpscaleWithModel": (),
    "InstantIDModelLoader": (),
    "KSampler": (),
    "LoadImage": (),
    "SaveImage": (),
    "TilePreprocessor": (),
    "UpscaleModelLoader": (),
    "VAEDecode": (),
    "VAEEncode": (),
}


def _named_model_files(node: dict[str, Any]) -> list[str]:
    """Return the model files this node names in its own inputs."""
    return [
        value
        for value in node.get("inputs", {}).values()
        if isinstance(value, str) and value.endswith(MODEL_SUFFIXES)
    ]


def _fetched_model_files(node: dict[str, Any]) -> list[str]:
    """Return the model files this node fetches without naming them anywhere."""
    return list(SELF_FETCHING_MODELS.get(node["class_type"], ()))


def graph_model_files(workflow: dict[str, Any]) -> list[str]:
    """Return every model filename the graph names in a node's inputs."""
    return [f for node in workflow.values() for f in _named_model_files(node)]


def unclassified_node_classes(workflow: dict[str, Any]) -> list[str]:
    """Return classes in the graph that `SELF_FETCHING_MODELS` does not classify.

    A node may fetch models with no field to name them, so an unclassified one is
    an unknown quantity, not a safe default -- and it cannot be recognised by how
    its class is spelled.
    """
    return sorted(
        {
            node["class_type"]
            for node in workflow.values()
            if node["class_type"] not in SELF_FETCHING_MODELS
        }
    )


def self_fetched_model_files(workflow: dict[str, Any]) -> list[str]:
    """Return the files the graph's nodes fetch for themselves without naming them."""
    return [f for node in workflow.values() for f in _fetched_model_files(node)]


def undeclared_files(filenames: list[str], manifest: Manifest) -> list[str]:
    """Return the filenames with no manifest entry, in order, without duplicates."""
    missing: list[str] = []
    for filename in filenames:
        if filename not in missing and manifest_dest(filename, manifest) is None:
            missing.append(filename)
    return missing


# ComfyUI's models root on the pod. Everything the manifest declares is a path
# relative to this, and `folder_paths` resolves every node's models from it.
MODELS_ROOT = "/opt/ComfyUI/models"

# The preprocessor nodes whose checkpoints `comfyui_controlnet_aux` fetches into
# its own `ckpts` directory -- container disk, unless AUX_ANNOTATOR_CKPTS_PATH
# says otherwise.
ANNOTATOR_NODES = ("DWPreprocessor", "LineArtPreprocessor")


def annotator_files(workflow: dict[str, Any]) -> list[str]:
    """Return every checkpoint the graph's annotator nodes fetch for themselves.

    Both halves of the binding, for these nodes only: what `DWPreprocessor` names
    in its own inputs, and what `LineArtPreprocessor` fetches while naming nothing.
    """
    return [
        filename
        for node in workflow.values()
        if node["class_type"] in ANNOTATOR_NODES
        for filename in _named_model_files(node) + _fetched_model_files(node)
    ]


def manifest_dest(filename: str, manifest: Manifest) -> str | None:
    """Return the destination the manifest declares for a graph filename, if any.

    A graph name is a path relative to its model folder, so it is matched against
    the tail of a destination -- `instantid/diffusion_pytorch_model.safetensors`
    is one entry and `openpose/diffusion_pytorch_model.safetensors` is another,
    and a bare basename match would confuse the two.
    """
    for entry in manifest["entries"]:
        if entry["dest"] == filename or entry["dest"].endswith(f"/{filename}"):
            return entry["dest"]
    return None


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
