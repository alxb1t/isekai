"""A delete's one owner: a render's or an edit's files, thumbnails and approval.

`delete_render` and `delete_edit` name the thumbnail of every image that goes while it
is a file, drop them, delete the files and, for a render, the approval its last render
leaves (D72), then unlink any named thumbnail that came back. The bodies they call are
here too, bound back at the stages that held them.

Stdlib only, and on `python -m isekai`'s import graph.
"""

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import NamedTuple

from isekai.foundation.artifacts import EDIT_FILE, read
from isekai.foundation.library import named_thumbnail
from isekai.foundation.run import (
    DESCRIPTION,
    OUTPUTS,
    PHOTO,
    PROMPTS,
    REVIEW,
    SHEETS,
    SOURCES,
    Run,
    approval_of,
    approved_versions,
    artifact_name,
    attempts,
    current_draft,
    delete_edits,
    edit_at,
    edit_files,
    edit_numbers,
    failures_alone,
    group_of,
    render_record,
    rendered_at,
    source_copy,
    version_of,
    versions,
)


def discard_render(image: Path) -> list[Path]:
    """Delete a render's image, its record, its edits, and a group left with failures.

    Every edit of the seed goes with it, images, records and composites, before the
    group is tested: an edit left in the group would keep it, and the approval, alive
    with no render to show. A group left holding failure records alone goes too, those
    records with it; return every path deleted, absolute. The image goes first, so a
    discard cut short leaves a record alone, which reads as unrendered, as a render
    cut short does. A path naming no render is refused, nothing deleted.
    e.g. outputs/001/42.png -> [.../001/42.png, .../001/42.render.json]
    e.g. outputs/001/7.png, the last beside 001.error.1.transient.json
    -> [.../7.png, .../7.render.json, .../001.error.1.transient.json, .../001]
    """
    seed = rendered_at(image).seed
    image = image.absolute()
    group = image.parent
    record = render_record(group, seed)
    image.unlink()
    deleted = [image]
    if record.is_file():
        record.unlink()
        deleted.append(record)
    deleted += delete_edits(group, seed, edit_numbers(group, seed))
    records = failures_alone(group)
    if records is not None:
        for path in records:
            path.unlink()
        group.rmdir()
        deleted += [*records, group]
    return deleted


def _holds_render(run: Run, flow: str, version: int) -> bool:
    """Return whether approval `version`'s group holds more than failure records."""
    group = group_of(run, flow, version)
    return group.exists() and failures_alone(group) is None


def withdraw(run: Run, flow: str, version: int) -> list[Path]:
    """Delete approval `version` once it holds no render; return what went, absolute.

    With it go each older approval whose group is gone or holds failure records
    alone, each with its prompt, failure records, group and source copy, and,
    where it was the newest, the draft waiting above it and that draft's source
    copy. A flow left with no approval keeps only its directory, its assignment:
    every path under sheets/, review/, prompts/ and sources/ goes, and under its
    own captions/, wd14/ and tags/, each where photo/ holds that kind, then those
    directories, then outputs/ when empty. Nothing is read, so nothing refuses.
    e.g. (run, f, 2), 001 rendered -> [f/prompts/002.json, f/review/002.approved.json]
    """
    directory = run.directory(flow, REVIEW)
    approved = approved_versions(directory)
    if version not in approved or _holds_render(run, flow, version):
        return []
    going = [
        one
        for one in approved
        if one == version or (one < version and not _holds_render(run, flow, one))
    ]
    prompts = run.directory(flow, PROMPTS)
    made: list[Path] = []
    for one in going:
        group = group_of(run, flow, one)
        made += [
            prompts / artifact_name(one),
            *(attempt.path for attempt in attempts(prompts, one)),
            *(failures_alone(group) or []),
            group,
            source_copy(run, flow, one),
            approval_of(run, flow, one),
        ]
    if version == approved[-1] and (draft := current_draft(directory)) is not None:
        made += [draft, source_copy(run, flow, version_of(draft))]
    gone = [path.absolute() for path in made if path.exists()]
    for path in gone:
        if path.is_dir():
            path.rmdir()
        else:
            path.unlink()
    if len(going) < len(approved):
        return gone
    shared = [kind for kind in DESCRIPTION if versions(run.directory(PHOTO, kind))]
    for name in (SHEETS, REVIEW, PROMPTS, SOURCES, *shared):
        held = run.directory(flow, name)
        if not held.exists():
            continue
        for path in [*sorted(held.rglob("*"), reverse=True), held]:
            if path.is_dir():
                path.rmdir()
            else:
                path.unlink()
            gone.append(path.absolute())
    outputs = run.directory(flow, OUTPUTS)
    if outputs.is_dir() and not any(outputs.iterdir()):
        outputs.rmdir()
        gone.append(outputs.absolute())
    return gone


