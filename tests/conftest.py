import json
from pathlib import Path

import pytest

from isekai.comfy_types import Workflow

# The suite reads the shipped graph itself: a byte-identical fixture copy with no
# drift check is a second thing to rename and a silent divergence waiting to
# happen (design.md D9).
WORKFLOWS = Path(__file__).parent.parent / "workflows"


def load_workflow(name: str) -> Workflow:
    return json.loads((WORKFLOWS / name).read_text())


@pytest.fixture
def workflow() -> Workflow:
    return load_workflow("pipeline.json")
