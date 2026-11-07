"""The hub in a browser: a tick assigns a flow, and Prepare runs what changed.

Prepare is the real `prepare` verb, run as the server's child on the suite's
doubles, so a cell reaches its sheet exactly as it would by hand.
"""

import re

import pytest
from playwright.sync_api import Locator, Page, expect

from tests.e2e.conftest import RENDER, Served

FLOW = "summon-anime-wai"
OTHER = "conjure-anime-wai"
# One CLI child imports the package, then prepares the photograph.
PREPARED = 60_000


def _cell(page: Page, source: str, flow: str = FLOW) -> Locator:
    return page.locator(f'.hub__cell[data-source="{source}.jpg"][data-flow="{flow}"]')


@pytest.mark.spec("ui:hub:a-tick-assigns-the-flow")
@pytest.mark.spec("ui:hub:an-edge-row-shows-the-head")
def test_a_tick_assigns_the_flow_and_survives_a_reload(
    page: Page, served: Served
) -> None:
    page.goto(served.hub_of("hub-tick"))
    expect(_cell(page, "tick")).to_have_attribute("data-stage", "none")
    # Rows aside and beside are selected; a click on tick's checkbox ticks it alone.
    page.keyboard.press("Shift+ArrowDown")
    _cell(page, "tick").get_by_role("checkbox").click()
    expect(_cell(page, "tick")).to_have_attribute("data-stage", "assigned")
    expect(_cell(page, "aside")).to_have_attribute("data-stage", "none")
    expect(_cell(page, "beside")).to_have_attribute("data-stage", "none")
    expect(page.locator(".hub__head")).to_have_css("gap", "12px")

    page.reload()

    expect(_cell(page, "tick")).to_have_attribute("data-stage", "assigned")
    expect(page.locator(".prepare-bar")).to_contain_text("1 change · Prepare")
    # In a short window the last row brings the foot into view, the first the head.
    page.set_viewport_size({"width": 1280, "height": 300})
    add = page.get_by_role("button", name="Add sources…")
    page.keyboard.press("j")
    page.keyboard.press("j")
    expect(add).not_to_be_in_viewport()
    page.keyboard.press("k")
    page.keyboard.press("k")
    expect(add).to_be_in_viewport()


@pytest.mark.spec("ui:prepare:prepare-runs-the-assigned-cells")
def test_prepare_takes_the_assigned_cells_to_their_sheet_and_no_other(
    page: Page, served: Served
) -> None:
    page.goto(served.hub_of("hub-prepare"))
    expect(_cell(page, "pick")).to_have_attribute("data-stage", "assigned")

    page.get_by_role("button", name="1 change · Prepare").click()

    # The reader is held, so the tagging is done and the reading waits.
    held = r"tag 1 of 1 · caption 0 of 1 · sheet 0 of 1 · \d+:\d+"
    try:
        strip = page.locator(".jobstrip__totals")
        bar = page.locator(".prepare-bar__cells")
        expect(strip).to_have_text(re.compile(held), timeout=PREPARED)
        initial = strip.inner_text()
        expect(bar).to_have_text(f"Prepare · {initial}")
        expect(strip).not_to_have_text(initial, timeout=3000)
        before_reload = strip.inner_text()
        page.reload()
        expect(strip).to_have_text(re.compile(held))
        elapsed = strip.inner_text().rsplit(" · ", 1)[1]
        assert elapsed >= before_reload.rsplit(" · ", 1)[1]
        expect(bar).to_have_text(re.compile(f"Prepare · {held}"))

        # A render has its own slot: the running Prepare holds no collection's Render.
        beside = page.context.new_page()
        beside.goto(served.hub_of(RENDER))
        expect(beside.locator("[data-render-bar] [data-render]")).to_be_enabled()
        beside.close()
    finally:
        served.prepare_release.touch()

    expect(_cell(page, "pick")).to_have_attribute(
        "data-stage", "sheet", timeout=PREPARED
    )
    expect(_cell(page, "skip")).to_have_attribute("data-stage", "none")
    expect(_cell(page, "pick", OTHER)).to_have_attribute("data-stage", "none")
    # Other collections' images may still show the Render bar; the Prepare bar is gone.
    expect(page.locator(".prepare-bar:not([data-render-bar])")).to_have_count(0)
