"""The approval of a draft: `approve` and its helpers.

It imports `records.py` and `budget.py`, and neither the front door nor another part.
"""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from isekai.foundation.artifacts import (
    APPROVED_FILE,
    DRAFT_FILE,
    SHEET_FILE,
    ApprovedProducer,
    Renders,
    ReviewApproved,
    read,
    renders_of,
    require,
)
from isekai.foundation.flow import OUTPUT_SUFFIX, Flow, Schema
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    APPROVED,
    NEW_VERSION,
    REVIEW,
    SHEETS,
    Run,
    approval_of,
    approved_versions,
    artifact_name,
    current_draft,
    group_of,
    is_rendered,
    latest,
    latest_artifact,
    next_version,
    sheet_of,
    stage_command,
    version_of,
)
from isekai.pipeline.review.budget import ENCODER_WINDOW, estimate_tokens, token_budget
from isekai.pipeline.review.records import (
    DISCARD,
    STAGE,
    _again,
    _differs,
    _publish,
    _recopy,
    came_from,
    copied_renders,
    is_copy,
    same_fields,
)
from isekai.shared.fields import validate
from isekai.shared.vocabulary import Vocabulary


def _window_warnings(
    run: Run,
    flow: str,
    fields: Mapping[str, Sequence[str]],
    schema: Schema,
    definition: Flow | None,
) -> list[str]:
    """Return the warning for a draft whose prompt passes the encoder's window."""
    warnings: list[str] = []
    estimate = (
        estimate_tokens(fields, schema)
        if definition is None
        else token_budget(fields, schema, definition).total
    )
    if estimate > ENCODER_WINDOW:
        warnings.append(
            f"{run.id}/{flow}: the assembled prompt is about {estimate} tokens "
            f"and the text encoder reads {ENCODER_WINDOW} at a time, so it will "
            "be chunked and averaged; the sheet is the record of what was asked "
            "for, so this is a warning and not a refusal"
        )
    return warnings


def approve(
    run: Run,
    flow: str,
    schema: Schema,
    vocabulary: Vocabulary,
    source: str | None = None,
    *,
    excluded: frozenset[str] = frozenset(),
    definition: Flow | None = None,
) -> tuple[Path | None, list[str]]:
    """Validate `flow`'s current draft and approve it, returning it and any warnings.

    With `source`, no draft is read: `source`'s latest approval is copied under
    `flow` instead.

    With `definition`, the over-window warning counts the assembled prompt; without
    it, the tags alone.

    Validation is the last place an invented tag can be caught: one that merely
    looks canonical passes every later check on its way into the prompt. The
    refusal says the tag is not in the vocabulary's *prediction set*, which is
    what is true -- that set is a subset of the wider tag corpus, so calling an
    absent tag unreal would overclaim.
    """
    if source is not None:
        return _copy_approval(
            run, flow, schema, vocabulary, source, excluded=excluded
        ), []
    directory = run.directory(flow, REVIEW)
    draft = current_draft(directory)
    if draft is None:
        if approved_versions(directory):
            # Already approved, and approving again would have nothing to act on.
            # A no-op rather than a refusal, because re-running every command is
            # the whole of resume and resume must not exit non-zero.
            return None, []
        raise Refusal(
            f"{run.id}: flow {flow} has no draft to approve; run "
            f"`{stage_command(run, STAGE, flow)}` to take a copy, "
            "edit it, then approve it"
        )

    version = version_of(draft)
    body = read(draft, DRAFT_FILE)
    # A hand-edited draft without a `fields` object holds no fields, so
    # validation refuses it naming every one it lacks.
    held = body.get("fields")
    fields: dict[str, list[str]] = (
        {name: list(tags) for name, tags in held.items()}
        if isinstance(held, dict)
        else {}
    )
    validate(fields, schema, vocabulary, excluded=excluded)

    warnings = _window_warnings(run, flow, fields, schema, definition)

    remedy = _recopy(run, flow, draft)
    for key, shape in (("sheet", int), ("producer", dict), ("vocabulary", dict)):
        require(draft, body, key, shape, remedy)
    renders = renders_of(
        draft,
        body,
        f"correct `renders` in {draft}, then run "
        f"`{stage_command(run, 'approve', flow)}` again",
    )
    sheet_version, producer = body["sheet"], body["producer"]
    origin = came_from(body)
    if origin is not None:
        _refuse_unchanged(run, flow, draft, origin, fields, renders)
    sheet_path = run.directory(flow, SHEETS) / artifact_name(sheet_version)
    approved_body: ReviewApproved = {
        "schema": APPROVED_FILE.schema,
        "producer": {
            **producer,
            "edited": _differs(fields, draft, sheet_path, _resheet(run, flow, draft)),
            "approved_from": version,
        },
        "flow": flow,
        "sheet": sheet_version,
        "vocabulary": body["vocabulary"],
        "fields": fields,
    }
    if "schema_document" in body:
        approved_body["schema_document"] = body["schema_document"]
    if "field_map" in body:
        approved_body["field_map"] = body["field_map"]
    # Written only where the draft states it, so an older draft's approval is
    # byte for byte what it always was.
    if "renders" in body:
        approved_body["renders"] = renders

    path = directory / artifact_name(version, APPROVED)
    _publish(run, flow, path, approved_body)
    draft.unlink()
    return path, warnings


