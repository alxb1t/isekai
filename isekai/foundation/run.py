"""The run directory: the only thing the four pipeline stages share.

A photograph becomes a run, and from then on every stage is handed a path inside
that run and hands back a numbered artifact. No stage reads another's output
directly, no stage holds state between invocations, and nothing outside this
module and its siblings decides what a file is called.

**Four properties carry the whole state model, and each is here rather than in a
convention:**

- **A run is identified by its photograph's bytes.** The id is a prefix of the
  photograph's SHA-256 plus a sanitised filename stem, so the same bytes reach the
  same directory -- re-offering a photograph is a resume, not a duplicate -- and a
  directory listing is still readable by a person.
- **Every artifact is written temp-then-replace.** Resume treats the presence of
  an artifact as proof its stage finished, so a truncated file under a final name
  would make resume skip a stage that never completed. Atomicity is a precondition
  of the state model, not a nicety.
- **Every "is this done?" test is a directory listing.** A filename carries
  exactly what resume decides on -- the version number, and approval where the
  concept applies -- and nothing else. What produced an artifact lives inside it
  and is read by a person, never by control flow.
- **A failure is an attempt, never a completion.** An error record is a *sibling*
  of the artifact it failed to produce and does not consume its number, because
  two stages take their number from an upstream artifact and have no next number
  to advance to. The kind and the attempt ordinal are in the name, so the retry
  decision stays a listing.

The siblings `names.py`, `rundir.py`, `layout.py` and `failures.py` hold the
identity and the names, the run and its frame, the numbering and the edit files,
and the failure budgets. This module imports them and re-exports every name, so a
module outside the foundation imports a run's names from here (D62).

Stdlib only, and on `python -m isekai`'s import graph.
"""

import os
import shlex
from collections.abc import Sequence
from pathlib import Path

from isekai.foundation.artifacts import (
    RUN_FILE,
    DigestRecord,
    Frame,
    InstructionsRecord,
    write,
)
from isekai.foundation.atomic_write import write_atomically
from isekai.foundation.failures import (
    BUDGETS,
    Attempt,
    Kind,
    StageFailure,
    across,
    attempts,
    check_budget,
    exhausted,
    failure_named,
    failures_alone,
    record_failure,
)
from isekai.foundation.layout import (
    EDIT_COMPOSITE,
    EDIT_PLACEMENT,
    EDIT_RECORD,
    EDIT_STEM,
    _laid_out,
    approval_of,
    approved_versions,
    artifact_name,
    delete_edits,
    edit_at,
    edit_files,
    edit_numbers,
    edit_stem,
    group_of,
    is_approved,
    is_edit_file,
    is_render,
    is_seed,
    is_sidecar,
    is_version,
    latest,
    latest_artifact,
    next_edit,
    next_version,
    placement_file,
    render_groups,
    render_image,
    render_record,
    rendered,
    rendered_seeds,
    sheet_of,
    sidecars,
    versions,
)
from isekai.foundation.names import (
    APPROVED,
    ARTIFACT,
    CAPTIONS,
    DESCRIPTION,
    ERROR,
    FRAME_NAME,
    ID_DIGEST_CHARS,
    ID_SEPARATOR,
    ID_SLUG_CHARS,
    OUTPUTS,
    PHOTO,
    PHOTOGRAPH_VERBS,
    PROMPTS,
    REVIEW,
    SHEETS,
    SIGNATURE_BYTES,
    SOURCES,
    TAGS,
    WD14,
    digest_of,
    media_type,
    run_id,
    slug,
)
from isekai.foundation.refusal import Refusal
from isekai.foundation.rundir import Run, assign, run_at, runs_in

