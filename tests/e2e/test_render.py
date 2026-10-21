"""Render from the browser: the dialog's confirmation, the session, the large view.

The server renders on the e2e doubles: a session that rents nothing and a
transport that answers at once. Each step waits on the page's own state.
"""

import re

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import FLOW, RENDER, SHOWN, Served


@pytest.mark.spec("ui:render:the-confirmation-starts-the-render")
def test_confirming_the_dialog_opens_the_session(page: Page, served: Served) -> None:
    page.goto(served.hub_of(SHOWN))
    expect(page.locator("[data-render]")).to_be_disabled()
    expect(page.locator("[data-render-reason]")).to_contain_text(
        "already has its Count"
    )

    page.goto(served.hub_of(RENDER))
    page.locator("[data-render]").click()
    confirm = page.locator("[data-confirm]")
    expect(confirm).to_be_enabled()
    expect(page.locator(".render-dialog")).to_contain_text("Render 1 image")
    expect(page).to_have_url(served.hub_of(RENDER))

    confirm.click()

    expect(page).to_have_url(f"{served.url}/session")
    expect(page.locator("[data-quiet]")).to_have_text("Nothing is billing.")
    expect(page.locator(".session__tile img")).to_have_count(1)


@pytest.mark.spec("ui:renders:the-large-view-shows-its-sheet")
def test_an_image_opened_from_the_grid_shows_the_approval_it_came_from(
    page: Page, served: Served
) -> None:
    page.goto(f"{served.url}/b/{SHOWN}/renders")
    tile = page.locator("[data-version='1'] [data-seed='7']")
    expect(tile.locator("img")).to_have_js_property("complete", True)

    tile.click()

    expect(page).to_have_url(
        f"{served.url}/b/{SHOWN}/renders/{served.shown.digest}/{FLOW}/v1/7"
    )
    sheet = page.locator("[data-sheet]")
    expect(sheet).to_contain_text("v1")
    expect(sheet).to_contain_text("hair_colour")
    page.keyboard.press("Escape")
    expect(page).to_have_url(f"{served.url}/b/{SHOWN}/renders")
    expect(tile).to_have_class(re.compile("renders__image--focused"))
    page.keyboard.press("Enter")
    expect(page.locator("[data-sheet]")).to_contain_text("v1")
