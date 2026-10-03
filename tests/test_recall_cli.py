import json
from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image

import evaluation.recall as recall
from evaluation.recall import Record
from evaluation.record import run_prefix
from isekai.boundary import wd14
from isekai.boundary.provision import DigestMismatch
from isekai.foundation.artifacts import APPROVED_FILE
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    APPROVED,
    ID_DIGEST_CHARS,
    OUTPUTS,
    REVIEW,
    Run,
    artifact_name,
    open_run,
)
from isekai.interface import wiring
from tests.stages import fake_tagger

FIXTURE = Path(__file__).resolve().parent / "recall"
SUMMON = "summon-anime-wai"
CONTROL = "control-anime-wai"
PINS = {"wd14/model.onnx": "m" * 64, "wd14/selected_tags.csv": "c" * 64}
# The tags a fake tagger sees in each render, by file name.
SEEN: dict[str, set[str]] = {
    "11.png": {"brown hair", "shirt"},
    "22.png": {"brown hair", "shirt", "jacket"},
    "33.png": {"blue hair"},
    "44.png": set(),
}


class _Tagger:
    """A fake reader over `SEEN`, recording every path it is handed."""

    def __init__(self, undecodable: frozenset[str] = frozenset()) -> None:
        self.undecodable = undecodable
        self.seen: list[Path] = []

    def __call__(self, path: Path) -> set[str]:
        self.seen.append(path)
        if path.name in self.undecodable:
            raise Refusal(f"{path} does not decode as an image")
        return SEEN[path.name]


def _approve(run: Run, flow: str, group: int, fields: dict[str, list[str]]) -> None:
    """Write the approval render group `group` is made from."""
    path = run.directory(flow, REVIEW, artifact_name(group, APPROVED))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema": APPROVED_FILE.schema, "fields": fields}))


def _render(run: Run, flow: str, group: int, *seeds: int) -> None:
    """Write one image per seed under render group `group`."""
    directory = run.directory(flow, OUTPUTS, f"{group:03d}")
    directory.mkdir(parents=True, exist_ok=True)
    for seed in seeds:
        Image.new("RGB", (8, 8)).save(directory / f"{seed}.png")


def _batch(root: Path, *, approve_second_group: bool = True) -> tuple[Path, Run, Run]:
    """Write two runs: `summon` rendered under two approvals, `control` under one."""
    runs = root / "batch" / "runs"
    for at, name in enumerate(("a.png", "b.png")):
        (root / "photos").mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (8, 8), (at * 90, 0, 0)).save(root / "photos" / name)
    a = open_run(root / "photos" / "a.png", runs)
    b = open_run(root / "photos" / "b.png", runs)
    _approve(
        a, SUMMON, 1, {"hair_colour": ["brown hair"], "clothes": ["shirt", "jacket"]}
    )
    _render(a, SUMMON, 1, 11, 22)
    if approve_second_group:
        _approve(a, SUMMON, 2, {"hair_colour": ["blue hair"], "bangs": ["swept bangs"]})
    _render(a, SUMMON, 2, 33)
    _approve(b, CONTROL, 1, {"eye_colour": ["green eyes"]})
    _render(b, CONTROL, 1, 44)
    return runs, a, b


def _run(
    monkeypatch: pytest.MonkeyPatch, tagger: _Tagger, runs: Path, *names: str
) -> int:
    monkeypatch.setattr(recall, "_reader", lambda models: (tagger, PINS))
    return recall.main([str(runs), *names])


def _record(runs: Path) -> Record:
    return json.loads((runs.parent / "recall.json").read_text())


@pytest.mark.spec("evaluation:recall:every-render-is-a-row")
def test_every_render_is_a_row_counted_against_its_groups_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs, _, _ = _batch(tmp_path)

    assert _run(monkeypatch, _Tagger(), runs) == 0

    rec = _record(runs)
    by_seed = {row["seed"]: row for row in rec["rows"]}
    assert set(by_seed) == {11, 22, 33, 44}
    assert {row["outcome"] for row in rec["rows"]} == {"read"}
    assert by_seed[11]["fields"]["clothes"] == {
        "asked": ["shirt", "jacket"],
        "missed": ["jacket"],
    }
    # Group 2's approval asks `blue hair`; group 1's would have been missed.
    assert by_seed[33]["fields"]["hair_colour"] == {
        "asked": ["blue hair"],
        "missed": [],
    }
    assert "bangs" not in by_seed[33]["fields"]
    assert rec["totals"][SUMMON]["hair_colour"] == {"read_back": 3, "asked": 3}
    assert rec["totals"][SUMMON]["clothes"] == {"read_back": 3, "asked": 4}
    assert rec["totals"][CONTROL]["eye_colour"] == {"read_back": 0, "asked": 1}


@pytest.mark.spec("evaluation:recall:an-unreadable-render-is-a-row")
def test_a_render_that_does_not_decode_is_its_own_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runs, _, _ = _batch(tmp_path)
    tagger = _Tagger(undecodable=frozenset({"22.png"}))

    assert _run(monkeypatch, tagger, runs) == 0

    outcomes = {row["seed"]: row["outcome"] for row in _record(runs)["rows"]}
    assert outcomes == {11: "read", 22: "unreadable", 33: "read", 44: "read"}
    assert "22.png does not decode" in capsys.readouterr().err


