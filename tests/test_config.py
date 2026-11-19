"""The block the config loaders share: read a JSON config by the keys a build reads."""

import json
from pathlib import Path

import pytest

from isekai.foundation.config import read_keyed


@pytest.mark.spec_exempt("structural: the block the config loaders share")
def test_read_keyed_returns_the_document_it_read(tmp_path: Path) -> None:
    path = tmp_path / "x.json"
    path.write_text(json.dumps({"b": 2, "a": 1}))

    assert read_keyed(path, ("a", "b")) == {"a": 1, "b": 2}
