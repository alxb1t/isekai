import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def qwen_workflow():
    return load_fixture("qwen-image-edit.json")


@pytest.fixture
def animagine_workflow():
    return load_fixture("animagine-instantid.json")


@pytest.fixture
def animagine_i2i_workflow():
    return load_fixture("animagine-i2i.json")