@pytest.mark.spec("evaluation:recall:a-render-without-its-approval-is-a-row")
def test_a_render_whose_approval_is_absent_is_its_own_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runs, _, _ = _batch(tmp_path, approve_second_group=False)
    tagger = _Tagger()

    assert _run(monkeypatch, tagger, runs) == 0

    outcomes = {row["seed"]: row["outcome"] for row in _record(runs)["rows"]}
    assert outcomes == {11: "read", 22: "read", 33: "no approval", 44: "read"}
    assert "002.approved.json is absent" in capsys.readouterr().err
    assert "33.png" not in {path.name for path in tagger.seen}


@pytest.mark.spec("evaluation:recall:a-render-without-its-approval-is-a-row")
def test_a_render_whose_approval_holds_a_field_that_is_not_tags_is_its_own_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runs, a, _ = _batch(tmp_path)
    damaged = a.directory(SUMMON, REVIEW, artifact_name(2, APPROVED))
    damaged.write_text(
        json.dumps(
            {"schema": APPROVED_FILE.schema, "fields": {"hair_colour": "blue hair"}}
        )
    )
    tagger = _Tagger()

    assert _run(monkeypatch, tagger, runs) == 0

    rows = {row["seed"]: row for row in _record(runs)["rows"]}
    assert rows[33]["outcome"] == "no approval"
    assert rows[33]["fields"] == {}
    assert "002.approved.json" in capsys.readouterr().err
    assert "33.png" not in {path.name for path in tagger.seen}


@pytest.mark.spec("evaluation:recall:named-runs-narrow-the-reading")
def test_named_runs_narrow_the_reading_and_an_unknown_name_refuses_first(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runs, a, b = _batch(tmp_path)
    tagger = _Tagger()

    assert _run(monkeypatch, tagger, runs, b.id) == 0
    assert {row["run"] for row in _record(runs)["rows"]} == {run_prefix(b.id)}
    assert {path.name for path in tagger.seen} == {"44.png"}

    (runs.parent / "recall.json").unlink()
    again = _Tagger()
    assert _run(monkeypatch, again, runs, a.id, "nobody") == 1
    assert "nobody" in capsys.readouterr().err
    assert again.seen == []
    assert not (runs.parent / "recall.json").exists()


@pytest.mark.spec("evaluation:recall:a-run-is-named-by-its-digest-prefix")
def test_a_row_names_its_run_by_its_digest_prefix_and_never_its_filename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    named = tmp_path / "photos" / "ada-lovelace.png"
    named.parent.mkdir()
    Image.new("RGB", (8, 8)).save(named)
    runs = tmp_path / "batch" / "runs"
    run = open_run(named, runs)
    _approve(run, SUMMON, 1, {"hair_colour": ["brown hair"]})
    _render(run, SUMMON, 1, 11)

    assert _run(monkeypatch, _Tagger(), runs) == 0

    written = (runs.parent / "recall.json").read_text()
    out = capsys.readouterr().out
    prefix = run.photo_record["sha256"][:ID_DIGEST_CHARS]
    assert "ada-lovelace" in run.id
    assert [row["run"] for row in json.loads(written)["rows"]] == [prefix]
    assert prefix in out
    assert "ada-lovelace" not in written + out


@pytest.mark.spec("evaluation:recall:the-record-names-the-tagger-and-its-floor")
def test_the_record_names_the_taggers_files_by_digest_and_its_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs, _, _ = _batch(tmp_path)

    assert _run(monkeypatch, _Tagger(), runs) == 0

    rec = _record(runs)
    assert rec["tagger"] == PINS
    assert rec["floor"] == wd14.FLOOR


@pytest.mark.spec("evaluation:recall:a-record-git-can-reach-is-refused")
def test_a_record_inside_the_working_tree_and_outside_the_ignored_root_is_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = tmp_path / "repository"
    runs, _, _ = _batch(repository)
    monkeypatch.setattr(wiring, "REPOSITORY", repository)
    monkeypatch.setattr(wiring, "DATA_ROOT", repository / ".data")
    tagger = _Tagger()

    assert _run(monkeypatch, tagger, runs) == 1

    refusal = capsys.readouterr().err
    assert str(runs.parent.resolve() / "recall.json") in refusal
    assert "then this command again" in refusal
    assert not (runs.parent / "recall.json").exists()
    assert tagger.seen == []


@pytest.mark.spec("evaluation:recall:the-record-names-the-tagger-and-its-floor")
def test_the_reader_records_each_file_the_tagger_verified_by_its_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pins = {
        wd14.LABELS_DEST: {"sha256": "b" * 64},
        wd14.MODEL_DEST: {"sha256": "a" * 64},
    }
    monkeypatch.setattr(
        wd14, "open_session", lambda models: replace(fake_tagger(), pins=pins)
    )

    _, digests = recall._reader(tmp_path)

    assert digests == {wd14.LABELS_DEST: "b" * 64, wd14.MODEL_DEST: "a" * 64}
    committed = json.loads((FIXTURE / "recall.json").read_text())
    assert set(committed["tagger"]) == set(digests)


@pytest.mark.spec("evaluation:pinned-artifacts:digest-mismatch-is-refused")
def test_a_tagger_file_that_does_not_match_its_pin_refuses_naming_the_fetch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runs, _, _ = _batch(tmp_path)

    def swapped(models: Path) -> wd14.LocalTagger:
        raise DigestMismatch(f"{wd14.MODEL_DEST}: expected {'a' * 64}, got {'f' * 64}")

    monkeypatch.setattr(wd14, "open_session", swapped)

    assert recall.main([str(runs)]) == 1

    refusal = capsys.readouterr().err
    assert refusal.startswith("refused: ")
    assert wd14.MODEL_DEST in refusal
    assert wd14.REMEDY in refusal
    assert not (runs.parent / "recall.json").exists()
