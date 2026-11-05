"""Stage (2): a tag list in, a sheet of canonical tags out.

A sheet is fields and nothing else. It carries no assembled prompt -- storing one
creates a footgun where a human edits the prompt block and a rebuild silently
overwrites it. **The fill itself is told nothing about flows** but whether a tag
list is expected: it is handed the tag list, the schema, the vocabulary and the
table, so the same code serves every flow without learning that flows exist, and
the flow decides only which directory is written.

**Nothing here is a model and nothing here is a seam.** A seam behind a Protocol
would exist so that a model's malformed answer is permanent for any
implementation. There is no answer: the stage reads one artifact and looks each
tag up in one committed table, so there is no transport to inject, no offline
double to satisfy an interface and no response whose structure could fail to match
the field list. The lookup is a dictionary in `isekai/shared/field_map.py`, and
the property it buys is stronger than the one that seam would assert -- a tagger
whose output layer **is** the vocabulary cannot name a tag outside it, so "no tag
is invented" holds by construction rather than by filtering.

**The schema is a data file, not code.** It can be checked without executing
anything, and a second schema -- a photoreal flow's, say -- is a file rather than
a branch. It declares, in order, that flow's own fields and which seven of them
are scored -- `summon-anime-wai` and `conjure-anime-wai` do not declare the same
field list, and neither number is a property of the stage; it
carries no version and no vocabulary, because inside a frozen flow directory the
digest proves the field list and the flow declares the vocabulary. Its reader
lives beside `Schema` in `isekai/foundation/flow.py`.

**Field names are slugs because they have to be.** An API that takes the schema
as a tool input schema enforces `^[a-zA-Z0-9_.-]{1,64}$` on property keys, and a
name carrying a space or a slash fails the first call with a hard 400. No stage
here sends the schema, and the rule stays: `flow.py`'s reader enforces it, and one
name everywhere removes the class of error.

Stdlib only.
"""

from collections.abc import Mapping
from pathlib import Path

from isekai.foundation.artifacts import (
    SHEET_FILE,
    WD14_FILE,
    DanbooruTag,
    Sheet,
    SheetProducer,
    read,
    require,
    write,
)
from isekai.foundation.flow import Schema
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    NEW_VERSION,
    PHOTO,
    SHEETS,
    WD14,
    Run,
    artifact_name,
    check_budget,
    latest,
    photo_of,
    record_failure,
    refusal_for,
    stage_command,
)
from isekai.shared.field_map import FieldMap, route
from isekai.shared.field_map import identity as field_map_identity
from isekai.shared.fields import validate
from isekai.shared.vocabulary import Vocabulary
from isekai.shared.vocabulary import identity as vocabulary_identity

# --- the stage: a tag list in, canonical fields out ---------------------------

# The name this stage's budget is keyed by. Its directory inside a run is the
# run's to name, not the stage's -- `run.SHEETS`.
STAGE = "sheet"

# What the sheet records as having filled it. The string the *tag* artifact's
# producer carries, because that is what the sheet's content comes from --
# written out rather than imported from `tagging.py`, since no stage imports
# another.
TAGGER = "wd14"

# What the sheet records as having filled it when the flow declares no tagger:
# no tag list and no model, so nothing unpinned shaped it (D31).
EMPTY = "empty"


