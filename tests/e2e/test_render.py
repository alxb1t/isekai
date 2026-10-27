"""Render from the browser: the dialog, the drawer, the large view, Revise, Compare.

A revision, a discard, a comparison and a draft from another flow each own a
collection, so none leans on another's draft. The server renders on the e2e doubles:
a session that rents nothing and a transport that answers at once. Each step
waits on the page's own state.
"""

import re

import pytest
from playwright.sync_api import Page, expect

from isekai.foundation.run import REVIEW
from isekai.pipeline.review import current_draft
from tests.e2e.conftest import (
    COMPARED,
    CONJURE,
    CONJURED,
    DAMAGED,
    DISCARDED,
    DRAWN,
    FLAT,
    FLOW,
    RENDER,
    REVISED,
    SHOWN,
    Served,
)


@pytest.mark.spec("ui:dialogs:the-render-dialog-opens-on-its-checkbox")
def test_the_render_dialog_opens_on_its_checkbox(page: Page, served: Served) -> None:
    # Cancelled, so the next test still confirms this collection's one image.
    page.goto(served.hub_of(RENDER))
    cell = page.locator('.hub__source[data-row="0"]')
    expect(cell).to_be_focused()
    # ⇧G acts on the Render bar, which shows once the offer is read.
    expect(page.locator("[data-render]")).to_be_enabled()

    page.keyboard.press("Shift+G")

    dialog = page.locator("dialog.render-dialog")
    keep = dialog.locator("[data-keep-open]")
    expect(keep).to_be_focused()
    # ↵ on the checkbox neither ticks it nor renders.
    page.keyboard.press("Enter")
    expect(keep).not_to_be_checked()
    expect(dialog).to_be_visible()
    for _ in range(dialog.locator("button:enabled, input").count()):
        page.keyboard.press("Tab")
        assert dialog.evaluate("(held) => held.contains(document.activeElement)")
    page.keyboard.press("Escape")
    expect(dialog).to_have_count(0)
    expect(cell).to_be_focused()


def _alone(page: Page, collection: str) -> None:
    """Untick every dialog row but `collection`'s, and wait for its quote."""
    dialog = page.locator("dialog.render-dialog")
    own = dialog.locator(f'[data-collection="{collection}"]')
    expect(own).to_contain_text("1 image")
    others = dialog.locator(
        f'[data-collection]:not([data-collection="{collection}"]) [data-tick]'
    )
    for index in range(others.count()):
        others.nth(index).uncheck()
    expect(own.locator("[data-tick]")).to_be_checked()
    expect(dialog.locator(".render-dialog__title")).to_have_text("Render 1 image")


@pytest.mark.spec("ui:render:the-confirmation-starts-the-render")
def test_confirming_the_dialog_opens_the_session(page: Page, served: Served) -> None:
    page.goto(served.hub_of(RENDER))
    page.locator("[data-render]").click()
    _alone(page, RENDER)
    confirm = page.locator("[data-confirm]")
    expect(confirm).to_be_enabled()
    expect(page).to_have_url(served.hub_of(RENDER))

    confirm.click()

    drawer = page.locator("dialog[data-drawer]")
    expect(drawer.locator("[data-quiet]")).to_have_text("Nothing is billing.")
    expect(drawer.locator("[data-session-image] img")).to_have_count(1)
    expect(page.locator(".render-dialog")).to_have_count(0)
    expect(page).to_have_url(served.hub_of(RENDER))
    # The drawer is over the hub: closed, the hub is beneath it.
    page.keyboard.press("Escape")
    expect(drawer).to_have_count(0)
    expect(page.locator(".hub__grid")).to_be_visible()


