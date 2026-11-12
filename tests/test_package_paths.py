"""The repo-root anchors, pinned to the directory that holds `pyproject.toml`.

Each constant in `ANCHORS` anchors a repository path on its own `__file__`
-- a schema is a flow's, reached through `FLOWS_DIR`, and the
repository root is `run.REPOSITORY`, named where `DATA_ROOT` already is. Each is
asserted **absolutely**: strip the anchor's own suffix, and what remains must be
the directory holding `pyproject.toml`. None of them is compared against another
constant, because two constants that move together prove nothing about where
either one landed.

The absolute form is the point. All but one break loudly when a file moves a
directory deeper without its expression following -- a missing `flows/`, a flow's
own directory or the manifest takes dozens of tests down at collection.
`DATA_ROOT` is the one that would relocate to `isekai/.data` with `RUNS_ROOT`
still beside it, leaving every assertion about the *relationship* between the two
green while the guard that keeps a run directory -- which holds a copy of a
photograph by construction -- one `git add` from publication quietly narrowed to
the package (D18).
"""

import ast
from collections.abc import Container
from pathlib import Path

import pytest

from evaluation import eval_models
from isekai.boundary import pod_start, provision, unpack
from isekai.foundation import caption_config, edit, flow, run
from isekai.pipeline import tattoos
from isekai.shared import field_map, ink, vocabulary

REPO_ROOT = Path(__file__).resolve().parent.parent

# Each anchor, beside the path it appends to the repository root. The suffix is
# how many `.parent` hops separate the constant from the root, spelled as the
# segments themselves so a wrong entry is wrong on its face rather than off by a
# count.
ANCHORS = (
    pytest.param(run.DATA_ROOT, (".data",), id="run.DATA_ROOT"),
    pytest.param(run.REPOSITORY, (), id="run.REPOSITORY"),
    pytest.param(flow.FLOWS_DIR, ("flows",), id="flow.FLOWS_DIR"),
    pytest.param(edit.EDITS_DIR, ("edits",), id="edit.EDITS_DIR"),
    pytest.param(
        provision.MANIFEST_PATH,
        ("config", "models.json"),
        id="provision.MANIFEST_PATH",
    ),
    pytest.param(
        provision.VOCABULARY_MANIFEST_PATH,
        ("config", "vocabulary.json"),
        id="provision.VOCABULARY_MANIFEST_PATH",
    ),
    pytest.param(
        provision.READER_MANIFEST_PATH,
        ("config", "reader.json"),
        id="provision.READER_MANIFEST_PATH",
    ),
    pytest.param(
        unpack.PLACEMENT_MANIFEST_PATH,
        ("config", "placement.json"),
        id="unpack.PLACEMENT_MANIFEST_PATH",
    ),
    pytest.param(
        eval_models.EVAL_MANIFEST_PATH,
        ("evaluation", "eval_models.json"),
        id="eval_models.EVAL_MANIFEST_PATH",
    ),
    pytest.param(
        provision.DEFAULT_MODELS_DIR,
        ("models",),
        id="provision.DEFAULT_MODELS_DIR",
    ),
    pytest.param(
        vocabulary.DEFAULT_MODELS_DIR,
        ("models",),
        id="vocabulary.DEFAULT_MODELS_DIR",
    ),
    pytest.param(
        field_map.FIELD_MAP_PATH,
        ("config", "field_map.json"),
        id="field_map.FIELD_MAP_PATH",
    ),
    pytest.param(
        caption_config.CAPTION_CONFIG_PATH,
        ("config", "caption.json"),
        id="caption_config.CAPTION_CONFIG_PATH",
    ),
    pytest.param(
        tattoos.TATTOO_CONFIG, ("config", "tattoo.json"), id="tattoos.TATTOO_CONFIG"
    ),
    pytest.param(ink.INK_CONFIG_PATH, ("config", "ink.json"), id="ink.INK_CONFIG_PATH"),
    pytest.param(
        pod_start.PROVISION,
        ("isekai", "boundary", "provision.py"),
        id="pod_start.PROVISION",
    ),
)


