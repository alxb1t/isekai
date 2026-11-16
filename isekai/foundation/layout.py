"""A run's numbering and completion, its seeds and its edit files.

The version numbers a directory holds and the one it takes next, the paths of a
flow's sheets and approvals, the seeds a render's file is named for, and the files
an edit writes beside its source. `run.py` re-exports each name; a module outside
the foundation imports them from there.

Stdlib only, and on `python -m isekai`'s import graph.
"""

import os
import re
from collections.abc import Iterable
from pathlib import Path

from isekai.foundation.artifacts import SEED_RANGE
from isekai.foundation.names import (
    APPROVED,
    ARTIFACT,
    FRAME_NAME,
    OUTPUTS,
    REVIEW,
    SHEETS,
)
from isekai.foundation.refusal import Refusal
from isekai.foundation.rundir import Run

# --- numbering and completion -------------------------------------------------


def versions(directory: Path) -> list[int]:
    """Return the artifact version numbers present in `directory`, ascending.

    A listing, not a read: error records are excluded by their own pattern, and a
    partial write is excluded because it is not named like an artifact at all.
    """
    if not directory.is_dir():
        return []
    found = {
        int(match.group("version"))
        for name in os.listdir(directory)
        if (match := ARTIFACT.match(name))
    }
    return sorted(found)


def latest(directory: Path) -> int | None:
    """Return the highest version present in `directory`, or None if it is empty."""
    numbered = versions(directory)
    return numbered[-1] if numbered else None


def next_version(directory: Path) -> int:
    """Return the number the next artifact written into `directory` takes.

    Refuse when no artifact's name can spell it.
    e.g. a directory holding 999.json -> Refusal
    """
    number = (latest(directory) or 0) + 1
    if not is_version(number):
        where = f"{directory.parent.name}/{directory.name}"
        raise Refusal(
            f"{where} holds version {number - 1}, the last a three-digit name "
            f"can spell; move {where} out of the run, then run the command again"
        )
    return number


def artifact_name(version: int, label: str | None = None) -> str:
    """Return the filename an artifact takes, with its optional approval label."""
    return f"{version:03d}.json" if label is None else f"{version:03d}.{label}.json"


def is_version(number: int) -> bool:
    """Return whether `number` is one an artifact's name can spell.

    e.g. 2 -> True, 0 -> False, 1000 -> False
    """
    return number > 0 and ARTIFACT.fullmatch(artifact_name(number)) is not None


def approval_of(run: Run, flow: str, version: int) -> Path:
    """Return the path of `flow`'s approval numbered `version` in `run`."""
    return run.directory(flow, REVIEW) / artifact_name(version, APPROVED)


def sheet_of(run: Run, flow: str, version: int) -> Path:
    """Return the path of `flow`'s sheet numbered `version` in `run`."""
    return run.directory(flow, SHEETS) / artifact_name(version)


def group_of(run: Run, flow: str, version: int) -> Path:
    """Return the outputs group the approval numbered `version` renders into."""
    return run.directory(flow, OUTPUTS, f"{version:03d}")


# A version as a filename spells it: ASCII digits alone, since `str.isdigit`
# also passes a superscript `int` cannot read.
_DIGITS = re.compile(r"[0-9]+")

# The most digits a seed is spelled in, so a longer one is refused unread.
_SEED_DIGITS = len(str(SEED_RANGE[-1]))


def is_seed(text: str) -> bool:
    """Return whether `text` spells a seed as a render's file is named for it.

    The canonical ASCII decimal of a seed the sampler takes, alone: a padded, a
    superscript or an out-of-range spelling names no render.
    e.g. "42" -> True; "0042", "²", "", "9" * 300 -> False
    """
    return (
        len(text) <= _SEED_DIGITS
        and _DIGITS.fullmatch(text) is not None
        and str(int(text)) == text
        and int(text) in SEED_RANGE
    )


def _laid_out(path: Path) -> bool:
    """Return whether `path` names a place in an outputs group of a run with a frame."""
    group = path.absolute().parent
    return (
        len(group.name) == 3
        and _DIGITS.fullmatch(group.name) is not None
        and group.parent.name == OUTPUTS
        and (group.parent.parent.parent / FRAME_NAME).is_file()
    )


# An edit's image is `<seed>.edit-<k>.png`: the seed of the render it descends
# from, then its number in that seed's chain. Its stem is no seed, so no render
# listing reads it as one.
EDIT_STEM = re.compile(r"^(?P<seed>[0-9]+)\.edit-(?P<k>[1-9][0-9]*)$")

# An edit's files beside its image, after the stem: the composite it was made from,
# its record and, for a placed tattoo, the placement it was made from.
EDIT_COMPOSITE = ".composite.png"
EDIT_RECORD = ".json"
EDIT_PLACEMENT = ".placement.json"


def is_edit_file(name: str) -> bool:
    """Return whether `name` is a file an edit writes beside its source.

    The image, record, composite and placement of an edit of a render's seed.
    e.g. "42.edit-1.placement.json" -> True; "42.edit-0.png", "x.edit-1.json" -> False
    """
    for suffix in (EDIT_COMPOSITE, EDIT_PLACEMENT, EDIT_RECORD, ".png"):
        named = EDIT_STEM.fullmatch(name.removesuffix(suffix))
        if name.endswith(suffix) and named and is_seed(named["seed"]):
            return True
    return False


