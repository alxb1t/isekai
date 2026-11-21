"""The draft's and the approval's reads and writes, and what the parts share.

Imports no part and not the front door.
"""

import shlex
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from isekai.foundation.artifacts import (
    APPROVED_FILE,
    DRAFT_FILE,
    SHEET_FILE,
    DraftImage,
    Renders,
    ReviewApproved,
    ReviewDraft,
    Sheet,
    create,
    read,
    renders_of,
    require,
    write,
)
from isekai.foundation.flow import OUTPUT_SUFFIX
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    DRAFT,
    NEW_VERSION,
    REVIEW,
    Run,
    approval_of,
    artifact_name,
    command,
    current_draft,
    group_of,
    next_version,
    render_image,
    rendered_seeds,
    stage_command,
)

STAGE = "review"

# The option that deletes a flow's waiting draft.
DISCARD = ("--discard",)


def _first_image(group: Path) -> Path | None:
    """Return the first image in a render group, or None."""
    return min(
        (
            render_image(group, seed, OUTPUT_SUFFIX)
            for seed in rendered_seeds(group, OUTPUT_SUFFIX)
        ),
        default=None,
    )


def _draft_command(image: Path, flow: str) -> str:
    """Return the command that drafts `flow` from `image`, as it is pasted.

    e.g. (r/f/outputs/001/7.png, f)
         -> "python -m isekai draft --flow f r/f/outputs/001/7.png"
    """
    return command("draft", "--flow", flow, shlex.quote(str(image)))


def _approval(run: Run, flow: str, version: int, retry: str) -> ReviewApproved:
    """Read the approval numbered `version`, refusing one a draft cannot copy."""
    copied = approval_of(run, flow, version)
    # An approved artifact is never replaced, so only a hand repairs it.
    remedy = f"restore it in {copied}, then {retry}"
    carried = read(copied, APPROVED_FILE, remedy=remedy)
    require(
        copied,
        carried,
        "sheet",
        int,
        f"a draft copied from it cannot name its sheet; add the sheet version "
        f"it was approved from as `sheet` in {copied}, then {retry}",
    )
    require(copied, carried, "vocabulary", dict, remedy)
    require(copied, carried, "fields", dict, remedy)
    return carried


def _write_draft(
    run: Run,
    flow: str,
    came_from: int,
    source: str,
    carried: Sheet | ReviewApproved,
    sheet_version: int,
    *,
    renders: Renders | None = None,
    version: int | None = None,
    image: DraftImage | None = None,
) -> Path:
    """Write `flow`'s draft numbered `version`, else the next, and return its path."""
    review_directory = run.directory(flow, REVIEW)
    number = next_version(review_directory) if version is None else version
    path = review_directory / artifact_name(number, DRAFT)
    draft: ReviewDraft = {
        "schema": DRAFT_FILE.schema,
        "producer": {"implementation": STAGE, "from": came_from, "source": source},
        "flow": flow,
        "sheet": sheet_version,
        "vocabulary": carried["vocabulary"],
        "fields": carried["fields"],
    }
    # Carried where the source records them, so the approval can name the
    # schema and table its fields came through, and a correction keeps its count.
    if "schema_document" in carried:
        draft["schema_document"] = carried["schema_document"]
    if "field_map" in carried:
        draft["field_map"] = carried["field_map"]
    if renders is not None:
        draft["renders"] = renders
    if image is not None:
        draft["producer"]["image"] = image
    write(path, DRAFT_FILE, draft)
    return path


def save_draft(
    run: Run,
    flow: str,
    fields: Mapping[str, Sequence[str]],
    renders: Renders | None = None,
) -> Path:
    """Replace the current draft's field values in place, and return its path.

    `renders`, when given, replaces the draft's count and seeds, refused as
    approval would refuse it.

    The one owner of a draft update. The draft's shape is otherwise built only at
    creation, and a second writer arriving without a single owner is how two shapes
    of one file drift apart.

    **It does not create.** `review()` owns that, and teaching this to create too
    would spend a version number on a stray keypress -- there is no Save control
    on the surface that calls it and no confirm step to attribute one to. The
    version and the sheet the draft records are its identity and are carried
    across untouched.

    **A changed field set is refused**, which is what makes this owner
    load-bearing rather than clerical: a missing field and a field the schema does
    not have are two of the four ways a sheet can be invalid at approval, and
    comparing the set at the one write point turns both from a property the
    editing surface is trusted to have into a property of the write path -- for
    one comparison, without opening the validator.
    """
    directory = run.directory(flow, REVIEW)
    path = current_draft(directory)
    if path is None:
        raise Refusal(
            f"{run.id}: flow {flow} has no draft to update; a draft is opened by "
            f"`{stage_command(run, STAGE, flow)}`, and an approved "
            "flow has none because approval is the end of it"
        )

    body = read(path, DRAFT_FILE)
    require(path, body, "fields", dict, _recopy(run, flow, path))
    existing = set(body["fields"])
    offered = set(fields)
    if offered != existing:
        missing = sorted(existing - offered)
        unknown = sorted(offered - existing)
        raise Refusal(
            f"{path.name}: an update replaces a draft's values and never its "
            f"field set; missing {missing}, unknown {unknown}"
        )

    updated: ReviewDraft = {
        **body,
        "fields": {name: list(fields[name]) for name in body["fields"]},
    }
    if renders is not None:
        fix = "nothing was saved; send a count of at least one and its seeds"
        updated["renders"] = renders_of(path, {"renders": renders}, fix)
    write(path, DRAFT_FILE, updated)
    return path


