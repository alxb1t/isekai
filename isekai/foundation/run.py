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

import hashlib
import json
import os
import re
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
from isekai.foundation.refusal import Refusal

# Everything a run produces or consumes lives under one gitignored root. The run
# directory holds a *copy of the photograph*, which is what makes a run
# reconstructable from disk and also what makes `runs/` hold personal photographs
# by construction -- so "nothing generated is outside the ignored root" is a
# structural fact here rather than one `.gitignore` line staying correct forever
# (design.md D14). `models/` deliberately stays where it is: it is fetched from a
# pinned manifest and is re-derivable byte for byte, so its loss costs a
# re-download rather than the loss of work.
DATA_ROOT = Path(__file__).resolve().parent.parent.parent / ".data"
RUNS_ROOT = DATA_ROOT / "runs"

# The repository root, derived from `DATA_ROOT` rather than recomputed, so the
# two cannot drift apart: both are then anchored to one `__file__`. Named here
# because this module owns `DATA_ROOT`; `interface/wiring.py` spelled the same
# expression until v0.22 rehomed `instructions_record`, which needs it too, and
# a second derivation is a second thing to keep true.
REPOSITORY = DATA_ROOT.parent

# Enough of the digest to separate two photographs and few enough characters to
# leave the slug legible in a listing. The whole digest is in the frame.
ID_DIGEST_CHARS = 12

# What separates the digest from the slug. An underscore, because `slug` maps
# every unsafe character to a hyphen and a hyphenated slug left a reader no way to
# see where the digest ended. A slug can never contain an underscore, so the
# boundary is unambiguous. Nothing parses the id -- `startswith` on the prefix is
# its only use -- so this is readability alone (design.md D10).
ID_SEPARATOR = "_"

# How much of a filename stem survives into the id. A stem is a human's label,
# not an identifier, so it is truncated rather than refused.
ID_SLUG_CHARS = 32

# Anything outside this is replaced in a slug. Deliberately narrow: the id becomes
# a directory name and is interpolated into messages, so a stem carrying a path
# separator, a shell metacharacter or a control byte must not survive it.
_UNSAFE = re.compile(r"[^a-z0-9]+")

