"""Review in a browser: the surface the shell carries, recorded.

Each test waits on the page's own state, never on time.
"""

import re

import pytest
from playwright.sync_api import Page, expect

from isekai.foundation.artifacts import DRAFT_FILE, read
from isekai.foundation.flow import load_flow
from isekai.foundation.run import REVIEW, Run, latest_artifact
from isekai.pipeline.review import DRAFT
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

    # Leaving inside the debounce sends the edit: the hub opens only once the
    # route's leave guard has had the draft written.
    page.keyboard.press("Escape")
    page.keyboard.press("Shift+KeyH")
    expect(page).to_have_url(served.hub)
    draft = latest_artifact(served.draft.directory(FLOW, REVIEW), DRAFT)
    assert draft is not None
    fields = read(draft, DRAFT_FILE)["fields"]
    assert any("blue eyes" in tags for tags in fields.values())


@pytest.mark.spec("ui:approval:approved-input-opens-read-only")
def test_an_approved_input_opens_read_only(page: Page, served: Served) -> None:
    _open(page, served, served.approved)
    expect(page.locator(".approve-bar__fact")).to_contain_text("Approved")
    expect(page.locator(".chip").first).to_be_visible()
    expect(page.locator("input.fragment")).to_have_count(0)
    expect(page.locator(".chip__x")).to_have_count(0)


@pytest.mark.spec("ui:review:the-photograph-opens-in-the-viewer")
def test_the_photograph_opens_in_the_viewer(page: Page, served: Served) -> None:
    _open(page, served, served.draft)
    expect(page.locator("input.fragment").first).to_be_visible()

    page.locator(".source .photo-frame").click()

    viewer = page.locator("dialog[data-viewer]")
    expect(viewer).to_contain_text("ada.jpg · 900×1200 · fit")
    page.keyboard.press("ArrowRight")
    expect(viewer).to_contain_text("bea.jpg · 1200×900 · fit")
    page.keyboard.press("Escape")
    expect(viewer).to_have_count(0)


@pytest.mark.spec("ui:cheatsheet:every-declared-criterion-is-answered")
def test_mod_k_opens_the_cheatsheet(page: Page, served: Served) -> None:
    _open(page, served, served.draft)
    expect(page.locator("input.fragment").first).to_be_visible()
    page.keyboard.press("ControlOrMeta+KeyK")
    groups = page.locator(".cheatsheet__group")
    expect(groups).to_have_count(len(load_flow(FLOW).schema.names))
    expect(page.locator(".overlay__foot")).to_contain_text(
        re.compile(r"\d+ tags shown")
    )


@pytest.mark.spec("ui:keys:a-command-waits-until-the-field-is-left")
def test_a_command_waits_until_the_field_is_left(page: Page, served: Served) -> None:
    _open(page, served, served.draft)
    field = page.locator("input.fragment").first
    field.click()
    field.press("Shift+KeyH")
    # The list the letter opens is the field's own, and the first Esc closes it.
    expect(page.locator(".drop__row").first).to_be_visible()
    field.press("Escape")
    expect(page.locator(".drop__row")).to_have_count(0)
    expect(field).to_have_value("H")
    expect(page).to_have_url(re.compile("/review/"))

    page.keyboard.press("Escape")
    page.keyboard.press("Shift+KeyH")
    expect(page).to_have_url(served.hub)
