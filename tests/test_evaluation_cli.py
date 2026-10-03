import json
from pathlib import Path

import pytest
from PIL import Image

import evaluation.__main__ as entry
from evaluation.cohort import Vector
from evaluation.eval_models import DETECTOR, ENCODER, load_eval_manifest
from evaluation.face import load
from isekai.boundary.provision import digest_of, entry_for
from isekai.foundation.flow import FLOWS_DIR
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import ID_DIGEST_CHARS, OUTPUTS, open_run
from isekai.interface import wiring
from tests.images import oversized_png

FLOW = "summon-anime-wai"
# Each image's face embedding, by file name; an absent name has no face found.
VECTORS: dict[str, Vector] = {
    "p1-1.png": [1.0, 0.0, 0.0],
    "p1-2.png": [0.9, 0.1, 0.0],
    "p2-1.png": [0.0, 1.0, 0.0],
    "11.png": [1.0, 0.05, 0.0],
}


class _Embedder:
    """A fake embedder reading `VECTORS`, recording every path it is handed."""

    def __init__(self, vectors: dict[str, Vector]) -> None:
        self.vectors = vectors
        self.seen: list[Path] = []

    def __call__(self, path: Path) -> Vector | None:
        self.seen.append(path)
        return self.vectors.get(path.name)


def _batch(root: Path) -> tuple[Path, Path]:
    """Write a cohort of three photographs and a batch of their runs.

    p1-1 is rendered and its face found, p1-2 is rendered with no face found, and
    p2-1 is never rendered.
    """
    cohort, runs = root / "cohort", root / "batch" / "runs"
    for colour, name in enumerate(sorted(VECTORS.keys() - {"11.png"})):
        (cohort / name[:2]).mkdir(parents=True, exist_ok=True)
        photo = cohort / name[:2] / name
        Image.new("RGB", (8, 8), (colour * 60, 0, 0)).save(photo)
        run = open_run(photo, runs)
        seed = {"p1-1.png": 11, "p1-2.png": 22}.get(name)
        if seed is not None:
            group = run.directory(FLOW, OUTPUTS, "001")
            group.mkdir(parents=True)
            Image.new("RGB", (8, 8)).save(group / f"{seed}.png")
    return runs, cohort


@pytest.mark.spec("evaluation:cohort:a-faceless-photograph-is-refused")
def test_a_cohort_photograph_with_no_face_refuses_before_any_render_is_opened(
    tmp_path: Path,
) -> None:
    runs, cohort = _batch(tmp_path)
    embed = _Embedder({k: v for k, v in VECTORS.items() if k != "p2-1.png"})

    with pytest.raises(Refusal, match="p2-1.png"):
        entry.score(runs, cohort, embed, FLOWS_DIR)
    assert all(path.is_relative_to(cohort) for path in embed.seen)


@pytest.mark.spec("evaluation:table:a-failure-is-a-row")
def test_a_render_with_no_face_and_an_unrendered_photograph_are_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    runs, cohort = _batch(tmp_path)
    monkeypatch.setattr(entry, "_embedder", lambda models: _Embedder(VECTORS))

    code = entry.main([str(runs), "--cohort", str(cohort)])

    rows = json.loads((runs.parent / "evaluation.json").read_text())["flows"][FLOW]
    outcomes = {row["photograph"]: row["outcome"] for row in rows["rows"]}
    assert code == 0
    assert outcomes == {
        "p1/p1-1.png": "hit",
        "p1/p1-2.png": "no face found",
        "p2/p2-1.png": "not rendered",
    }
    assert "p2/p2-1.png  not rendered" in capsys.readouterr().out


class _Decoding(_Embedder):
    """The fake embedder, opening each image as the real one does first."""

    def __call__(self, path: Path) -> Vector | None:
        load(path)
        return super().__call__(path)


@pytest.mark.spec("evaluation:cohort:an-undecodable-file-is-refused")
def test_a_cohort_file_that_is_not_an_image_refuses_naming_it(tmp_path: Path) -> None:
    runs, cohort = _batch(tmp_path)
    (cohort / "p1" / "notes.txt").write_text("not a photograph")
    embed = _Decoding(VECTORS)

    with pytest.raises(Refusal, match=r"notes\.txt.*remove it from the cohort"):
        entry.score(runs, cohort, embed, FLOWS_DIR)
    assert all(path.is_relative_to(cohort) for path in embed.seen)


@pytest.mark.spec("evaluation:table:an-unreadable-render-is-a-row")
def test_a_render_that_does_not_decode_is_its_own_row(tmp_path: Path) -> None:
    runs, cohort = _batch(tmp_path)
    (render,) = runs.glob(f"*/{FLOW}/{OUTPUTS}/001/22.png")
    render.write_bytes(b"\x89PNG trunc")
    vectors = {**VECTORS, "22.png": [0.9, 0.1, 0.0]}

    rec, _ = entry.score(runs, cohort, _Decoding(vectors), FLOWS_DIR)

    outcomes = {r["photograph"]: r["outcome"] for r in rec["flows"][FLOW]["rows"]}
    assert outcomes == {
        "p1/p1-1.png": "hit",
        "p1/p1-2.png": "unreadable",
        "p2/p2-1.png": "not rendered",
    }


