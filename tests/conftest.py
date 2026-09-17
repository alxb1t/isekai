import copy
import json
from pathlib import Path

import pytest

from isekai.boundary.comfy_types import Workflow
from isekai.boundary.provision import Manifest, load_manifest
from isekai.foundation.flow import Schema, load_flow
from isekai.pipeline.sheet import load_schema
from isekai.shared.vocabulary import Vocabulary, read_tags
from tests.images import jpeg_bytes

# A small stand-in for the provisioned tag list, with the same shape and the same
# spelling: general tags in category 0, and the character and meta tags the
# loader drops. Shared here rather than imported from one test module by another,
# which would make that module undeletable.
CSV = """tag_id,name,category,count
9999999,general,9,1000000
1,long_hair,0,3645082
2,short_hair,0,1904624
3,medium_hair,0,273659
4,very_long_hair,0,783428
5,wavy_hair,0,83362
6,brown_hair,0,1267072
7,blue_eyes,0,1490640
8,brown_eyes,0,747352
9,thick_eyebrows,0,77258
10,dark_skin,0,233165
11,simple_background,0,1420030
12,glasses,0,309385
13,smile,0,2365730
14,looking_at_viewer,0,2696730
15,jeans,0,200000
16,shirt,0,1382452
17,collared_shirt,0,321941
18,hair,0,50000
19,hatsune_miku,4,500000
"""


@pytest.fixture(scope="session")
def _shipped_workflow() -> Workflow:
    """Read and parse the shipped graph once for the whole session.

    The suite reads the shipped graph itself: a byte-identical fixture copy with
    no drift check is a second thing to rename and a silent divergence waiting to
    happen (design.md D9). It is reached through the flow that declares it rather
    than through a path constant, so the fixture and the render path agree on
    which file the shipped graph is by construction.
    """
    return json.loads(load_flow("summon-v1").graph_path.read_text())


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


@pytest.fixture(scope="session")
def _shipped_schema() -> Schema:
    """Read and parse the tracked identity schema once for the whole session.

    Same argument as the shipped graph and the tracked manifest above: the suite
    reads the tracked file itself, and reads it once.
    """
    return load_schema()


@pytest.fixture
def schema(_shipped_schema: Schema) -> Schema:
    """Return the tracked identity schema."""
    return _shipped_schema


@pytest.fixture
def vocabulary() -> Vocabulary:
    """Return a small offline vocabulary with the real one's shape and spelling.

    Offline by construction: the provisioned 308 KB list is gitignored, so a suite
    that needed it would not run in CI at all.
    """
    return Vocabulary("wd14/selected_tags.csv", "f" * 40, "a" * 64, read_tags(CSV))


def snapshot(directory: Path) -> dict[str, bytes]:
    """Return every file under `directory`, by relative name, with its bytes."""
    return {
        str(path.relative_to(directory)): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }
