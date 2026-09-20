"""The shared derivation module, and what each deriver takes from it.

`scripts/` is declared a source root in `pyproject.toml` -- operator tooling, not
a package, and not on `python -m isekai`'s import graph. Nothing here reaches the
network: the two digest strategies are checked for *which one a spec routes to*,
which is the decision, and the fetch itself is the derivers' own business and is
verified by re-running them.
"""

import hashlib
import json
from pathlib import Path

import derive_eval_manifest
import derive_manifest
import derive_vocabulary
import manifest as shared
import pytest
from manifest import Manifest, Source

DERIVERS = (derive_manifest, derive_eval_manifest, derive_vocabulary)

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
    monkeypatch.setattr(shared.urllib.request, "urlopen", _opener(b"whole", {}, seen))

    shared.digest_of_url("https://example.invalid/a.csv", 1 << 20)

    # urllib title-cases every header name it is handed.
    assert seen == [{"User-agent": shared.USER_AGENT, "Accept-encoding": "identity"}]
