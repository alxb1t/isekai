"""Review in a browser: the chooser, and approving that stays, fails and cancels."""

import pytest
from playwright.sync_api import Page, Route, expect

from tests.e2e.conftest import CHOSEN, CONJURE, Served


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
    expect(page.locator(".approve-bar")).to_contain_text(
        "approved as 001.approved.json and read-only"
    )


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


@pytest.mark.spec("ui:review:cancel-approve-opens-the-sheet-again")
def test_cancel_approve_opens_the_sheet_again(page: Page, served: Served) -> None:
    (only,) = served.queues["queue-cancels"]
    page.goto(served.review(only, "queue-cancels"))
    _approve(page)
    expect(page.locator("input.fragment")).to_have_count(0)

    page.get_by_role("button", name="Cancel approve").click()

    expect(page.locator("input.fragment").first).to_be_visible()
    expect(page.get_by_role("button", name="Approve sheet")).to_be_enabled()
    expect(page).to_have_url(served.review(only, "queue-cancels"))


@pytest.mark.spec("ui:review:the-chooser-opens-a-flow")
def test_the_chooser_opens_a_flow(page: Page, served: Served) -> None:
    chooser = f"{served.url}/b/{CHOSEN}/review"
    page.goto(chooser)
    rows = page.locator("[data-flow-row]")
    expect(rows).to_have_count(2)
    expect(rows.nth(0)).to_be_focused()

    page.keyboard.press("j")
    page.keyboard.press("Enter")

    expect(page).to_have_url(f"{chooser}/{served.chosen.digest}/{CONJURE}")
    expect(page.locator("input.fragment").first).to_be_visible()
    expect(page.locator(".rail__card--current")).to_be_focused()
    page.keyboard.press("Escape")
    expect(page).to_have_url(chooser)
    expect(rows.nth(1)).to_be_focused()
