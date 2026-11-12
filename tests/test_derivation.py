"""The shared derivation module, and what each deriver takes from it.

`tools/` is operator tooling, imported from the repository root the way
`python -m tools.<name>` runs it. Nothing here reaches the network: the two digest
strategies are checked for *which one a spec routes to*, which is the decision,
and the fetch itself is the derivers' own business and is verified by re-running
them.
"""

import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

from isekai.boundary.provision import PINNED_SOURCE
from isekai.boundary.unpack import PLACEMENT_MANIFEST_PATH
from tools import (
    derive_eval_manifest,
    derive_manifest,
    derive_placement,
    derive_reader,
    derive_vocabulary,
)
from tools import manifest as shared
from tools.manifest import Manifest, Source, Spec, Wanted

DERIVERS = (
    derive_manifest,
    derive_eval_manifest,
    derive_vocabulary,
    derive_reader,
    derive_placement,
)

SHARED_NAMES = ("Manifest", "ManifestEntry", "Source", "Spec")


@pytest.mark.spec("model-provisioning:derivation:entry-type-has-one-definition")
@pytest.mark.parametrize("name", SHARED_NAMES)
def test_every_deriver_takes_its_entry_types_from_the_shared_module(
    name: str,
) -> None:
    shared_type = getattr(shared, name)
    for deriver in DERIVERS:
        assert getattr(deriver, name, shared_type) is shared_type, (
            f"{deriver.__name__} declares a competing {name}"
        )


@pytest.mark.spec("model-provisioning:derivation:entry-type-has-one-definition")
def test_no_deriver_declares_a_type_of_its_own_under_a_shared_name() -> None:
    for deriver in DERIVERS:
        source = Path(deriver.__file__ or "").read_text()
        for name in SHARED_NAMES:
            assert f"class {name}(" not in source, (
                f"{deriver.__name__} re-declares {name}"
            )


@pytest.mark.spec("model-provisioning:derivation:both-digest-strategies-are-shared")
@pytest.mark.parametrize("strategy", ("published_digest", "blob_digest"))
def test_both_digest_strategies_live_in_the_shared_module(strategy: str) -> None:
    shared_strategy = getattr(shared, strategy)
    assert callable(shared_strategy)
    for deriver in DERIVERS:
        assert getattr(deriver, strategy, shared_strategy) is shared_strategy, (
            f"{deriver.__name__} carries a {strategy} of its own"
        )


@pytest.mark.spec("model-provisioning:derivation:both-digest-strategies-are-shared")
def test_an_artifact_not_stored_as_a_large_file_is_hashed_by_fetching_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    taken: list[str] = []

    def published(source: Source) -> tuple[str, int]:
        taken.append("lfs")
        return "a" * 64, 1

    def blob(source: Source) -> tuple[str, int]:
        taken.append("blob")
        return "b" * 64, 2

    monkeypatch.setattr(shared, "published_digest", published)
    monkeypatch.setattr(shared, "blob_digest", blob)
    source = Source("org/repo", "0" * 40, "small.csv")
    assert shared.digest_of(source, lfs=False) == ("b" * 64, 2)
    assert shared.digest_of(source, lfs=True) == ("a" * 64, 1)
    assert taken == ["blob", "lfs"]


@pytest.mark.spec("model-provisioning:derivation:rerun-is-byte-identical")
def test_every_deriver_writes_through_the_one_writer() -> None:
    for deriver in DERIVERS:
        assert deriver.write is shared.write


@pytest.mark.spec("model-provisioning:derivation:rerun-is-byte-identical")
def test_writing_the_same_manifest_twice_produces_the_same_bytes(
    tmp_path: Path,
) -> None:
    body: Manifest = {
        "pinned": "2026-09-14",
        "publishers": ["SmilingWolf"],
        "entries": [
            {"dest": "a/b.csv", "sha256": "0" * 64, "bytes": 3, "sources": ["u"]}
        ],
    }
    first, second = tmp_path / "one.json", tmp_path / "two.json"
    shared.write(body, first)
    shared.write(json.loads(first.read_text()), second)
    assert first.read_bytes() == second.read_bytes()


# --- what a fetched digest is taken over -------------------------------------
#
# Offline, through a fake `urlopen`. The module docstring's rule stands -- nothing
# here reaches the network -- and these two assert what `digest_of_url` refuses
# rather than what any host happens to serve.


class _FakeResponse:
    """The two things `digest_of_url` reads off a response, and nothing else."""

    def __init__(self, body: bytes, headers: dict[str, str]) -> None:
        self.headers = headers
        self._body = body

    def read(self, amount: int) -> bytes:
        return self._body[:amount]

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def _opener(body: bytes, headers: dict[str, str], seen: list[dict[str, str]]) -> object:
    """Return a `urlopen` double that records the headers each request carried."""

    def urlopen(request: object, timeout: int = 0) -> _FakeResponse:
        seen.append(dict(getattr(request, "headers", {})))
        return _FakeResponse(body, headers)

    return urlopen


