"""The page's keys in a browser: the key list, a field, `Esc` and the pane keys.

One journey on a collection of its own. Each step leaves the sheet as it found it,
so none leans on another.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import Served

# What the key list covers: a focus in any of these is a focus in the page behind it.
BEHIND = ".rail, .source, .form, .appbar"
# The page's own check for macOS, `isMac` in `ui/src/stores/keys.ts`.
MAC = (
    "() => /mac|iphone|ipad/i.test("
    "navigator.userAgentData?.platform ?? navigator.platform ?? '')"
)
FIELD = "() => Boolean(document.activeElement?.matches('input.fragment'))"
COVERED = f"() => Boolean(document.activeElement?.closest('{BEHIND}'))"


def _pane(page: Page, mac: bool, toward: str) -> None:
    """Press the pane key `toward`, `h` or `l`, as the platform reads it."""
    if mac:
        page.keyboard.press(f"Control+Key{toward.upper()}")
        return
    if page.evaluate(FIELD):
        page.keyboard.press("Escape")
    page.keyboard.press(toward)


@pytest.mark.spec("ui:dialogs:the-key-list-holds-the-focus-in-a-browser")
@pytest.mark.spec("ui:keys:a-letter-typed-in-a-tag-field-is-text")
@pytest.mark.spec("ui:keys:the-pane-keys-move-the-focus-in-a-browser")
def test_the_keys_hold_in_a_browser(page: Page, served: Served) -> None:
    (only,) = served.queues["keys-hold"]
    review = served.review(only, "keys-hold")
    page.goto(review)
    card = page.locator(".rail__card--current")
    field = page.locator("input.fragment").first
    expect(field).to_be_visible()
    expect(card).to_be_focused()

    # The key list keeps the focus off the page behind it, and closes three ways.
    dialog = page.locator("dialog[data-key-list]")
    opener = page.locator('button[title^="the key list"]')
    page.keyboard.press("Control+Slash")
    expect(dialog).to_be_visible()
    for key in ("Tab", "Tab", "Shift+Tab", "Shift+Tab", "Shift+Tab"):
        page.keyboard.press(key)
        assert not page.evaluate(COVERED)
    page.keyboard.press("Control+Slash")
    expect(dialog).to_have_count(0)
    expect(card).to_be_focused()
    page.keyboard.press("Control+Slash")
    expect(dialog).to_be_visible()
    page.keyboard.press("Escape")
    expect(dialog).to_have_count(0)
    expect(card).to_be_focused()
    opener.click()
    expect(dialog).to_be_visible()
    page.mouse.click(5, 5)
    expect(dialog).to_have_count(0)
    expect(opener).to_be_focused()
    expect(page).to_have_url(review)

    # A letter typed in a tag field is text: no pane or row moves.
    field.click()
    field.press_sequentially("hjkl")
    expect(field).to_have_value("hjkl")
    expect(field).to_be_focused()
    expect(page).to_have_url(review)
    field.fill("")

    # Esc closes the suggestion list first, then leaves the field.
    field.press_sequentially("eyes")
    rows = page.locator(".drop__row")
    expect(rows).to_have_count(2)
    page.keyboard.press("Escape")
    expect(rows).to_have_count(0)
    expect(field).to_be_focused()
    expect(field).to_have_value("eyes")
    page.keyboard.press("Escape")
    expect(field).not_to_be_focused()
    expect(page).to_have_url(review)
    field.fill("")

    # The pane keys take the focus from the rail to the source, the sheet and ④.
    mac = bool(page.evaluate(MAC))
    card.focus()
    _pane(page, mac, "l")
    expect(page.locator(".source")).to_be_focused()
    _pane(page, mac, "l")
    expect(field).to_be_focused()
    _pane(page, mac, "l")
    steps = page.locator(".renders-block").locator("button:not(:disabled), input")
    expect(steps.first).to_be_focused()
    _pane(page, mac, "h")
    expect(field).to_be_focused()
