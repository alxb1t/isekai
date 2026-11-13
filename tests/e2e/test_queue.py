"""Review in a browser: the chooser, and approving that stays, fails and cancels."""

import pytest
from playwright.sync_api import Page, Request, Route, expect

from isekai.foundation.artifacts import APPROVED_FILE, read
from isekai.foundation.run import APPROVED, REVIEW, Run, latest_artifact
from tests.e2e.conftest import CHOSEN, CONJURE, FLOW, Served
from tests.e2e.guard import Refused
from tests.e2e.held import hold, sent


def _approve(page: Page) -> None:
    """Press Approve once the sheet is open and editable."""
    button = page.get_by_role("button", name="Approve sheet")
    expect(page.locator("input.fragment").first).to_be_visible()
    button.click()


@pytest.mark.spec("ui:review:approve-stays-on-the-sheet")
@pytest.mark.spec("ui:review:cancel-approve-opens-the-sheet-again")
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

    # Cancel approve opens the sheet again, where it was.
    page.get_by_role("button", name="Cancel approve").click()
    expect(page.locator("input.fragment").first).to_be_visible()
    expect(page.get_by_role("button", name="Approve sheet")).to_be_enabled()
    expect(page).to_have_url(served.review(first, "queue-stays"))


@pytest.mark.spec("ui:review:a-failure-after-approval-is-shown")
def test_a_failure_reading_the_next_state_shows_in_the_approve_bar(
    page: Page, served: Served, refusals: list[Refused]
) -> None:
    (only,) = served.queues["queue-fails"]
    page.goto(served.review(only, "queue-fails"))
    expect(page.locator("input.fragment").first).to_be_visible()

    def refuse(route: Route) -> None:
        route.fulfill(status=409, json={"refusal": "the hub could not be read"})

    refusals.append(Refused(409, "/api/c/queue-fails/hub"))
    page.route("**/api/c/queue-fails/hub", refuse)
    _approve(page)
    expect(page.locator(".approve-bar__refusal")).to_contain_text(
        "the hub could not be read"
    )
    expect(page).to_have_url(served.review(only, "queue-fails"))


@pytest.mark.spec("ui:review:the-chooser-opens-a-flow")
def test_the_chooser_opens_a_flow(page: Page, served: Served) -> None:
    chooser = f"{served.url}/c/{CHOSEN}/review"
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


PUTS = "**/api/c/save-holds/review/**/draft"
REFUSAL = "the draft is not at that save"
APPROVED_BAR = "approved as 001.approved.json and read-only"


def _edit(page: Page) -> None:
    """Commit the first suggestion for `eyes` into the sheet's first field."""
    field = page.locator("input.fragment").first
    expect(field).to_be_visible()
    field.click()
    field.press_sequentially("eyes")
    # Enter commits only once the dropdown is open: wait for the suggestion first.
    expect(page.locator(".drop__row").first).to_contain_text("blue eyes")
    field.press("Enter")
    row = page.locator(".row", has=field)
    expect(row.locator(".chip", has_text="blue eyes")).to_be_visible()


def _holds_the_edit(run: Run) -> None:
    """Assert `run`'s newest approval holds the tag `_edit` committed."""
    approval = latest_artifact(run.directory(FLOW, REVIEW), APPROVED)
    assert approval is not None
    fields = read(approval, APPROVED_FILE)["fields"]
    assert any("blue eyes" in tags for tags in fields.values())


@pytest.mark.spec("ui:save:an-approval-waits-for-a-save-held-at-the-network")
def test_approve_waits_for_a_save_held_at_the_network(
    page: Page, served: Served
) -> None:
    first, _ = served.queues["save-holds"]
    page.goto(served.review(first, "save-holds"))
    held = hold(page, PUTS)
    approvals: list[str] = []

    def note(request: Request) -> None:
        if request.url.endswith("/approve"):
            approvals.append(request.url)

    page.on("request", note)
    _edit(page)
    # The route must see the save first: a keepalive request it missed fails here.
    save = sent(page, held)
    page.get_by_role("button", name="Approve sheet").click()
    page.wait_for_timeout(500)
    assert approvals == []
    save.continue_()
    expect(page.locator(".approve-bar")).to_contain_text(APPROVED_BAR)
    assert len(approvals) == 1
    _holds_the_edit(first)


@pytest.mark.spec("ui:save:a-refused-save-is-sent-again-by-the-next-approval")
def test_a_refused_save_is_sent_again_by_the_next_approval(
    page: Page, served: Served, refusals: list[Refused]
) -> None:
    _, second = served.queues["save-holds"]
    refusals.append(Refused(409, "/api/c/save-holds/review/"))
    page.goto(served.review(second, "save-holds"))
    held = hold(page, PUTS)
    _edit(page)
    sent(page, held).fulfill(status=409, json={"refusal": REFUSAL})
    expect(page.locator(".approve-bar")).to_contain_text(REFUSAL)
    page.get_by_role("button", name="Approve sheet").click()
    sent(page, held, 1).continue_()
    expect(page.locator(".approve-bar")).to_contain_text(APPROVED_BAR)
    _holds_the_edit(second)
