"""Writing bytes to a path so that a reader never sees a half-written file.

This takes a path and bytes and knows nothing about runs -- which is why it is
here rather than in `run.py`, where it was written. Two consumers already call it
by name: the run directory writes every artifact through it, and `generate.py`
writes the rendered PNG through it, a file that is not JSON and is not numbered by
the run's artifact convention.

**The run's JSON convention stayed behind.** `run.write_json` encodes `indent=2`
and a trailing newline -- a run's artifact format, not a write primitive -- and a
module that imports nothing first-party cannot carry it.

Stdlib only, and on `python -m isekai`'s import graph.
"""

import os
import tempfile
from pathlib import Path


def write_atomically(path: Path, body: bytes) -> None:
    """Write `body` to `path` through a temporary file on the same filesystem.

    The temporary file is created in the destination's own directory, so the
    replace is a rename within one filesystem and is atomic. It is also named
    outside the artifact patterns, so a crash between the write and the replace
    leaves something a listing does not mistake for an artifact.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".partial"
    )
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(body)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
