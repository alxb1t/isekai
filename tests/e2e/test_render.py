"""Render from the browser: the dialog's confirmation and the session it opens.

The server renders on the e2e doubles: a session that rents nothing and a
transport that answers at once. Each step waits on the page's own state.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import RENDER, Served


@pytest.mark.spec("ui:render:the-confirmation-starts-the-render")
def test_confirming_the_dialog_opens_the_session(page: Page, served: Served) -> None:
    page.goto(served.hub_of(RENDER))
    page.locator("[data-render]").click()
    confirm = page.locator("[data-confirm]")
    expect(confirm).to_be_enabled()
    expect(page.locator(".render-dialog")).to_contain_text("Render 1 image")
    expect(page).to_have_url(served.hub_of(RENDER))

    confirm.click()

    expect(page).to_have_url(f"{served.url}/session")
    expect(page.locator("[data-quiet]")).to_have_text("Nothing is billing.")
