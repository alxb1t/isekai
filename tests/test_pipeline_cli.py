"""The pipeline's own entry point: its verbs, its refusals, and its stdlib guard.

`convert.py`'s surface is not touched by anything here, and a test asserts that
rather than trusting it: the two entry points are separate modules and only one
of them is new.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from isekai.__main__ import VERBS, build_parser, main

ROOT = Path(__file__).resolve().parent.parent

EXPECTED_VERBS = ("caption", "sheet", "review", "approve", "generate", "show")


def _module(*args: str) -> subprocess.CompletedProcess[str]:
    """Invoke `python -m isekai` the way an operator does, and capture everything."""
    return subprocess.run(
        [sys.executable, "-m", "isekai", *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


@pytest.mark.spec("cli:pipeline-surface:verbs-are-subcommands")
def test_the_six_verbs_are_the_ones_the_change_declares() -> None:
    assert tuple(name for name, _ in VERBS) == EXPECTED_VERBS


@pytest.mark.spec("cli:pipeline-surface:verbs-are-subcommands")
@pytest.mark.parametrize("verb", EXPECTED_VERBS)
def test_each_verb_is_reachable_as_a_subcommand(verb: str) -> None:
    assert build_parser().parse_args([verb]).verb == verb


@pytest.mark.spec("cli:pipeline-surface:verbs-are-subcommands")
def test_the_help_lists_every_verb() -> None:
    result = _module("--help")

    assert result.returncode == 0, result.stderr
    for verb in EXPECTED_VERBS:
        assert verb in result.stdout


@pytest.mark.spec("cli:pipeline-surface:verbs-are-subcommands")
def test_the_pipeline_surface_does_not_load_the_render_surface() -> None:
    # The render path is left unchanged by being left alone: importing the
    # pipeline's entry point must not pull in the parser `convert.py` drives.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import isekai.__main__, sys; print('isekai.cli' in sys.modules)",
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "False"


@pytest.mark.spec("cli:pipeline-surface:unknown-verb-is-refused")
def test_an_unknown_verb_is_refused_before_any_work_begins() -> None:
    result = _module("frobnicate")

    assert result.returncode != 0
    assert "invalid choice: 'frobnicate'" in result.stderr


@pytest.mark.spec("cli:pipeline-surface:unknown-verb-is-refused")
def test_the_refusal_lists_the_verbs_that_are_available() -> None:
    result = _module("frobnicate")

    for verb in EXPECTED_VERBS:
        assert verb in result.stderr


@pytest.mark.spec("cli:pipeline-surface:unknown-verb-is-refused")
def test_no_verb_at_all_is_refused_too() -> None:
    assert _module().returncode != 0


@pytest.mark.spec("cli:pipeline-surface:entry-point-is-stdlib-only")
def test_the_pipeline_entry_point_imports_with_site_packages_off_the_path() -> None:
    # The second guard, beside the one that holds `convert.py`. Same mechanism:
    # `-S` leaves no site-packages on `sys.path` inside this venv, so a
    # third-party import anywhere in this entry point's graph raises.
    result = subprocess.run(
        [sys.executable, "-S", "-c", "import isekai.__main__"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.spec("cli:pipeline-surface:entry-point-is-stdlib-only")
def test_the_run_directory_module_imports_with_site_packages_off_the_path() -> None:
    result = subprocess.run(
        [sys.executable, "-S", "-c", "import isekai.run"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.spec_exempt("structural: the parser dispatches nothing yet")
def test_parsing_a_verb_succeeds() -> None:
    assert main(["show"]) == 0