def _assert_anchors_the_repository_root(anchor: Path, suffix: tuple[str, ...]) -> None:
    """Strip the anchor's own suffix; what remains must be the repository root.

    The root is identified by `pyproject.toml` rather than by another constant,
    because a constant that moves with the anchor proves nothing about where
    either one landed. The segments are then compared by name, which the strip
    counts but never reads.
    """
    root = anchor
    for _ in suffix:
        root = root.parent

    assert (root / "pyproject.toml").is_file(), (
        f"{root} holds no pyproject.toml, so it is not the repository root"
    )
    assert anchor == REPO_ROOT.joinpath(*suffix), (
        f"{anchor} is not the repository root joined to {suffix}"
    )


def file_anchored(root: Path) -> list[str]:
    """Return each module-level constant built on `__file__`, as `module.NAME`.

    e.g. `ink.py` holding `INK_CONFIG_PATH = Path(__file__)...` → `ink.INK_CONFIG_PATH`
    """
    found = []
    for package in ("isekai", "evaluation"):
        for path in sorted((root / package).rglob("*.py")):
            for node in ast.parse(path.read_text()).body:
                if isinstance(node, ast.Assign):
                    names = [t for t in node.targets if isinstance(t, ast.Name)]
                elif isinstance(node, ast.AnnAssign) and isinstance(
                    node.target, ast.Name
                ):
                    names = [node.target]
                else:
                    continue
                uses_file = any(
                    isinstance(n, ast.Name) and n.id == "__file__"
                    for n in ast.walk(node.value or node)
                )
                if uses_file:
                    found += [f"{path.stem}.{name.id}" for name in names]
    return found


def unlisted(found: list[str], listed: Container[object]) -> list[str]:
    """Return each constant of `found` that no id of `listed` names."""
    return [name for name in found if name not in listed]


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
@pytest.mark.parametrize("package", ["isekai", "evaluation"])
def test_the_assertion_fails_when_it_lands_on_the_package_instead(
    package: str,
) -> None:
    # Where a constant strips back to if its module moves a directory deeper and
    # its expression does not gain a `.parent`: the top-level package holding it,
    # not the repository. Each anchor's suffix cancels against its own hops, so
    # every one reduces to one of these paths.
    with pytest.raises(AssertionError):
        _assert_anchors_the_repository_root(REPO_ROOT / package, ())


@pytest.mark.spec_exempt(
    "structural: every constant anchored on `__file__` is listed in `ANCHORS`"
)
def test_every_file_anchored_constant_is_listed() -> None:
    found = file_anchored(REPO_ROOT)

    assert found, "the scan read no constant anchored on `__file__`"
    assert unlisted(found, {param.id for param in ANCHORS}) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_every_file_anchored_constant_is_listed"
)
def test_the_check_catches_a_constant_missing_from_the_list(tmp_path: Path) -> None:
    package = tmp_path / "isekai"
    package.mkdir()
    (package / "here.py").write_text(
        "from pathlib import Path\n"
        "LISTED = Path(__file__).parent\n"
        "MISSING: Path = Path(__file__).parent / 'x'\n"
        "PLAIN = 1\n"
        "def f():\n"
        "    LOCAL = __file__\n"
    )

    found = file_anchored(tmp_path)

    assert found == ["here.LISTED", "here.MISSING"]
    assert unlisted(found, {"here.LISTED"}) == ["here.MISSING"]


@pytest.mark.spec_exempt(
    "structural: twin of test_each_anchor_resolves_to_the_repository_root"
)
def test_the_assertion_fails_when_a_segment_is_misnamed() -> None:
    with pytest.raises(AssertionError):
        _assert_anchors_the_repository_root(REPO_ROOT / "data", (".data",))
