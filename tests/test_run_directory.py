"""The run directory: identity, the frame, numbering, atomicity, failure, refusal.

Every test here is a directory on `tmp_path`. Nothing reaches the network, and
nothing opens an artifact to decide whether a stage is done -- which is the
property under test as much as it is the way the tests are written.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

import isekai.foundation.atomic_write as atomic_write_module
from isekai.foundation.artifacts import (
    CAPTION_FILE,
    RUN_FILE,
    SHEET_FILE,
    Caption,
    Failure,
    Sheet,
    read,
    write,
    write_json,
)
from isekai.foundation.flow import Schema, load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    BUDGETS,
    DATA_ROOT,
    FRAME_NAME,
    RUNS_ROOT,
    Kind,
    Run,
    across,
    approved_versions,
    artifact_name,
    attempts,
    check_budget,
    instructions_record,
    is_approved,
    latest,
    next_version,
    open_run,
    record_failure,
    refusal_for,
    run_id,
    slug,
    versions,
    write_atomically,
)
from isekai.interface.cli import build_parser
from isekai.interface.wiring import Wiring, wiring, wiring_from
from isekai.pipeline.caption import FakeReader
from isekai.pipeline.generate import prompt_artifact, render
from isekai.pipeline.review import approve, review
from isekai.shared.vocabulary import Vocabulary
from tests.conftest import snapshot
from tests.fakes import FakeComfyClient
from tests.images import jpeg_bytes, png_bytes
from tests.stages import CAPTION_BRIEFING as BRIEFING_PATH
from tests.stages import caption, sheet, write_wd14

FLOW = "summon-anime-wai"

# Only a record's filename is read, so one failure serves every budget test.
_FAILURE: Failure = {"stage": "caption", "detail": "the reader timed out"}


@pytest.fixture
def runs(tmp_path: Path) -> Path:
    """Return an empty runs root, standing in for `.data/runs/`."""
    return tmp_path / "runs"


def _photo(tmp_path: Path, name: str, body: bytes) -> Path:
    """Write a photograph outside any run and return its path."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / name
    path.write_bytes(body)
    return path


# --- identity -----------------------------------------------------------------


@pytest.mark.spec("run-directory:identity:id-is-hash-and-slug")
def test_the_id_begins_with_a_digest_prefix_and_continues_with_the_stem(
    tmp_path: Path, runs: Path
) -> None:
    body = jpeg_bytes(800, 600)
    run = open_run(_photo(tmp_path, "Aunt Ada's Photo.jpg", body), runs)

    digest = run.frame["photo"]["sha256"]
    # An underscore, and the slug's own hyphens are what make it readable: with a
    # hyphen there is no way to see where the digest ends, and a slug can never
    # carry an underscore.
    assert run.id == f"{digest[:12]}_aunt-ada-s-photo"
    assert run.path.name == run.id
    assert run.id.count("_") == 1


@pytest.mark.spec("run-directory:identity:id-is-hash-and-slug")
def test_the_frame_records_the_whole_digest_not_just_the_prefix(
    tmp_path: Path, runs: Path
) -> None:
    run = open_run(_photo(tmp_path, "p.jpg", jpeg_bytes(800, 600)), runs)

    digest = run.frame["photo"]["sha256"]
    assert len(digest) == 64
    assert run.id.startswith(digest[:12])


@pytest.mark.spec("run-directory:identity:id-is-hash-and-slug")
@pytest.mark.parametrize(
    ("stem", "expected"),
    [
        ("holiday snap", "holiday-snap"),
        ("../../etc/passwd", "etc-passwd"),
        ("Ünïcödé", "n-c-d"),
        ("!!!", "photo"),
        ("", "photo"),
    ],
)
def test_the_slug_keeps_nothing_that_could_leave_the_directory(
    stem: str, expected: str
) -> None:
    assert slug(stem) == expected


@pytest.mark.spec("run-directory:identity:same-name-different-bytes-differ")
def test_two_photographs_sharing_a_filename_get_different_runs(
    tmp_path: Path, runs: Path
) -> None:
    first = open_run(_photo(tmp_path / "a", "p.jpg", jpeg_bytes(800, 600)), runs)
    second = open_run(_photo(tmp_path / "b", "p.jpg", jpeg_bytes(640, 480)), runs)

    assert first.id != second.id
    write_json(first.directory(FLOW, "captions") / "001.json", {})
    assert versions(second.path / FLOW / "captions") == []


@pytest.mark.spec("run-directory:identity:same-bytes-resume-the-same-run")
def test_the_same_photograph_twice_is_one_run(tmp_path: Path, runs: Path) -> None:
    body = jpeg_bytes(800, 600)
    first = open_run(_photo(tmp_path / "a", "p.jpg", body), runs)
    write_json(first.path / FLOW / "captions" / "001.json", {})

    second = open_run(_photo(tmp_path / "b", "renamed.jpg", body), runs)

    assert second.path == first.path
    assert sorted(os.listdir(runs)) == [first.id]
    assert versions(second.path / FLOW / "captions") == [1]


