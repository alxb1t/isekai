import hashlib
from pathlib import Path

import pytest

from isekai.provision import (
    DigestMismatch,
    Entry,
    Manifest,
    decide,
    digest_of,
    land,
    plan,
    verify,
)
from tests.fakes import FakeFetcher

PAYLOAD = b"the intended bytes"
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()
OTHER = hashlib.sha256(b"somebody else's bytes").hexdigest()

PRIMARY = "https://huggingface.co/a/mirror/resolve/" + "0" * 40 + "/model.onnx"
ALTERNATE = "https://huggingface.co/a/publisher/resolve/" + "1" * 40 + "/model.onnx"


def _entry(sources: list[str] | None = None) -> Entry:
    return {
        "dest": "controlnet/model.onnx",
        "sha256": DIGEST,
        "bytes": len(PAYLOAD),
        "sources": sources if sources is not None else [PRIMARY, ALTERNATE],
    }


def _manifest(entries: list[Entry]) -> Manifest:
    return {"pinned": "2026-09-04", "publishers": [], "entries": entries}


def _place(models_dir: Path, entry: Entry, payload: bytes) -> Path:
    dest = models_dir / entry["dest"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(payload)
    return dest


@pytest.mark.spec("model-provisioning:byte-verification:mismatched-bytes-are-rejected")
def test_verify_accepts_bytes_whose_digest_matches(tmp_path: Path) -> None:
    path = tmp_path / "model.onnx"
    path.write_bytes(PAYLOAD)
    verify(path, DIGEST)


@pytest.mark.spec("model-provisioning:byte-verification:mismatched-bytes-are-rejected")
def test_verify_rejects_bytes_whose_digest_differs(tmp_path: Path) -> None:
    path = tmp_path / "model.onnx"
    path.write_bytes(b"somebody else's bytes")
    with pytest.raises(DigestMismatch):
        verify(path, DIGEST)


@pytest.mark.spec("model-provisioning:byte-verification:mismatched-bytes-are-rejected")
def test_a_mismatch_names_the_file_the_expected_digest_and_the_computed_one(
    tmp_path: Path,
) -> None:
    path = tmp_path / "model.onnx"
    path.write_bytes(b"somebody else's bytes")
    with pytest.raises(DigestMismatch) as raised:
        verify(path, DIGEST)
    message = str(raised.value)
    assert str(path) in message
    assert DIGEST in message
    assert digest_of(path) in message


@pytest.mark.spec(
    "model-provisioning:byte-verification:a-present-file-is-verified-not-skipped"
)
def test_a_present_file_whose_bytes_match_is_skipped(tmp_path: Path) -> None:
    entry = _entry()
    _place(tmp_path, entry, PAYLOAD)
    assert decide(entry, tmp_path, FakeFetcher()).action == "skip"


@pytest.mark.spec(
    "model-provisioning:byte-verification:a-present-file-is-verified-not-skipped"
)
def test_a_present_file_whose_bytes_were_replaced_is_not_accepted_by_name(
    tmp_path: Path,
) -> None:
    entry = _entry()
    _place(tmp_path, entry, b"somebody else's bytes")
    decision = decide(entry, tmp_path, FakeFetcher())
    assert decision.action == "abort"
    assert entry["dest"] in decision.reason


@pytest.mark.spec(
    "model-provisioning:byte-verification:a-present-file-is-verified-not-skipped"
)
def test_a_present_file_is_hashed_rather_than_pre_flighted(tmp_path: Path) -> None:
    entry = _entry()
    _place(tmp_path, entry, PAYLOAD)
    fetcher = FakeFetcher()
    decide(entry, tmp_path, fetcher)
    assert fetcher.asked == []


@pytest.mark.spec(
    "model-provisioning:byte-verification:a-present-file-that-fails-is-not-deleted"
)
def test_a_present_file_that_fails_verification_survives_the_abort(
    tmp_path: Path,
) -> None:
    entry = _entry()
    dest = _place(tmp_path, entry, b"somebody else's bytes")
    assert decide(entry, tmp_path, FakeFetcher()).action == "abort"
    assert dest.exists()
    assert dest.read_bytes() == b"somebody else's bytes"


@pytest.mark.spec("model-provisioning:byte-verification:a-failed-download-never-lands")
def test_an_interrupted_transfer_leaves_nothing_at_the_destination(
    tmp_path: Path,
) -> None:
    entry = _entry()
    partial = tmp_path / "model.onnx.partial"
    partial.write_bytes(PAYLOAD[:6])
    with pytest.raises(DigestMismatch):
        land(entry, tmp_path, partial)
    assert not (tmp_path / entry["dest"]).exists()
    assert not partial.exists()


@pytest.mark.spec("model-provisioning:byte-verification:a-failed-download-never-lands")
def test_after_a_failed_transfer_the_next_run_sees_the_file_as_absent(
    tmp_path: Path,
) -> None:
    entry = _entry()
    partial = tmp_path / "model.onnx.partial"
    partial.write_bytes(PAYLOAD[:6])
    with pytest.raises(DigestMismatch):
        land(entry, tmp_path, partial)
    assert decide(entry, tmp_path, FakeFetcher()).action == "fetch"


@pytest.mark.spec_exempt(
    "structural: the landing happy path the failure scenarios are read against"
)
def test_a_verified_transfer_lands_under_the_final_name(tmp_path: Path) -> None:
    entry = _entry()
    partial = tmp_path / "model.onnx.partial"
    partial.write_bytes(PAYLOAD)
    land(entry, tmp_path, partial)
    dest = tmp_path / entry["dest"]
    assert dest.read_bytes() == PAYLOAD
    assert not partial.exists()


@pytest.mark.spec(
    "model-provisioning:preflight:published-digest-mismatch-aborts-before-transfer"
)
def test_a_source_publishing_a_different_digest_is_rejected_and_the_next_offered(
    tmp_path: Path,
) -> None:
    entry = _entry()
    fetcher = FakeFetcher({PRIMARY: OTHER, ALTERNATE: DIGEST})
    decision = decide(entry, tmp_path, fetcher)
    assert decision.action == "fetch"
    assert decision.urls[0] == ALTERNATE
    assert fetcher.asked == [PRIMARY, ALTERNATE]


@pytest.mark.spec(
    "model-provisioning:preflight:published-digest-mismatch-aborts-before-transfer"
)
def test_every_source_publishing_a_different_digest_aborts_before_any_transfer(
    tmp_path: Path,
) -> None:
    entry = _entry()
    decision = decide(entry, tmp_path, FakeFetcher({PRIMARY: OTHER, ALTERNATE: OTHER}))
    assert decision.action == "abort"
    assert PRIMARY in decision.reason
    assert ALTERNATE in decision.reason


@pytest.mark.spec(
    "model-provisioning:preflight:published-digest-mismatch-aborts-before-transfer"
)
def test_a_source_publishing_no_digest_is_downloaded_and_post_verified(
    tmp_path: Path,
) -> None:
    entry = _entry()
    decision = decide(entry, tmp_path, FakeFetcher())
    assert decision.action == "fetch"
    assert decision.urls[0] == PRIMARY


@pytest.mark.spec(
    "model-provisioning:preflight:published-digest-mismatch-aborts-before-transfer"
)
def test_a_source_publishing_the_declared_digest_is_offered_first(
    tmp_path: Path,
) -> None:
    entry = _entry()
    decision = decide(entry, tmp_path, FakeFetcher({PRIMARY: DIGEST}))
    assert decision.action == "fetch"
    assert decision.urls[0] == PRIMARY


@pytest.mark.spec(
    "model-provisioning:source-fallback:the-plan-carries-every-surviving-source"
)
def test_every_source_surviving_the_pre_flight_is_offered_in_manifest_order(
    tmp_path: Path,
) -> None:
    decision = decide(_entry(), tmp_path, FakeFetcher())
    assert decision.action == "fetch"
    assert decision.urls == (PRIMARY, ALTERNATE)


@pytest.mark.spec(
    "model-provisioning:source-fallback:the-plan-carries-every-surviving-source"
)
def test_a_source_rejected_before_transfer_is_absent_from_the_offered_sources(
    tmp_path: Path,
) -> None:
    decision = decide(_entry(), tmp_path, FakeFetcher({PRIMARY: OTHER}))
    assert decision.action == "fetch"
    assert decision.urls == (ALTERNATE,)


@pytest.mark.spec(
    "model-provisioning:source-fallback:the-plan-carries-every-surviving-source"
)
def test_the_plan_line_carries_the_whole_ordered_source_list(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    entry = _entry()
    assert plan(_manifest([entry]), tmp_path, FakeFetcher()) == 0
    target = tmp_path / entry["dest"]
    assert capsys.readouterr().out.splitlines() == [
        f"FETCH\t{target}\t{PRIMARY}\t{ALTERNATE}"
    ]


@pytest.mark.spec_exempt("structural: the CLI surface the shell driver calls")
def test_plan_reports_a_present_and_verified_entry_as_a_skip(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    entry = _entry()
    _place(tmp_path, entry, PAYLOAD)
    manifest = _manifest([entry])
    assert plan(manifest, tmp_path, FakeFetcher()) == 0
    target = tmp_path / entry["dest"]
    assert capsys.readouterr().out.splitlines() == [f"SKIP\t{target}"]


@pytest.mark.spec_exempt("structural: the CLI surface the shell driver calls")
def test_plan_reports_an_absent_entry_as_a_fetch_with_its_url(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    entry = _entry([PRIMARY])
    assert plan(_manifest([entry]), tmp_path, FakeFetcher()) == 0
    assert capsys.readouterr().out.splitlines() == [
        f"FETCH\t{tmp_path / entry['dest']}\t{PRIMARY}"
    ]


@pytest.mark.spec_exempt("structural: the CLI surface the shell driver calls")
def test_plan_exits_non_zero_before_emitting_any_transfer_when_an_entry_aborts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = _entry()
    _place(tmp_path, bad, b"somebody else's bytes")
    absent: Entry = {**_entry(), "dest": "controlnet/other.onnx"}
    assert plan(_manifest([bad, absent]), tmp_path, FakeFetcher()) == 1
    captured = capsys.readouterr()
    assert "FETCH" not in captured.out
    assert bad["dest"] in captured.err


ESCAPES = "../../etc/cron.d/payload"
ABSOLUTE = "/etc/cron.d/payload"


@pytest.mark.spec(
    "model-provisioning:immutable-pins:an-escaping-destination-is-refused"
)
def test_a_destination_climbing_out_of_the_models_root_is_refused(
    tmp_path: Path,
) -> None:
    entry: Entry = {**_entry(), "dest": ESCAPES}
    decision = decide(entry, tmp_path, FakeFetcher())
    assert decision.action == "abort"
    assert ESCAPES in decision.reason


@pytest.mark.spec(
    "model-provisioning:immutable-pins:an-escaping-destination-is-refused"
)
def test_an_absolute_destination_is_refused(tmp_path: Path) -> None:
    entry: Entry = {**_entry(), "dest": ABSOLUTE}
    decision = decide(entry, tmp_path, FakeFetcher())
    assert decision.action == "abort"
    assert ABSOLUTE in decision.reason


@pytest.mark.spec(
    "model-provisioning:immutable-pins:an-escaping-destination-is-refused"
)
def test_an_escaping_destination_is_refused_before_the_pre_flight(
    tmp_path: Path,
) -> None:
    fetcher = FakeFetcher()
    decide({**_entry(), "dest": ESCAPES}, tmp_path, fetcher)
    assert fetcher.asked == []


@pytest.mark.spec(
    "model-provisioning:immutable-pins:an-escaping-destination-is-refused"
)
def test_the_plan_line_carries_the_already_resolved_destination(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    entry = _entry([PRIMARY])
    assert plan(_manifest([entry]), tmp_path, FakeFetcher()) == 0
    target = tmp_path / entry["dest"]
    assert capsys.readouterr().out.splitlines() == [f"FETCH\t{target}\t{PRIMARY}"]


MALFORMED = [
    "https://huggingface.co/a/mirror/resolve/main/model.onnx",
    "https://huggingface.co/a/mirror/resolve/" + "0" * 40 + "/mo del.onnx",
    "https://huggingface.co/a/mirror/resolve/" + "0" * 40 + "/m.onnx\nhttp://evil",
    "file:///etc/passwd",
]


@pytest.mark.spec(
    "model-provisioning:immutable-pins:a-malformed-source-is-refused-at-runtime"
)
@pytest.mark.parametrize("source", MALFORMED)
def test_a_source_that_is_not_a_pinned_whitespace_free_url_is_refused(
    tmp_path: Path, source: str
) -> None:
    decision = decide(_entry([source]), tmp_path, FakeFetcher())
    assert decision.action == "abort"
    assert source in decision.reason


@pytest.mark.spec(
    "model-provisioning:immutable-pins:a-malformed-source-is-refused-at-runtime"
)
def test_a_malformed_source_is_never_offered_to_the_pre_flight(
    tmp_path: Path,
) -> None:
    fetcher = FakeFetcher()
    decide(_entry([MALFORMED[0], PRIMARY]), tmp_path, fetcher)
    assert fetcher.asked == [PRIMARY]


@pytest.mark.spec(
    "model-provisioning:immutable-pins:an-entry-with-no-sources-is-refused"
)
def test_an_entry_declaring_no_sources_is_refused_by_name(tmp_path: Path) -> None:
    decision = decide(_entry([]), tmp_path, FakeFetcher())
    assert decision.action == "abort"
    assert "no source" in decision.reason
    # an entry that offered nothing and an entry whose every offer was refused
    # are different failures with different fixes
    assert "rejected" not in decision.reason
