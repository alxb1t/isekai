"""Render from the browser: the dialog, the session, the large view, Revise, Compare.

A revision, a discard and a comparison each own a batch, so none leans on
another's draft. The server renders on the e2e doubles: a session that rents
nothing and a transport that answers at once. Each step waits on the page's own
state.
"""

import re

import pytest
from playwright.sync_api import Page, expect

from isekai.foundation.run import REVIEW
from isekai.pipeline.review import current_draft
from tests.e2e.conftest import (
    COMPARED,
    DAMAGED,
    DISCARDED,
    FLOW,
    RENDER,
    REVISED,
    SHOWN,
    Served,
)


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
    expect(page.locator(".session__tile img")).to_have_count(1)


@pytest.mark.spec("ui:renders:the-large-view-shows-its-sheet")
def test_an_image_opened_from_the_grid_shows_the_approval_it_came_from(
    page: Page, served: Served
) -> None:
    page.goto(f"{served.url}/b/{SHOWN}/renders")
    tile = page.locator("[data-version='1'][data-seed='7']")
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


@pytest.mark.spec("ui:renders:a-source-opens-in-the-viewer")
def test_a_source_opens_in_the_viewer(page: Page, served: Served) -> None:
    grid = f"{served.url}/b/{SHOWN}/renders"
    page.goto(grid)

    page.locator("[data-source-thumb]").click()

    viewer = page.locator("dialog[data-viewer]")
    expect(viewer).to_be_visible()
    expect(viewer).to_contain_text("hal.jpg")
    box, size = viewer.bounding_box(), page.viewport_size
    assert box is not None and size is not None
    assert box["width"] <= size["width"] and box["height"] <= size["height"]
    page.keyboard.press("Escape")
    expect(viewer).to_have_count(0)
    expect(page).to_have_url(grid)


@pytest.mark.spec("ui:renders:a-damaged-versions-images-are-drawn")
def test_a_damaged_versions_images_are_drawn_and_hold_the_focus(
    page: Page, served: Served
) -> None:
    page.goto(f"{served.url}/b/{DAMAGED}/renders")

    expect(page.locator("[data-damaged]")).to_be_visible()
    image = page.locator("[data-version='1'][data-seed='7']")
    expect(image.locator("img")).to_have_js_property("complete", True)
    expect(image).to_have_class(re.compile("renders__image--focused"))
    # Its count refuses, so the Render bar stays, disabled, with that reason.
    bar = page.locator("[data-render-bar]")
    expect(bar.locator("[data-render-reason]")).to_contain_text("restore it in")
    expect(bar.locator("[data-render]")).to_be_disabled()


@pytest.mark.spec("ui:hub:a-rendered-cell-opens-its-newest-image")
def test_a_rendered_cell_opens_its_newest_image(page: Page, served: Served) -> None:
    page.goto(served.hub_of(SHOWN))
    rendered = page.locator(f'.hub__cell[data-flow="{FLOW}"][data-stage="rendered"]')

    rendered.click()

    expect(page).to_have_url(
        f"{served.url}/b/{SHOWN}/renders/{served.shown.digest}/{FLOW}/v1/7"
    )
    expect(page.locator("[data-sheet]")).to_contain_text("v1")
    page.keyboard.press("Escape")
    expect(page).to_have_url(served.hub_of(SHOWN))


@pytest.mark.spec("ui:revise:revise-opens-review-on-the-revision")
def test_revise_opens_review_on_the_revision(page: Page, served: Served) -> None:
    digest = served.revised.digest
    page.goto(f"{served.url}/b/{REVISED}/renders/{digest}/{FLOW}/v1/7")
    expect(page.locator("[data-revise]")).to_be_visible()
    page.keyboard.press("e")
    confirm = page.locator("[data-revise-confirm]")
    expect(confirm).to_contain_text("copies v1 · prefills seed 7")

    confirm.locator("[data-confirm]").click()

    review = f"{served.url}/b/{REVISED}/review/{digest}/{FLOW}"
    expect(page).to_have_url(review)
    expect(page.locator("[data-revised] img")).to_have_js_property("complete", True)
    expect(page.locator(".renders-block")).to_contain_text("seed 7")
    expect(page.locator(".form")).to_contain_text("revision of render 7")
    row = page.locator(".row", has_text="hair_colour")
    row.locator(".chip__x").first.click()
    expect(page.locator("[data-changed='hair_colour']")).to_contain_text("was")
    page.get_by_role("button", name="Approve sheet").click()
    expect(page.locator(".form")).to_contain_text("approved")
    expect(page.locator("input.fragment")).to_have_count(0)
    expect(page).to_have_url(review)


@pytest.mark.spec("ui:revise:discard-asks-before-it-deletes")
def test_discard_asks_before_it_deletes(page: Page, served: Served) -> None:
    review = served.review(served.discarded, DISCARDED)
    page.goto(review)
    expect(page.locator("[data-revised] img")).to_have_js_property("complete", True)

    page.locator("[data-discard]").click()
    asking = page.locator("[data-discard-confirm]")
    expect(asking).to_contain_text("Delete this draft and its edits?")
    asking.get_by_role("button", name="Keep").click()

    expect(asking).to_have_count(0)
    expect(page.locator("[data-discard]")).to_be_visible()
    expect(page).to_have_url(review)
    assert current_draft(served.discarded.directory(FLOW, REVIEW)) is not None


@pytest.mark.spec("ui:compare:compare-shows-the-pair-and-the-change")
def test_compare_shows_both_versions_of_a_seed_and_the_field_that_changed(
    page: Page, served: Served
) -> None:
    large = f"{served.url}/b/{COMPARED}/renders/{served.compared.digest}/{FLOW}/v2/7"
    page.goto(large)
    expect(page.locator("[data-compare]")).to_contain_text("Compare with v1")

    page.keyboard.press("c")

    expect(page).to_have_url(f"{large}/compare")
    images = page.locator("[data-side] img")
    expect(images).to_have_count(2)
    expect(images.nth(0)).to_have_js_property("complete", True)
    expect(page.locator("[data-changed]")).to_contain_text("clothes")
    expect(page.locator("[data-changed]")).to_contain_text("collared shirt")
