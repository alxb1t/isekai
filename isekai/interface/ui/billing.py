"""What may be billing, read from gpunit's own records under `.gpunit/` (D7).

gpunit records each pod and window volume it creates; reading those records adds
no state to disagree with them. gpunit is asked for its status only at start,
every half minute while a session runs or an alert is open, and on Check again.

```
pod or pending, no session running    ─▶ the pod alert; Render disabled
volume, its end in the future          ─▶ the quiet item, until `ends`
volume past its end · volume.pending   ─▶ the band
the job's open or close went unanswered ─▶ the band, until gpunit holds no volume
```
"""

import json
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from isekai.boundary.gpu import Volume
from isekai.interface.ui.events import Broadcast

# How often gpunit is asked while a session runs or an alert is open, in seconds.
INTERVAL_S = 30.0


def utc_now() -> str:
    """Return now in gpunit's form, which orders as its strings do."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def read(records: Path, *, running: bool, raised: bool, now: str) -> dict[str, Any]:
    """Return what gpunit's records under `records` say may be billing.

    `running` is whether a session runs, whose own pod is not an alert; `raised`
    is a volume alert the job raised.
    e.g. a `pod` record and no session -> {"pod": True, "volume": None}
    """
    pod = (records / "pod").exists() or (records / "pending").exists()
    volume: dict[str, Any] | None = None
    held = records / "volume"
    if held.exists():
        ends = _ends(held)
        past = ends is None or ends <= now
        volume = {"state": "band" if past or raised else "open", "ends": ends}
    elif (records / "volume.pending").exists() or raised:
        volume = {"state": "band", "ends": None}
    return {"pod": pod and not running, "volume": volume}


def _ends(path: Path) -> str | None:
    """Return the window's recorded end, or None for a record that does not say."""
    try:
        ends = json.loads(path.read_text(encoding="utf-8")).get("ends")
    except (OSError, ValueError, AttributeError):
        return None
    return ends if isinstance(ends, str) else None


class Billing:
    """The billing state the page shows, and when gpunit is asked again."""

    def __init__(
        self,
        volume: Volume,
        log: Path,
        broadcast: Broadcast,
        running: Callable[[], bool],
        *,
        now: Callable[[], str] = utc_now,
    ) -> None:
        """Read `volume`'s records, asking gpunit through it; append to `log`."""
        self._volume = volume
        self._log = log
        self._broadcast = broadcast
        self._running = running
        self._now = now
        self._raised = False
        self._lock = threading.Lock()
        self._stop = threading.Event()

    def state(self) -> dict[str, Any]:
        """Return the billing state from the records as they are now."""
        with self._lock:
            raised = self._raised
        return read(
            self._volume.records,
            running=self._running(),
            raised=raised,
            now=self._now(),
        )

    def alerting(self) -> bool:
        """Return whether a pod may be billing or a volume is past its window."""
        found = self.state()
        return found["pod"] or (found["volume"] or {}).get("state") == "band"

    def raise_volume(self) -> None:
        """Raise the volume alert: the job's open or close went unanswered."""
        with self._lock:
            self._raised = True
        self.publish()

    def check(self) -> dict[str, Any]:
        """Ask gpunit, then read its records; an alert clears only on their word."""
        self._volume.status(self._log)
        records = self._volume.records
        with self._lock:
            if self._raised and not any(
                (records / name).exists() for name in ("volume", "volume.pending")
            ):
                self._raised = False
        return self.publish()

    def publish(self) -> dict[str, Any]:
        """Tell every page the billing state, and return it."""
        found = self.state()
        self._broadcast.publish("billing", found)
        return found

    def watch(self, interval: float = INTERVAL_S) -> threading.Thread:
        """Ask gpunit once now, then every `interval` while a session or alert is."""

        def loop() -> None:
            self.check()
            while not self._stop.wait(interval):
                if self._running() or self.alerting():
                    self.check()

        thread = threading.Thread(target=loop, daemon=True)
        thread.start()
        return thread

    def close(self) -> None:
        """Stop asking."""
        self._stop.set()