# What a copy does not take from its source's producer: where the source came from.
_NOT_COPIED = frozenset({"copied_from", "drafted_from", "image"})


def _copy_approval(
    run: Run,
    flow: str,
    schema: Schema,
    vocabulary: Vocabulary,
    source: str,
    *,
    excluded: frozenset[str],
) -> Path | None:
    """Write `source`'s latest approval under `flow`, or None if `flow` is in step.

    `flow` is in step when its latest approval is a copy holding the fields and
    renders a copy of `source`'s latest would, listed or rendered; anything else
    is copied over under the next number. The fields are validated against
    `flow`'s schema, so a copy the target cannot hold is refused like any draft.
    `sheet` is `flow`'s newest sheet, which a revision of the copy is compared
    against; a `flow` with none refuses.
    """
    origin = run.directory(source, REVIEW)
    versions_held = approved_versions(origin)
    if not versions_held:
        raise Refusal(
            f"{run.id}: {flow} is copied from {source}, which has no approved "
            f"sheet; run `{stage_command(run, STAGE, source)}`, edit the draft, "
            f"then `{stage_command(run, 'approve', source)}` first"
        )
    approval = versions_held[-1]
    directory = run.directory(flow, REVIEW)
    path = origin / artifact_name(approval, APPROVED)
    body = read(path, APPROVED_FILE)
    remedy = f"delete {path}, then run {_again(run, source)} to approve it afresh"
    for key, shape in (
        ("fields", dict),
        ("sheet", int),
        ("producer", dict),
        ("vocabulary", dict),
    ):
        require(path, body, key, shape, remedy)
    fields = {name: list(tags) for name, tags in body["fields"].items()}
    renders = copied_renders(run, source, approval, body)
    mine = latest_artifact(directory, APPROVED)
    if mine is not None:
        newest = read(mine, APPROVED_FILE)
        afresh = f"delete {mine}, then run {_again(run, flow)} to approve it afresh"
        require(mine, newest, "producer", dict, afresh)
        require(mine, newest, "fields", dict, afresh)
        if is_copy(newest["producer"]) and same_fields(newest["fields"], fields):
            mine_renders = copied_renders(
                run, flow, approved_versions(directory)[-1], newest
            )
            if mine_renders["count"] == renders["count"] and set(
                mine_renders["seeds"]
            ) == set(renders["seeds"]):
                return None
    # Neither flow has a draft to edit, so a tag's fix goes through `source`'s own;
    # a field `flow`'s schema does not fit is no edit to `source`, so it goes
    # through `flow`'s own sheet instead.
    copy = stage_command(run, "approve", flow, options=("--from", source))
    validate(
        fields,
        schema,
        vocabulary,
        excluded=excluded,
        remedy=f"run {_again(run, source)}, delete it from that draft, run "
        f"`{stage_command(run, 'approve', source)}`, then `{copy}` again",
        schema_remedy=f"copy from a flow whose schema declares {schema.name}'s "
        f"fields, or run "
        f"{_again(run, flow)}, edit the draft, then "
        f"`{stage_command(run, 'approve', flow)}` to approve {flow} on its own",
    )
    sheet_version = latest(run.directory(flow, SHEETS))
    if sheet_version is None:
        raise Refusal(
            f"{run.id}: flow {flow} has no sheet to copy {source}'s approval onto; "
            f"run `{stage_command(run, 'sheet', flow)}`, then `{copy}` again"
        )
    again = (
        f"run `{stage_command(run, 'sheet', flow, options=NEW_VERSION)}`, "
        f"then `{copy}` again"
    )
    target = sheet_of(run, flow, sheet_version)
    held = read(target, SHEET_FILE, remedy=again)
    require(target, held, "fields", dict, again)

    kept = {k: v for k, v in body["producer"].items() if k not in _NOT_COPIED}
    edited = not same_fields(held["fields"], fields)
    producer = cast(ApprovedProducer, kept | {"copied": True, "edited": edited})
    copied: ReviewApproved = {
        **body,
        "producer": producer,
        "flow": flow,
        "sheet": sheet_version,
        "fields": fields,
        "renders": renders,
    }
    written = directory / artifact_name(next_version(directory), APPROVED)
    _publish(run, flow, written, copied)
    return written


