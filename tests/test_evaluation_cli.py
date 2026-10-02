import json
from pathlib import Path

import pytest
from PIL import Image

import evaluation.__main__ as entry
from evaluation.cohort import Vector
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
