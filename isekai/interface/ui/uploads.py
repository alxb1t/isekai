"""Hold the upload session: `Reader` and `Imports`.

`Reader` reads one open import's uploads, and `Imports` holds each open import of a
library. Both call the import stage only as `importing.<name>`, so a test that
replaces `importing.read` or `importing.commit` reaches them. It imports no web
framework.
"""

import queue
import shutil
import tempfile
import threading
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from isekai.foundation.refusal import Refusal
from isekai.pipeline import importing


def _record(
    name: str, state: importing.Upload, fields: Mapping[str, object]
) -> dict[str, Any]:
    return {"file": name, "state": state, **fields}


class Reader:
    """Read a staging folder's uploads one at a time, in the order they landed.

    Each upload is named by its own id, so two of one name keep their own states,
    and held in a dot-named folder until its turn. Each change of its state is
    published: `waiting`, `converting`, then a `Staged` state or `refused`.
    e.g. `{"upload": "u1", "file": "a.heic", "state": "converted", "name": "a.jpg"}`
    """

    def __init__(
        self, staging: Path, limit: int, publish: Callable[[dict[str, Any]], None]
    ) -> None:
        """Start the thread that reads what `put` holds."""
        self._staging = staging
        self._limit = limit
        self._publish = publish
        self._lock = threading.Lock()
        self._files: dict[str, dict[str, Any]] = {}
        self._queue: queue.Queue[tuple[str, str, Path] | None] = queue.Queue()
        self._uploads = 0
        self._sealed = False
        self._stopped = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def put(self, name: str, body: bytes) -> dict[str, Any]:
        """Hold an upload for reading; return its id, its name and `waiting`."""
        importing.refuse_name(name)
        record = _record(name, "waiting", {})
        # Checked and named under the lock `seal` takes, before the disk is
        # touched: no upload lands once a commit has sealed the reader, and one
        # named before holds `seal` off as `waiting` until it is read.
        with self._lock:
            if self._stopped:
                raise _closed(name)
            if self._sealed:
                raise Refusal(
                    f"{name}: Import is already committing this import; once the "
                    "collection's hub opens, add it with Add sources"
                )
            self._uploads += 1
            upload = f"u{self._uploads}"
            self._files[upload] = record
        try:
            held = Path(tempfile.mkdtemp(dir=self._staging, prefix=".upload-")) / name
            try:
                held.write_bytes(body)
            except BaseException:
                shutil.rmtree(held.parent, ignore_errors=True)
                raise
        except Exception as failed:
            # A folder a cancel deleted, or a full disk, refuses this upload alone.
            refusal = str(_closed(name)) if self._stopped else _failed(name, failed)
            self._set(upload, name, "refused", {"refusal": refusal})
            raise Refusal(refusal) from failed
        state = {"upload": upload, **record}
        self._publish(state)
        self._queue.put((upload, name, held))
        return state

    def files(self) -> dict[str, dict[str, Any]]:
        """Return every upload's name and state, by its id."""
        with self._lock:
            return {upload: dict(state) for upload, state in self._files.items()}

    def remove(self, name: str) -> None:
        """Delete the file read as `name` and forget its upload; refuse once sealed.

        A skipped upload staged nothing of its own, so it is not one to remove,
        and one skipped as a copy of `name` is forgotten with it: the sheet hands
        the file to a copy it still shows rather than remove it.
        """
        importing.refuse_name(name)
        # Under the lock `seal` takes, so no commit walks the folder mid-removal.
        with self._lock:
            if self._sealed:
                raise Refusal(
                    f"{name}: Import is already committing this import; once the "
                    "collection's hub opens, delete it from the collection's sources/"
                )
            uploads = [
                upload
                for upload, one in self._files.items()
                if one.get("name") == name and one["state"] in _STAGED
            ]
            if not uploads:
                raise Refusal(f"{name}: not staged in this import; nothing to remove")
            uploads += [
                upload
                for upload, one in self._files.items()
                if one.get("copy_of") == name
            ]
            with importing.CLAIM:
                (self._staging / name).unlink(missing_ok=True)
            for upload in uploads:
                del self._files[upload]

    def seal(self) -> None:
        """Refuse while sealed or a file is unread, else refuse uploads until `unseal`.

        Refusing a second seal keeps a second commit of one import from running
        beside the first, so only the commit that sealed the reader unseals it.
        """
        with self._lock:
            if self._sealed:
                raise Refusal(
                    "Import is already committing this import; wait for it to finish"
                )
            states = self._files.values()
            unread = sum(one["state"] in _UNREAD for one in states)
            if unread:
                raise Refusal(
                    f"{len(states) - unread} of {len(states)} files are read; wait "
                    "for the rest, then import"
                )
            self._sealed = True

    def unseal(self) -> None:
        """Take uploads again, after a commit that was refused."""
        with self._lock:
            self._sealed = False

    def halt(self) -> None:
        """Ask the thread to stop once the file being read is done."""
        with self._lock:
            self._stopped = True
        self._queue.put(None)

    def stop(self) -> None:
        """Stop reading and wait for the file being read; the rest stay unread."""
        self.halt()
        self._thread.join()

    def _run(self) -> None:
        """Read each held upload in turn until stopped."""
        while (item := self._queue.get()) is not None and not self._stopped:
            upload, name, held = item
            self._set(upload, name, "converting", {})
            try:
                staged = importing.read(held, self._staging, self._limit)
                state: importing.Upload = staged.state
                fields: Mapping[str, object] = {
                    "name": staged.name,
                    "carries": list(staged.carries),
                    "copy_of": staged.copy_of,
                }
            except Refusal as refused:
                state, fields = "refused", {"refusal": str(refused)}
            except Exception as failed:
                # Anything else, a full disk or a decoder's own error, refuses this
                # file alone: the thread lives on to read the next.
                state, fields = "refused", {"refusal": _failed(name, failed)}
            finally:
                shutil.rmtree(held.parent, ignore_errors=True)
            self._set(upload, name, state, fields)

    def _set(
        self,
        upload: str,
        name: str,
        state: importing.Upload,
        fields: Mapping[str, object],
    ) -> None:
        """Record and publish `upload`'s `state`, uploaded as `name`."""
        record = _record(name, state, fields)
        with self._lock:
            self._files[upload] = record
        self._publish({"upload": upload, **record})


