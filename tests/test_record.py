"""The record: each file of `tests/record/` is what a fresh pass derives.

A red test here means an output moved. `uv run python -m tests.record` writes the
files again, and the diff shows what moved.
"""

from pathlib import Path

import pytest

from isekai.foundation.run import Run
from tests.record import (
    FILES,
    FIRST_FLOW,
    FLOWS,
    RECORD,
    REGENERATE,
    SEED,
    Done,
    derive,
    differing,
    offline,
)


@pytest.fixture(scope="module")
def done(tmp_path_factory: pytest.TempPathFactory) -> Done:
    """Run the pass once for the module."""
    return offline(tmp_path_factory.mktemp("record"))


@pytest.fixture(scope="module")
def derived(done: Done) -> dict[str, str]:
    """Return each record file's text, derived from the module's pass."""
    return derive(done)


def _group(run: Run, flow: str) -> Path:
    return run.path / flow / "outputs" / "001"


@pytest.mark.spec_exempt("structural: the pass renders every flow and the edit")
def test_the_pass_renders_every_flow_and_the_edit(done: Done) -> None:
    for flow in FLOWS:
        assert (_group(done.run, flow) / f"{SEED}.png").is_file(), flow
    assert (_group(done.run, FIRST_FLOW) / f"{SEED}.edit-1.png").is_file()


@pytest.mark.spec_exempt("structural: a record file is what the writer derives")
@pytest.mark.parametrize("name", sorted(FILES))
def test_each_record_file_is_what_the_writer_derives(
    name: str, derived: dict[str, str]
) -> None:
    committed = RECORD / f"{name}.json"
    assert committed.is_file() and committed.read_text() == derived[name], REGENERATE


@pytest.mark.spec_exempt(
    "structural: the record directory holds the files the writer names"
)
def test_the_record_directory_holds_the_files_the_writer_names(
    derived: dict[str, str],
) -> None:
    assert differing(RECORD, derived) == [], REGENERATE


@pytest.mark.spec_exempt(
    "structural: twin of test_the_record_directory_holds_the_files_the_writer_names"
)
def test_a_stale_record_file_is_caught(tmp_path: Path) -> None:
    derived = {"kept": "1\n", "stale": "2\n", "absent": "3\n"}
    (tmp_path / "kept.json").write_text("1\n")
    (tmp_path / "stale.json").write_text("0\n")
    (tmp_path / "extra.json").write_text("4\n")
    assert differing(tmp_path, derived) == ["absent", "extra", "stale"]
