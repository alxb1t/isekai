"""The run directory: the only thing the four pipeline stages share.

A photograph becomes a run, and from then on every stage is handed a path inside
that run and hands back a numbered artifact. No stage reads another's output
directly, no stage holds state between invocations, and nothing outside this
module decides what a file is called.

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

Stdlib only, and on `python -m isekai`'s import graph.
"""

import os
import shlex
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeVar

from isekai.foundation.artifacts import (
    ERROR_FILE,
    RUN_FILE,
    DigestRecord,
    ErrorRecord,
    Failure,
    Frame,
    InstructionsRecord,
    write,
)
from isekai.foundation.atomic_write import write_atomically
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
    is_seed,
    is_version,
    latest,
    latest_artifact,
    next_edit,
    next_version,
    placement_file,
    sheet_of,
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
from isekai.foundation.rundir import Run, assign

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
    "is_seed",
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
    "rendered_at",
    "run_id",
    "sheet_of",
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

Kind = Literal["transient", "permanent"]

# What each stage may spend before it costs a person's attention instead. Reading
# and sorting are cheap and flaky, so they get three; assembling and rendering get
# one, because a render that has failed once should be looked at rather than paid
# for again.
#
# The two taggers are split on the same axis rather than sharing a number.
# `tags` is a hosted model over HTTP, so it is flaky in exactly the way `caption`
# is and gets its three. `wd14` is a local pass over a
# digest-verified graph, and what can still fail there is **this photograph's own
# bytes** -- a header no decoder can read. That is permanent by construction, so
# one attempt is the whole budget, exactly as `assemble` and `render` are one.
#
# The two file conditions that would fail identically for every input -- an
# absent model, bytes that disagree with the pin -- are deliberately **not**
# counted here. They are conditions about this build rather than about a
# photograph, so the tagger is opened before the stage's `try` and refuses the
# batch once instead of writing one error record per input for a single fix.
#
# **`sheet` is one for `wd14`'s reason.** It reached a hosted model once and had
# three; it is now a dictionary lookup over an artifact already on disk, so there
# is no transient failure left for a second attempt to catch -- which is exactly
# what `"wd14": 1` above already records for the other local producer. The stage
# records every failure as permanent, so a second attempt waits on a deletion.
#
# A missing entry here is not a missing feature, it is a crash: `BUDGETS[stage]`
# below is a bare lookup, and `across()` and `main()` both catch only `Refusal`
# -- so an unlisted stage name escapes as a raw traceback in a package where
# every failure is a named refusal.
BUDGETS: Mapping[str, int] = {
    "caption": 3,
    "wd14": 1,
    "tags": 3,
    "sheet": 1,
    "assemble": 1,
    "render": 1,
}

T = TypeVar("T")


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


# --- failures and budgets -----------------------------------------------------


@dataclass(frozen=True)
class Attempt:
    """One recorded failure against a known artifact: how it failed, and where.

    It carries no version: `attempts` is always asked about one, so storing it
    here would be the caller's own argument handed back.
    """

    attempt: int
    kind: Kind
    path: Path


def attempts(directory: Path, version: int) -> list[Attempt]:
    """Return the failures recorded against `version`, in attempt order.

    A listing. Counting attempts, and deciding whether the last one was permanent,
    are both retry decisions, which is why the kind and the ordinal are in the
    name rather than inside the file.
    """
    if not directory.is_dir():
        return []
    found: list[Attempt] = []
    for name in os.listdir(directory):
        named = failure_named(name)
        if named is not None and named[0] == version:
            found.append(Attempt(named[1], named[2], directory / name))
    return sorted(found, key=lambda recorded: recorded.attempt)


def failure_named(name: str) -> tuple[int, int, Kind] | None:
    """Return the version, attempt and kind a failure record's name carries.

    None when `name` is not a failure record.
    e.g. `"002.error.1.transient.json"` → `(2, 1, "transient")`
    """
    match = ERROR.match(name)
    if match is None:
        return None
    kind: Kind = "permanent" if match.group("kind") == "permanent" else "transient"
    return int(match.group("version")), int(match.group("attempt")), kind


