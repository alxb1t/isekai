"""The drafts' verbs: `draft` and `discard`."""

import argparse
from functools import cache
from pathlib import Path

from isekai.foundation.flow import load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import EDIT_STEM, RUNS_ROOT, edit_at, rendered_at
from isekai.interface.drafting import draft_from_image, refuse_image_drafts
from isekai.interface.verbs.common import Verb, require_tracked
from isekai.interface.wiring import Wiring
from isekai.pipeline.edit import discard_edit
from isekai.pipeline.generate import discard_render
from isekai.pipeline.review import Revision, withdraw


def run_draft(args: argparse.Namespace, wired: Wiring) -> int:
    """Write `args.target`'s draft from every image, or, when any is refused, none."""
    target = args.target
    images = args.images
    require_tracked([target], wired)
    flow = load_flow(target, wired.flows_dir)
    vocabulary = cache(wired.vocabulary)
    field_map = cache(lambda: wired.field_map(vocabulary()))
    refused: list[str] = []
    located: list[tuple[Path, Revision]] = []
    for image in images:
        try:
            located.append((image, rendered_at(image)))
        except Refusal as unrendered:
            refused.append(f"{image}: {unrendered}")
    answers = refuse_image_drafts(flow, located, vocabulary, field_map)
    refused += [
        f"{image}: {answer}"
        for (image, _), answer in zip(located, answers, strict=True)
        if answer is not None
    ]
    if not refused:
        for _, one in located:
            draft = draft_from_image(flow, one, vocabulary, field_map)
            print(f"draft wrote {draft.relative_to(draft.parents[3])}", file=wired.out)
    for message in refused:
        print(f"refused: {message}", file=wired.err)
    return 1 if refused else 0


def run_discard(args: argparse.Namespace, wired: Wiring) -> int:
    """Delete one render or edit, printing each path deleted.

    A path that is an edit's image deletes that edit and every edit made from it,
    and nothing else. Any other path is a render's: it goes with its edits and its
    thumbnails. Refused, deleting nothing, while a render session holds the
    collection, as the app's delete is. The thumbnails go while the image still
    names them. A render that was its approval's last takes that approval with
    it, through `withdraw`; the run's files print before the thumbnails. The
    library is imported here for `run_ui`'s reason: it is off `python -m isekai`'s
    import graph.
    """
    image = args.image
    edited = EDIT_STEM.match(image.stem) is not None
    try:
        run, flow, version = (edit_at if edited else rendered_at)(image)[:3]
    except Refusal as unnamed:
        print(
            f"refused: {image}: {unnamed}; a render's path is "
            "<run>/<flow>/outputs/<NNN>/<seed>.png and an edit's is "
            "<run>/<flow>/outputs/<NNN>/<seed>.edit-<k>.png",
            file=wired.err,
        )
        return 1
    from isekai.interface.ui import drop_thumbnails, render_running

    if render_running(run):
        print(
            f"refused: {image}: A render session is running. Wait for it to end, "
            "then discard the render again.",
            file=wired.err,
        )
        return 1
    if edited:
        deleted = discard_edit(image)
        for path in deleted:
            print(
                f"discard deleted {path.relative_to(run.path.parent)}", file=wired.out
            )
        return 0
    thumbnails = drop_thumbnails(run, image)
    deleted = [*discard_render(image), *withdraw(run, flow, version)]
    for path in deleted:
        print(f"discard deleted {path.relative_to(run.path.parent)}", file=wired.out)
    for path in thumbnails:
        print(
            f"discard deleted {path.relative_to(run.path.parents[2])}", file=wired.out
        )
    return 0


def draft_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `draft`'s arguments to `parser`."""
    # One target: an image's path names everything a draft needs but that.
    parser.add_argument(
        "--flow",
        dest="target",
        required=True,
        metavar="FLOW",
        help="the flow to draft; an image's own flow is a revision",
    )
    parser.add_argument(
        "images",
        nargs="+",
        type=Path,
        help="rendered images, each <run>/<flow>/outputs/<NNN>/<seed>.png",
    )
    parser.set_defaults(photos=[], runs=RUNS_ROOT)


def discard_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `discard`'s arguments to `parser`."""
    parser.add_argument(
        "image", type=Path, help="the render, <run>/<flow>/outputs/<NNN>/<seed>.png"
    )
    parser.set_defaults(photos=[], runs=RUNS_ROOT)


DRAFT_ROW = Verb(
    "draft",
    "copy the approval a rendered image came from into a flow's draft",
    draft_arguments,
    run_draft,
)
DISCARD_ROW = Verb(
    "discard",
    "delete a render: its image, its record and its thumbnails",
    discard_arguments,
    run_discard,
)
