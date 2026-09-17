"""The repo-root anchors, pinned to the directory that holds `pyproject.toml`.

Six constants across five files anchor a repository path on their own `__file__`
-- v0.16's fold took `SCHEMAS_DIR` and `BRIEFINGS_DIR` with it, because a schema
and a briefing are a flow's now and a flow is reached through `FLOWS_DIR`. Each is
asserted **absolutely**: strip the anchor's own suffix, and what remains must be
the directory holding `pyproject.toml`. None of them is compared against another
constant, because two constants that move together prove nothing about where
either one landed.

The absolute form is the point. Five of the six break loudly when a file moves a
directory deeper without its expression following -- a missing `flows/`, a flow's
own directory or the manifest takes dozens of tests down at collection.
`DATA_ROOT` is the one that would relocate to `isekai/.data` with `RUNS_ROOT`
still beside it, leaving every assertion about the *relationship* between the two
green while the guard that keeps a run directory -- which holds a copy of a
photograph by construction -- one `git add` from publication quietly narrowed to
the package (design.md D7).

Written while every anchor was still correct, and green across the restructure
that moved the files carrying them.
"""

from pathlib import Path

import pytest

from isekai.boundary import claude_cli, provision
from isekai.evaluation import eval_models
from isekai.foundation import flow, run

REPO_ROOT = Path(__file__).resolve().parent.parent

# Each anchor, beside the path it appends to the repository root. The suffix is
# how many `.parent` hops separate the constant from the root, spelled as the
# segments themselves so a wrong entry is wrong on its face rather than off by a
# count.
ANCHORS = (
    pytest.param(run.DATA_ROOT, (".data",), id="run.DATA_ROOT"),
    pytest.param(flow.FLOWS_DIR, ("flows",), id="flow.FLOWS_DIR"),
    pytest.param(
        provision.MANIFEST_PATH,
        ("scripts", "models.json"),
        id="provision.MANIFEST_PATH",
    ),
    pytest.param(
        provision.VOCABULARY_MANIFEST_PATH,
        ("scripts", "vocabulary.json"),
        id="provision.VOCABULARY_MANIFEST_PATH",
    ),
    pytest.param(
        eval_models.EVAL_MANIFEST_PATH,
        ("scripts", "eval_models.json"),
        id="eval_models.EVAL_MANIFEST_PATH",
    ),
    pytest.param(claude_cli.ROOT, (), id="claude_cli.ROOT"),
)


def _assert_anchors_the_repository_root(anchor: Path, suffix: tuple[str, ...]) -> None:
    """Strip the anchor's own suffix; what remains must be the repository root.

    The root is identified by `pyproject.toml` rather than by another constant,
    because a constant that moves with the anchor proves nothing about where
    either one landed.
    """
    root = anchor
    for _ in suffix:
        root = root.parent

    assert (root / "pyproject.toml").is_file(), (
        f"{root} holds no pyproject.toml, so it is not the repository root"
    )


@pytest.mark.spec_exempt(
    "structural: pins each repo-root anchor to the repository, so moving a file a "
    "directory deeper cannot silently relocate what it points at"
)
@pytest.mark.parametrize(("anchor", "suffix"), ANCHORS)
def test_each_anchor_resolves_to_the_repository_root(
    anchor: Path, suffix: tuple[str, ...]
) -> None:
    _assert_anchors_the_repository_root(anchor, suffix)


@pytest.mark.spec_exempt(
    "structural: the assertion above proves nothing unless it can go red"
)
def test_the_assertion_fails_when_it_lands_on_the_package_instead() -> None:
    # Where every one of these constants strips back to if its module moves into a
    # group directory and its expression does not gain a `.parent`: the package,
    # not the repository. One case, not six -- each anchor's suffix cancels
    # against its own hops, so all six reduce to exactly this path, and
    # parametrizing would advertise per-anchor coverage that does not exist.
    with pytest.raises(AssertionError):
        _assert_anchors_the_repository_root(REPO_ROOT / "isekai", ())