@pytest.mark.spec("ui:sessions:the-drawer-holds-the-render")
def test_the_drawer_holds_the_render(page: Page, served: Served) -> None:
    page.goto(served.hub_of(DRAWN))
    page.locator("[data-render]").click()
    _alone(page, DRAWN)
    page.locator("[data-confirm]").click()

    drawer = page.locator("dialog[data-drawer]")
    image = drawer.locator("[data-session-image] img")
    expect(image).to_have_js_property("complete", True)
    expect(page).to_have_url(served.hub_of(DRAWN))
    # Half the window at least, against its right edge.
    box, size = drawer.bounding_box(), page.viewport_size
    assert box is not None and size is not None
    assert box["width"] >= max(size["width"] / 2, 480) - 1
    assert box["x"] + box["width"] == pytest.approx(size["width"], abs=1)
    page.keyboard.press("Enter")
    viewer = page.locator("dialog[data-viewer]")
    expect(viewer.locator("img")).to_have_attribute("src", re.compile(r"/image$"))
    page.keyboard.press("Escape")
    expect(viewer).to_have_count(0)
    expect(drawer).to_be_visible()
    page.keyboard.press("Escape")
    expect(drawer).to_have_count(0)
    expect(page.locator(".hub__grid")).to_be_visible()
    page.keyboard.press("Control+Semicolon")
    expect(drawer.locator("[data-outcome]")).to_have_text("done")
    # A click on the backdrop closes it.
    page.mouse.click(10, size["height"] / 2)
    expect(drawer).to_have_count(0)


@pytest.mark.spec("ui:renders:the-large-view-shows-its-sheet")
def test_an_image_opened_from_the_grid_shows_the_approval_it_came_from(
    page: Page, served: Served
) -> None:
    page.goto(f"{served.url}/c/{SHOWN}/renders")
    tile = page.locator("[data-version='1'][data-seed='7']")
    expect(tile.locator("img")).to_have_js_property("complete", True)

    tile.click()

    expect(page).to_have_url(
        f"{served.url}/c/{SHOWN}/renders/{served.shown.digest}/{FLOW}/v1/7"
    )
    sheet = page.locator("[data-sheet]")
    expect(sheet).to_contain_text("v1")
    expect(sheet).to_contain_text("hair_colour")
    page.keyboard.press("Escape")
    expect(page).to_have_url(f"{served.url}/c/{SHOWN}/renders")
    expect(tile).to_have_class(re.compile("renders__image--focused"))
    page.keyboard.press("Enter")
    expect(page.locator("[data-sheet]")).to_contain_text("v1")
    # Esc comes back focused on the image it closed, not the grid's first.
    page.goto(f"{served.url}/c/{COMPARED}/renders")
    second = page.locator("[data-version='2'][data-seed='7']")
    expect(second.locator("img")).to_have_js_property("complete", True)
    second.click()
    expect(page.locator("[data-sheet]")).to_contain_text("v2")
    page.keyboard.press("Escape")
    expect(second).to_have_class(re.compile("renders__image--focused"))
    expect(second).to_be_in_viewport()
    expect(page.locator("[data-version='1'][data-seed='7']")).not_to_have_class(
        re.compile("renders__image--focused")
    )
    # From a row's first image, h reaches its source, and ↵ opens its photograph.
    page.goto(f"{served.url}/c/{SHOWN}/renders")
    expect(tile).to_have_class(re.compile("renders__image--focused"))
    page.keyboard.press("h")
    expect(page.locator("[data-source]")).to_have_class(
        re.compile("renders__source--focused")
    )
    page.keyboard.press("Enter")
    viewer = page.locator("dialog[data-viewer]")
    expect(viewer.locator("img")).to_have_attribute(
        "src", f"/api/c/{SHOWN}/sources/hal.jpg"
    )


