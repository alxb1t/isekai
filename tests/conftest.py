import copy
import json
from pathlib import Path

import pytest

from isekai.comfy_types import Workflow
from isekai.provision import Manifest, load_manifest
from isekai.workflow import PIPELINE_PATH
from tests.images import jpeg_bytes


@pytest.fixture(scope="session")
def _shipped_workflow() -> Workflow:
    """Read and parse the shipped graph once for the whole session.

    The suite reads the shipped graph itself: a byte-identical fixture copy with
    no drift check is a second thing to rename and a silent divergence waiting to
    happen (design.md D9).
    """
    return json.loads(PIPELINE_PATH.read_text())


@pytest.fixture
def workflow(_shipped_workflow: Workflow) -> Workflow:
    """Return a private copy of the shipped graph, so a test may mutate it freely."""
    return copy.deepcopy(_shipped_workflow)


@pytest.fixture(scope="session")
def _shipped_manifest() -> Manifest:
    """Read and parse the tracked manifest once for the whole session.

    Same argument as the shipped graph above: the suite reads the tracked file
    itself, so there is no second copy to drift.
    """
    return load_manifest()


@pytest.fixture
def manifest(_shipped_manifest: Manifest) -> Manifest:
    """Return a private copy of the manifest, so a test may malform it freely."""
    return copy.deepcopy(_shipped_manifest)


@pytest.fixture
def photo(tmp_path: Path) -> str:
    """Write a readable photo to disk and return its path.

    Injection reads the photo's header to derive the render target, so every test
    that runs injection needs a file that actually exists. 1600x1200 is a plain
    landscape input with no rounding subtlety in it -- the sizes that do are
    asserted directly against `working_resolution`.
    """
    path = tmp_path / "photo.jpg"
    path.write_bytes(jpeg_bytes(1600, 1200))
    return str(path)
