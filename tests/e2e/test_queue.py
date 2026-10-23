"""Approving in Review, in a browser: the sheet stays, and a later failure shows."""

import pytest
from playwright.sync_api import Page, Route, expect

from tests.e2e.conftest import Served


def _approve(page: Page) -> None:
    """Press Approve once the sheet is open and editable."""
    button = page.get_by_role("button", name="Approve sheet")
    expect(page.locator("input.fragment").first).to_be_visible()
    button.click()


@pytest.mark.spec("ui:review:approve-stays-on-the-sheet")
def test_approve_stays_on_the_sheet(page: Page, served: Served) -> None:
    first, _ = served.queues["queue-stays"]
    page.goto(served.review(first, "queue-stays"))
    _approve(page)
    expect(page.locator(".rail__card--current .mark--filled")).to_be_visible()
    expect(page).to_have_url(served.review(first, "queue-stays"))
    expect(page.locator("input.fragment")).to_have_count(0)
    expect(page.locator(".rail__card--current")).to_contain_text("cid.jpg")


@pytest.mark.spec("ui:review:a-failure-after-approval-is-shown")
def test_a_failure_reading_the_next_state_shows_in_the_approve_bar(
    page: Page, served: Served
) -> None:
    (only,) = served.queues["queue-fails"]
    page.goto(served.review(only, "queue-fails"))
    expect(page.locator("input.fragment").first).to_be_visible()

    def refuse(route: Route) -> None:
        route.fulfill(status=409, json={"refusal": "the hub could not be read"})

    page.route("**/api/b/queue-fails/hub", refuse)
    _approve(page)
    expect(page.locator(".approve-bar__refusal")).to_contain_text(
        "the hub could not be read"
    )
    expect(page).to_have_url(served.review(only, "queue-fails"))