@pytest.mark.spec("model-provisioning:derivation:a-truncated-fetch-is-refused")
def test_a_body_shorter_than_the_declared_length_is_refused_not_hashed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[dict[str, str]] = []
    monkeypatch.setattr(
        shared.urllib.request,
        "urlopen",
        _opener(b"partial", {"Content-Length": "308468"}, seen),
    )

    with pytest.raises(SystemExit) as refused:
        shared.digest_of_url("https://example.invalid/a.csv", 1 << 20)

    message = str(refused.value)
    assert "truncated" in message
    assert "7" in message and "308468" in message


@pytest.mark.spec("model-provisioning:derivation:a-truncated-fetch-is-refused")
def test_a_complete_body_is_hashed(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[dict[str, str]] = []
    monkeypatch.setattr(
        shared.urllib.request,
        "urlopen",
        _opener(b"whole", {"Content-Length": "5"}, seen),
    )

    assert shared.digest_of_url("https://example.invalid/a.csv", 1 << 20) == (
        hashlib.sha256(b"whole").hexdigest(),
        5,
    )


@pytest.mark.spec(
    "model-provisioning:derivation:fetched-digest-demands-identity-encoding"
)
def test_the_fetch_declares_that_only_the_identity_coding_is_acceptable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[dict[str, str]] = []
    monkeypatch.setattr(
        shared.urllib.request,
        "urlopen",
        _opener(b"whole", {"Content-Length": "5"}, seen),
    )

    shared.digest_of_url("https://example.invalid/a.csv", 1 << 20)

    # urllib title-cases every header name it is handed.
    assert seen == [{"User-agent": shared.USER_AGENT, "Accept-encoding": "identity"}]


@pytest.mark.spec(
    "model-provisioning:derivation:fetched-digest-demands-identity-encoding"
)
def test_a_coded_response_is_refused_even_though_identity_was_asked_for(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The ask is not the guard. A server may ignore `Accept-Encoding`, and a
    # gzip stream has the right `Content-Length` for itself -- so the truncation
    # check would pass over it and the digest would be of the compressed bytes.
    seen: list[dict[str, str]] = []
    monkeypatch.setattr(
        shared.urllib.request,
        "urlopen",
        _opener(b"gzipped", {"Content-Length": "7", "Content-Encoding": "gzip"}, seen),
    )

    with pytest.raises(SystemExit) as refused:
        shared.digest_of_url("https://example.invalid/a.csv", 1 << 20)

    assert "gzip" in str(refused.value)


@pytest.mark.spec("model-provisioning:derivation:a-truncated-fetch-is-refused")
def test_a_response_declaring_no_length_is_refused_rather_than_trusted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Without a declared length there is nothing to compare a short read
    # against, so the truncation guard silently opts out. On a route whose whole
    # contract is byte-identical re-derivation, that is worth refusing.
    seen: list[dict[str, str]] = []
    monkeypatch.setattr(shared.urllib.request, "urlopen", _opener(b"whole", {}, seen))

    with pytest.raises(SystemExit) as refused:
        shared.digest_of_url("https://example.invalid/a.csv", 1 << 20)

    assert "Content-Length" in str(refused.value)


# --- a zip entry's members ----------------------------------------------------
#
# The archive is streamed with `read(n)` to its end, which the double above does
# not do: its `read` returns the same prefix every time, and would never end the
# copy.


class _ArchiveResponse:
    """A response that serves a small zip from its start to its end."""

    def __init__(self, body: bytes) -> None:
        self._body = io.BytesIO(body)

    def read(self, amount: int = -1) -> bytes:
        return self._body.read(amount)

    def __enter__(self) -> "_ArchiveResponse":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def _zip(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        for name, body in files.items():
            bundle.writestr(name, body)
    return buffer.getvalue()


def _serving(
    monkeypatch: pytest.MonkeyPatch, archive: bytes, asked: list[str] | None = None
) -> None:
    """Make `urlopen` serve `archive`, and publish its digest as an LFS object."""

    def urlopen(request: object, timeout: int = 0) -> _ArchiveResponse:
        if asked is not None:
            asked.append(getattr(request, "full_url", ""))
        return _ArchiveResponse(archive)

    monkeypatch.setattr(shared.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(
        shared,
        "published_digest",
        lambda source: (hashlib.sha256(archive).hexdigest(), len(archive)),
    )


ARCHIVE_SOURCE = Source("org/archive", "0" * 40, "net.zip")
WANTED = (
    Wanted("encoder.onnx", "sam2/encoder.onnx"),
    Wanted("decoder.onnx", "sam2/decoder.onnx"),
)


@pytest.mark.spec_exempt(
    "structural: a zip entry's members are digested from the archive it reads"
)
def test_derive_unpack_digests_each_member_found_by_its_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = _zip({"net/m.encoder.onnx": b"enc", "net/m.decoder.onnx": b"decoder"})
    asked: list[str] = []
    _serving(monkeypatch, archive, asked)

    entry = shared.entry_for(Spec("sam2/net.zip", (ARCHIVE_SOURCE,), unpack=WANTED))

    assert entry["sha256"] == hashlib.sha256(archive).hexdigest()
    assert entry["unpack"] == [
        {
            "member": "net/m.encoder.onnx",
            "dest": "sam2/encoder.onnx",
            "sha256": hashlib.sha256(b"enc").hexdigest(),
            "bytes": 3,
        },
        {
            "member": "net/m.decoder.onnx",
            "dest": "sam2/decoder.onnx",
            "sha256": hashlib.sha256(b"decoder").hexdigest(),
            "bytes": 7,
        },
    ]
    assert asked == [ARCHIVE_SOURCE.url()]


@pytest.mark.spec_exempt(
    "structural: a spec with no members leaves its entry as every other manifest has it"
)
def test_derive_unpack_leaves_an_entry_without_members_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _serving(monkeypatch, b"not read")

    entry = shared.entry_for(Spec("a/b.onnx", (ARCHIVE_SOURCE,)))

    assert set(entry) == {"dest", "sha256", "bytes", "sources"}


@pytest.mark.spec_exempt(
    "structural: a suffix that matches no member or several is refused, never guessed"
)
@pytest.mark.parametrize(
    "files",
    [
        {"net/other.onnx": b"x", "net/m.decoder.onnx": b"y"},
        {
            "a/m.encoder.onnx": b"x",
            "b/m.encoder.onnx": b"z",
            "net/m.decoder.onnx": b"y",
        },
    ],
    ids=["none", "several"],
)
def test_derive_unpack_refuses_a_suffix_matching_none_or_several(
    monkeypatch: pytest.MonkeyPatch, files: dict[str, bytes]
) -> None:
    _serving(monkeypatch, _zip(files))

    with pytest.raises(SystemExit, match="encoder.onnx"):
        shared.entry_for(Spec("sam2/net.zip", (ARCHIVE_SOURCE,), unpack=WANTED))


@pytest.mark.spec_exempt(
    "structural: a member is read only from the archive the published id names"
)
def test_derive_unpack_refuses_an_archive_that_is_not_the_published_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    served = _zip({"net/m.encoder.onnx": b"enc", "net/m.decoder.onnx": b"dec"})
    _serving(monkeypatch, served)
    monkeypatch.setattr(shared, "published_digest", lambda source: ("f" * 64, 1))

    with pytest.raises(SystemExit, match="no member was read"):
        shared.entry_for(Spec("sam2/net.zip", (ARCHIVE_SOURCE,), unpack=WANTED))


@pytest.mark.spec_exempt(
    "structural: the placement deriver declares pinned sources by its own publishers"
)
def test_derive_placement_pins_every_source_to_a_publisher() -> None:
    assert derive_placement.PINNED == "2026-11-11"
    assert derive_placement.PUBLISHERS == ("yzd-v", "vietanhdev")
    for spec in derive_placement.SPECS:
        for source in spec.sources:
            assert PINNED_SOURCE.match(source.url())
            assert source.repo.split("/")[0] in derive_placement.PUBLISHERS


@pytest.mark.spec_exempt(
    "structural: the placement deriver builds the entries and the archive's members"
)
def test_derive_placement_builds_the_detector_the_estimator_and_the_archive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = _zip({"net/m.encoder.onnx": b"enc", "net/m.decoder.onnx": b"dec"})
    _serving(monkeypatch, archive)
    monkeypatch.setattr(
        shared,
        "published_digest",
        lambda source: (
            (hashlib.sha256(archive).hexdigest(), len(archive))
            if source.path.endswith(".zip")
            else ("c" * 64, 9)
        ),
    )

    manifest = derive_placement.derive()

    assert manifest["pinned"] == "2026-11-11"
    assert [entry["dest"] for entry in manifest["entries"]] == [
        "dwpose/yolox_l.onnx",
        "dwpose/dw-ll_ucoco_384.onnx",
        "sam2/sam2.1_hiera_small_20260221.zip",
    ]
    assert [m["dest"] for m in manifest["entries"][2]["unpack"]] == [
        "sam2/encoder.onnx",
        "sam2/decoder.onnx",
    ]
    assert "unpack" not in manifest["entries"][0]


@pytest.mark.spec_exempt(
    "structural: the placement deriver writes the manifest the provisioner reads"
)
def test_derive_placement_main_writes_the_placement_manifest_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    body: Manifest = {
        "pinned": "2026-11-11",
        "publishers": ["yzd-v"],
        "entries": [
            {"dest": "a/b.onnx", "sha256": "0" * 64, "bytes": 3, "sources": ["u"]}
        ],
    }
    assert derive_placement.MANIFEST_PATH == PLACEMENT_MANIFEST_PATH
    written = tmp_path / "placement.json"
    monkeypatch.setattr(derive_placement, "MANIFEST_PATH", written)
    monkeypatch.setattr(derive_placement, "derive", lambda: body)

    derive_placement.main()

    assert json.loads(written.read_text()) == body