@pytest.mark.spec("ui:renders:a-source-opens-in-the-viewer")
def test_a_source_opens_in_the_viewer(page: Page, served: Served) -> None:
    grid = f"{served.url}/c/{SHOWN}/renders"
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
    page.goto(f"{served.url}/c/{DAMAGED}/renders")

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
    expect(
        rendered.locator("[data-version='1'][data-seed='7'] img")
    ).to_have_js_property("complete", True)

    rendered.click()

    viewer = page.locator("dialog[data-viewer]")
    expect(viewer.locator("img")).to_have_attribute("src", re.compile(r"/v1/7/image$"))
    expect(page).to_have_url(served.hub_of(SHOWN))
    page.keyboard.press("Enter")
    expect(page).to_have_url(
        f"{served.url}/c/{SHOWN}/renders/{served.shown.digest}/{FLOW}/v1/7"
    )
    expect(page.locator("[data-sheet]")).to_contain_text("v1")
    page.keyboard.press("Escape")
    expect(page).to_have_url(served.hub_of(SHOWN))
    expect(rendered).to_have_class(re.compile("hub__cell--focused"))
    expect(rendered).to_be_focused()
    expect(rendered).to_be_in_viewport()


@pytest.mark.spec("ui:hub:the-source-cell-opens-its-photograph")
def test_the_source_cell_opens_its_photograph(page: Page, served: Served) -> None:
    page.goto(served.hub_of(SHOWN))
    first = page.locator('.hub__cell[data-row="0"][data-column="1"]')
    expect(first).to_be_visible()
    page.keyboard.press("l")
    expect(first).to_be_focused()

    page.keyboard.press("h")
    source = page.locator('.hub__source[data-row="0"]')
    expect(source).to_be_focused()
    expect(source.locator(".hub__action")).to_be_visible()
    thumb = source.locator(".hub__thumb").bounding_box()
    images = page.locator('.hub__cell[data-row="0"] .hub__images').bounding_box()
    assert thumb is not None and images is not None
    assert thumb["y"] + thumb["height"] == pytest.approx(
        images["y"] + images["height"], abs=1
    )
    page.keyboard.press("Enter")

    viewer = page.locator("dialog[data-viewer]")
    expect(viewer.locator("img")).to_have_attribute(
        "src", f"/api/c/{SHOWN}/sources/hal.jpg"
    )
    expect(viewer.locator("img")).to_have_js_property("complete", True)


@pytest.mark.spec("ui:revise:revise-opens-review-on-the-revision")
def test_revise_opens_review_on_the_revision(page: Page, served: Served) -> None:
    digest = served.revised.digest
    page.goto(f"{served.url}/c/{REVISED}/renders/{digest}/{FLOW}/v1/7")
    expect(page.locator("[data-draft-from]")).to_be_visible()
    page.keyboard.press("Shift+D")
    dialog = page.locator("[data-draft-dialog]")
    expect(dialog).to_contain_text(f"Draft from this · {FLOW} v1 · seed 7")
    expect(dialog.locator("[data-target]").first).to_be_focused()
    expect(dialog.locator("[data-target]").first).to_contain_text(f"{FLOW}revise")

    page.keyboard.press("Enter")

    review = f"{served.url}/c/{REVISED}/review/{digest}/{FLOW}"
    expect(page).to_have_url(review)
    expect(page.locator("[data-revised] img")).to_have_js_property("complete", True)
    expect(page.locator(".renders-block")).to_contain_text("seed 7")
    expect(page.locator(".form")).to_contain_text("revision of render 7")
    row = page.locator(".row", has_text="hair_colour")
    with page.expect_response(lambda response: response.request.method == "PUT"):
        row.locator(".chip__x").first.click()
    expect(page.locator("[data-changed='hair_colour']")).to_contain_text("was")
    expect(page.locator(".receipt__when")).to_contain_text("saved")
    draft = current_draft(served.revised.directory(FLOW, REVIEW))
    assert draft is not None
    before = draft.read_bytes()
    page.goto(f"{served.url}/c/{REVISED}/renders/{digest}/{FLOW}/v1/7")
    expect(page.locator("[data-draft-from]")).to_be_visible()
    page.keyboard.press("Shift+D")
    page.keyboard.press("Enter")
    expect(page).to_have_url(review)
    expect(page.locator("[data-draft-dialog]")).to_have_count(0)
    expect(page.locator("[data-changed='hair_colour']")).to_contain_text("was")
    assert current_draft(served.revised.directory(FLOW, REVIEW)) == draft
    assert draft.read_bytes() == before
    page.get_by_role("button", name="Approve sheet").click()
    expect(page.locator(".form")).to_contain_text("approved")
    expect(page.locator("input.fragment")).to_have_count(0)
    expect(page).to_have_url(review)
    expect(page.locator("[data-revised] img")).to_be_visible()
    expect(page.locator("[data-changed='hair_colour']")).to_contain_text("was")


