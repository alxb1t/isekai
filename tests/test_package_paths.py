"""The eight repo-root anchors, pinned to the repository root while they are right.

Seven files compute a repo-root path as `Path(__file__).resolve().parent.parent`.
v0.15's restructure moves every one of them a directory deeper, and that expression
then yields `isekai/` instead of the repository. Six of the eight constants below
fail loudly when that happens -- a missing `flows/`, `schemas/`, `briefings/` or
manifest breaks dozens of tests at collection. `DATA_ROOT` does not: it becomes
`isekai/.data`, `RUNS_ROOT` moves with it, and every test that asserts the
*relationship* between the two still passes, while the guard that keeps a run
directory -- which holds a copy of a photograph by construction -- out of one
`git add` quietly narrows to refuse only paths inside the package (design.md D7).

So these assertions are **absolute**: each one strips the anchor's own suffix and
demands that what is left is the directory holding `pyproject.toml`. None of them
compares two constants that would move together. They are written here, now, while
every anchor is still correct, so they pass today and go red the moment a file moves
without gaining its `.parent`. They are the detector, not the fix.
"""

from pathlib import Path

import pytest

from isekai import caption, claude_cli, eval_models, flow, provision, run, sheet

REPO_ROOT = Path(__file__).resolve().parent.parent

# Each anchor, beside the path it appends to the repository root. The suffix is how
# many `.parent` hops separate the constant from the root, spelled as the segments
# themselves so a wrong entry is wrong on its face rather than off by a count.
ANCHORS: tuple[tuple[str, Path, tuple[str, ...]], ...] = (
    ("run.DATA_ROOT", run.DATA_ROOT, (".data",)),
    ("flow.FLOWS_DIR", flow.FLOWS_DIR, ("flows",)),
    ("sheet.SCHEMAS_DIR", sheet.SCHEMAS_DIR, ("schemas",)),
    ("caption.BRIEFINGS_DIR", caption.BRIEFINGS_DIR, ("briefings",)),
    (
        "provision.MANIFEST_PATH",
        provision.MANIFEST_PATH,
        ("scripts", "models.json"),
    ),
    (
        "provision.VOCABULARY_MANIFEST_PATH",
        provision.VOCABULARY_MANIFEST_PATH,
        ("scripts", "vocabulary.json"),
    ),
    (
        "eval_models.EVAL_MANIFEST_PATH",
        eval_models.EVAL_MANIFEST_PATH,
        ("scripts", "eval_models.json"),
    ),
    ("claude_cli.ROOT", claude_cli.ROOT, ()),
)

ANCHOR_IDS = tuple(name for name, _, _ in ANCHORS)
CASES = tuple((anchor, suffix) for _, anchor, suffix in ANCHORS)


def _assert_anchors_the_repository_root(anchor: Path, suffix: tuple[str, ...]) -> None:
    """Strip the anchor's own suffix; what remains must be the repository root.

    The root is identified by `pyproject.toml` rather than by another constant,
    because a constant that moves with the anchor proves nothing about where either
    one landed.
    """
    root = anchor
    for _ in suffix:
        root = root.parent

    assert (root / "pyproject.toml").is_file(), (
        f"{root} holds no pyproject.toml, so it is not the repository root"
    )
    assert root == REPO_ROOT


@pytest.mark.spec_exempt(
    "structural: pins each repo-root anchor to the repository, so the restructure "
    "cannot move a file a directory deeper and silently relocate it"
)
@pytest.mark.parametrize(("anchor", "suffix"), CASES, ids=ANCHOR_IDS)
def test_each_anchor_resolves_to_the_repository_root(
    anchor: Path, suffix: tuple[str, ...]
) -> None:
    _assert_anchors_the_repository_root(anchor, suffix)


@pytest.mark.spec_exempt(
    "structural: the detector above proves nothing unless it can go red"
)
@pytest.mark.parametrize(("anchor", "suffix"), CASES, ids=ANCHOR_IDS)
def test_the_detector_fails_when_an_anchor_stops_one_level_short(
    anchor: Path, suffix: tuple[str, ...]
) -> None:
    # What every one of these constants becomes if its module moves into a group
    # directory and its expression does not gain a `.parent`: the same suffix, hung
    # off the package instead of off the repository. A check that cannot fail is not
    # a check, and this one has to survive a rename storm intact.
    one_level_short = REPO_ROOT.joinpath("isekai", *suffix)

    with pytest.raises(AssertionError):
        _assert_anchors_the_repository_root(one_level_short, suffix)
