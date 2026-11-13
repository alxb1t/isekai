"""The browser tests' guard: what it fails a test on, with no browser."""

import pytest

from tests.e2e.guard import Refused, Seen, faults


@pytest.mark.spec_exempt(
    "structural: the browser tests' guard names a page error, a console error, "
    "a server error and an undeclared refusal"
)
def test_the_guard_names_each_fault() -> None:
    seen = Seen(
        errors=["boom"],
        consoles=[("error", "TypeError: x is not a function")],
        responses=[(500, "/api/library"), (404, "/api/gone")],
    )

    assert faults(seen, []) == [
        "page error: boom",
        "console error: TypeError: x is not a function",
        "server error: 500 /api/library",
        "undeclared refusal: 404 /api/gone",
    ]


@pytest.mark.spec_exempt(
    "structural: the browser tests' guard lets by what a page may log"
)
def test_the_guard_lets_a_failed_load_a_warning_and_a_declared_refusal_by() -> None:
    seen = Seen(
        consoles=[
            (
                "error",
                "Failed to load resource: the server responded with a status "
                "of 409 (Conflict)",
            ),
            ("warning", "deprecated"),
            ("log", "hello"),
        ],
        responses=[(200, "/api/library"), (409, "/api/c/queue-fails/hub")],
    )

    assert faults(seen, [Refused(409, "/api/c/queue-fails")]) == []


@pytest.mark.spec_exempt(
    "structural: the browser tests' guard refuses a declared refusal "
    "that no response met"
)
def test_a_declaration_nothing_answers_is_a_fault() -> None:
    declared = [Refused(409, "/api/c/x/")]

    assert faults(Seen(responses=[(200, "/api/library")]), declared) == [
        "declared refusal never answered: 409 /api/c/x/"
    ]
    assert faults(Seen(responses=[(404, "/api/c/x/hub")]), declared) == [
        "undeclared refusal: 404 /api/c/x/hub",
        "declared refusal never answered: 409 /api/c/x/",
    ]
