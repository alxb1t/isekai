"""Review as a queue, in a browser: Approve moves on, and a later failure shows."""

import pytest
from playwright.sync_api import Page, Route, expect

from tests.e2e.conftest import Served


def _approve(page: Page) -> None:
    """Press Approve once the sheet is open and editable."""
    button = page.get_by_role("button", name="Approve sheet")
    expect(page.locator("input.fragment").first).to_be_visible()
    button.click()


@pytest.mark.spec("ui:queue:approve-moves-to-the-next-sheet")
def test_approve_opens_the_next_unapproved_sheet(page: Page, served: Served) -> None:
    first, second = served.queues["queue-moves"]
    page.goto(served.review(first, "queue-moves"))
    _approve(page)
    expect(page).to_have_url(served.review(second, "queue-moves"))
    expect(page.locator(".rail__card--current")).to_contain_text("dot.jpg")


@pytest.mark.spec("ui:queue:after-the-last-sheet-the-hub-opens")
def test_approving_the_last_sheet_opens_the_hub(page: Page, served: Served) -> None:
    (only,) = served.queues["queue-last"]
    page.goto(served.review(only, "queue-last"))
    _approve(page)
    expect(page).to_have_url(served.hub_of("queue-last"))
    expect(page.get_by_text("nothing left to review")).to_be_visible()


@pytest.mark.spec("ui:queue:a-failure-after-approval-is-shown")
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
