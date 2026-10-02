import json
from pathlib import Path

import pytest
from PIL import Image

import evaluation.__main__ as entry
from evaluation.cohort import Vector
from evaluation.face import load
from isekai.foundation.flow import FLOWS_DIR
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import OUTPUTS, open_run

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


@pytest.mark.spec("evaluation:table:an-unreadable-run-is-reported")
def test_a_run_that_cannot_be_read_is_listed_and_the_others_are_scored(
    tmp_path: Path,
) -> None:
    runs, cohort = _batch(tmp_path)
    (damaged,) = runs.glob("*_p1-2")
    (stray,) = runs.glob("*_p2-1")
    (damaged / "run.json").write_text("{not json")
    (stray / "a-retired-flow").mkdir()

    rec, _ = entry.score(runs, cohort, _Embedder(VECTORS), FLOWS_DIR)

    outcomes = {r["photograph"]: r["outcome"] for r in rec["flows"][FLOW]["rows"]}
    assert rec["unreadable"] == sorted([damaged.name, stray.name])
    assert outcomes == {
        "p1/p1-1.png": "hit",
        "p1/p1-2.png": "not rendered",
        "p2/p2-1.png": "not rendered",
    }
