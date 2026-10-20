"""Review in a browser: the surface the shell carries, recorded.

Each test waits on the page's own state, never on time.
"""

import re

import pytest
from playwright.sync_api import Page, expect

from isekai.foundation.flow import load_flow
from isekai.foundation.run import Run
from tests.e2e.conftest import FLOW, Served


def _open(page: Page, served: Served, run: Run) -> None:
    """Load `run`'s review in the batch."""
    page.goto(served.review(run))


@pytest.mark.spec("ui:vocabulary:matches-are-ranked-by-post-count")
def test_a_tag_is_committed_from_the_ranked_autocomplete(
    page: Page, served: Served
) -> None:
    _open(page, served, served.draft)
    field = page.locator("input.fragment").first
    field.click()
    field.press_sequentially("eyes")
    rows = page.locator(".drop__row")
    expect(rows).to_have_count(2)
    expect(rows.nth(0)).to_contain_text("blue eyes")
    expect(rows.nth(1)).to_contain_text("brown eyes")
    expect(rows.nth(0).locator(".drop__posts")).to_contain_text("1,490,640")
    field.press("Enter")
    row = page.locator(".row", has=field)
    expect(row.locator(".chip", has_text="blue eyes")).to_be_visible()


@pytest.mark.spec("ui:approval:approved-input-opens-read-only")
def test_an_approved_input_opens_read_only(page: Page, served: Served) -> None:
    _open(page, served, served.approved)
    expect(page.locator(".approve-bar__fact")).to_contain_text("Approved")
    expect(page.locator(".chip").first).to_be_visible()
    expect(page.locator("input.fragment")).to_have_count(0)
    expect(page.locator(".chip__x")).to_have_count(0)


@pytest.mark.spec("ui:cheatsheet:every-declared-criterion-is-answered")
def test_option_space_opens_the_cheatsheet(page: Page, served: Served) -> None:
    _open(page, served, served.draft)
    expect(page.locator("input.fragment").first).to_be_visible()
    page.keyboard.press("Alt+Space")
    groups = page.locator(".cheatsheet__group")
    expect(groups).to_have_count(len(load_flow(FLOW).schema.names))
    expect(page.locator(".overlay__foot")).to_contain_text(
        re.compile(r"\d+ tags shown")
    )
