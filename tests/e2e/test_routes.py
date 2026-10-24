"""The shell's routes in a browser: every screen has a URL that survives a reload."""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import SHOWN, Served


@pytest.mark.spec("ui:routes:a-reload-lands-on-the-same-screen")
def test_a_reload_lands_on_the_same_hub_and_the_same_review(
    page: Page, served: Served
) -> None:
    page.goto(served.url)
    expect(page.locator(".library__row[data-batch]").first).to_be_focused()
    page.locator(".library__row", has_text=served.batch).focus()
    page.keyboard.press("Enter")
    expect(page).to_have_url(served.hub)
    expect(page.locator(".appbar__place")).to_have_text(served.batch)
    expect(page.locator(".hub__file", has_text="ada.jpg")).to_be_visible()
    page.reload()
    expect(page).to_have_url(served.hub)
    expect(page.locator(".hub__file", has_text="ada.jpg")).to_be_visible()

    page.goto(served.review(served.approved))
    current = page.locator(".rail__card--current")
    expect(current).to_contain_text("bea.jpg")
    expect(page.locator(".approve-bar__fact")).to_contain_text("Approved")
    page.reload()
    expect(page).to_have_url(served.review(served.approved))
    expect(current).to_contain_text("bea.jpg")
    expect(page.locator(".approve-bar__fact")).to_contain_text("Approved")

    page.goto(served.hub)
    page.locator('.hub__cell[data-row="0"][data-stage="draft"]').click()
    expect(page).to_have_url(served.review(served.draft))
    expect(page.locator(".rail__card--current")).to_contain_text("ada.jpg")

    page.goto(served.hub)
    page.goto(f"{served.url}/b/{served.batch}/review")
    expect(page).to_have_url(served.review(served.draft))
    expect(current).to_contain_text("ada.jpg")
    page.go_back()
    expect(page).to_have_url(served.hub)

    empty = f"{served.url}/b/{SHOWN}/review"
    page.goto(empty)
    expect(page.locator("[data-review-head]")).to_contain_text("No sheet waits")
    expect(page).to_have_url(empty)


@pytest.mark.spec("ui:routes:an-unknown-batch-is-refused")
def test_an_unknown_batch_is_refused_with_the_way_back(
    page: Page, served: Served
) -> None:
    page.goto(f"{served.url}/b/no-such-batch/hub")
    expect(page.locator(".refusal__reason")).to_contain_text("no-such-batch")
    page.get_by_role("link", name="Back to the library").click()
    expect(page).to_have_url(f"{served.url}/")
    expect(page.locator(".library__name", has_text=served.batch)).to_be_visible()