@pytest.mark.spec("ui:conjure-from:conjure-from-this-opens-review")
def test_conjure_from_this_opens_review(page: Page, served: Served) -> None:
    digest = served.conjured.digest
    page.goto(f"{served.url}/c/{CONJURED}/renders/{digest}/{FLOW}/v1/7")
    expect(page.locator("[data-draft-from]")).to_contain_text("Draft from this")
    page.keyboard.press("Shift+D")
    rows = page.locator("[data-draft-dialog] [data-target]")
    expect(rows.first).to_be_focused()
    for _ in range([CONJURE in text for text in rows.all_inner_texts()].index(True)):
        page.keyboard.press("j")
    expect(rows.filter(has_text=CONJURE)).to_be_focused()

    page.keyboard.press("Enter")

    expect(page).to_have_url(f"{served.url}/c/{CONJURED}/review/{digest}/{CONJURE}")
    expect(page.locator(".form")).to_contain_text(f"from {FLOW} v1")
    expect(page.locator("[data-changed='clothes']")).to_contain_text("was")
    expect(page.locator("[data-caption-heading]")).to_contain_text(f"caption · {FLOW}")
    revised = page.locator("[data-revised]")
    expect(revised).to_contain_text(f"drafted from {FLOW} v1 · seed 7")
    expect(revised.locator("img")).to_have_js_property("complete", True)
    expect(revised.locator("img")).not_to_have_js_property("naturalWidth", 0)


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


@pytest.mark.spec("ui:revise:side-by-side-shows-the-pair")
def test_side_by_side_shows_the_pair(page: Page, served: Served) -> None:
    page.goto(served.review(served.discarded, DISCARDED))
    expect(page.locator("[data-revised] img")).to_have_js_property("complete", True)

    page.locator("input.fragment").first.click()

    page.keyboard.press("Control+KeyP")

    pair = page.locator("dialog[data-pair] img")
    expect(pair).to_have_count(2)
    for one in (pair.nth(0), pair.nth(1)):
        expect(one).to_have_js_property("complete", True)
    # One read of both boxes: the dialog re-centres as each image's ratio lands.
    page.wait_for_function(
        """() => {
          const [a, b] = [...document.querySelectorAll('dialog[data-pair] img')]
            .map((one) => one.getBoundingClientRect())
          return a.height > 0 && Math.abs(a.height - b.height) <= 1 && a.top === b.top
        }"""
    )
    page.keyboard.press("Control+KeyP")
    viewer = page.locator("dialog[data-viewer]")
    expect(page.locator("dialog[data-pair]")).to_have_count(0)
    expect(viewer.locator("img")).to_have_count(1)
    expect(viewer.locator("img")).to_have_attribute("src", re.compile(r"/photo$"))
    page.keyboard.press("Escape")
    expect(viewer).to_have_count(0)


