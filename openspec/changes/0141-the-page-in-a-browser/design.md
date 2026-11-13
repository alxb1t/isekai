# The page in a browser — design

The browser suite fails on nothing the page logs, and the key list's focus, a letter typed in a tag field, the pane keys and Approve pressed over a held save are held by no browser test. This change adds a guard on the browser context and a browser test for each, which CI proves after the merge. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The audit read the suite at `d3f72349`. A build cannot start Chromium, so a browser test it writes is first run by CI after the merge ([D8](#d8)); each step below therefore asserts only what the code in the cut's reading shows, and fails loudly when the page differs.

| gap | where it lives at the cut |
|---|---|
| no hook fails a test on a page error; `page` is the plugin's own | `tests/e2e/conftest.py`; pytest-playwright's `context` and `page` fixtures |
| the expected failures are the hub's stubbed 409 and the unknown collection's | `tests/e2e/test_queue.py` `test_a_failure_reading_the_next_state_shows_in_the_approve_bar`; `tests/e2e/test_routes.py` |
| one test opens a second page | `tests/e2e/test_prepare.py` `page.context.new_page()` |
| the key list's held focus is proven by a grep of its component | `ui/src/composables/useHeldFocus.ts`, `ui/src/components/KeyList.vue`, `ui/src/stores/keys.test.ts` |
| the pane keys and a field's letters are pressed in no browser | `ui/src/panes.ts` `paneKeys`; `ui/src/views/Review.vue` `movePane` |
| Approve over a held save, and a refused save sent again, are unproven; the draft's PUT is sent with `keepalive` | `ui/src/api.ts` `saveDraft`; `ui/src/views/Review.vue` `approve`; `ui/src/composables/useSheet.ts` |

```
 tests/e2e/guard.py ◀── conftest.py `context`   fails a test on what the page logs           (phase 1)
 tests/test_e2e_guard.py                         the guard's rules, no browser                 (phase 1)
 tests/e2e/test_keys.py                          key list · a field · Esc · pane keys         (phase 2)
 tests/e2e/held.py ◀── test_queue.py · test_import.py   a request held at the network         (phase 3)
```

## Goals / Non-Goals

**Goals**
- A browser test that uses a page fails on a page error, a console error that is no failed load, a 5xx, and a 4xx it did not declare.
- The key list's held focus, a letter typed in a tag field, `Esc` and the pane keys are pressed in a browser, on Linux and on the Mac.
- Approve pressed while the draft's save is held at the network waits for it, and a lone refused save is sent again by the next Approve; the test first asserts the route saw the PUT.