@pytest.mark.spec("evaluation:table:an-unreadable-render-is-a-row")
def test_a_render_too_large_to_open_is_its_own_row(tmp_path: Path) -> None:
    runs, cohort = _batch(tmp_path)
    (render,) = runs.glob(f"*/{FLOW}/{OUTPUTS}/001/22.png")
    render.write_bytes(oversized_png())
    vectors = {**VECTORS, "22.png": [0.9, 0.1, 0.0]}

    rec, notes = entry.score(runs, cohort, _Decoding(vectors), FLOWS_DIR)

    outcomes = {r["photograph"]: r["outcome"] for r in rec["flows"][FLOW]["rows"]}
    assert outcomes["p1/p1-2.png"] == "unreadable"
    assert outcomes["p1/p1-1.png"] == "hit"
    assert any("22.png does not decode" in note for note in notes)


@pytest.mark.spec("evaluation:table:the-latest-group-is-ranked")
def test_the_first_seed_of_the_latest_render_group_is_the_one_ranked(
    tmp_path: Path,
) -> None:
    runs, cohort = _batch(tmp_path)
    run = open_run(cohort / "p1" / "p1-1.png", runs)
    later = run.directory(FLOW, OUTPUTS, "002")
    later.mkdir()
    for seed in (33, 44):
        Image.new("RGB", (8, 8)).save(later / f"{seed}.png")
    vectors = {**VECTORS, "33.png": [0.0, 1.0, 0.0], "44.png": [1.0, 0.0, 0.0]}
    embed = _Embedder(vectors)

    rec, _ = entry.score(runs, cohort, embed, FLOWS_DIR)

    row = next(
        r for r in rec["flows"][FLOW]["rows"] if r["photograph"] == "p1/p1-1.png"
    )
    assert (row["seed"], row["also_rendered"]) == (33, [11, 44])
    assert row["outcome"] == "miss"
    assert [p.name for p in embed.seen if p.parent.parent == later.parent] == ["33.png"]


@pytest.mark.spec("evaluation:table:an-empty-latest-group-is-not-rendered")
def test_a_latest_group_holding_no_render_is_not_rendered(tmp_path: Path) -> None:
    runs, cohort = _batch(tmp_path)
    run = open_run(cohort / "p1" / "p1-1.png", runs)
    failed = run.directory(FLOW, OUTPUTS, "002")
    failed.mkdir()
    (failed / "001.error.1.permanent.json").write_text("{}")
    embed = _Embedder(VECTORS)

    rec, _ = entry.score(runs, cohort, embed, FLOWS_DIR)

    row = next(
        r for r in rec["flows"][FLOW]["rows"] if r["photograph"] == "p1/p1-1.png"
    )
    assert row["outcome"] == "not rendered"
    assert "11.png" not in {path.name for path in embed.seen}


@pytest.mark.spec("evaluation:table:an-unreadable-run-is-reported")
def test_a_run_that_cannot_be_read_is_listed_and_the_others_are_scored(
    tmp_path: Path,
) -> None:
    runs, cohort = _batch(tmp_path)
    (damaged,) = runs.glob("*_p1-2")
    (stray,) = runs.glob("*_p2-1")
    (damaged / "run.json").write_text("{not json")
    (stray / "a-retired-flow").mkdir()

    rec, notes = entry.score(runs, cohort, _Embedder(VECTORS), FLOWS_DIR)

    outcomes = {r["photograph"]: r["outcome"] for r in rec["flows"][FLOW]["rows"]}
    assert rec["unreadable"] == 2
    assert all(any(run.name in note for note in notes) for run in (damaged, stray))
    assert outcomes == {
        "p1/p1-1.png": "hit",
        "p1/p1-2.png": "not rendered",
        "p2/p2-1.png": "not rendered",
    }


@pytest.mark.spec("evaluation:table:an-unreadable-flow-costs-only-its-own")
def test_a_flow_this_build_does_not_carry_costs_its_run_only_that_flow(
    tmp_path: Path,
) -> None:
    runs, cohort = _batch(tmp_path)
    (run,) = runs.glob("*_p1-1")
    (run / "a-retired-flow").mkdir()

    rec, notes = entry.score(runs, cohort, _Embedder(VECTORS), FLOWS_DIR)

    outcomes = {r["photograph"]: r["outcome"] for r in rec["flows"][FLOW]["rows"]}
    assert outcomes["p1/p1-1.png"] == "hit"
    assert rec["unreadable"] == 1
    assert any(f"move {run / 'a-retired-flow'} out of the run" in n for n in notes)


