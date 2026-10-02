import json
from pathlib import Path

import pytest
from PIL import Image

import evaluation.recall as recall
from evaluation.recall import Record
from isekai.boundary import wd14
from isekai.foundation.artifacts import APPROVED_FILE
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    APPROVED,
    OUTPUTS,
    REVIEW,
    Run,
    artifact_name,
    open_run,
)
from isekai.interface import wiring

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


@pytest.mark.spec("evaluation:recall:named-runs-narrow-the-reading")
def test_named_runs_narrow_the_reading_and_an_unknown_name_refuses_first(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runs, a, b = _batch(tmp_path)
    tagger = _Tagger()

    assert _run(monkeypatch, tagger, runs, b.id) == 0
    assert {row["run"] for row in _record(runs)["rows"]} == {b.id}
    assert {path.name for path in tagger.seen} == {"44.png"}

    (runs.parent / "recall.json").unlink()
    again = _Tagger()
    assert _run(monkeypatch, again, runs, a.id, "nobody") == 1
    assert "nobody" in capsys.readouterr().err
    assert again.seen == []
    assert not (runs.parent / "recall.json").exists()


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
