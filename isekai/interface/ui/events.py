"""The page's event stream: a snapshot on connect, then each change as it happens.

Server-Sent Events over plain HTTP, one way, from the server to every open page.
A job publishes; each connection holds its own queue, so a slow page delays no
other. No web framework, so the stream is tested with no server involved.

```
connect ─▶ snapshot {job, hub?} ─▶ job {…} ─▶ cell {…} ─▶ … ─▶ (keep-alive)
```
"""

import json
import queue
import threading
from collections.abc import Callable, Iterator
from typing import Any

# How long a quiet stream waits before it sends a comment, so a proxy or the
# browser keeps the connection open.
HEARTBEAT = 15.0

Event = tuple[str, dict[str, Any]]

# The event that ends a stream rather than reaching the page.
CLOSE = "close"


class Broadcast:
    """Every open stream's queue; a published event reaches each of them."""

    def __init__(self) -> None:
        """Start with no stream open."""
        self._lock = threading.Lock()
        self._queues: list[queue.Queue[Event]] = []

    def subscribe(self) -> "queue.Queue[Event]":
        """Return a new queue that every later event is put on."""
        found: queue.Queue[Event] = queue.Queue()
        with self._lock:
            self._queues.append(found)
        return found

    def unsubscribe(self, found: "queue.Queue[Event]") -> None:
        """Stop putting events on `found`."""
        with self._lock:
            if found in self._queues:
                self._queues.remove(found)

    def publish(self, kind: str, data: dict[str, Any]) -> None:
        """Put one event on every open stream's queue."""
        with self._lock:
            for one in self._queues:
                one.put((kind, data))

    def close(self) -> None:
        """End every open stream: the server is stopping."""
        self.publish(CLOSE, {})


def frame(kind: str, data: dict[str, Any]) -> str:
    """Return one event as the stream writes it.

    e.g. ("job", {"state": "done"}) -> an `event: job` line, its `data:`, a blank line
    """
    return f"event: {kind}\ndata: {json.dumps(data)}\n\n"


def stream(
    broadcast: Broadcast,
    snapshot: Callable[[], dict[str, Any]],
    *,
    batch: str | None = None,
    heartbeat: float = HEARTBEAT,
) -> Iterator[str]:
    """Yield the snapshot, then every event for `batch`, until the reader stops.

    Subscribed before the snapshot is read, so nothing between the two is lost.
    A `cell` event of another batch is not sent; every `job` event is.
    """
    found = broadcast.subscribe()
    try:
        yield frame("snapshot", snapshot())
        while True:
            try:
                kind, data = found.get(timeout=heartbeat)
            except queue.Empty:
                yield ": keep-alive\n\n"
                continue
            if kind == CLOSE:
                return
            if kind == "cell" and data.get("batch") != batch:
                continue
            yield frame(kind, data)
    finally:
        broadcast.unsubscribe(found)