__all__ = [
    "APPROVED",
    "ARTIFACT",
    "BUDGETS",
    "CAPTIONS",
    "DATA_ROOT",
    "DESCRIPTION",
    "EDIT_COMPOSITE",
    "EDIT_PLACEMENT",
    "EDIT_RECORD",
    "EDIT_STEM",
    "ERROR",
    "FRAME_NAME",
    "ID_DIGEST_CHARS",
    "ID_SEPARATOR",
    "ID_SLUG_CHARS",
    "NEW_VERSION",
    "OUTPUTS",
    "PHOTO",
    "PHOTOGRAPH_VERBS",
    "PROMPTS",
    "REPOSITORY",
    "REVIEW",
    "RUNS_ROOT",
    "SHEETS",
    "SIGNATURE_BYTES",
    "SOURCES",
    "TAGS",
    "WD14",
    "Attempt",
    "Kind",
    "Run",
    "StageFailure",
    "across",
    "approval_of",
    "approved_versions",
    "artifact_name",
    "assign",
    "attempts",
    "check_budget",
    "constant_record",
    "delete_edits",
    "digest_of",
    "edit_at",
    "edit_files",
    "edit_numbers",
    "edit_stem",
    "exhausted",
    "failure_named",
    "failures_alone",
    "find_run",
    "group_of",
    "instructions_record",
    "is_approved",
    "is_edit_file",
    "is_render",
    "is_seed",
    "is_sidecar",
    "is_version",
    "latest",
    "latest_artifact",
    "media_type",
    "migrate_command",
    "next_edit",
    "next_version",
    "open_run",
    "photo_of",
    "placement_file",
    "record_failure",
    "refusal_for",
    "render_groups",
    "render_image",
    "render_record",
    "rendered",
    "rendered_at",
    "rendered_seeds",
    "run_at",
    "run_id",
    "runs_in",
    "sheet_of",
    "sidecars",
    "slug",
    "stage_command",
    "unmigrated",
    "versions",
]

# Everything a run produces or consumes lives under one gitignored root. The run
# directory holds a *copy of the photograph*, which is what makes a run
# reconstructable from disk and also what makes `runs/` hold personal photographs
# by construction -- so "nothing generated is outside the ignored root" is a
# structural fact here rather than one `.gitignore` line staying correct forever
# (D18). `models/` deliberately stays where it is: it is fetched from a
# pinned manifest and is re-derivable byte for byte, so its loss costs a
# re-download rather than the loss of work.
DATA_ROOT = Path(__file__).resolve().parent.parent.parent / ".data"
RUNS_ROOT = DATA_ROOT / "runs"

# The repository root, derived from `DATA_ROOT` rather than recomputed, so the
# two cannot drift apart: both are then anchored to one `__file__`. Named here
# because this module owns `DATA_ROOT` and `instructions_record` needs it, and a
# second derivation is a second thing to keep true.
REPOSITORY = DATA_ROOT.parent


def _run_for(digest: str, runs_root: Path) -> Run | None:
    """Return the existing run for `digest`, found by listing rather than by name.

    The id carries a *slug* as well as a digest prefix, and the slug comes from a
    filename somebody is free to change -- so resumption keys on the bytes and the
    readable half is decoration. The frame's full digest is checked against the
    whole hash, which is what turns a prefix collision from a silent mixing of two
    people's photographs into a refusal.
    """
    if not runs_root.is_dir():
        return None
    prefix = f"{digest[:ID_DIGEST_CHARS]}{ID_SEPARATOR}"
    for name in sorted(os.listdir(runs_root)):
        if not name.startswith(prefix):
            continue
        run = Run(name, runs_root / name)
        if not run.frame_path.exists():
            continue
        if run._photo_record("sha256") == digest:
            return run
        raise Refusal(
            f"{name} already holds a different photograph with the same "
            f"{ID_DIGEST_CHARS}-character digest prefix; rename that run "
            "directory to keep both, and offer this photograph again"
        )
    return None


def open_run(photo: Path, runs_root: Path = RUNS_ROOT) -> Run:
    """Return the run for `photo`'s bytes, creating it only if it is not there.

    The same bytes always reach the same directory, so offering a photograph a
    second time resumes its run and the artifacts already present decide what is
    left to do. Two photographs sharing a filename land in different runs, because
    the id is derived from content and the name is only the readable half.
    """
    body = _photo_bytes(photo)
    kind, suffix = media_type(body)
    digest = digest_of(body)
    existing = _run_for(digest, runs_root)
    if existing is not None:
        return existing

    identifier = run_id(digest, photo.stem)
    run = Run(identifier, runs_root / identifier)
    name = f"photo{suffix}"
    run.path.mkdir(parents=True, exist_ok=True)
    write_atomically(run.path / name, body)
    # The frame records what the photograph *is* and never where it came from: a
    # run that points at a file somebody later moved is not reconstructable, and
    # being reconstructable from disk is the frame's whole job.
    frame: Frame = {
        "schema": RUN_FILE.schema,
        "id": identifier,
        "photo": {
            "name": name,
            "sha256": digest,
            "bytes": len(body),
            "media_type": kind,
        },
    }
    write(run.frame_path, RUN_FILE, frame)
    return run