@pytest.mark.spec("ui:compare:side-by-side-sets-the-image-beside-its-photograph")
def test_side_by_side_sets_the_image_beside_its_photograph(
    page: Page, served: Served
) -> None:
    large = f"{served.url}/c/{COMPARED}/renders/{served.compared.digest}/{FLOW}/v2/7"
    page.goto(large)
    expect(page.locator("[data-sheet]")).to_contain_text("v2")
    expect(page.locator("[data-side-by-side]")).to_have_count(0)

    # The photograph is the pick's top row.
    page.keyboard.press("Shift+C")
    picker = page.locator("dialog[data-compare-pick]")
    expect(picker.get_by_role("button", name=f"{FLOW} · v1 · seed 7")).to_be_focused()
    page.keyboard.press("k")
    expect(picker.get_by_role("button", name="photograph")).to_be_focused()
    page.keyboard.press("Enter")

    expect(page).to_have_url(f"{large}/compare/photo")
    pair = page.locator("[data-side] img")
    expect(pair).to_have_count(2)
    expect(pair.nth(0)).to_have_attribute("src", re.compile(r"/photo$"))
    expect(pair.nth(1)).to_have_attribute("src", re.compile(r"/v2/7/image$"))
    for one in (pair.nth(0), pair.nth(1)):
        expect(one).to_have_js_property("complete", True)
    page.wait_for_function(
        """() => {
          const [a, b] = [...document.querySelectorAll('[data-side] img')]
            .map((one) => one.getBoundingClientRect())
          return a.height > 0 && Math.abs(a.height - b.height) <= 1 && a.top === b.top
        }"""
    )
    expect(page.locator("[data-changed]")).to_have_count(0)
    page.keyboard.press("Escape")
    expect(page).to_have_url(large)


@pytest.mark.spec("ui:compare:compare-shows-the-pair-and-the-change")
def test_compare_shows_both_versions_of_a_seed_each_under_its_head(
    page: Page, served: Served
) -> None:
    large = f"{served.url}/c/{COMPARED}/renders/{served.compared.digest}/{FLOW}/v2/7"
    page.goto(large)
    expect(page.locator("[data-compare]")).to_contain_text("Compare with…")

    # ⇧C opens the source's grid on this seed's older version, this image marked,
    # the head naming the focused tile.
    page.keyboard.press("Shift+C")
    picker = page.locator("dialog[data-compare-pick]")
    expect(picker.locator(".viewer__title")).to_have_text(
        f"Compare {FLOW} v2 · seed 7 with {FLOW} v1 · seed 7…"
    )
    expect(picker.locator(".pick__flow")).to_have_text(["photo", FLOW, FLAT])
    expect(picker.locator("[data-origin]")).to_have_attribute(
        "aria-label", f"{FLOW} · v2 · seed 7"
    )
    expect(picker.get_by_role("button", name=f"{FLOW} · v1 · seed 7")).to_be_focused()
    page.keyboard.press("Enter")

    # The image picked is on the left, the one compare started from on the right,
    # each under its head alone, and no change block.
    expect(page).to_have_url(f"{large}/compare/{FLOW}/v1/7")
    left = page.locator("[data-side='left'] figcaption")
    right = page.locator("[data-side='right'] figcaption")
    expect(left).to_have_text(f"{FLOW} · v1 · seed 7")
    expect(right).to_have_text(f"{FLOW} · v2 · seed 7")
    images = page.locator("[data-side] img")
    expect(images).to_have_count(2)
    expect(images.nth(0)).to_have_js_property("complete", True)
    expect(page.locator("[data-changed]")).to_have_count(0)
    # A pick of another flow's image compares it, its head naming the other seed.
    page.goto(large)
    expect(page.locator("[data-compare]")).to_be_visible()
    page.keyboard.press("Shift+C")
    expect(picker.get_by_role("button", name=f"{FLOW} · v1 · seed 7")).to_be_focused()
    page.keyboard.press("j")
    expect(picker.get_by_role("button", name=f"{FLAT} · v1 · seed 9")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page).to_have_url(f"{large}/compare/{FLAT}/v1/9")
    expect(left).to_have_text(f"{FLAT} · v1 · seed 9")
    expect(right).to_have_text(f"{FLOW} · v2 · seed 7")