def _publish(run: Run, flow: str, path: Path, approved: ReviewApproved) -> None:
    """Write `approved` at `path`, refusing a number another writer has taken first."""
    body: ReviewApproved = approved
    try:
        create(path, APPROVED_FILE, body)
    except FileExistsError:
        raise Refusal(
            f"{path.name} already exists in {flow}/{REVIEW}/ and an approved "
            f"artifact is never replaced; run {_again(run, flow)} to correct it "
            "under the next number"
        ) from None


def _again(run: Run, flow: str) -> str:
    """Return the command that copies `flow`'s draft afresh under the next number."""
    return f"`{stage_command(run, STAGE, flow, options=NEW_VERSION)}`"


def _recopy(run: Run, flow: str, draft: Path) -> str:
    """Return the remedy for a draft that lost a key: a fresh copy, newly numbered."""
    return f"delete {draft}, then run {_again(run, flow)} to take a fresh copy"


def _differs(
    fields: Mapping[str, Sequence[str]], draft: Path, source: Path, remedy: str
) -> bool:
    """Say whether `fields` differs from the sheet it was copied from.

    Computed rather than declared. Whether a sheet was actually corrected is the
    difference between the 0.568 route and the 0.917 one, and a flag the operator
    sets is an assumption wearing a fact's clothes. A missing sheet is refused
    rather than read as unedited, which would be exactly such an assumption.
    """
    if not source.exists():
        raise Refusal(
            f"{draft.name}: was copied from {source}, which is not there, so "
            f"whether it was edited cannot be computed; {remedy}"
        )
    body = read(source, SHEET_FILE, remedy=remedy)
    require(source, body, "fields", dict, remedy)
    return not same_fields(body["fields"], fields)


def same_fields(
    one: Mapping[str, Sequence[str]], other: Mapping[str, Sequence[str]]
) -> bool:
    """Return whether two `fields` objects hold the same tags, field by field."""
    return {name: list(tags) for name, tags in one.items()} == {
        name: list(tags) for name, tags in other.items()
    }


def draft_image(body: Mapping[str, object]) -> DraftImage | None:
    """Return the image a draft or approval was written from, or None.

    e.g. producer `{…, "image": {"flow": "f", "version": 1, "seed": 7}}` -> that
    """
    producer = body.get("producer")
    image = producer.get("image") if isinstance(producer, Mapping) else None
    if not isinstance(image, Mapping):
        return None
    flow, version, seed = image.get("flow"), image.get("version"), image.get("seed")
    if not (isinstance(flow, str) and type(version) is int and type(seed) is int):
        return None
    return {"flow": flow, "version": version, "seed": seed}


def came_from(body: Mapping[str, object]) -> int | None:
    """Return the approval of its own flow a draft or approval was copied from.

    A copy of a sheet, or of another flow's approval, names none.
    e.g. producer `{"from": 1, "source": "review"}` -> 1
    """
    producer = body.get("producer")
    if not isinstance(producer, Mapping) or is_copy(
        cast(Mapping[str, object], producer)
    ):
        return None
    version = producer.get("from")
    if producer.get("source") != REVIEW or isinstance(version, bool):
        return None
    return version if isinstance(version, int) else None


def is_copy(producer: Mapping[str, object]) -> bool:
    """Return whether an approval's producer says it is a copy of another flow's.

    An older copy says so by `copied_from`, whose value is not read.
    e.g. {'copied': True} -> True; {'copied_from': {…}} -> True; {'from': 1} -> False
    """
    return producer.get("copied") is True or "copied_from" in producer


def copied_renders(run: Run, flow: str, version: int, body: ReviewApproved) -> Renders:
    """Return approval `version` of `flow`'s renders with every seed it rendered listed.

    Its listed seeds come first, then each seed its group holds an image of, and
    the count rises to their number where it is lower, so a copy renders the
    same seeds once and never reads its source again.
    e.g. {count 2, seeds []}, outputs/001/{11.png, 12.png} -> {count 2, seeds [11, 12]}
    """
    path = approval_of(run, flow, version)
    listed = renders_of(path, body, f"restore it in {path} by hand")
    group = group_of(run, flow, version)
    rendered = rendered_seeds(group, OUTPUT_SUFFIX)
    seeds = listed["seeds"] + [s for s in rendered if s not in listed["seeds"]]
    return {"count": max(listed["count"], len(seeds)), "seeds": seeds}