# --- the frame ----------------------------------------------------------------


@pytest.mark.spec("run-directory:frame:photograph-is-copied-in")
def test_the_photograph_is_copied_in_rather_than_pointed_at(
    tmp_path: Path, runs: Path
) -> None:
    body = jpeg_bytes(800, 600)
    source = _photo(tmp_path, "p.jpg", body)
    run = open_run(source, runs)

    assert run.photo.read_bytes() == body
    assert str(source) not in run.frame_path.read_text()
    assert str(source.parent) not in run.frame_path.read_text()


@pytest.mark.spec("run-directory:frame:extension-is-preserved")
def test_a_png_keeps_its_extension_and_its_media_type(
    tmp_path: Path, runs: Path
) -> None:
    run = open_run(_photo(tmp_path, "p.png", png_bytes(800, 600)), runs)

    assert run.photo.name.endswith(".png")
    assert run.frame["photo"]["media_type"] == "image/png"


@pytest.mark.spec("run-directory:frame:extension-is-preserved")
def test_a_png_named_jpg_is_stored_under_the_extension_its_bytes_are(
    tmp_path: Path, runs: Path
) -> None:
    # A filename that lies about its bytes does not get to carry the lie inside
    # the run: the extension is derived from the header, never copied.
    run = open_run(_photo(tmp_path, "lying.jpg", png_bytes(800, 600)), runs)

    assert run.photo.name == "photo.png"
    assert run.frame["photo"]["media_type"] == "image/png"


@pytest.mark.spec("run-directory:frame:digest-proves-the-copy")
def test_the_frame_records_the_digest_the_size_and_the_media_type(
    tmp_path: Path, runs: Path
) -> None:
    import hashlib

    body = jpeg_bytes(800, 600)
    run = open_run(_photo(tmp_path, "p.jpg", body), runs)

    photo = run.frame["photo"]
    assert photo["sha256"] == hashlib.sha256(run.photo.read_bytes()).hexdigest()
    assert photo["bytes"] == len(body)
    assert photo["media_type"] == "image/jpeg"


@pytest.mark.spec("run-directory:frame:digest-proves-the-copy")
def test_a_photograph_this_build_cannot_read_stops_the_run_naming_the_fix(
    tmp_path: Path, runs: Path
) -> None:
    with pytest.raises(Refusal) as refused:
        open_run(_photo(tmp_path, "p.tiff", b"II*\x00 not a jpeg or a png"), runs)

    assert "JPEG" in str(refused.value) and "PNG" in str(refused.value)
    assert "convert the photograph" in str(refused.value)
    assert not runs.exists()


# --- atomicity ----------------------------------------------------------------

# `write_atomically` lives in `isekai.foundation.atomic_write`; these patch that module
# by name rather than `run`, which merely imports it. Patching through `run` would
# have passed either way -- `run.os` IS the global `os` module object -- so naming
# the real subject is what makes these break on a move rather than sleep through
# it (design.md D4).


@pytest.mark.spec("run-directory:atomicity:interrupted-write-leaves-nothing")
def test_a_failed_write_leaves_no_artifact_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "captions" / "001.json"

    def interrupted(descriptor: int) -> None:
        raise OSError("the disk went away mid-write")

    monkeypatch.setattr(atomic_write_module.os, "fsync", interrupted)

    with pytest.raises(OSError):
        write_atomically(target, b"half a file")

    assert not target.exists()
    assert list(target.parent.iterdir()) == []


@pytest.mark.spec("run-directory:atomicity:interrupted-write-leaves-nothing")
def test_a_failed_rename_leaves_neither_the_artifact_nor_its_temporary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "captions" / "001.json"

    def refused(source: object, destination: object) -> None:
        raise OSError("the rename did not happen")

    monkeypatch.setattr(atomic_write_module.os, "replace", refused)

    with pytest.raises(OSError):
        write_atomically(target, b"a whole file that never lands")

    assert not target.exists()
    assert list(target.parent.iterdir()) == []


@pytest.mark.spec("run-directory:atomicity:interrupted-write-leaves-nothing")
def test_a_partial_write_is_never_mistaken_for_an_artifact(tmp_path: Path) -> None:
    directory = tmp_path / "captions"
    directory.mkdir()
    (directory / ".001.json.abcdef.partial").write_text("half a file")

    assert versions(directory) == []
    assert latest(directory) is None