@pytest.mark.spec("evaluation:table:the-record-names-no-unscored-run")
def test_the_record_counts_an_outside_and_an_unreadable_run_and_names_neither(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    runs, cohort = _batch(tmp_path)
    stranger = tmp_path / "elsewhere" / "stranger.png"
    stranger.parent.mkdir()
    Image.new("RGB", (8, 8), (0, 0, 200)).save(stranger)
    outside = open_run(stranger, runs).id
    (damaged,) = runs.glob("*_p2-1")
    (damaged / "run.json").write_text("{not json")
    monkeypatch.setattr(entry, "_embedder", lambda models: _Embedder(VECTORS))

    code = entry.main([str(runs), "--cohort", str(cohort)])

    written = (runs.parent / "evaluation.json").read_text()
    rec = json.loads(written)
    out, err = capsys.readouterr()
    assert code == 0
    named = {row["run"] for rows in rec["flows"].values() for row in rows["rows"]}
    assert (rec["outside_the_cohort"], rec["unreadable"]) == (1, 1)
    for run in (outside, damaged.name):
        assert run not in written + out
        assert run[:ID_DIGEST_CHARS] not in named | {*out.split()}
        assert run in err


@pytest.mark.spec("evaluation:table:a-run-is-named-by-its-digest-prefix")
def test_a_scored_run_is_named_by_its_digest_prefix_and_never_its_filename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _, cohort = _batch(tmp_path)
    named = tmp_path / "photos" / "ada-lovelace.png"
    named.parent.mkdir()
    named.write_bytes((cohort / "p1" / "p1-1.png").read_bytes())
    runs = tmp_path / "named" / "runs"
    run = open_run(named, runs)
    group = run.directory(FLOW, OUTPUTS, "001")
    group.mkdir(parents=True)
    Image.new("RGB", (8, 8)).save(group / "11.png")
    vectors = {**VECTORS, "11.png": [0.0, 1.0, 0.0]}
    monkeypatch.setattr(entry, "_embedder", lambda models: _Embedder(vectors))

    assert entry.main([str(runs), "--cohort", str(cohort)]) == 0

    written = (runs.parent / "evaluation.json").read_text()
    out = capsys.readouterr().out
    prefix = run.photo_record["sha256"][:ID_DIGEST_CHARS]
    (row,) = [r for r in json.loads(written)["flows"][FLOW]["rows"] if r["run"]]
    assert "ada-lovelace" in run.id
    assert (row["run"], row["outcome"]) == (prefix, "miss")
    assert f"run {prefix} seed 11" in out
    assert "ada-lovelace" not in written + out


@pytest.mark.spec("evaluation:table:a-run-is-named-by-its-digest-prefix")
def test_a_renamed_run_is_named_by_the_digest_its_frame_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    runs, cohort = _batch(tmp_path)
    (run,) = runs.glob("*_p1-2")
    prefix = run.name[:ID_DIGEST_CHARS]
    run.rename(runs / "ada-lovelace-old")
    monkeypatch.setattr(entry, "_embedder", lambda models: _Embedder(VECTORS))

    assert entry.main([str(runs), "--cohort", str(cohort)]) == 0

    written = (runs.parent / "evaluation.json").read_text()
    out = capsys.readouterr().out
    rows = json.loads(written)["flows"][FLOW]["rows"]
    assert {r["photograph"]: r["run"] for r in rows}["p1/p1-2.png"] == prefix
    assert f"run {prefix} seed 22" in out
    assert "ada-lovelace" not in written + out


@pytest.mark.spec("evaluation:table:a-record-git-can-reach-is-refused")
def test_a_record_inside_the_working_tree_and_outside_the_ignored_root_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repository = tmp_path / "repository"
    runs, cohort = _batch(repository)
    monkeypatch.setattr(wiring, "REPOSITORY", repository)
    monkeypatch.setattr(wiring, "DATA_ROOT", repository / ".data")
    embed = _Embedder(VECTORS)
    monkeypatch.setattr(entry, "_embedder", lambda models: embed)

    code = entry.main([str(runs), "--cohort", str(cohort)])

    assert code == 1
    assert str(runs.parent.resolve() / "evaluation.json") in capsys.readouterr().err
    assert not (runs.parent / "evaluation.json").exists()
    assert embed.seen == []


@pytest.mark.spec("evaluation:pinned-artifacts:the-record-names-the-bytes")
def test_the_record_names_each_model_and_cohort_photograph_by_its_digest(
    tmp_path: Path,
) -> None:
    runs, cohort = _batch(tmp_path)
    manifest = load_eval_manifest()

    rec, _ = entry.score(runs, cohort, _Embedder(VECTORS), FLOWS_DIR)

    assert rec["encoder"] == {
        role: {"dest": dest, "sha256": entry_for(manifest, dest)["sha256"]}
        for role, dest in (("detector", DETECTOR), ("encoder", ENCODER))
    }
    assert rec["cohort"]["sha256"] == {
        f"{photo.parent.name}/{photo.name}": digest_of(photo)
        for photo in sorted(cohort.glob("*/*"))
    }
