"""What may be billing, read from gpunit's records, and when an alert clears.

gpunit is a double here: a `Volume` whose verbs write or delete record files in a
temporary `.gpunit/`, as gpunit would, and reach nothing.
"""

import json
from collections.abc import Sequence
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from isekai.boundary.gpu import Say, Seams, Volume  # noqa: E402
from isekai.interface.ui import HOST, events  # noqa: E402
from isekai.interface.ui.app import create_app  # noqa: E402
from isekai.interface.ui.billing import Billing, read  # noqa: E402
from tests.stages import bare_wiring  # noqa: E402

PORT = 8767
NOW = "2026-10-21T12:00:00Z"


def _volume(records: Path, asked: list[str]) -> Volume:
    """Return a gpunit double over `records`: it records each verb, changes nothing."""

    def run(argv: Sequence[str], say: Say) -> int:
        asked.append(" ".join(argv))
        return 0

    return Volume(run=run, records=records)


def _window(records: Path, ends: str) -> None:
    """Write gpunit's window record, ending at `ends`."""
    records.mkdir(parents=True, exist_ok=True)
    body = {"id": "v1", "datacenter": "EU-RO-1", "size_gb": 50, "ends": ends}
    (records / "volume").write_text(json.dumps(body))


@pytest.mark.spec("ui:billing:a-pod-record-is-an-alert")
def test_a_pod_record_with_no_session_is_an_alert_and_disables_render(
    tmp_path: Path,
) -> None:
    records = tmp_path / ".gpunit"
    records.mkdir()
    (records / "pod").write_text("{}")
    (tmp_path / "lib" / "b" / "sources").mkdir(parents=True)
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html>")
    wired = bare_wiring(
        runs_root=tmp_path / "lib" / "b" / "runs",
        session=Seams(environ={"RUNPOD_API_KEY": "k"}),
        volume=_volume(records, []),
    )
    app = create_app(
        tmp_path / "lib",
        wired,
        flows=("summon-anime-wai",),
        bundle=dist,
        wire=lambda runs: wired,
        host=HOST,
        port=PORT,
    )

    quote = TestClient(app, base_url=f"http://{HOST}:{PORT}").post(
        "/api/c/b/render/quote"
    )

    assert read(records, running=False, raised=False, now=NOW)["pod"] is True
    assert read(records, running=True, raised=False, now=NOW)["pod"] is False
    assert quote.json()["disabled"] == "A pod may still be billing."


@pytest.mark.spec("ui:billing:an-alert-clears-on-evidence")
def test_check_again_keeps_the_alert_while_gpunit_still_holds_the_pod(
    tmp_path: Path,
) -> None:
    records = tmp_path / ".gpunit"
    records.mkdir()
    (records / "pending").touch()
    asked: list[str] = []
    billing = Billing(
        _volume(records, asked),
        tmp_path / "log",
        events.Broadcast(),
        lambda: False,
        now=lambda: NOW,
    )
    billing.raise_volume()
    _window(records, "2026-10-21T13:00:00Z")

    still = billing.check()

    assert asked == ["status --json"]
    assert still["pod"] is True
    assert still["volume"] == {"state": "band", "ends": "2026-10-21T13:00:00Z"}
    (records / "pending").unlink()
    (records / "volume").unlink()
    assert billing.check() == {"pod": False, "volume": None}


@pytest.mark.spec("ui:billing:a-volume-past-its-window-takes-the-band")
def test_a_volume_past_its_recorded_end_takes_the_band(tmp_path: Path) -> None:
    records = tmp_path / ".gpunit"
    _window(records, "2026-10-21T13:00:00Z")
    before = read(records, running=False, raised=False, now=NOW)
    _window(records, "2026-10-21T11:00:00Z")

    after = read(records, running=False, raised=False, now=NOW)

    assert before["volume"] == {"state": "open", "ends": "2026-10-21T13:00:00Z"}
    assert after["volume"] == {"state": "band", "ends": "2026-10-21T11:00:00Z"}
    (records / "volume").unlink()
    (records / "volume.pending").touch()
    pending = read(records, running=False, raised=False, now=NOW)
    assert pending["volume"] == {"state": "band", "ends": None}