@pytest.mark.spec("run-directory:atomicity:final-move-is-atomic")
def test_the_temporary_file_shares_the_artifacts_filesystem(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "captions" / "001.json"
    where: list[Path] = []
    real = atomic_write_module.tempfile.mkstemp

    def watched(dir: Path, prefix: str, suffix: str) -> tuple[int, str]:
        where.append(Path(dir))
        return real(dir=dir, prefix=prefix, suffix=suffix)

    monkeypatch.setattr(atomic_write_module.tempfile, "mkstemp", watched)
    write_atomically(target, b"whole")

    assert where == [target.parent]
    assert target.read_bytes() == b"whole"


@pytest.mark.spec("run-directory:atomicity:final-move-is-atomic")
def test_the_artifact_appears_at_its_final_path_in_one_step(tmp_path: Path) -> None:
    target = tmp_path / "captions" / "001.json"
    write_json(target, {"schema": CAPTION_FILE.schema})

    assert json.loads(target.read_text())["schema"]["name"] == "caption"
    assert [p.name for p in target.parent.iterdir()] == ["001.json"]


# --- numbering and provenance -------------------------------------------------


@pytest.mark.spec("run-directory:numbering:each-directory-counts-its-own")
def test_each_stage_numbers_within_its_own_directory(
    tmp_path: Path, runs: Path
) -> None:
    run = open_run(_photo(tmp_path, "p.jpg", jpeg_bytes(800, 600)), runs)
    captions, sheets = run.directory(FLOW, "captions"), run.directory(FLOW, "sheets")

    write_json(captions / artifact_name(next_version(captions)), {})
    write_json(captions / artifact_name(next_version(captions)), {})
    write_json(sheets / artifact_name(next_version(sheets)), {})

    assert versions(captions) == [1, 2]
    assert versions(sheets) == [1]


def _sheet_from_wd14(
    run: Run, version: int, schema: Schema, vocabulary: Vocabulary
) -> Sheet:
    """Fill a sheet from WD14 list `version`, and return what was written."""
    write_wd14(run, version=version)
    path = sheet(run, schema, vocabulary, tags=None)
    assert path is not None
    return read(path, SHEET_FILE)


@pytest.mark.spec("run-directory:numbering:each-directory-counts-its-own")
def test_the_link_between_stages_is_the_producer_record(
    tmp_path: Path, runs: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = open_run(_photo(tmp_path, "p.jpg", jpeg_bytes(800, 600)), runs)

    written = _sheet_from_wd14(run, 2, schema, vocabulary)

    assert written["producer"]["from"] == 2
    assert "counter" not in written


@pytest.mark.spec("run-directory:provenance:artifact-declares-its-schema")
def test_every_artifact_carries_a_schema_name_and_an_integer_version(
    tmp_path: Path, runs: Path
) -> None:
    run = open_run(_photo(tmp_path, "p.jpg", jpeg_bytes(800, 600)), runs)
    path = caption(run, FakeReader())
    assert path is not None

    artifact = read(path, CAPTION_FILE)

    assert artifact["schema"]["name"] == "caption"
    assert isinstance(artifact["schema"]["version"], int)


@pytest.mark.spec("run-directory:provenance:producer-records-the-briefing")
def test_a_producer_records_the_briefings_path_and_digest(
    tmp_path: Path,
) -> None:
    # The record under assertion is the one the producer would write -- built by
    # `instructions_record` off the briefing the stage actually reads, never
    # constructed here. A record this test builds itself pins a literal the code
    # is free to stop writing.
    def written(briefing_path: Path) -> Caption:
        record = instructions_record(briefing_path)
        path = tmp_path / f"{record['sha256']}.json"
        artifact: Caption = {
            "schema": CAPTION_FILE.schema,
            "producer": {
                "implementation": "ollama",
                "models": [],
                "pinned": False,
                "briefing": record,
            },
            "prose": "the same prose either way",
        }
        write(path, CAPTION_FILE, artifact)
        return read(path, CAPTION_FILE)

    elsewhere = tmp_path / "other.md"
    elsewhere.write_text("Different standing instructions entirely.")

    one, other = written(BRIEFING_PATH), written(elsewhere)

    assert (
        one["producer"]["briefing"]["path"]
        == "flows/summon-anime-wai/caption.briefing.md"
    )
    assert (
        one["producer"]["briefing"]["sha256"] != other["producer"]["briefing"]["sha256"]
    )


@pytest.mark.spec("run-directory:provenance:producer-records-its-source")
def test_a_producer_names_the_upstream_version_it_came_from(
    tmp_path: Path, runs: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = open_run(_photo(tmp_path, "p.jpg", jpeg_bytes(800, 600)), runs)

    assert _sheet_from_wd14(run, 3, schema, vocabulary)["producer"]["from"] == 3


@pytest.mark.spec("run-directory:provenance:unpinned-producer-is-declared")
def test_an_unpinnable_producer_says_so_rather_than_claiming_a_pin(
    tmp_path: Path, runs: Path
) -> None:
    run = open_run(_photo(tmp_path, "p.jpg", jpeg_bytes(800, 600)), runs)
    path = caption(run, FakeReader(models=("x",)))
    assert path is not None

    producer = read(path, CAPTION_FILE)["producer"]

    assert producer["pinned"] is False
    assert "revision" not in producer
    assert "sha256" not in producer


# --- schema refusal -----------------------------------------------------------


@pytest.mark.spec("run-directory:schema:unknown-version-is-refused")
def test_an_artifact_from_a_newer_version_is_refused_without_being_parsed(
    tmp_path: Path,
) -> None:
    path = tmp_path / "001.json"
    path.write_text(
        json.dumps({"schema": {"name": "caption", "version": 2}, "prose": "unread"})
    )

    with pytest.raises(Refusal) as refused:
        read(path, CAPTION_FILE)

    message = str(refused.value)
    assert "001.json" in message
    assert "2" in message and str(CAPTION_FILE.version) in message
    assert "unread" not in message


@pytest.mark.spec("run-directory:schema:refusal-names-the-fix")
def test_the_schema_refusal_states_a_remedy_this_build_can_point_at(
    tmp_path: Path,
) -> None:
    path = tmp_path / "001.json"
    path.write_text(json.dumps({"schema": {"name": "caption", "version": 99}}))

    with pytest.raises(Refusal) as refused:
        read(path, CAPTION_FILE)

    message = str(refused.value)
    assert "upgrade isekai" in message
    assert f"delete {path}, then run the stage that wrote it again" in message
    # No migration command is offered, because this build ships none.
    assert "migrate" not in message


@pytest.mark.spec("run-directory:schema:unknown-version-is-refused")
def test_a_typed_read_refuses_an_unknown_version(tmp_path: Path) -> None:
    path = tmp_path / "001.json"
    write_json(path, {"schema": {"name": "caption", "version": 2}, "prose": "unread"})

    with pytest.raises(Refusal) as refused:
        read(path, CAPTION_FILE)

    assert str(refused.value) == (
        "001.json: declares schema version 2 and this build reads version 1; "
        f"upgrade isekai to a build that declares version 2, or delete {path}, "
        "then run the stage that wrote it again"
    )


@pytest.mark.spec("run-directory:schema:an-unreadable-artifact-is-refused-by-name")
@pytest.mark.parametrize(
    ("body", "cause"),
    [
        ('{"schema": {"name": "caption", "vers', "is not valid JSON"),
        ('[{"prose": "uninterpreted"}]', "is not a JSON object"),
        (
            '{"schema": ["uninterpreted"], "prose": "uninterpreted"}',
            "schema block is not an object",
        ),
    ],
)
def test_an_unreadable_artifact_is_refused_by_name(
    tmp_path: Path, body: str, cause: str
) -> None:
    path = tmp_path / "001.json"
    path.write_text(body)

    with pytest.raises(Refusal) as refused:
        read(path, CAPTION_FILE)

    message = str(refused.value)
    assert message.startswith("001.json: ")
    assert cause in message
    assert "uninterpreted" not in message
    assert f"delete {path}, then run the stage that wrote it again" in message


# --- completion by listing ----------------------------------------------------


@pytest.mark.spec("run-directory:readdir:approval-is-in-the-filename")
def test_approval_is_determinable_without_opening_the_file(tmp_path: Path) -> None:
    directory = tmp_path / "review" / "summon-anime-wai"
    directory.mkdir(parents=True)
    (directory / "001.draft.json").write_text("{}")
    (directory / "002.approved.json").write_text("{}")

    assert approved_versions(directory) == [2]
    assert is_approved("002.approved.json")
    assert not is_approved("001.draft.json")


@pytest.mark.spec("run-directory:readdir:approval-is-in-the-filename")
def test_deciding_approval_reads_no_file(tmp_path: Path) -> None:
    directory = tmp_path / "review" / "summon-anime-wai"
    directory.mkdir(parents=True)
    unreadable = directory / "001.approved.json"
    unreadable.write_text("{ this is not json at all")

    assert approved_versions(directory) == [1]


@pytest.mark.spec("run-directory:readdir:filename-carries-only-decidable-facts")
def test_a_filename_carries_its_version_and_its_approval_and_nothing_else() -> None:
    assert artifact_name(7) == "007.json"
    assert artifact_name(7, "approved") == "007.approved.json"
    assert artifact_name(7, "draft") == "007.draft.json"


@pytest.mark.spec("run-directory:readdir:filename-carries-only-decidable-facts")
def test_the_producing_model_appears_only_inside_the_artifact(
    tmp_path: Path, runs: Path
) -> None:
    run = open_run(_photo(tmp_path, "p.jpg", jpeg_bytes(800, 600)), runs)
    path = caption(run, FakeReader(models=("joycaption-beta-one-q4k",)))
    assert path is not None

    assert "joycaption" not in path.name
    assert "joycaption-beta-one-q4k" in path.read_text()


# --- failures and budgets -----------------------------------------------------


@pytest.mark.spec("run-directory:failure:error-is-a-sibling-of-its-artifact")
def test_an_error_record_sits_beside_where_its_artifact_would_have_gone(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "captions"
    directory.mkdir()

    record_failure(
        directory, 1, "transient", {"stage": "caption", "detail": "rate limited"}
    )

    assert versions(directory) == []
    assert next_version(directory) == 1


@pytest.mark.spec("run-directory:failure:kind-and-attempt-are-in-the-filename")
def test_the_attempts_ordinal_and_kind_are_in_the_filename(tmp_path: Path) -> None:
    directory = tmp_path / "captions"
    directory.mkdir()

    first = record_failure(directory, 1, "transient", _FAILURE)
    second = record_failure(directory, 1, "permanent", _FAILURE)

    assert first.name == "001.error.1.transient.json"
    assert second.name == "001.error.2.permanent.json"
    assert [(a.attempt, a.kind) for a in attempts(directory, 1)] == [
        (1, "transient"),
        (2, "permanent"),
    ]


@pytest.mark.spec("run-directory:failure:failed-attempts-survive-the-fix")
def test_a_failed_attempt_is_kept_when_a_later_one_succeeds(tmp_path: Path) -> None:
    directory = tmp_path / "captions"
    directory.mkdir()
    failure = record_failure(directory, 1, "transient", _FAILURE)

    write_json(
        directory / artifact_name(next_version(directory)),
        {"schema": {"name": "c", "version": 1}, "producer": {}},
    )

    assert failure.exists()
    assert versions(directory) == [1]


@pytest.mark.spec("run-directory:budget:permanent-is-never-retried")
def test_a_permanent_failure_is_refused_without_attempting_the_work(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "captions"
    directory.mkdir()
    record_failure(directory, 1, "permanent", _FAILURE)

    with pytest.raises(Refusal) as refused:
        check_budget("caption", directory, 1, Run("aunt-ada", tmp_path))

    message = str(refused.value)
    assert message.startswith("aunt-ada: ")
    assert "see captions/001.error.1.permanent.json;" in message


@pytest.mark.spec("run-directory:budget:at-budget-the-stage-refuses")
def test_a_stage_at_its_budget_refuses_naming_the_photograph_and_the_record(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "captions"
    directory.mkdir()
    for _ in range(BUDGETS["caption"]):
        record_failure(directory, 1, "transient", _FAILURE)

    with pytest.raises(Refusal) as refused:
        check_budget("caption", directory, 1, Run("aunt-ada", tmp_path))

    message = str(refused.value)
    assert message.startswith("aunt-ada: ")
    assert f"see captions/001.error.{BUDGETS['caption']}.transient.json;" in message


@pytest.mark.spec("run-directory:budget:at-budget-the-stage-refuses")
def test_a_deleted_record_is_never_overwritten(tmp_path: Path) -> None:
    directory = tmp_path / "captions"
    directory.mkdir()
    first = record_failure(directory, 1, "transient", _FAILURE)
    second = record_failure(directory, 1, "transient", _FAILURE)
    first.unlink()

    third = record_failure(directory, 1, "transient", _FAILURE)

    assert second.exists()
    assert third.name == "001.error.3.transient.json"
    assert [a.attempt for a in attempts(directory, 1)] == [2, 3]


@pytest.mark.spec("cli:refusals:refusal-names-the-remedy")
@pytest.mark.parametrize(
    ("kinds", "remedy"),
    [
        (["permanent"], "fix what it names and delete it, then run"),
        (
            ["transient"] * BUDGETS["caption"],
            "fix what it names and delete it, then run",
        ),
        (["transient"], "again once what it names is fixed"),
    ],
)
def test_a_record_that_refuses_the_next_run_names_its_deletion(
    tmp_path: Path, kinds: list[Kind], remedy: str
) -> None:
    directory = tmp_path / "summon-anime-wai" / "captions"
    directory.mkdir(parents=True)
    for kind in kinds:
        record = record_failure(directory, 1, kind, _FAILURE)

    refusal = refusal_for(
        "reader",
        "aunt-ada",
        kinds[-1],
        "timed out",
        record,
        "captions",
        "caption",
        "summon-anime-wai",
        "caption",
    )

    message = str(refusal)
    assert f"see summon-anime-wai/captions/{record.name}," in message
    assert remedy in message
    assert message.endswith(
        "`python -m isekai caption --flow summon-anime-wai aunt-ada`"
        + ("" if "delete" in remedy else " again once what it names is fixed")
    )


@pytest.mark.spec("run-directory:budget:at-budget-the-stage-refuses")
def test_a_stage_below_its_budget_is_allowed_to_attempt_again(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "captions"
    directory.mkdir()
    record_failure(directory, 1, "transient", _FAILURE)

    check_budget("caption", directory, 1, Run("aunt-ada", tmp_path))


@pytest.mark.spec("run-directory:budget:at-budget-the-stage-refuses")
def test_the_rendering_stages_budget_is_one() -> None:
    assert BUDGETS == {
        "caption": 3,
        "wd14": 1,
        "tags": 3,
        "sheet": 1,
        "assemble": 1,
        "render": 1,
    }


@pytest.mark.spec("tagging:budget:each-tagger-has-its-own-budget")
@pytest.mark.parametrize(("stage", "spend"), [("wd14", 1), ("tags", 3)])
def test_each_tagger_refuses_by_name_at_its_own_budget(
    tmp_path: Path, stage: str, spend: int
) -> None:
    assert BUDGETS[stage] == spend
    directory = tmp_path / stage
    directory.mkdir()
    for _ in range(spend):
        record_failure(directory, 1, "transient", _FAILURE)

    with pytest.raises(Refusal) as refused:
        check_budget(stage, directory, 1, Run("aunt-ada", tmp_path))

    message = str(refused.value)
    assert stage in message
    assert f"{stage}/" in message
    assert f"001.error.{spend}.transient.json" in message


@pytest.mark.spec("tagging:budget:each-tagger-has-its-own-budget")
@pytest.mark.parametrize("stage", ["wd14", "tags"])
def test_a_tagger_below_its_budget_attempts_again_rather_than_raising_keyerror(
    tmp_path: Path, stage: str
) -> None:
    directory = tmp_path / stage
    directory.mkdir()

    check_budget(stage, directory, 1, Run("aunt-ada", tmp_path))


@pytest.mark.spec("run-directory:budget:one-failure-does-not-halt-the-batch")
def test_one_photographs_failure_does_not_cost_the_others_their_turn() -> None:
    done: list[str] = []

    def work(name: str) -> None:
        if name == "bad":
            raise Refusal(f"{name}: no")
        done.append(name)

    refused = across(["a", "bad", "b"], work)

    assert done == ["a", "b"]
    assert refused == ["bad: no"]


@pytest.mark.spec("run-directory:budget:one-failure-does-not-halt-the-batch")
def test_every_failure_is_reported_together_at_the_end() -> None:
    def work(name: str) -> None:
        raise Refusal(f"{name}: no")

    assert across(["a", "b"], work) == ["a: no", "b: no"]


# --- the frame is an artifact too ---------------------------------------------


@pytest.mark.spec("run-directory:provenance:artifact-declares-its-schema")
def test_the_frame_declares_its_own_schema(tmp_path: Path, runs: Path) -> None:
    run = open_run(_photo(tmp_path, "p.jpg", jpeg_bytes(800, 600)), runs)

    assert run.frame_path.name == FRAME_NAME
    assert read(run.frame_path, RUN_FILE)["schema"] == {
        "name": "run",
        "version": RUN_FILE.version,
    }


@pytest.mark.spec("run-directory:schema:an-unreadable-artifact-is-refused-by-name")
def test_a_damaged_frame_names_a_remedy_that_works(tmp_path: Path, runs: Path) -> None:
    """A stage given the run id cannot reach a run with no frame; the path can."""
    photo = _photo(tmp_path, "p.jpg", jpeg_bytes(800, 600))
    run = open_run(photo, runs)
    run.frame_path.write_text("{not json")

    with pytest.raises(Refusal) as refused:
        _ = run.frame

    message = str(refused.value)
    assert f"delete {run.frame_path}" in message
    assert "offer the photograph again by its path" in message
    assert "run the stage that wrote it again" not in message

    run.frame_path.unlink()
    again = open_run(photo, runs)
    assert again == run and again.frame["photo"]["name"] == "photo.jpg"


@pytest.mark.spec_exempt("structural: the id helper, exercised directly")
def test_the_run_id_is_the_digest_prefix_and_the_slug() -> None:
    assert run_id("f" * 64, "Holiday Snap") == f"{'f' * 12}_holiday-snap"


@pytest.mark.spec("run-directory:identity:same-name-different-bytes-differ")
def test_a_digest_prefix_collision_is_refused_rather_than_mixed(
    tmp_path: Path, runs: Path
) -> None:
    # Two different photographs must never share a run. The id's readable half is
    # decoration, so the full digest in the frame is what decides.
    run = open_run(_photo(tmp_path / "a", "p.jpg", jpeg_bytes(800, 600)), runs)
    frame = run.frame
    frame["photo"]["sha256"] = "0" * 64
    write_json(run.frame_path, frame)

    with pytest.raises(Refusal) as refused:
        open_run(_photo(tmp_path / "b", "p.jpg", jpeg_bytes(800, 600)), runs)

    assert run.id in str(refused.value)
    assert "rename that run directory" in str(refused.value)


# --- the ignored roots --------------------------------------------------------

REPO = Path(__file__).resolve().parent.parent

# One path per directory a tracked producer names a photograph or a render under.
# `.data/` is the single ignored root (design.md D14), and v0.14 made it the only
# one that is generated into: the run directory holds a copy of the photograph,
# and `evaluation/baseline/build_contact_sheets.py` -- which pastes the reference
# photograph beside the renders -- now defaults `--renders` to `.data/baseline` and is
# documented to write its sheets under `.data/labels`, where it used to use
# `outputs/`. `.inputs/baseline` is the one exception and is not generated at
# all: an operator puts source photographs there by hand. All four hold a
# person's likeness by construction.
GENERATED = (
    ".data/runs/000000000000-ada/photo.jpg",
    ".data/baseline/ada/0.png",
    ".data/labels/pair-01.png",
    ".inputs/baseline/ada.png",
)


@pytest.mark.spec_exempt(
    "structural: the repository's own ignore rules, which no stage can assert"
)
@pytest.mark.parametrize("generated", GENERATED)
def test_every_directory_a_producer_writes_a_photograph_into_is_ignored(
    generated: str,
) -> None:
    # `git check-ignore` rather than a grep over `.gitignore`: the property is
    # that git ignores the path, and a rule that reads right while matching
    # nothing is exactly the failure this guards against.
    decided = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", generated],
        cwd=REPO,
        capture_output=True,
        text=True,
    )

    assert decided.returncode == 0, f"{generated} is not ignored: {decided.stderr}"


# --- where a run root may point -----------------------------------------------

# The defect the flag had was never "outside `.data/`" -- it was "inside the git
# working tree, where nothing ignores it". `--runs /Volumes/BigDisk/runs` is safe
# because version control cannot reach it; `--runs ./acceptance-runs` is the hole,
# and `run.py` copies the photograph into the run directory by construction, so
# such a directory holds personal photographs one `git add` from being published
# (design.md D7).


def _wiring(*flags: str) -> Wiring:
    """Build the real wiring the way the command line does, parser included.

    Through `build_parser` rather than a hand-built `Namespace`: the rule under
    test is about what `--runs` may be given, and fabricating the parser's output
    would leave the flag itself -- its name, its `type`, its default -- asserted
    by nothing.
    """
    return wiring(build_parser().parse_args(["show", *flags]))


@pytest.mark.spec("run-directory:containment:in-tree-run-root-is-refused")
def test_a_run_root_inside_the_working_tree_is_refused_before_anything_is_created() -> (
    None
):
    inside = REPO / "acceptance-runs"

    with pytest.raises(Refusal) as refused:
        _wiring("--runs", str(inside))

    message = str(refused.value)
    assert str(inside) in message
    assert ".data" in message
    # Refused before any run is created -- the check is on the root, not on the
    # first photograph offered to it.
    assert not inside.exists()


def _a_second_spelling_of(path: Path) -> Path | None:
    """Probe for a name the filesystem opens as `path` itself, or `None`.

    Probed rather than assumed. APFS is case-insensitive by default and the
    scenario below is only expressible where that is true; CI is Linux, where the
    swapped spelling is simply a path that does not exist and the probe says so.
    """
    text = str(path)
    swapped = next(
        (
            text[:i] + ch.swapcase() + text[i + 1 :]
            for i, ch in enumerate(text)
            if ch.isalpha()
        ),
        None,
    )
    if swapped is None:
        return None
    other = Path(swapped)
    try:
        return other if path.samefile(other) else None
    except OSError:
        return None


_ANOTHER_NAME = _a_second_spelling_of(REPO)


@pytest.mark.spec("run-directory:containment:containment-is-decided-by-identity")
@pytest.mark.skipif(
    _ANOTHER_NAME is None,
    reason="case-sensitive filesystem: no second spelling of the tree exists to give",
)
def test_containment_is_decided_by_identity_not_by_the_text_of_the_path() -> None:
    # `Path.resolve()` follows symlinks and drops `..`, but it does not fold case,
    # so this path compares as a different path and is the same directory. Text
    # cannot decide that; the filesystem can.
    assert _ANOTHER_NAME is not None
    inside = _ANOTHER_NAME / "acceptance-runs"

    with pytest.raises(Refusal) as refused:
        _wiring("--runs", str(inside))

    assert ".data" in str(refused.value)
    assert not inside.exists()


@pytest.mark.spec("run-directory:containment:in-tree-run-root-is-refused")
def test_wiring_from_cannot_be_used_to_skip_the_containment_guard() -> None:
    """The argv-free door is the same door.

    `wiring_from` exists so a front end that never parses a command line still
    cannot compose a `Wiring` without this check -- which is the whole reason the
    extraction was made, so it is asserted rather than assumed (design.md D1).
    """
    inside = REPO / "acceptance-runs"

    with pytest.raises(Refusal) as refused:
        wiring_from(runs=inside)

    assert str(inside) in str(refused.value)
    assert not inside.exists()


@pytest.mark.spec("run-directory:containment:external-run-root-is-accepted")
def test_a_run_root_outside_the_repository_is_accepted_and_runs_are_created_under_it(
    tmp_path: Path,
) -> None:
    # No containment check applies out here, because version control cannot reach
    # it -- which is what keeps the flag useful for a run on another disk.
    outside = tmp_path / "acceptance-runs"
    wired = _wiring("--runs", str(outside))

    made = open_run(_photo(tmp_path, "ada.jpg", jpeg_bytes(800, 600)), wired.runs_root)

    assert made.path.parent == outside
    assert (made.path / FRAME_NAME).is_file()


@pytest.mark.spec("run-directory:containment:default-is-the-ignored-root")
def test_the_default_run_root_is_under_the_ignored_data_root() -> None:
    # No `--runs` at all: the default is the parser's, not this test's.
    wired = _wiring()

    assert wired.runs_root == RUNS_ROOT
    assert DATA_ROOT in wired.runs_root.parents


# --- the layout: input above, flow below --------------------------------------


def _carry(
    run: Run, flow: str, schema: Schema, vocabulary: Vocabulary, seed: int = 42
) -> None:
    """Carry one run through every stage for one flow, with no network."""
    loaded = load_flow(flow)
    caption(run, FakeReader(prose="Brown hair, brown eyes."), flow=flow)
    sheet(
        run,
        schema,
        vocabulary,
        flow=flow,
    )
    review(run, flow)
    approve(run, flow, schema, vocabulary)
    prompt_artifact(run, loaded, schema)
    render(run, loaded, FakeComfyClient(), seeds=[seed], poll=0)


@pytest.mark.spec("run-directory:layout:stage-artifacts-live-under-the-flow")
def test_the_layout_is_the_input_above_and_every_stage_below_the_flow(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = open_run(
        _photo(tmp_path, "ada.jpg", jpeg_bytes(1200, 900)), tmp_path / "runs"
    )

    _carry(run, FLOW, schema, vocabulary)

    for stage in ("captions", "sheets", "review", "prompts", "outputs"):
        assert (run.path / FLOW / stage).is_dir(), stage
        assert not (run.path / stage).exists(), stage


@pytest.mark.spec("run-directory:layout:stage-artifacts-live-under-the-flow")
def test_the_layout_puts_nothing_above_the_flow_but_the_input_and_its_frame(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = open_run(
        _photo(tmp_path, "ada.jpg", jpeg_bytes(1200, 900)), tmp_path / "runs"
    )

    _carry(run, FLOW, schema, vocabulary)

    files = sorted(path.name for path in run.path.iterdir() if path.is_file())
    directories = sorted(path.name for path in run.path.iterdir() if path.is_dir())
    assert files == sorted((FRAME_NAME, run.photo.name))
    assert directories == [FLOW]


@pytest.mark.spec("run-directory:layout:a-second-flow-adds-one-subtree")
def test_the_layout_gains_one_subtree_when_a_second_flow_is_added(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = open_run(
        _photo(tmp_path, "ada.jpg", jpeg_bytes(1200, 900)), tmp_path / "runs"
    )
    _carry(run, FLOW, schema, vocabulary)
    before = snapshot(run.path / FLOW)

    caption(run, FakeReader(prose="Brown hair."), flow="summon-v2")

    assert sorted(path.name for path in run.path.iterdir() if path.is_dir()) == [
        FLOW,
        "summon-v2",
    ]
    assert snapshot(run.path / FLOW) == before


@pytest.mark.spec("run-directory:layout:the-input-is-copied-once")
def test_the_layout_holds_one_copy_of_the_input_however_many_flows_run(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = open_run(
        _photo(tmp_path, "ada.jpg", jpeg_bytes(1200, 900)), tmp_path / "runs"
    )

    _carry(run, FLOW, schema, vocabulary)
    caption(run, FakeReader(prose="Brown hair."), flow="summon-v2")

    copies = [path for path in run.path.rglob("*.jpg") if path.is_file()]
    assert copies == [run.photo]
    assert versions(run.path) == []
    assert (run.path / FRAME_NAME).is_file()


@pytest.mark.spec("run-directory:layout:one-flow-s-work-is-one-directory")
def test_the_layout_survives_one_flows_directory_being_removed(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    run = open_run(
        _photo(tmp_path, "ada.jpg", jpeg_bytes(1200, 900)), tmp_path / "runs"
    )
    _carry(run, FLOW, schema, vocabulary)
    caption(run, FakeReader(prose="Brown hair."), flow="summon-v2")
    kept = snapshot(run.path / FLOW)

    shutil.rmtree(run.path / "summon-v2")

    assert snapshot(run.path / FLOW) == kept
    assert run.photo.is_file()
    assert (run.path / FRAME_NAME).is_file()