def sheet(
    run: Run,
    flow: str,
    schema: Schema,
    vocabulary: Vocabulary,
    field_map: FieldMap,
    *,
    tagged: bool,
    flow_digest: str,
    new_version: bool = False,
    tags_from: str | None = None,
) -> tuple[Path | None, list[str]]:
    """Route the photograph's tag list into a sheet, under this flow, with its warnings.

    `tagged` says whether the flow declares the tagger, and has no default
    because a default decides silently. Untagged, no list is read and every
    field is written empty for the person to fill (D31).
    `flow_digest` is recorded and never read. `tags_from` names the flow a draft
    drew this first sheet from; it is recorded and never read for the fill.

    **The fill is told nothing about flows beyond `tagged`, and reaches nothing
    at all.** It is handed the photograph's tag list, `photo/wd14/`'s, the schema,
    the vocabulary and the table, so the same code serves every flow without
    learning that flows exist; `flow` decides which directory is written (D17).

    **For a tagged flow, an absent tag list is a
    refusal.** A sheet with every field empty is legal and therefore silent, so
    writing one when the tagger never ran would hide the only thing the operator
    needs told. The rule that a missing tag artifact is an absent aid still holds
    for the *hosted* tagger, which contributes nothing to a sheet; it cannot hold
    for the local one the sheet is filled from.

    Returns the artifact's path, or None when this flow already had a sheet;
    a kept sheet filled from a superseded tag list is warned about.
    """
    directory = run.directory(flow, SHEETS)
    kept = latest(directory)
    if kept is not None and not new_version:
        if not tagged:
            return None, []
        return None, _superseded(run, flow, directory, kept)
    version = (kept or 0) + 1

    artifact: Sheet = prepare_sheet(
        run,
        flow,
        schema,
        vocabulary,
        field_map,
        tagged=tagged,
        flow_digest=flow_digest,
        tags_from=tags_from,
        version=version,
    )
    path = directory / artifact_name(version)
    write(path, SHEET_FILE, artifact)
    return path, []


def prepare_sheet(
    run: Run,
    flow: str,
    schema: Schema,
    vocabulary: Vocabulary,
    field_map: FieldMap,
    *,
    tagged: bool,
    flow_digest: str,
    tags_from: str | None = None,
    version: int = 1,
) -> Sheet:
    """Prepare the sheet's checked contents before writing it.

    A draft's first sheet is filled as `sheet` fills one, with `tags_from`
    recorded and never read for the fill. A damaged tag list keeps the sheet
    stage's permanent-failure record, but not for a draft: a draft batch checks
    every fill before its first sheet, and that check writes nothing.
    """
    directory = run.directory(flow, SHEETS)
    if not tagged:
        # No tagger was going to run, so an empty sheet hides nothing; and
        # nothing here can fail, so no budget is checked.
        fields = route((), field_map, schema)
        made_by: SheetProducer = {
            "implementation": EMPTY,
            "models": [],
            "pinned": True,
            "artifacts": {},
        }
        validate(fields, schema, vocabulary, excluded=field_map.excluded)
    else:
        fields, made_by = _from_tag_list(
            run, flow, directory, version, schema, vocabulary, field_map, tags_from
        )
    if tags_from is not None:
        made_by["tags_from"] = tags_from

    artifact: Sheet = {
        "schema": SHEET_FILE.schema,
        "producer": made_by,
        "schema_document": {"name": schema.name},
        "vocabulary": vocabulary_identity(vocabulary),
        "field_map": field_map_identity(field_map),
        "flow_digest": flow_digest,
        "fields": fields,
    }
    return artifact


def _superseded(run: Run, flow: str, directory: Path, kept: int) -> list[str]:
    """Return a warning when the kept sheet's tag list is below the flow's latest.

    A sheet it cannot read, or one with no list number, gives none: review
    refuses an unreadable sheet by name. Nor does a first sheet a draft wrote:
    it is built from another flow's approval, so a later list is not weighed
    against it.
    """
    newest = latest(photo_of(run, WD14))
    if newest is None:
        return []
    try:
        filled = read(directory / artifact_name(kept), SHEET_FILE)
    except Refusal:
        return []
    if tagged_from(filled) is not None:
        return []
    producer = filled.get("producer")
    source = producer.get("from") if isinstance(producer, dict) else None
    # `bool` is an `int`, and a hand-edited `true` is not a list number.
    if not isinstance(source, int) or isinstance(source, bool) or source >= newest:
        return []
    listed = f"{PHOTO}/{WD14}"
    return [
        f"{run.id}/{flow}: sheet {kept:03d} was filled from "
        f"{listed}/{artifact_name(source)}, and {listed}/{artifact_name(newest)} "
        f"is newer; run `{stage_command(run, STAGE, flow, options=NEW_VERSION)}`"
    ]


