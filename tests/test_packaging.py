"""What the project declares it needs, and that each name is declared once.

**One module, because these are one invariant.** The two tests here arrived in
v0.22.3 in two files -- one under the tagger, one under the review surface --
because that is which feature noticed them. Neither is about a tagger or a
surface: both assert the shape of `pyproject.toml`, and split across two files
they carried two copies of the same requirement-name parser and two reads of the
same manifest.

**The defect they exist against was the gate itself.** While the tagger's stack
and the server sat in extras, `uv sync --locked` -- gate command one, with no
`--extra` -- removed them on every run, because uv makes the environment match
exactly what it is told. The symptom looked like a missing install rather than a
removal, so it recurred: the operator kept re-running `uv sync --extra tagging`.
"""

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# What a run actually reaches, by the verb that reaches it. The scorer is absent
# on purpose -- an evaluator is not a way to render, so `eval` stays optional.
RUNTIME_STACK = {
    "onnxruntime": "the local tagger's SwinV2 session, on every `caption`",
    "numpy": "the tagger's prepared array in and probability vector out",
    "pillow": "the tagger's open, composite, pad and resize",
    "fastapi": "the review surface's server",
    "uvicorn": "what runs the review surface",
}


@pytest.fixture(scope="session")
def manifest() -> dict:
    """Parse the tracked `pyproject.toml` once.

    Session-scoped and reading the tracked file itself, which is the shape
    `conftest.py` already establishes for every other tracked file the suite
    reads: there is no second copy to drift.
    """
    return tomllib.loads((ROOT / "pyproject.toml").read_text())


def names(specs: list[str]) -> set[str]:
    """Return the package names in a PEP 508 requirement list, normalised.

    Spelled once, here, rather than at each call site. It handles the spec forms
    this manifest uses -- a pin, a floor, an extras bracket -- and deliberately
    not markers, `~=` or URLs: none appears in this project, and a parser wider
    than its input is a claim about cases nothing tests.
    """
    return {re.split(r"[=<>!~ ;\[]", spec)[0].strip().lower() for spec in specs}


@pytest.mark.spec_exempt(
    "structural: the manifest's shape, which no scenario describes"
)
def test_everything_a_run_reaches_is_a_declared_dependency(manifest: dict) -> None:
    declared = names(manifest["project"]["dependencies"])

    for package, why in RUNTIME_STACK.items():
        assert package in declared, (
            f"{package} is not a declared dependency, but a run reaches it: "
            f"{why}. In an extra, `uv sync --locked` strips it on every gate run."
        )


@pytest.mark.spec_exempt("structural: it keeps one pin list from becoming two")
def test_no_package_is_named_in_more_than_one_list(manifest: dict) -> None:
    """A name lives in exactly one list, so two copies of it cannot drift apart.

    **This is the general form of a rule v0.22.3 found the hard way.** While the
    server lived in a `ui` extra that gate command one never installed, the `dev`
    group had to re-pin the same two packages so `tests/test_ui_api.py` would run
    at all, and a test held the two lists equal. Making them declared removed the
    second list rather than keeping it in step -- and the rule that removal
    implies is not *"`dependencies` and `dev` must not overlap"* but this one,
    which also catches an extra re-flooring what the project already pins.
    """
    lists = {"dependencies": manifest["project"]["dependencies"]}
    lists |= manifest["project"]["optional-dependencies"]
    lists["dev"] = manifest["dependency-groups"]["dev"]

    seen: dict[str, str] = {}
    for label, specs in lists.items():
        for package in names(specs):
            assert package not in seen, (
                f"{package} is named in both `{seen[package]}` and `{label}`. "
                "One of the two will drift; name it where it belongs and let "
                "the other inherit it."
            )
            seen[package] = label


@pytest.mark.spec_exempt(
    "structural: the manifest's shape, which no scenario describes"
)
def test_the_scorers_stack_is_the_only_optional_one(manifest: dict) -> None:
    # `eval` is a measurement stack, not a way to render, so a checkout that
    # never scores anything should not carry `torch`. It is the only extra left:
    # everything a *run* reaches is declared above.
    extras = manifest["project"]["optional-dependencies"]

    assert set(extras) == {"eval"}
    assert {"torch", "transformers"} <= names(extras["eval"])
