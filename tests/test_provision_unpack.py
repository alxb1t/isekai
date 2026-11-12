"""A zip entry's members: unpacked by declared destination, each verified.

The archive is built in memory and served by `FakeFetcher`, so the suite stays
offline. The names in it are the publisher's and decide nothing: only the
destinations the manifest declares are written.
"""

import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

from isekai.boundary import unpack
from isekai.boundary.provision import (
    DigestMismatch,
    Manifest,
    UnknownArtifact,
    UnpinnedArtifact,
)
from isekai.boundary.unpack import (
    Member,
    UnpackRefused,
    ZipEntry,
    decide_members,
    fetch,
    member_for,
    resolve_member,
    unpack_members,
)
from tests.fakes import FakeFetcher

ENCODER = b"the encoder's bytes"
DECODER = b"the decoder's bytes"

SOURCE = "https://huggingface.co/some/archive/resolve/" + "a" * 40 + "/net.zip"
MUTABLE = "https://huggingface.co/some/archive/resolve/main/net.zip"


def _zip(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name, body in files.items():
            bundle.writestr(name, body)
    return buffer.getvalue()


def _digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _member(name: str, dest: str, body: bytes, size: int | None = None) -> Member:
    return {
        "member": name,
        "dest": dest,
        "sha256": _digest(body),
        "bytes": len(body) if size is None else size,
    }


def _entry(archive: bytes, members: list[Member], source: str = SOURCE) -> ZipEntry:
    return {
        "dest": "sam2/net.zip",
        "sha256": _digest(archive),
        "bytes": len(archive),
        "sources": [source],
        "unpack": members,
    }


def _manifest(entry: ZipEntry) -> Manifest:
    return {"pinned": "2026-11-11", "publishers": ["some"], "entries": [entry]}


def _both() -> list[Member]:
    return [
        _member("net/encoder.onnx", "sam2/encoder.onnx", ENCODER),
        _member("net/decoder.onnx", "sam2/decoder.onnx", DECODER),
    ]


def _archive() -> bytes:
    return _zip({"net/encoder.onnx": ENCODER, "net/decoder.onnx": DECODER})


def _on_disk(models: Path, entry: ZipEntry, archive: bytes) -> Path:
    """Place `archive` where `entry` declares it and return its path."""
    path = models / entry["dest"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(archive)
    return path


def _files(root: Path) -> set[str]:
    return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}


@pytest.mark.spec("model-provisioning:unpack:a-verified-archive-lands-its-members")
def test_unpack_lands_the_archive_and_each_member_at_its_destination(
    tmp_path: Path,
) -> None:
    archive = _archive()
    entry = _entry(archive, _both())
    fetcher = FakeFetcher(served={SOURCE: archive})

    assert fetch(_manifest(entry), tmp_path, fetcher) == 0

    assert _digest((tmp_path / "sam2/net.zip").read_bytes()) == entry["sha256"]
    assert (tmp_path / "sam2/encoder.onnx").read_bytes() == ENCODER
    assert (tmp_path / "sam2/decoder.onnx").read_bytes() == DECODER
    assert [url for url, _ in fetcher.fetched] == [SOURCE]


@pytest.mark.spec("model-provisioning:unpack:the-archive-names-no-destination")
def test_unpack_names_decide_nothing_but_the_declared_destinations(
    tmp_path: Path,
) -> None:
    models = tmp_path / "models"
    archive = _zip(
        {
            "net/encoder.onnx": ENCODER,
            "net/decoder.onnx": DECODER,
            "../escape.onnx": b"outside",
            "/absolute.onnx": b"outside",
        }
    )
    entry = _entry(archive, _both())

    assert fetch(_manifest(entry), models, FakeFetcher(served={SOURCE: archive})) == 0

    assert _files(tmp_path) == {
        "models/sam2/net.zip",
        "models/sam2/encoder.onnx",
        "models/sam2/decoder.onnx",
    }


@pytest.mark.spec("model-provisioning:unpack:the-archive-names-no-destination")
def test_unpack_names_a_declared_destination_that_escapes_is_refused(
    tmp_path: Path,
) -> None:
    archive = _archive()
    escaping = _member("net/encoder.onnx", "../escape.onnx", ENCODER)
    entry = _entry(archive, [escaping])

    assert decide_members(entry, tmp_path / "models") != []
    assert fetch(_manifest(entry), tmp_path / "models", FakeFetcher()) == 1
    assert not (tmp_path / "escape.onnx").exists()


@pytest.mark.spec(
    "model-provisioning:unpack:a-member-that-does-not-verify-is-removed-and-refused"
)
def test_unpack_digest_refuses_naming_both_and_leaves_nothing(
    tmp_path: Path,
) -> None:
    archive = _archive()
    wrong = _member(
        "net/encoder.onnx", "sam2/encoder.onnx", b"other bytes", len(ENCODER)
    )
    entry = _entry(archive, [wrong])
    _on_disk(tmp_path, entry, archive)

    with pytest.raises(DigestMismatch) as refused:
        unpack_members(entry, tmp_path / entry["dest"], tmp_path)

    message = str(refused.value)
    assert "net/encoder.onnx" in message
    assert wrong["sha256"] in message
    assert _digest(ENCODER) in message
    assert _files(tmp_path) == {"sam2/net.zip"}


@pytest.mark.spec("model-provisioning:unpack:a-member-past-its-size-is-refused")
def test_unpack_size_refuses_a_member_past_it_reading_one_byte_over(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    big = b"a" * 5000
    archive = _zip({"net/encoder.onnx": big})
    entry = _entry(archive, [_member("net/encoder.onnx", "sam2/encoder.onnx", big, 4)])
    _on_disk(tmp_path, entry, archive)
    returned: list[int] = []
    original = zipfile.ZipExtFile.read

    def counting(self: zipfile.ZipExtFile, n: int | None = -1) -> bytes:
        data = original(self, n)
        returned.append(len(data))
        return data

    monkeypatch.setattr(zipfile.ZipExtFile, "read", counting)

    with pytest.raises(UnpackRefused, match="net/encoder.onnx"):
        unpack_members(entry, tmp_path / entry["dest"], tmp_path)

    assert sum(returned) == 5
    assert _files(tmp_path) == {"sam2/net.zip"}


@pytest.mark.spec(
    "model-provisioning:unpack:a-gone-member-is-unpacked-with-no-transfer"
)
def test_unpack_gone_member_is_written_again_with_no_transfer(
    tmp_path: Path,
) -> None:
    archive = _archive()
    entry = _entry(archive, _both())
    assert fetch(_manifest(entry), tmp_path, FakeFetcher(served={SOURCE: archive})) == 0
    (tmp_path / "sam2/decoder.onnx").unlink()
    again = FakeFetcher()

    assert fetch(_manifest(entry), tmp_path, again) == 0

    assert (tmp_path / "sam2/decoder.onnx").read_bytes() == DECODER
    assert again.fetched == []


@pytest.mark.spec("model-provisioning:unpack:a-member-the-archive-lacks-is-refused")
def test_unpack_missing_member_is_refused_naming_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    archive = _zip({"net/encoder.onnx": ENCODER})
    entry = _entry(archive, _both())
    _on_disk(tmp_path, entry, archive)

    with pytest.raises(UnpackRefused, match="net/decoder.onnx"):
        unpack_members(entry, tmp_path / entry["dest"], tmp_path)

    fetcher = FakeFetcher(served={SOURCE: archive})
    assert fetch(_manifest(entry), tmp_path / "again", fetcher) == 1
    assert "net/decoder.onnx" in capsys.readouterr().err


@pytest.mark.spec(
    "model-provisioning:unpack:a-present-member-with-other-bytes-stops-the-fetch"
)
def test_unpack_stop_halts_the_fetch_before_a_transfer_and_keeps_the_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    archive = _archive()
    entry = _entry(archive, _both())
    stale = tmp_path / "sam2/decoder.onnx"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"somebody else's bytes")
    fetcher = FakeFetcher(served={SOURCE: archive})

    assert fetch(_manifest(entry), tmp_path, fetcher) == 1

    assert fetcher.fetched == []
    assert stale.read_bytes() == b"somebody else's bytes"
    assert "sam2/decoder.onnx" in capsys.readouterr().err
    assert not (tmp_path / "sam2/net.zip").exists()


@pytest.mark.spec(
    "model-provisioning:unpack:a-member-resolves-only-when-its-digest-verifies"
)
def test_unpack_resolve_verifies_the_members_own_digest(tmp_path: Path) -> None:
    archive = _archive()
    manifest = _manifest(_entry(archive, _both()))
    assert fetch(manifest, tmp_path, FakeFetcher(served={SOURCE: archive})) == 0

    path = resolve_member("sam2/encoder.onnx", tmp_path, manifest)
    assert path == tmp_path / "sam2/encoder.onnx"

    path.write_bytes(b"changed")
    with pytest.raises(DigestMismatch):
        resolve_member("sam2/encoder.onnx", tmp_path, manifest)


@pytest.mark.spec(
    "model-provisioning:unpack:a-member-resolves-only-when-its-digest-verifies"
)
def test_unpack_resolve_refuses_an_unknown_member_and_an_unpinned_archive(
    tmp_path: Path,
) -> None:
    archive = _archive()
    manifest = _manifest(_entry(archive, _both()))
    with pytest.raises(UnknownArtifact):
        member_for(manifest, "sam2/other.onnx")

    unpinned = _manifest(_entry(archive, _both(), MUTABLE))
    with pytest.raises(UnpinnedArtifact):
        resolve_member("sam2/encoder.onnx", tmp_path, unpinned)


@pytest.mark.spec_exempt(
    "structural: the command line is `fetch` over the real fetcher and a named manifest"
)
def test_unpack_cli_fetches_the_manifest_it_names_into_the_models_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = _archive()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(_manifest(_entry(archive, _both()))))
    monkeypatch.setattr(
        unpack, "HuggingFaceFetcher", lambda: FakeFetcher(served={SOURCE: archive})
    )

    code = unpack.main(["fetch", "--models-dir", str(tmp_path / "m"), str(manifest)])

    assert code == 0
    assert (tmp_path / "m/sam2/encoder.onnx").read_bytes() == ENCODER


@pytest.mark.spec_exempt(
    "structural: the remedy a refusal prints is the command this module runs"
)
def test_unpack_remedy_names_this_module_and_the_manifest_it_defaults_to() -> None:
    assert unpack.PLACEMENT_REMEDY.endswith(
        f"-m isekai.boundary.unpack fetch config/{unpack.PLACEMENT_MANIFEST_PATH.name}"
    )