**Non-Goals**
- A product file, a requirement, a format version, a flag, a verb or a decision in force. `docs/decisions.md` is not edited.
- A mutant: the replay runs pytest and vitest, never a browser.
- A step that runs the browser tests before the merge: CI holds them.
- A scenario's key moving to a browser test: it changes a `Layers` line, which modifies a requirement.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The guard is a `context` fixture in `tests/e2e/conftest.py` that requests the plugin's own and listens on it | [Q64](../../../docs/decisions.md): the guard sits on the browser context, only where a test uses a page, so the second page of `test_prepare.py` is covered and `test_gpu.py`, which uses none, is not | an autouse fixture, which would start a browser for `test_gpu.py`; a listener on `page` |
| [D2](#d2) | What the guard refuses is one pure function, `faults`, in `tests/e2e/guard.py`, held by `tests/test_e2e_guard.py` with no browser | `T6`: the twin is at the lowest layer, a unit test, never a new browser test | a browser test of the guard |
| [D3](#d3) | A test declares a 4xx it expects by appending `Refused(status, path)` to the `refusals` fixture; a declaration no response met is a fault | Q64: a test declares the 4xx it expects; a declaration that nothing answers would bless a stub that no longer runs | one status list for every test; a marker, which needs a registration |
| [D4](#d4) | The keys are one journey, `test_the_keys_hold_in_a_browser` in `tests/e2e/test_keys.py`, on a collection of its own | Q65: one journey; [T2](#tests) finds no test that reaches a clean editable Review | steps added to `test_the_photograph_opens_in_the_viewer`, which ends on a changed viewport and a saved edit |
| [D5](#d5) | The pane key is pressed as the platform reads it: `⌃H` `⌃L` when the page's own check says macOS, else `Esc` out of a field and `h` `l` | Q65: keys pressed so Linux and the Mac agree; the spec moves panes by `⌃H` `⌃L` on macOS and by `h` `l` elsewhere | one key for both, which one platform ignores |
| [D6](#d6) | The key list is held as a dialog the focus never leaves for the page behind: its `Tab` and `⇧Tab` are pressed and the page's panes are asserted not to hold the focus | the key list holds no control, so `useHeldFocus` has nothing to wrap; see [C9](#d6) | a `Tab` count that wraps, which the dialog's lack of controls cannot show |
| [D7](#d7) | Each of Approve's cases is its own test in `tests/e2e/test_queue.py`, over a collection of sheets, one for each; a held request is `hold` and `sent` from `tests/e2e/held.py` | Q66: the route first asserts it saw the PUT, so a `keepalive` request it missed fails loudly; `T3`: a case stands alone | one test with the second case after Cancel approve |
| [D8](#d8) | A build runs `uv run pytest tests/e2e --collect-only -q` and the gate; the first run of each test is CI's, after the merge, and a red run is fixed by a patch at once | Q63: the sandbox has no browser, and a browser step written in a build has been red at its first run | a run before the merge, which is a MinionsFactory matter |
| [D9](#d9) | Scenarios are added under the requirements that name each behaviour, each end-to-end; each requirement's text is the one `0140-the-sheet-and-the-keys` leaves | Q65: the browser test binds scenarios added under existing requirements; a patch adds a scenario, never a requirement | `skip_specs`; a MODIFIED SHALL |

### D1

`tests/e2e/conftest.py` gains the fixtures below. The `context` parameter is the plugin's own, so the override wraps it; a test that asks for `page` gets the guard, a test that asks for neither does not. The teardown runs before the plugin closes the context.

```python
@pytest.fixture
def refusals() -> list[Refused]:
    """The 4xx the test expects: it appends a `Refused` for each."""
    return []


@pytest.fixture
def context(
    context: BrowserContext, refusals: list[Refused]
) -> Iterator[BrowserContext]:
    """Fail the test on what its pages log, as `guard.faults` reads it."""
    seen = Seen()
    context.on("weberror", lambda web: seen.errors.append(web.error.message))
    context.on(
        "console", lambda message: seen.consoles.append((message.type, message.text))
    )
    context.on(
        "response",
        lambda response: seen.responses.append(
            (response.status, urlsplit(response.url).path)
        ),
    )
    yield context
    found = faults(seen, refusals)
    assert not found, "the page misbehaved:\n" + "\n".join(found)
```

### D2

```python
FAILED_LOAD = "Failed to load resource"


@dataclass(frozen=True)
class Refused:
    """A 4xx a test expects: its status, and what the request's path starts with."""

    status: int
    path: str


@dataclass
class Seen:
    """What a context saw: page errors, console messages, and responses."""

    errors: list[str] = field(default_factory=list)
    consoles: list[tuple[str, str]] = field(default_factory=list)
    responses: list[tuple[int, str]] = field(default_factory=list)


def answered(refusal: Refused, status: int, path: str) -> bool:
    """Return whether a response of `status` at `path` is the one `refusal` declares."""
    return status == refusal.status and path.startswith(refusal.path)


def faults(seen: Seen, expected: Sequence[Refused]) -> list[str]:
    """Return each thing a browser test must fail on, one line each, in the order seen."""
    found = [f"page error: {text}" for text in seen.errors]
    found += [
        f"console {kind}: {text}"
        for kind, text in seen.consoles
        if kind == "error" and not text.startswith(FAILED_LOAD)
    ]
    for status, path in seen.responses:
        if status >= 500:
            found.append(f"server error: {status} {path}")
        elif status >= 400 and not any(answered(one, status, path) for one in expected):
            found.append(f"undeclared refusal: {status} {path}")
    found += [
        f"declared refusal never answered: {one.status} {one.path}"
        for one in expected
        if not any(answered(one, status, path) for status, path in seen.responses)
    ]
    return found
```

A failed load is Chromium's own console line for any non-2xx response, so the response check holds it and the console check lets it by. The test ends in an error at teardown, naming each fault.

### D3

The declarations at the cut: `test_a_failure_reading_the_next_state_shows_in_the_approve_bar` stubs the hub's read and appends `Refused(409, "/api/c/queue-fails/hub")`; the unknown collection of `test_a_reload_lands_on_the_same_hub_and_the_same_review` appends `Refused(409, "/api/c/no-such-collection/")`, a prefix that holds both of its refused reads, as the server answers a refusal with `REFUSED = 409` (`isekai/interface/ui/app.py:198`) and `collection` raises a `Refusal` for a name the library lacks (`isekai/interface/ui/library.py:278`). The refused save of [D7](#d7) appends `Refused(409, "/api/c/save-holds/review/")`.

### D4

The journey opens the one sheet of the collection `keys-hold` and leaves it as it found it: no tag is committed, and each typed text is cleared. The steps, in order:

| step | what it presses | what it asserts |
|---|---|---|
| the key list | `⌃/`, then `Tab` and `⇧Tab` presses, then `⌃/`; `⌃/` and `Esc`; the app bar's `?` and a click at the window's corner | the dialog shows; the focus never sits in a pane, the rail or the app bar behind it; each close returns the focus to the rail's card, the `?` button for the last |
| a field | `hjkl` typed into the first tag field | the field holds `hjkl`, keeps the focus, the address is unchanged |
| `Esc` | `eyes` typed, then `Esc` twice | the suggestions for `eyes` show; the first `Esc` closes them, the field keeps its focus and text; the second leaves the field |
| the pane keys | from the rail's card, the pane key on to ④, then the other way | the focus is on the source pane, the first field, the first enabled control of ④, then the first field |

`tests/e2e/test_keys.py`, whole:

```python
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
MAC = "() => /mac|iphone|ipad/i.test(navigator.userAgentData?.platform ?? navigator.platform ?? '')"
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
```

### D5

The page decides macOS by `isMac` in `ui/src/stores/keys.ts`; the journey reads the same test of `navigator`, so the key it presses is the one the page declared:

```python
MAC = "() => /mac|iphone|ipad/i.test(navigator.userAgentData?.platform ?? navigator.platform ?? '')"
```

On macOS `Control+KeyH` and `Control+KeyL` move between the panes from a field or not. Elsewhere `h` and `l` do, outside a field, so the helper presses `Escape` first when the focus is in a tag field: `Esc` blurs the field and the pane stays the one last entered.

### D6

The key list is `dialog[data-key-list]`, closed by `⌃/`, `Esc` and a click on its backdrop. It holds no control, so `Tab` and `⇧Tab` have nothing to wrap: the journey presses each and asserts the focus is never in `.rail`, `.source`, `.form` or `.appbar`, which the modal dialog makes inert. The wrap is the Render dialog's step, pressed already by `ui:dialogs:the-render-dialog-opens-on-its-first-photograph`; row C9 of the brief reads *holds and wraps* so.

### D7

The collection `save-holds` holds the sources `lou` and `max`, as `QUEUES` holds `queue-stays`; each test opens one. `tests/e2e/held.py`:

```python
def hold(page: Page, pattern: str, method: str = "PUT") -> list[Route]:
    """Hold each `method` request to `pattern`, appending it to the list returned."""
    held: list[Route] = []

    def take(route: Route) -> None:
        if route.request.method == method:
            held.append(route)
        else:
            route.continue_()

    page.route(pattern, take)
    return held


def sent(page: Page, held: list[Route], nth: int = 0) -> Route:
    """Return the `nth` held request, once the page has sent it."""
    for _ in range(100):
        if len(held) > nth:
            return held[nth]
        page.wait_for_timeout(50)
    raise AssertionError("the held request was never sent")
```

`sent` is `test_import.py`'s `_sent`, moved, with `nth` for a later request; a PUT the route never saw fails there.

The first case holds the PUT, presses Approve, asserts no `/approve` request goes in half a second, releases the PUT, and reads the approval from disk. The second answers the PUT `409` itself, waits for the refusal in the approve bar, presses Approve, releases the next PUT, and reads the approval. In `tests/e2e/test_queue.py`, after the tests it holds:

```python
PUTS = "**/api/c/save-holds/review/**/draft"
REFUSAL = "the draft is not at that save"
APPROVED_BAR = "approved as 001.approved.json and read-only"


def _edit(page: Page) -> None:
    """Commit the first suggestion for `eyes` into the sheet's first field."""
    field = page.locator("input.fragment").first
    expect(field).to_be_visible()
    field.click()
    field.press_sequentially("eyes")
    field.press("Enter")
    row = page.locator(".row", has=field)
    expect(row.locator(".chip", has_text="blue eyes")).to_be_visible()


def _holds_the_edit(run: Run) -> None:
    """Assert `run`'s newest approval holds the tag `_edit` committed."""
    approval = latest_artifact(run.directory(FLOW, REVIEW), APPROVED)
    assert approval is not None
    fields = read(approval, APPROVED_FILE)["fields"]
    assert any("blue eyes" in tags for tags in fields.values())


@pytest.mark.spec("ui:save:an-approval-waits-for-a-save-held-at-the-network")
def test_approve_waits_for_a_save_held_at_the_network(
    page: Page, served: Served
) -> None:
    first, _ = served.queues["save-holds"]
    page.goto(served.review(first, "save-holds"))
    held = hold(page, PUTS)
    approvals: list[str] = []

    def note(request: Request) -> None:
        if request.url.endswith("/approve"):
            approvals.append(request.url)

    page.on("request", note)
    _edit(page)
    # The route must see the save first: a keepalive request it missed fails here.
    save = sent(page, held)
    page.get_by_role("button", name="Approve sheet").click()
    page.wait_for_timeout(500)
    assert approvals == []
    save.continue_()
    expect(page.locator(".approve-bar")).to_contain_text(APPROVED_BAR)
    assert len(approvals) == 1
    _holds_the_edit(first)


@pytest.mark.spec("ui:save:a-refused-save-is-sent-again-by-the-next-approval")
def test_a_refused_save_is_sent_again_by_the_next_approval(
    page: Page, served: Served, refusals: list[Refused]
) -> None:
    _, second = served.queues["save-holds"]
    refusals.append(Refused(409, "/api/c/save-holds/review/"))
    page.goto(served.review(second, "save-holds"))
    held = hold(page, PUTS)
    _edit(page)
    sent(page, held).fulfill(status=409, json={"refusal": REFUSAL})
    expect(page.locator(".approve-bar")).to_contain_text(REFUSAL)
    page.get_by_role("button", name="Approve sheet").click()
    sent(page, held, 1).continue_()
    expect(page.locator(".approve-bar")).to_contain_text(APPROVED_BAR)
    _holds_the_edit(second)
```

The imports it needs: `Request` from `playwright.sync_api`; `APPROVED_FILE` and `read` from `isekai.foundation.artifacts`; `APPROVED`, `REVIEW`, `Run` and `latest_artifact` from `isekai.foundation.run`; `FLOW` from `tests.e2e.conftest`; `Refused` from `tests.e2e.guard`; `hold` and `sent` from `tests.e2e.held`.

### D8

The build collects the browser tests and runs the gate, as the sandbox has no Chromium. CI runs `make e2e` after the gate on every push, so the first run of each test is the one after the merge. A red run is read at once and fixed by a patch.

### D9

| requirement | scenario added | key | layer |
|---|---|---|---|
| `ui` · *A dialog holds the focus from its first control while it is open* | the key list holds the focus in a browser | `ui:dialogs:the-key-list-holds-the-focus-in-a-browser` | e2e |
| `ui` · *Each command has one key, declared once, and none fires while typing* | a letter typed in a tag field is text | `ui:keys:a-letter-typed-in-a-tag-field-is-text` | e2e |
| the same | the pane keys move the focus in a browser | `ui:keys:the-pane-keys-move-the-focus-in-a-browser` | e2e |
| `ui` · *The page's save state is true to the requests in flight, and a pending edit is sent on leaving* | an approval waits for a save held at the network | `ui:save:an-approval-waits-for-a-save-held-at-the-network` | e2e |
| the same | a refused save is sent again by the next approval | `ui:save:a-refused-save-is-sent-again-by-the-next-approval` | e2e |

The brief leaves their keys unplaced beyond *scenarios added under existing requirements* (Q65); the cut reads each where its requirement already speaks: the dialog requirement names the key list, the keys requirement the field and the panes, the save requirement the approval. The guard of phase 1 is no behaviour of the page, so its twin carries `spec_exempt("structural: …")`. The requirements are restated below the text `0140-the-sheet-and-the-keys` leaves them, which this change's delta carries whole.

## Tests

End-to-end tests and one unit test file are added, none deleted or merged, so no row maps a removal. The tests each file holds at the cut, by `git grep -c -E '^def test_' -- <file>`, and what it gains:

| file | tests at the cut | gains | phase |
|---|---|---|---|
| `tests/test_e2e_guard.py` | none | the guard's rules, one test per fault and one for what it lets by | 1 |
| `tests/e2e/guard.py` | none: no test, the guard's code | `Refused`, `Seen` and `faults` | 1 |
| `tests/e2e/conftest.py` | none: fixtures | the `refusals` and `context` fixtures, and the collections `keys-hold` and `save-holds` | 1, 2, 3 |
| `tests/e2e/test_queue.py` | 3 | its hub test declares its 409; the approval over a held save; the refused save sent again | 1, 3 |
| `tests/e2e/test_routes.py` | 1 | the unknown collection's 409 declared | 1 |
| `tests/e2e/test_keys.py` | none | the keys' journey | 2 |
| `tests/e2e/held.py` | none: no test, the held request's helpers | `hold` and `sent` | 3 |
| `tests/e2e/test_import.py` | 3 | `_sent` moved to `held.py` as `sent`: no assertion changes | 3 |

| layer | added | command |
|---|---|---|
| unit | the guard's tests, in `tests/test_e2e_guard.py` | `git grep -c -E '^def test_' -- tests/test_e2e_guard.py` |
| end-to-end | `test_the_keys_hold_in_a_browser`, and the two of `tests/e2e/test_queue.py` | `git grep -c -E '^def test_' -- tests/e2e` |

The suite's 19 tests at the cut, 18 of them on a page, `git grep -c -E '^def test_' -- tests/e2e` summed, run on Chromium alone: the three added run 3 times, **3 end-to-end runs**, 3 tests × 1 engine. `T4` holds: one engine, as the suite runs one, and each outcome is client behaviour — focus, key events and a held request — that no server-rendered check shows. The guard adds a listener to each of the 18 and no run.

Why a new end-to-end test, each (`T1`, `T2`):

| test | lowest layer that can fail | why none extends |
|---|---|---|
| `test_the_keys_hold_in_a_browser` | the browser: focus order, key events and the dialog's inert page are the browser's | `test_the_photograph_opens_in_the_viewer` ends on a changed viewport, an open list and a saved edit; no other test reaches an editable Review with nothing open |
| the approval over a held save | the browser: whether its request routing sees a `keepalive` PUT is the unverified fact | no test holds a request on Review; a held PUT needs an editable sheet that no earlier test has approved |
| the refused save sent again | the unit test `ui:save:a-lone-failed-save-is-sent-again` holds the logic; the browser holds that the page's own request is the one refused | as above; a second sheet keeps each case alone (`T3`) |

Each new test's commit body says why none fits.

## Dependencies

None.

## Risks / Trade-offs

- **A build cannot run any of this.** Each test is checked by `--collect-only` and the gate alone; CI's run after the merge is the first. A red run is a patch at once (Q63), and each assertion below is chosen so it fails loudly and never falsely green.
- **The guard may refuse a line the suite already logs.** Only the hub's stubbed 409 and the unknown collection's refused reads are known; a console error or a 4xx outside them turns a green test red at CI. That is the guard working, and its fix is a declaration or a patch of the page.
- **`page.route` may not see a `keepalive` request.** Whether it does is unverified at the cut; `sent` raises when it never arrives, so the case fails and says so.
- **The key list's wrap is not pressed.** It holds no control; the Render dialog's step holds the wrap, and a control added to the key list is the moment to extend the journey.
- **The pane keys rest on focusable panes.** `.source` carries `tabindex="0"` and ④ `tabindex="-1"`, so a pane that loses its focus target turns the journey red.

## Verdict

Ready to build. Each phase ends on a green `make gate`; the browser tests are proven by CI after the merge.
