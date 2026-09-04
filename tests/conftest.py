import json
from pathlib import Path

import pytest

from isekai.comfy_types import Workflow

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> Workflow:
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def animagine_i2i_cn_workflow() -> Workflow:
    return load_fixture("animagine-i2i-cn.json")
