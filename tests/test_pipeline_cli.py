"""The pipeline's own entry point: its verbs, its refusals, and its stdlib guard.

This is the only entry point: v0.14 deleted the single-command surface `convert.py`
carried, so the stdlib-only runtime rule now has exactly one subject and the guard
that holds it lives here, beside the falsification that keeps it honest.
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


def _stdlib_import(statement: str) -> subprocess.CompletedProcess[str]:
    """Run one import under `-S`, with the repository on the path and nothing else.

    The mechanism is `-S`, chosen over an AST walk against `sys.stdlib_module_names`
    because it was verified to work here: inside this uv venv, `-S` leaves no
    site-packages on `sys.path` at all, so a third-party import anywhere in the
    graph raises rather than resolving. Spelled once, because the guards below and
    the falsification that keeps them honest must run under identical conditions --
    a falsification that differs from what it falsifies proves nothing.
    """
    return subprocess.run(
        [sys.executable, "-S", "-c", statement],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
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
    result = _stdlib_import("import isekai.__main__")

    assert result.returncode == 0, result.stderr


@pytest.mark.spec("cli:pipeline-surface:entry-point-is-stdlib-only")
def test_the_run_directory_module_imports_with_site_packages_off_the_path() -> None:
    result = _stdlib_import("import isekai.run")

    assert result.returncode == 0, result.stderr


@pytest.mark.spec_exempt(
    "structural: the two guards above prove nothing unless -S really refuses"
)
def test_the_stdlib_guard_would_actually_catch_a_third_party_import() -> None:
    # A check that cannot fail is not a check. If `-S` ever stopped removing
    # site-packages, the two guards above would pass for the wrong reason and an
    # accidental wheel in `python -m isekai`'s import graph would ship silently.
    # It moved here with the guard it falsifies: it used to sit beside the one
    # that held `convert.py`, and that guard died with its target.
    result = _stdlib_import("import pytest")

    assert result.returncode != 0
    assert "No module named 'pytest'" in result.stderr


@pytest.mark.spec_exempt("structural: the parser dispatches nothing yet")
def test_parsing_a_verb_succeeds() -> None:
    assert main(["show"]) == 0
