import copy
import json

import pytest

from isekai.comfy_types import Workflow
from isekai.provision import Manifest, load_manifest
from isekai.workflow import PIPELINE_PATH


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