def failures_alone(directory: Path) -> list[Path] | None:
    """Return the failure records `directory` holds when they are all it holds, sorted.

    None when it is no directory or holds anything else; an empty one gives [].
    e.g. outputs/002/ holding 002.error.1.permanent.json alone -> [that record]
    """
    if not directory.is_dir():
        return None
    held = sorted(directory.iterdir())
    if any(not path.is_file() or failure_named(path.name) is None for path in held):
        return None
    return held


def record_failure(
    directory: Path,
    version: int,
    kind: Kind,
    failure: Failure,
) -> Path:
    """Write an error record beside where `version`'s artifact would have gone.

    The failure does not consume the version number: a later successful attempt
    writes `version` itself, and the error records stay beside it. The attempt is
    the highest recorded plus one, so deleting an earlier record never makes the
    next one overwrite a later one.
    """
    recorded = attempts(directory, version)
    ordinal = recorded[-1].attempt + 1 if recorded else 1
    path = directory / f"{version:03d}.error.{ordinal}.{kind}.json"
    # By name, never the failure spread whole: its keys must not land among
    # ours. The seed sits between stage and detail, as `tests/golden/error.json`.
    record: ErrorRecord = {
        "schema": ERROR_FILE.schema,
        "version": version,
        "attempt": ordinal,
        "kind": kind,
        "stage": failure["stage"],
        **({"seed": failure["seed"]} if "seed" in failure else {}),
        "detail": failure["detail"],
    }
    write(path, ERROR_FILE, record)
    return path


def _spent(
    stage: str, recorded: Sequence[Attempt]
) -> Literal["permanent", "budget"] | None:
    """Return why `recorded` bars `stage` another attempt, or None if it does not.

    The one statement of the retry rule: a permanent record short-circuits the
    count, and otherwise the stage may try until it is at its budget.
    """
    if not recorded:
        return None
    if recorded[-1].kind == "permanent":
        return "permanent"
    return "budget" if len(recorded) >= BUDGETS[stage] else None


def exhausted(stage: str, directory: Path, version: int) -> bool:
    """Say whether `stage` may not attempt `version` again: permanent, or at budget."""
    return _spent(stage, attempts(directory, version)) is not None


def check_budget(stage: str, directory: Path, version: int, run: Run) -> None:
    """Refuse if `stage` may not attempt `version` again, naming why and where.

    A permanent failure short-circuits the count: it will fail the same way every
    time, so retrying it spends for nothing. A stage at its transient budget
    refuses too, because without one every resume retries every failure forever
    and at the rendering stage that costs money on every pass.
    e.g. `see photo/wd14/001.error.1.permanent.json`
    """
    recorded = attempts(directory, version)
    why = _spent(stage, recorded)
    if why is None:
        return
    where = recorded[-1].path.relative_to(run.path)
    if why == "permanent":
        raise Refusal(
            f"{run.id}: {stage} failed permanently -- see {where}; read the "
            "record, fix what it names, then delete it to let this stage attempt "
            "again"
        )
    budget = BUDGETS[stage]
    raise Refusal(
        f"{run.id}: {stage} has used its {budget} attempt"
        f"{'' if budget == 1 else 's'} -- see {where}; read the records, fix what "
        "they name, then delete them to let this stage attempt again"
    )


def across(items: Sequence[T], work: Callable[[T], None]) -> list[str]:
    """Run `work` over every item, collecting refusals instead of stopping at one.

    One photograph's failure must not cost the other nine their turn, and a
    failure reported when it happens scrolls off before the batch ends -- so every
    refusal is collected and returned for the caller to report together.
    """
    refused: list[str] = []
    for item in items:
        try:
            work(item)
        except Refusal as refusal:
            refused.append(str(refusal))
    return refused


class StageFailure(Exception):
    """A model call did not return what a stage can use, and the kind says what next."""

    def __init__(self, kind: Kind, detail: str) -> None:
        """Carry the kind and the detail an error record is written from."""
        super().__init__(detail)
        self.kind = kind
        self.detail = detail


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
