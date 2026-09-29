"""Stage (2): a tag list in, a sheet of canonical tags out.

A sheet is fields and nothing else. It carries no assembled prompt -- storing one
creates a footgun where a human edits the prompt block and a rebuild silently
overwrites it. **The fill itself is told nothing about flows** but whether a tag
list is expected: it is handed the tag list, the schema, the vocabulary and the
table, so the same code serves every flow without learning that flows exist, and
the flow decides only which directory is read and written.

**Nothing here is a model and nothing here is a seam.** Two sorter
implementations used to live in this file behind a Protocol, and the argument for
the seam was that a malformed answer had to be permanent for either. There is no
answer: the stage reads one artifact and looks each tag up in one committed table,
so there is no transport to inject, no offline double to satisfy an interface and
no response whose structure could fail to match the field list. What replaced them
is a dictionary lookup in `isekai/shared/field_map.py`, and the property it buys
is stronger than the one the seam asserted -- a tagger whose output layer **is**
the vocabulary cannot name a tag outside it, so "no tag is invented" holds by
construction rather than by filtering.

**The schema is a data file, not code.** It can be checked without executing
anything, and a second schema -- a photoreal flow's, say -- is a file rather than
a branch. It declares, in order, that flow's own fields and which seven of them
are scored -- `summon-anime-wai` and `conjure-anime-wai` do not declare the same
field list, and neither number is a property of the stage; it
carries no version and no vocabulary, because inside a frozen flow directory the
digest proves the field list and the flow declares the vocabulary. Its reader
lives beside `Schema` in `isekai/foundation/flow.py`.

**Field names are slugs because they have to be.** The structured-output flag
became a tool input schema at the API, which enforces `^[a-zA-Z0-9_.-]{1,64}$` on
property keys; several of the names then in the schema carried a space or a slash
and the first call hit a hard 400. The flag is gone with the sorters and the rule
is not:
`flow.py`'s reader still enforces it, and one name everywhere removes the class of
error.

Stdlib only.
"""

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
    SHEETS,
    WD14,
    Run,
    artifact_name,
    check_budget,
    latest,
    record_failure,
    refusal_for,
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
# producer carries, because that is what the sheet's content now comes from --
# written out rather than imported from `tagging.py`, since no stage imports
# another.
TAGGER = "wd14"

# What the sheet records as having filled it when the flow declares no tagger:
# no tag list and no model, so nothing unpinned shaped it (0032 design D3).
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
) -> tuple[Path | None, list[str]]:
    """Route this flow's tag list into a sheet, under that flow, with its warnings.

    `tagged` says whether the flow declares the tagger, and has no default
    because a default decides silently. Untagged, no list is read and every
    field is written empty for the person to fill (0032 design D3).
    `flow_digest` is recorded and never read (0033 design D5).

    **The fill is told nothing about flows beyond `tagged`, and reaches nothing
    at all.** It is handed a tag list, the schema, the vocabulary and the table,
    so the same code serves every flow without learning that flows exist; `flow`
    decides only which directory is read and written. A flow shares nothing, so
    the tag list read here is the one produced under this flow's own directory
    (design.md D5).

    **For a tagged flow, an absent tag list is a refusal.** A sheet with every
    field empty is legal and therefore silent, so writing one when the tagger
    never ran would hide the only thing the operator needs told. The rule that a
    missing tag artifact is an absent aid still holds for the *hosted* tagger,
    which contributes nothing to a sheet; it cannot hold for the local one the
    sheet is filled from (design.md D21).

    Returns the artifact's path, or None when this flow already had a sheet;
    a kept sheet filled from a superseded tag list is warned about (0048 design D5).
    """
    directory = run.directory(flow, SHEETS)
    kept = latest(directory)
    if kept is not None and not new_version:
        if not tagged:
            return None, []
        return None, _superseded(run, flow, directory, kept)
    version = (kept or 0) + 1

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
        validate(fields, schema, vocabulary)
    else:
        fields, made_by = _from_tag_list(
            run, flow, directory, version, schema, vocabulary, field_map
        )

    path = directory / artifact_name(version)
    artifact: Sheet = {
        "schema": SHEET_FILE.schema,
        "producer": made_by,
        "schema_document": {"name": schema.name},
        "vocabulary": vocabulary_identity(vocabulary),
        "field_map": field_map_identity(field_map),
        "flow_digest": flow_digest,
        "fields": fields,
    }
    write(path, SHEET_FILE, artifact)
    return path, []


def _superseded(run: Run, flow: str, directory: Path, kept: int) -> list[str]:
    """Return a warning when the kept sheet's tag list is below the flow's latest.

    A sheet it cannot read, or one with no list number, gives none: review
    refuses an unreadable sheet by name.
    """
    newest = latest(run.directory(flow, WD14))
    if newest is None:
        return []
    try:
        filled = read(directory / artifact_name(kept), SHEET_FILE)
    except Refusal:
        return []
    producer = filled.get("producer")
    source = producer.get("from") if isinstance(producer, dict) else None
    # `bool` is an `int`, and a hand-edited `true` is not a list number.
    if not isinstance(source, int) or isinstance(source, bool) or source >= newest:
        return []
    return [
        f"{run.id}/{flow}: sheet {kept:03d} was filled from "
        f"{WD14}/{artifact_name(source)}, and {WD14}/{artifact_name(newest)} "
        f"is newer; run `python -m isekai sheet --flow {flow} --new-version {run.id}`"
    ]


def _from_tag_list(
    run: Run,
    flow: str,
    directory: Path,
    version: int,
    schema: Schema,
    vocabulary: Vocabulary,
    field_map: FieldMap,
) -> tuple[dict[str, list[str]], SheetProducer]:
    """Return the checked fields routed from this flow's tag list, and who filled them.

    Refuses naming `tag` when the list is absent, and records nothing: running
    `tag` is the fix, and a record would bar the sheet that follows. The budget is
    checked next; a damaged list or a tag outside the vocabulary is then recorded
    as permanent, since this stage fails the same way every time (0048 design D4).
    """
    listed_dir = run.directory(flow, WD14)
    source = latest(listed_dir)
    if source is None:
        raise Refusal(
            f"{run.id}: there is no tag list to fill a sheet for {flow} from; run "
            f"`python -m isekai tag --flow {flow} {run.id}` first, "
            f"which writes {flow}/{WD14}/"
        )

    check_budget(STAGE, directory, version, run)
    try:
        fields, made_by = _route(run, flow, source, schema, field_map)
        validate(fields, schema, vocabulary)
    except Refusal as failed:
        detail = str(failed)
        record = record_failure(
            directory, version, "permanent", {"stage": STAGE, "detail": detail}
        )
        raise refusal_for(
            STAGE, run.id, "permanent", detail, record, SHEETS, STAGE, flow, STAGE
        ) from failed
    return fields, made_by


def _route(
    run: Run, flow: str, source: int, schema: Schema, field_map: FieldMap
) -> tuple[dict[str, list[str]], SheetProducer]:
    """Return the fields routed from tag list `source`, and who filled them.

    Refuses naming the fix when the list is damaged.
    """
    listed_path = run.directory(flow, WD14) / artifact_name(source)
    listed = read(listed_path, WD14_FILE)
    remedy = (
        f"run `python -m isekai tag --flow {flow} --new-version {run.id}`, "
        f"then `python -m isekai sheet --flow {flow} --new-version {run.id}`"
    )
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