def find_run(photo: Path, runs_root: Path = RUNS_ROOT) -> Run | None:
    """Return the run for `photo`'s bytes when there is one, creating nothing."""
    return _run_for(digest_of(_photo_bytes(photo)), runs_root)


def _photo_bytes(photo: Path) -> bytes:
    """Return a photograph's bytes, refusing one that cannot be read."""
    try:
        return photo.read_bytes()
    except OSError as unreadable:
        raise Refusal(
            f"{photo.name}: cannot be read ({unreadable.strerror}); "
            "check the path and the file's permissions, then offer it again"
        ) from unreadable


def rendered_at(image: Path) -> tuple[Run, str, int, int]:
    """Return the run, flow, approval and seed a rendered image's path names.

    e.g. runs/0d4b…_ada/summon-anime-wai/outputs/001/1840266731.png
         -> (that run, "summon-anime-wai", 1, 1840266731)
    """
    group = image.absolute().parent
    flow_directory = group.parent.parent
    run_directory = flow_directory.parent
    run = Run(run_directory.name, run_directory)
    if not (is_seed(image.stem) and image.is_file() and _laid_out(image)):
        # A path inside a run names the run whose renders it can list.
        listed = (
            f"run `{stage_command(run, 'show')}` to list the seeds its renders "
            "wrote, and give the path of one"
            if (run_directory / FRAME_NAME).is_file()
            else "give the path of one"
        )
        raise Refusal(
            f"is not an image a render wrote; {listed}, "
            f"<run>/<flow>/{OUTPUTS}/<NNN>/<seed>.png"
        )
    return run, flow_directory.name, int(group.name), int(image.stem)


# The option that asks a stage verb for the next version of its file.
NEW_VERSION = ("--new-version",)


def stage_command(run: Run, verb: str, *flows: str, options: Sequence[str] = ()) -> str:
    """Return the command that runs `verb` on `run` for `flows`, as it is pasted.

    e.g. (run, "sheet", "f", options=NEW_VERSION)
         -> "python -m isekai sheet --flow f --new-version r"

    The run's own root is named whenever it is not the default, or the pasted
    command would look under `.data/runs` for a run that lives elsewhere.
    """
    root = run.path.parent
    naming = "".join(f" --flow {flow}" for flow in flows)
    runs = (
        ""
        if root.resolve() == RUNS_ROOT.resolve()
        else f" --runs {shlex.quote(str(root))}"
    )
    words = " ".join((*options, run.id))
    return f"python -m isekai {verb}{naming}{runs} {words}"


def migrate_command(run: Run) -> str:
    """Return the command that copies `run`'s description into `photo/`, as pasted.

    e.g. a run under `.data/runs` -> "python -m isekai migrate"
    """
    root = run.path.parent
    if root.resolve() == RUNS_ROOT.resolve():
        return "python -m isekai migrate"
    return f"python -m isekai migrate --runs {shlex.quote(str(root))}"


def unmigrated(run: Run) -> list[str]:
    """Return the kinds of description a flow of `run` holds and `photo/` lacks.

    In `DESCRIPTION`'s order; an error record alone is no artifact.
    e.g. a flow's `wd14/001.json` and no `photo/` -> ["wd14"]
    """
    return [
        kind
        for kind in DESCRIPTION
        if not versions(run.directory(PHOTO, kind))
        and any(versions(run.directory(flow, kind)) for flow in run.flows)
    ]


