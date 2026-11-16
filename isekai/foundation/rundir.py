"""`Run`, one photograph's directory and its frame, and `assign`.

A run is the directory a photograph becomes. `Run` reads its frame and the
photograph's copy, refusing a damaged one by name; `assign` creates or removes a
flow's directory in it. `run.py` re-exports each name; a module outside the
foundation imports them from there.

Stdlib only, and on `python -m isekai`'s import graph.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from isekai.foundation.artifacts import RUN_FILE, Frame, PhotoRecord, read, require
from isekai.foundation.names import FRAME_NAME, ID_DIGEST_CHARS, PHOTO
from isekai.foundation.refusal import Refusal

# The fields of the frame's photograph record, each with the shape it holds.
_PHOTO_FIELDS: tuple[tuple[str, type], ...] = (
    ("name", str),
    ("sha256", str),
    ("bytes", int),
    ("media_type", str),
)


@dataclass(frozen=True)
class Run:
    """One photograph's directory, and the frame that says what it is."""

    id: str
    path: Path

    @property
    def digest(self) -> str:
        """Return the digest prefix the identifier begins with, the run's short name."""
        return self.id[:ID_DIGEST_CHARS]

    @property
    def frame_path(self) -> Path:
        """Return the path of the run's frame."""
        return self.path / FRAME_NAME

    @property
    def _remedy(self) -> str:
        """Return the fix for a damaged frame."""
        # A stage verb given the run id cannot reach a run with no frame, while
        # `open_run` passes over one, so the path is what re-creates it.
        return f"delete {self.frame_path}, then offer the photograph again by its path"

    @property
    def frame(self) -> Frame:
        """Return the run's frame, refusing a version this build does not read."""
        return read(self.frame_path, RUN_FILE, remedy=self._remedy)

    @property
    def photo_record(self) -> PhotoRecord:
        """Return the frame's record of its photograph, refusing one missing a field.

        Each field is checked by name, so a hand-edited record is a refusal to
        whoever reads it rather than a `KeyError` three frames later.
        """
        frame = self.frame
        require(self.frame_path, frame, "photo", dict, self._remedy)
        record: Mapping[str, object] = {**frame["photo"]}
        for key, shape in _PHOTO_FIELDS:
            require(self.frame_path, record, key, shape, self._remedy)
        return frame["photo"]

    def _photo_record(self, key: str) -> str:
        """Return the frame's `photo[key]`, refusing by name a value not a string."""
        record: Mapping[str, object] = {**self.photo_record}
        require(self.frame_path, record, key, str, self._remedy)
        return str(record[key])

    @property
    def photo(self) -> Path:
        """Return the path of the photograph's copy inside the run.

        The name is a file's word, not a path: one that could leave the run is
        refused, or the run would serve and upload any image on the machine.
        """
        name = self._photo_record("name")
        if name in ("", ".", "..") or "/" in name or "\\" in name:
            raise Refusal(
                f"{FRAME_NAME}: names its photograph {name!r}, which is not one "
                f"plain filename; {self._remedy}"
            )
        path = self.path / name
        if path.is_symlink():
            raise Refusal(
                f"{FRAME_NAME}: its photograph {name!r} is a link, which could point "
                f"outside the run; {self._remedy}"
            )
        return path

    @property
    def flows(self) -> list[str]:
        """Return the flows this run holds work for, by identifier.

        The run owns the layout, so the fact that a flow's work is one directory
        directly under the run is stated here and asked for elsewhere rather than
        re-derived by each caller. `photo/` is the photograph's description, not a
        flow, and is left out.
        """
        if not self.path.is_dir():
            return []
        return sorted(
            path.name
            for path in self.path.iterdir()
            if path.is_dir() and path.name != PHOTO
        )

    def directory(self, *parts: str) -> Path:
        """Return a stage's directory inside this run, whether or not it exists.

        Deliberately does not create it: a command that refuses must leave the run
        exactly as it found it, and an empty directory nobody asked for is a
        change. Every writer here creates its parent on the way past.
        """
        return self.path.joinpath(*parts)


def assign(run: Run, flow: str, *, remove: bool = False) -> bool:
    """Create `flow`'s empty directory in `run`; with `remove`, delete it while empty.

    Return whether the run changed. A run holding a flow's directory is assigned
    to it, so a tick is the layout's own fact; an untick never deletes work.
    """
    if flow == PHOTO:
        raise Refusal(
            f"{PHOTO}: a name a run keeps for its photograph's description, "
            "never a flow"
        )
    directory = run.directory(flow)
    if not remove:
        if directory.is_dir():
            return False
        directory.mkdir()
        return True
    if not directory.is_dir():
        return False
    if any(directory.iterdir()):
        raise Refusal(
            f"{run.id}: {flow} holds work, so it stays assigned; to unassign it, "
            f"delete {run.id}/{flow}/ by hand"
        )
    directory.rmdir()
    return True