# The states of a file the reader has not finished with.
_UNREAD = frozenset({"waiting", "converting"})

# The states of a file read into the staging folder under its own name.
_STAGED = frozenset({"ready", "converted", "not cleaned"})


def _closed(name: str) -> Refusal:
    """Return the refusal of an upload `name` to an import that is closed."""
    return Refusal(
        f"{name}: its import is closed; close the sheet and choose the files again"
    )


def _failed(name: str, failed: Exception) -> str:
    """Return the refusal of `name`, whose reading raised `failed`."""
    return (
        f"{name}: reading it failed ({type(failed).__name__}: {failed}); free disk "
        "space if it is full, then add it again, or export a JPEG copy and add that"
    )


class Imports:
    """Every open import of a library, each a staging folder and its reader.

    A reader starts when its import opens. It is sealed before a commit touches
    the folder, so no upload lands in it, and stops before a cancel does.
    """

    def __init__(
        self, library: Path, limit: int, publish: Callable[[str, dict[str, Any]], None]
    ) -> None:
        """Hold no import yet; `publish` takes an import's id and a file's state."""
        self._library = library
        self._limit = limit
        self._publish = publish
        self._lock = threading.Lock()
        self._open: dict[str, tuple[Path, Reader]] = {}

    def open(self) -> str:
        """Open an import: a new staging folder and its reader; return its id."""
        folder = importing.stage(self._library)
        staged = folder.name
        reader = Reader(folder, self._limit, lambda one: self._publish(staged, one))
        with self._lock:
            self._open[staged] = (folder, reader)
        return staged

    def folder(self, staged: str) -> Path:
        """Return the staging folder of the open import `staged`, or refuse."""
        return self._named(staged)[0]

    def reader(self, staged: str) -> Reader:
        """Return the reader of the open import `staged`, or refuse."""
        return self._named(staged)[1]

    def commit(
        self, staged: str, name: str, as_is: Iterable[str] = (), *, add: bool = False
    ) -> importing.Committed:
        """Commit import `staged` as `commit` does, once every file is read.

        Its reader is sealed first and unsealed on a refusal, so the sheet can add
        more and import again.
        """
        folder, reader = self._named(staged)
        reader.seal()
        try:
            done = importing.commit(folder, self._library, name, as_is, add=add)
        except BaseException:
            reader.unseal()
            raise
        self._close(staged)
        return done

    def cancel(self, staged: str) -> None:
        """Stop import `staged`'s reader, then delete its staging folder."""
        folder = self._close(staged)
        importing.cancel(folder)

    def close(self) -> None:
        """Stop every reader, each finishing the file it is reading."""
        with self._lock:
            readers = [reader for _, reader in self._open.values()]
            self._open.clear()
        for reader in readers:
            reader.halt()
        for reader in readers:
            reader.stop()

    def _named(self, staged: str) -> tuple[Path, Reader]:
        """Return the folder and reader of the open import `staged`, or refuse."""
        with self._lock:
            found = self._open.get(staged)
        if found is None:
            raise Refusal(
                f"no import {staged!r} is open; close the sheet and choose the "
                "files again"
            )
        return found

    def _close(self, staged: str) -> Path:
        """Forget import `staged` and stop its reader; return its folder."""
        folder, reader = self._named(staged)
        with self._lock:
            self._open.pop(staged, None)
        reader.stop()
        return folder