def edit_stem(seed: int, k: int) -> str:
    """Return the stem every file of edit `k` of `seed` starts with.

    e.g. (42, 2) -> "42.edit-2"
    """
    return f"{seed}.edit-{k}"


def edit_files(group: Path, seed: int, k: int) -> tuple[Path, Path, Path]:
    """Return the image, record and composite of edit `k` of `seed`, in `group`.

    e.g. (group, 42, 1) -> (42.edit-1.png, 42.edit-1.json, 42.edit-1.composite.png)
    """
    stem = group / edit_stem(seed, k)
    return (
        stem.with_name(f"{stem.name}.png"),
        stem.with_name(f"{stem.name}{EDIT_RECORD}"),
        stem.with_name(f"{stem.name}{EDIT_COMPOSITE}"),
    )


def placement_file(group: Path, seed: int, k: int) -> Path:
    """Return the placement record of edit `k` of `seed`, in `group`.

    e.g. (group, 42, 1) -> 42.edit-1.placement.json
    """
    return group / f"{edit_stem(seed, k)}{EDIT_PLACEMENT}"


def edit_numbers(group: Path, seed: int) -> list[int]:
    """Return the numbers of `seed`'s edits that hold any file in `group`, ascending.

    A listing: an image, a record, a composite or a placement each holds its number.
    e.g. a group holding 42.edit-1.json and 42.edit-3.png -> [1, 3]
    """
    if not group.is_dir():
        return []
    found: set[int] = set()
    for name in os.listdir(group):
        for suffix in (".png", EDIT_COMPOSITE, EDIT_PLACEMENT, EDIT_RECORD):
            match = EDIT_STEM.fullmatch(name.removesuffix(suffix))
            if name.endswith(suffix) and match and int(match["seed"]) == seed:
                found.add(int(match["k"]))
                break
    return sorted(found)


def next_edit(group: Path, seed: int) -> int:
    """Return the number the next edit of `seed` takes in `group`."""
    numbered = edit_numbers(group, seed)
    return numbered[-1] + 1 if numbered else 1


def delete_edits(group: Path, seed: int, numbers: Iterable[int]) -> list[Path]:
    """Delete each file of the edits `numbers` of `seed` in `group`; return those gone.

    Each edit's image goes first, then its record, its placement and its composite, so
    a delete cut short leaves a request that reads as pending rather than an image no
    record explains.
    e.g. (group, 42, [1]) -> [42.edit-1.png, 42.edit-1.json, 42.edit-1.composite.png]
    """
    deleted: list[Path] = []
    for number in numbers:
        image, record, composite = edit_files(group, seed, number)
        for path in (image, record, placement_file(group, seed, number), composite):
            if path.is_file():
                path.unlink()
                deleted.append(path)
    return deleted


def edit_at(image: Path) -> tuple[Run, str, int, int, int]:
    """Return the run, flow, approval, seed and number an edit image's path names.

    The image is on disk, or its record is: a pending edit has no image yet.
    e.g. runs/0d4b…_ada/summon-anime-wai/outputs/001/42.edit-2.png
         -> (that run, "summon-anime-wai", 1, 42, 2)
    """
    group = image.absolute().parent
    run_directory = group.parent.parent.parent
    named = EDIT_STEM.match(image.stem) if image.suffix == ".png" else None
    present = image.is_file() or image.with_suffix(EDIT_RECORD).is_file()
    if (
        named is None
        or not is_seed(named.group("seed"))
        or not (present and _laid_out(image))
    ):
        raise Refusal(
            "is not an edit's image; give the path of one, "
            f"<run>/<flow>/{OUTPUTS}/<NNN>/<seed>.edit-<k>.png"
        )
    return (
        Run(run_directory.name, run_directory),
        group.parent.parent.name,
        int(group.name),
        int(named.group("seed")),
        int(named.group("k")),
    )


def latest_artifact(directory: Path, label: str | None = None) -> Path | None:
    """Return the highest artifact in `directory` carrying `label`, or None.

    The run owns the layout, so *which file is the current one* is answered here
    rather than by each reader globbing for it. A glob would also be wrong: an
    error record is `NNN.error.<attempt>.<kind>.json`, which `*.json` matches and
    `ARTIFACT` does not, so a failed second attempt beside a good first artifact
    would sort last and be read as one.
    """
    numbered = [
        version
        for version in versions(directory)
        if (directory / artifact_name(version, label)).is_file()
    ]
    return directory / artifact_name(numbered[-1], label) if numbered else None


def is_approved(name: str) -> bool:
    """Say whether a filename is an approved artifact, without opening anything."""
    match = ARTIFACT.match(name)
    return match is not None and match.group("label") == "approved"


def approved_versions(directory: Path) -> list[int]:
    """Return the versions in `directory` whose filenames say they are approved."""
    if not directory.is_dir():
        return []
    return sorted(
        int(match.group("version"))
        for name in os.listdir(directory)
        if is_approved(name) and (match := ARTIFACT.match(name))
    )
