"""A gpunit verb as a child: what it hands `say`, and when.

A short Python script stands in for gpunit, started with `run_gpunit`'s own keywords.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from isekai.boundary import gpu
from isekai.boundary.gpu import run_gpunit

POPEN = subprocess.Popen

# Prints `first`, then `after` once the marker in argv[1] exists, or `late` at 10 s.
WAITS = """
import pathlib, sys, time
print("first", flush=True)
marker = pathlib.Path(sys.argv[1])
deadline = time.monotonic() + 10
while not marker.exists() and time.monotonic() < deadline:
    time.sleep(0.01)
print("after" if marker.exists() else "late")
"""


def _runs(monkeypatch: pytest.MonkeyPatch, script: str, *args: str) -> None:
    """Make `run_gpunit` start `script` on `args` in gpunit's place."""

    def started(argv: list[str], **kwargs: Any) -> subprocess.Popen[str]:  # noqa: ANN401 -- Popen's
        return POPEN([sys.executable, "-c", script, *args], **kwargs)

    monkeypatch.setattr(gpu.subprocess, "Popen", started)


@pytest.mark.spec_exempt("structural: gpunit's lines reach say as they come")
def test_run_gpunit_says_a_line_before_the_verb_exits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    marker = tmp_path / "heard"
    _runs(monkeypatch, WAITS, str(marker))
    heard: list[str] = []

    def say(line: str) -> None:
        heard.append(line)
        if line == "first":
            marker.touch()

    run_gpunit(["status"], say)
    assert heard == ["first", "after"]