def _from_tag_list(
    run: Run,
    flow: str,
    directory: Path,
    version: int,
    schema: Schema,
    vocabulary: Vocabulary,
    field_map: FieldMap,
    drafted_from: str | None,
) -> tuple[dict[str, list[str]], SheetProducer]:
    """Return the checked fields routed from the photograph's tag list, and who.

    Refuses naming `tag` when the list is absent, and records nothing: running
    `tag` is the fix, and a record would bar the sheet that follows. The budget is
    checked next; a damaged list or a tag outside the vocabulary is then recorded
    as permanent, since this stage fails the same way every time (D21) -- save for
    a draft's fill, `drafted_from` set, which is refused and recorded nowhere.
    """
    source = latest(photo_of(run, WD14))
    if source is None:
        raise Refusal(
            f"{run.id}: there is no tag list to fill a sheet for {flow} from; run "
            f"`{stage_command(run, 'tag')}` first, which writes {PHOTO}/{WD14}/"
        )

    retag = stage_command(run, "tag", options=NEW_VERSION)
    if drafted_from is not None:
        # The image a draft starts from is the draft verb's, never this stage's.
        remedy = f"run `{retag}`, then draft {flow} from the {drafted_from} image again"
        fields, made_by = _route(run, source, schema, field_map, remedy)
        validate(fields, schema, vocabulary, excluded=field_map.excluded, remedy=remedy)
        return fields, made_by

    check_budget(STAGE, directory, version, run)
    # No sheet exists yet to edit, so every fix is a new tag list.
    remedy = (
        f"run `{retag}`, then `{stage_command(run, STAGE, flow, options=NEW_VERSION)}`"
    )
    try:
        fields, made_by = _route(run, source, schema, field_map, remedy)
        validate(fields, schema, vocabulary, excluded=field_map.excluded, remedy=remedy)
    except Refusal as failed:
        detail = str(failed)
        record = record_failure(
            directory, version, "permanent", {"stage": STAGE, "detail": detail}
        )
        raise refusal_for(
            STAGE, run, "permanent", detail, record, SHEETS, STAGE, flow, STAGE
        ) from failed
    return fields, made_by


def tagged_from(body: Mapping[str, object]) -> str | None:
    """Return the flow a draft drew a sheet from, recorded as `tags_from`, else None.

    e.g. producer `{…, "tags_from": "summon-anime-wai"}` -> "summon-anime-wai"
    """
    producer = body.get("producer")
    source = producer.get("tags_from") if isinstance(producer, Mapping) else None
    return source if isinstance(source, str) else None


def _route(
    run: Run,
    source: int,
    schema: Schema,
    field_map: FieldMap,
    remedy: str,
) -> tuple[dict[str, list[str]], SheetProducer]:
    """Return the fields routed from the photograph's tag list `source`, and who.

    Refuses naming `remedy` when the list is damaged.
    """
    listed_path = photo_of(run, WD14) / artifact_name(source)
    listed = read(listed_path, WD14_FILE)
    for key, shape in (("tags", list), ("producer", dict)):
        require(listed_path, listed, key, shape, remedy)
    tags, producer = listed["tags"], listed["producer"]
    for key, shape in (("models", list), ("pinned", bool), ("artifacts", dict)):
        require(listed_path, producer, key, shape, remedy)
    for index, one in enumerate(tags):
        if not isinstance(one, dict) or "tag" not in one:
            raise Refusal(
                f"{listed_path.name}: its tag entry {index} records no `tag`; {remedy}"
            )
    # `str()`: a hand-edited list's non-string tag routes nowhere, never raises.
    fields = route((DanbooruTag(str(one["tag"])) for one in tags), field_map, schema)
    made_by: SheetProducer = {
        # The producer of the *tags* is the producer of the sheet now, so the
        # pin it was verified against travels across rather than being
        # re-derived: these are the digests that session actually opened.
        "implementation": TAGGER,
        "models": list(producer["models"]),
        "pinned": producer["pinned"],
        "artifacts": dict(producer["artifacts"]),
        "from": source,
    }
    if "floor" in producer:
        made_by["floor"] = producer["floor"]
    return fields, made_by