# The magic bytes the header parser on the render path reads, and the extension
# and media type each one *is*. The extension is derived from the bytes rather
# than copied from the source name: the rule is that a filename must not lie
# about its contents, and copying a `.jpg` that holds a PNG would enshrine the
# lie inside the run.
_SIGNATURES: tuple[tuple[bytes, str, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
)

# The frame: what the run is, written once when the run is created.
FRAME_NAME = "run.json"

# The stage directories, and the label an approved artifact carries. The run owns
# the layout, so a stage that needs another stage's directory asks the run rather
# than importing the stage -- which is what closed five of the six stage-to-stage
# edges (design.md D6). `approved` is here for the same reason: `review` writes it
# and both `generate` and the inspection command read it.
#
# **Every one of them sits under a flow**: `runs/<input-id>/<flow-id>/<stage>/`.
# Above the flow split is what every flow shares, and the only thing every flow
# shares is the input itself. Nesting stage-first meant adding a flow scattered
# four entries across four stage directories; flow-first, adding a flow adds one
# subtree and retiring one flow's work is removing one directory.
CAPTIONS = "captions"
WD14 = "wd14"
TAGS = "tags"
SHEETS = "sheets"
REVIEW = "review"
PROMPTS = "prompts"
OUTPUTS = "outputs"
APPROVED = "approved"

# `001`, and `001.approved` / `001.draft` where a stage has that concept.
ARTIFACT = re.compile(r"^(?P<version>\d{3})(?:\.(?P<label>[a-z]+))?\.json$")

# `001.error.1.transient` -- the version it stands in for, the attempt ordinal,
# and the kind, all decidable without opening anything.
_ERROR = re.compile(
    r"^(?P<version>\d{3})\.error\.(?P<attempt>\d+)\.(?P<kind>transient|permanent)\.json$"
)

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
# what `"wd14": 1` above already records for the other local producer.
#
# A missing entry here is not a missing feature, it is a crash: `BUDGETS[stage]`
# below is a bare lookup, and `across()` and `main()` both catch only `Refusal`
# -- so an unlisted stage name escapes as a raw traceback in a package where
# every failure is a named refusal (design.md D6).
BUDGETS: Mapping[str, int] = {
    "caption": 3,
    "wd14": 1,
    "tags": 3,
    "sheet": 1,
    "assemble": 1,
    "render": 1,
}

T = TypeVar("T")


# --- identity -----------------------------------------------------------------


def slug(stem: str) -> str:
    """Return the readable half of a run id: lowercase, hyphenated, bounded.

    A stem that survives nothing -- all punctuation, or empty -- yields `photo`,
    so the id is always `<digest>_<something>` and never ends in a bare underscore.
    Every unsafe character becomes a hyphen, which is why the id's own separator
    is an underscore: a slug can never contain one, so the boundary between the
    digest and the readable half is unambiguous (design.md D10).
    """
    cleaned = _UNSAFE.sub("-", stem.lower()).strip("-")[:ID_SLUG_CHARS].strip("-")
    return cleaned or "photo"


def digest_of(body: bytes) -> str:
    """Return the SHA-256 of `body`, lowercase and in full."""
    return hashlib.sha256(body).hexdigest()


def run_id(digest: str, stem: str) -> str:
    """Return the run id for a photograph: a digest prefix, then a readable slug."""
    return f"{digest[:ID_DIGEST_CHARS]}{ID_SEPARATOR}{slug(stem)}"


def media_type(body: bytes) -> tuple[str, str]:
    """Return the media type and canonical extension the photograph's bytes are.

    Read from the bytes, never from the name. A header this build cannot identify
    stops the run rather than defaulting -- the render path reads JPEG and PNG
    headers and nothing else, so a third format would fail later and further from
    the cause.
    """
    for signature, kind, suffix in _SIGNATURES:
        if body.startswith(signature):
            return kind, suffix
    raise Refusal(
        "this build reads JPEG and PNG photographs, and these bytes are neither; "
        "convert the photograph to JPEG or PNG and offer it again"
    )


# --- the run and its frame ----------------------------------------------------


@dataclass(frozen=True)
class Run:
    """One photograph's directory, and the frame that says what it is."""

    id: str
    path: Path

    @property
    def frame_path(self) -> Path:
        """Return the path of the run's frame."""
        return self.path / FRAME_NAME

    @property
    def frame(self) -> Frame:
        """Return the run's frame, parsed, with no version check."""
        parsed: Frame = json.loads(self.frame_path.read_text())
        return parsed

    @property
    def photo(self) -> Path:
        """Return the path of the photograph's copy inside the run."""
        return self.path / str(self.frame["photo"]["name"])

    @property
    def flows(self) -> list[str]:
        """Return the flows this run holds work for, by identifier.

        The run owns the layout, so the fact that a flow's work is one directory
        directly under the run is stated here and asked for elsewhere rather than
        re-derived by each caller.
        """
        if not self.path.is_dir():
            return []
        return sorted(path.name for path in self.path.iterdir() if path.is_dir())

    def directory(self, *parts: str) -> Path:
        """Return a stage's directory inside this run, whether or not it exists.

        Deliberately does not create it: a command that refuses must leave the run
        exactly as it found it, and an empty directory nobody asked for is a
        change. Every writer here creates its parent on the way past.
        """
        return self.path.joinpath(*parts)


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
        if run.frame["photo"]["sha256"] == digest:
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
    try:
        body = photo.read_bytes()
    except OSError as unreadable:
        raise Refusal(
            f"{photo.name}: cannot be read ({unreadable.strerror}); "
            "check the path and the file's permissions, then offer it again"
        ) from unreadable

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
    """Return the number the next artifact written into `directory` takes."""
    return (latest(directory) or 0) + 1


def artifact_name(version: int, label: str | None = None) -> str:
    """Return the filename an artifact takes, with its optional approval label."""
    return f"{version:03d}.json" if label is None else f"{version:03d}.{label}.json"


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
    found = [
        Attempt(
            int(match.group("attempt")),
            _kind(match.group("kind")),
            directory / name,
        )
        for name in os.listdir(directory)
        if (match := _ERROR.match(name)) and int(match.group("version")) == version
    ]
    return sorted(found, key=lambda recorded: recorded.attempt)


def _kind(name: str) -> Kind:
    """Narrow a filename's kind field to the two values the pattern allows."""
    return "permanent" if name == "permanent" else "transient"


def record_failure(
    directory: Path,
    version: int,
    kind: Kind,
    failure: Failure,
) -> Path:
    """Write an error record beside where `version`'s artifact would have gone.

    The failure does not consume the version number: a later successful attempt
    writes `version` itself, and the error records stay beside it.
    """
    ordinal = len(attempts(directory, version)) + 1
    path = directory / f"{version:03d}.error.{ordinal}.{kind}.json"
    record: ErrorRecord = {
        "schema": ERROR_FILE.schema,
        "version": version,
        "attempt": ordinal,
        "kind": kind,
        **failure,
    }
    write(path, ERROR_FILE, record)
    return path


def check_budget(stage: str, directory: Path, version: int, photo: str) -> None:
    """Refuse if `stage` may not attempt `version` again, naming why and where.

    A permanent failure short-circuits the count: it will fail the same way every
    time, so retrying it spends for nothing. A stage at its transient budget
    refuses too, because without one every resume retries every failure forever
    and at the rendering stage that costs money on every pass.
    """
    recorded = attempts(directory, version)
    if recorded and recorded[-1].kind == "permanent":
        raise Refusal(
            f"{photo}: {stage} failed permanently -- see "
            f"{recorded[-1].path.name} in {directory.name}/; read the record, fix "
            "what it names, then delete it to let this stage attempt again"
        )
    budget = BUDGETS[stage]
    if len(recorded) >= budget:
        raise Refusal(
            f"{photo}: {stage} has used its {budget} attempt"
            f"{'' if budget == 1 else 's'} -- see {recorded[-1].path.name} in "
            f"{directory.name}/; read the records, fix what they name, then "
            "delete them to let this stage attempt again"
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


def refusal_for(
    stage: str,
    run_id: str,
    kind: Kind,
    detail: str,
    record: Path,
    area: str,
    verb: str,
    flow: str,
) -> Refusal:
    """Build the refusal a stage raises after recording a failed attempt.

    One shape for both stages: what failed, how it failed, where the record is,
    and the command to run once what it names is fixed. Stated here beside
    `StageFailure` rather than twice, because the two stages differ only in nouns.

    **`flow` is threaded in rather than patched at the call sites.** Every stage
    verb has taken `--flow`, required, since v0.16, so the command this built
    without it was one argparse refuses -- and copy-pasting the remedy a refusal
    states got an operator a usage error instead of the fix. One argument makes
    that true of every caller at once, including the ones a later stage adds.

    **And the flow is passed once, not twice.** The record's location is
    `<flow>/<area>/`, so taking a ready-made `where` beside `flow` would be the
    same fact in two forms, with nothing but caller discipline holding them in
    agreement -- a refusal naming one flow's record and another flow's remedy is
    the exact class of defect this argument exists to close. `area` is the stage
    directory alone; this joins them.
    """
    return Refusal(
        f"{run_id}: the {stage} failed ({kind}) -- {detail}; "
        f"see {record.name} in {flow}/{area}/, and run "
        f"`python -m isekai {verb} --flow {flow}` again "
        "once what it names is fixed"
    )


def instructions_record(path: Path) -> InstructionsRecord:
    """Return the path and digest of an instruction text, for a producer record.

    This is the variable the evidence says matters most: one change to a reader's
    instructions moved its score from 0.518 to 0.307 and manufactured nineteen
    identity marks. An artifact whose provenance names the model but not the
    instructions cannot explain its own result (design.md D7).
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
    one that does not exist** (design.md D16).

    So the key is simply absent rather than empty or placeheld. A consumer asking
    where the text came from gets no answer, which is the true one -- it came
    from this build, and the digest is what identifies which build. The
    alternative considered and refused was another file in the flow directory:
    that is the trade v0.19 already priced when `joycaption.Modelfile` went to
    `scripts/` instead, and a tag prompt shapes the operator's reading rather
    than the render, so it makes no per-flow claim.
    """
    return {"sha256": digest_of(text.encode())}