def photo_of(run: Run, stage: str) -> Path:
    """Return the directory of the photograph's `stage` in `run`, or refuse.

    A run whose description sits under its flows, not in `photo/` (D17), is
    refused before anything is written, so a stage that refuses leaves the run as
    it found it.
    e.g. (run, WD14) -> runs/<id>/photo/wd14
    """
    kinds = unmigrated(run)
    if kinds:
        named = (
            kinds[0] if len(kinds) == 1 else f"{', '.join(kinds[:-1])} and {kinds[-1]}"
        )
        verb = "sits" if len(kinds) == 1 else "sit"
        raise Refusal(
            f"{run.id}: its {named} {verb} under its flows, not in {PHOTO}/; run "
            f"`{migrate_command(run)}`, which copies them there"
        )
    return run.directory(PHOTO, stage)


def refusal_for(
    stage: str,
    run: Run,
    kind: Kind,
    detail: str,
    record: Path,
    area: str,
    verb: str,
    flow: str | None,
    budget: str,
) -> Refusal:
    """Build the refusal a stage raises after recording a failed attempt.

    One shape for both stages: what failed, how it failed, where the record is,
    and the command to run once what it names is fixed. Stated here beside
    `StageFailure` rather than twice, because the two stages differ only in nouns.

    **`flow` is threaded in rather than patched at the call sites.** A stage on a
    flow threads its flow in, since its verb names one with `--flow`; the
    photograph's stages, `caption` and `tag`, pass `None`, since theirs refuse one
    (D17). One
    argument makes the pasted command right for every caller at once.

    **And the flow is passed once, not twice.** The record's location is
    `<flow>/<area>/`, or `photo/<area>/` for `None`, so taking a ready-made
    `where` beside `flow` would be the same fact in two forms, with nothing but
    caller discipline holding them in agreement -- a refusal naming one flow's
    record and another flow's remedy is the exact class of defect this argument
    exists to close. `area` is the stage directory alone; this joins them.

    `budget` is the `BUDGETS` key. When the record refuses the next run -- it is
    permanent, or fills the budget -- the remedy deletes it first, since running
    again would only be refused.

    A failure above version 1 sits beside the version before it, which a bare
    rerun keeps as complete, so the command asks for the next version. `tag`
    runs both taggers, so its `--new-version` also writes a new version of the
    list that did not fail.
    """
    # `record_failure` names every record `NNN.error.…`.
    version = int(record.name[:3])
    asked = NEW_VERSION if version > 1 else ()
    flows = () if flow is None else (flow,)
    command = f"`{stage_command(run, verb, *flows, options=asked)}`"
    where = f"{PHOTO if flow is None else flow}/{area}/{record.name}"
    if exhausted(budget, record.parent, version):
        return Refusal(
            f"{run.id}: the {stage} failed ({kind}) -- {detail}; see {where}, fix "
            f"what it names and delete it, then run {command}"
        )
    return Refusal(
        f"{run.id}: the {stage} failed ({kind}) -- {detail}; see {where}, and run "
        f"{command} again once what it names is fixed"
    )


def instructions_record(path: Path) -> InstructionsRecord:
    """Return the path and digest of an instruction text, for a producer record.

    This is the variable the evidence says matters most: one change to a reader's
    instructions moved its score from 0.518 to 0.307 and manufactured nineteen
    identity marks. An artifact whose provenance names the model but not the
    instructions cannot explain its own result.
    """
    resolved = path.resolve()
    inside = resolved.is_relative_to(REPOSITORY)
    return {
        "path": str(resolved.relative_to(REPOSITORY)) if inside else resolved.name,
        "sha256": digest_of(path.read_bytes()),
    }


def constant_record(text: str) -> DigestRecord:
    """Return the digest of an instruction text this build holds, with no path.

    `instructions_record` above takes a `Path` and hashes the file behind it,
    which a producer whose instructions are a module constant cannot use: there
    is no file and no location, and **a record that invented a path would assert
    one that does not exist**.

    So the key is simply absent rather than empty or placeheld. A consumer asking
    where the text came from gets no answer, which is the true one -- it came
    from this build, and the digest is what identifies which build. Another
    file in the flow directory is refused: `joycaption.Modelfile` sits in
    `config/` for the same trade, and a tag prompt shapes the operator's reading rather
    than the render, so it makes no per-flow claim.
    """
    return {"sha256": digest_of(text.encode())}