def _refuse_unchanged(
    run: Run,
    flow: str,
    draft: Path,
    version: int,
    fields: Mapping[str, Sequence[str]],
    renders: Renders,
) -> None:
    """Refuse a draft that would render only images its approval already makes.

    That is a draft with its approval's fields whose every image is a listed
    seed its approval lists or rendered: rendering it pays for what exists. New
    seeds alone are a change, and a count above its seeds draws new ones.
    e.g. 002 from 001, fields equal, `{count 1, seeds [7]}`, 001 rendered 7 -> refused
    """
    origin = approval_of(run, flow, version)
    remedy = f"restore {origin}, then run `{stage_command(run, 'approve', flow)}` again"
    if not origin.exists():
        raise Refusal(
            f"{draft.name}: was copied from {origin}, which is not there, so "
            f"whether it changes anything cannot be computed; {remedy}"
        )
    body = read(origin, APPROVED_FILE, remedy=remedy)
    seeds = renders["seeds"]
    group = group_of(run, flow, version)
    made = set(renders_of(origin, body, remedy)["seeds"]) | {
        seed for seed in seeds if is_rendered(group, seed, OUTPUT_SUFFIX)
    }
    held = body.get("fields")
    same = isinstance(held, Mapping) and same_fields(held, fields)
    if not same or renders["count"] > len(seeds) or not set(seeds) <= made:
        return
    raise Refusal(
        f"{draft.name}: has the fields of {origin.name} and only its seeds "
        f"{', '.join(map(str, seeds))}, so it would render the images of "
        f"{run.id}/{group.relative_to(run.path)}/ again; edit a field, the "
        f"count or the seeds in {draft}, then run "
        f"`{stage_command(run, 'approve', flow)}` again, or run "
        f"`{stage_command(run, STAGE, flow, options=DISCARD)}`"
    )


def _resheet(run: Run, flow: str, draft: Path) -> str:
    """Return the remedy for a draft whose sheet cannot be compared against.

    The sheet is kept rather than deleted: deleting it would free its number for
    the next `sheet` run to reuse under different content. With no approval, a
    new sheet and a fresh copy of it give `edited` something true to be computed
    against, and the old draft stays to carry the correction across. A re-opened
    draft is copied from the approval, which names this same sheet, so a fresh
    copy would be refused again; there the fix is to keep the approval.
    """
    approved = approved_versions(draft.parent)
    if approved:
        return (
            f"delete {draft} to leave {flow} approved as "
            f"{artifact_name(approved[-1], APPROVED)} records it"
        )
    return (
        f"run `{stage_command(run, 'sheet', flow, options=NEW_VERSION)}`, then "
        f"{_again(run, flow)} to copy the new sheet; {draft.name} keeps your "
        "edits to carry across"
    )
