"""The hub in a browser: a tick assigns a flow, and Prepare runs what changed.

Prepare's stages are the real verbs, run as the server's children on the
suite's doubles, so a cell reaches its sheet exactly as it would by hand.
"""

import re

import pytest
from playwright.sync_api import Locator, Page, expect

from tests.e2e.conftest import Served

FLOW = "summon-anime-wai"
OTHER = "conjure-anime-wai"
# Three CLI children start in turn, each importing the package.
PREPARED = 60_000


def _cell(page: Page, source: str, flow: str = FLOW) -> Locator:
    return page.locator(f'.hub__cell[data-source="{source}.jpg"][data-flow="{flow}"]')


@pytest.mark.spec("ui:hub:a-tick-assigns-the-flow")
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


@pytest.mark.spec("ui:prepare:prepare-runs-the-assigned-cells")
def test_prepare_takes_the_assigned_cells_to_their_sheet_and_no_other(
    page: Page, served: Served
) -> None:
    page.goto(served.hub_of("hub-prepare"))
    expect(_cell(page, "pick")).to_have_attribute("data-stage", "assigned")

    page.get_by_role("button", name="1 change · Prepare").click()

    try:
        strip = page.locator(".jobstrip__totals")
        bar = page.locator(".prepare-bar__cells")
        expect(strip).to_have_text(re.compile(r"0 of 1 cell done · \d+:\d+"))
        initial = strip.inner_text()
        expect(bar).to_have_text(f"Prepare · {initial}")
        expect(strip).not_to_have_text(initial, timeout=3000)
        before_reload = strip.inner_text()
        page.reload()
        expect(strip).to_have_text(re.compile(r"0 of 1 cell done · \d+:\d+"))
        elapsed = strip.inner_text().rsplit(" · ", 1)[1]
        assert elapsed >= before_reload.rsplit(" · ", 1)[1]
        expect(bar).to_have_text(re.compile(r"Prepare · 0 of 1 cell done · \d+:\d+"))
    finally:
        served.prepare_release.touch()

    expect(_cell(page, "pick")).to_have_attribute(
        "data-stage", "sheet", timeout=PREPARED
    )
    expect(_cell(page, "skip")).to_have_attribute("data-stage", "none")
    expect(_cell(page, "pick", OTHER)).to_have_attribute("data-stage", "none")
    expect(page.locator(".prepare-bar")).to_have_count(0)