def _chain(group: Path, seed: int, number: int) -> list[int]:
    """Return edit `number` of `seed` and every edit whose source chain reaches it.

    An edit whose record cannot be read is refused, so a caller deletes nothing first.
    e.g. 42.edit-1, with 42.edit-2 made from it -> [1, 2]
    """
    sources: dict[int, str | None] = {}
    for held in edit_numbers(group, seed):
        record = edit_files(group, seed, held)[1]
        sources[held] = read(record, EDIT_FILE)["source"] if record.is_file() else None
    taken = {number}
    while grown := {
        held
        for held, source in sources.items()
        if held not in taken
        and source in {edit_files(group, seed, each)[0].name for each in taken}
    }:
        taken |= grown
    return sorted(taken)


def discard_edit(image: Path) -> list[Path]:
    """Delete an edit, pending or run, and every edit whose source chain reaches it.

    Return every path deleted, absolute. An edit whose record cannot be read is
    refused before anything is deleted, so a chain is never left half taken.
    e.g. 42.edit-1.png, with 42.edit-2 made from it -> both edits' three files
    """
    ref = edit_at(image)
    group = image.absolute().parent
    return delete_edits(group, ref.seed, _chain(group, ref.seed, ref.k))


class Deleted(NamedTuple):
    """What a delete removed: the run's files, then the library's thumbnails."""

    files: list[Path]
    thumbnails: list[Path]


def _edit_images(group: Path, seed: int, numbers: Iterable[int]) -> list[Path]:
    """Return the images of edits `numbers` of `seed` that are files, in order."""
    return [
        own
        for number in numbers
        if (own := edit_files(group, seed, number)[0]).is_file()
    ]


def _named(run: Run, images: Iterable[Path]) -> list[Path]:
    """Return where each of `images`' thumbnails sits, made or not.

    A run outside a collection has no library, so no thumbnail. The images must still
    be files: their bytes name the thumbnails.
    """
    names = (named_thumbnail(run, image) for image in images)
    return [name for name in names if name is not None]


def _unlinked(names: Iterable[Path]) -> list[Path]:
    """Delete each of `names` that is a file; return those, in order."""
    found = [name for name in names if name.is_file()]
    for name in found:
        name.unlink()
    return found


def _deleted(names: list[Path], delete: Callable[[], list[Path]]) -> Deleted:
    """Return what `delete` removed, with the thumbnails of `names` unlinked twice.

    Once before the files go, and once after, for a thumbnail a request rebuilt in
    between: it names an image that is gone, and nothing else would delete it.
    """
    dropped = _unlinked(names)
    files = delete()
    late = [name for name in _unlinked(names) if name not in dropped]
    return Deleted(files, [*dropped, *late])


def delete_render(image: Path) -> Deleted:
    """Delete a render, its edits, their thumbnails and the approval its last leaves.

    The path is checked first, so one naming no render deletes nothing. The thumbnails
    go while their images are files: the render's, then each edit's in number order.
    e.g. outputs/001/42.png, with 42.edit-1.png
    -> files [..., 42.png, ...], thumbnails [42, 42.edit-1]
    """
    ref = rendered_at(image)
    group = image.absolute().parent
    edits = _edit_images(group, ref.seed, edit_numbers(group, ref.seed))
    return _deleted(
        _named(ref.run, [image, *edits]),
        lambda: [*discard_render(image), *withdraw(ref.run, ref.flow, ref.version)],
    )


def delete_edit(image: Path) -> Deleted:
    """Delete an edit and every edit made from it, with each one's thumbnail.

    An edit whose record cannot be read is refused before anything is deleted.
    e.g. 42.edit-1.png, with 42.edit-2 made from it -> thumbnails [edit-1, edit-2]
    """
    ref = edit_at(image)
    group = image.absolute().parent
    numbers = _chain(group, ref.seed, ref.k)
    return _deleted(
        _named(ref.run, _edit_images(group, ref.seed, numbers)),
        lambda: delete_edits(group, ref.seed, numbers),
    )
