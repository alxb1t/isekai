## MODIFIED Requirements

### Requirement: The page's save state is true to the requests in flight, and a pending edit is sent on leaving

The system SHALL report a draft as saving exactly while a save it started is unanswered, whatever order saves and
input switches answer in, and SHALL send a pending edit when the page leaves the sheet — to another sheet, another
screen, or by closing — by a request the browser keeps alive past the page. A save SHALL wait for the sheet's save in
flight and state the draft it wrote, and a page closing while an edit waits behind a save in flight SHALL ask before
it goes. An approval SHALL wait for a save in flight, and state the draft that save wrote.

The saved receipt is the only thing on the page that speaks about saving, so a counter one stale answer can drive
below zero silences it for the rest of the input. An edit typed inside the debounce is the operator's work, and
closing the tab is an ordinary way to leave. An edit or an approval pressed inside a save's round trip is the
operator's own, not another tab's, and a closing page never reads the receipt it would have to state. A save waiting
behind another carries the whole draft, so a later edit replaces its payload instead of queueing a second request, and
a failed save leaves the draft pending only when no later save of the sheet waits. Of two reads of one sheet in
flight, only the newest SHALL land, so an older read answering late never replaces the operator's edits.

#### Scenario: a stale save cannot clear the saving state
- **Key:** `ui:save:a-stale-save-cannot-clear-saving`
- **Layers:** unit
- **WHEN** an input switch answers before the save it interrupted
- **THEN** the saving state clears only when that save answers
- **AND** the saved receipt returns

#### Scenario: a pending edit is sent on leaving
- **Key:** `ui:save:a-pending-edit-is-sent-on-leaving`
- **Layers:** unit
- **WHEN** the page leaves a sheet inside the debounce
- **THEN** the pending edit is sent with a request kept alive past the page
- **AND** a page closing while an edit waits behind an unanswered save asks before it goes

#### Scenario: an approval waits for a save in flight
- **Key:** `ui:save:an-approval-waits-for-a-save-in-flight`
- **Layers:** unit
- **WHEN** Approve is pressed while a save is unanswered
- **THEN** the approval is sent once that save answers, stating the draft it wrote

#### Scenario: edits inside one slow save are sent as one request
- **Key:** `ui:save:edits-inside-a-slow-save-are-sent-as-one-request`
- **Layers:** unit
- **WHEN** several edits each pause past the debounce while one save is unanswered
- **THEN** one further save is sent once it answers, holding every edit

#### Scenario: a failed save leaves nothing to send again
- **Key:** `ui:save:a-failed-save-leaves-nothing-to-send-again`
- **Layers:** unit
- **WHEN** a save fails while a later save of the sheet waits behind it
- **THEN** the later save holds every edit
- **AND** nothing is sent again once it answers

#### Scenario: a lone failed save is sent again
- **Key:** `ui:save:a-lone-failed-save-is-sent-again`
- **Layers:** unit
- **WHEN** a save fails and no later save of the sheet waits behind it
- **THEN** the edit is pending again
- **AND** the next flush sends it, holding that edit

#### Scenario: a burst of edits is one save
- **Key:** `ui:save:a-burst-of-edits-is-one-save`
- **Layers:** unit
- **WHEN** edits are typed less than the debounce apart
- **THEN** nothing is sent until the debounce has passed since the last
- **AND** one save then holds every edit

#### Scenario: the newest read of a sheet is the one that lands
- **Key:** `ui:save:the-newest-read-of-a-sheet-is-the-one-that-lands`
- **Layers:** unit
- **WHEN** two reads of one sheet are in flight and the older answers first
- **THEN** the sheet stays loading until the newest read answers
- **AND** an edit made after that is saved with the edit in it

#### Scenario: an approval waits for a save held at the network
- **Key:** `ui:save:an-approval-waits-for-a-save-held-at-the-network`
- **Layers:** e2e
- **WHEN** Approve is pressed while the draft's save is held at the network
- **THEN** no approval is sent until the save answers
- **AND** the approval then holds the edit that save wrote

#### Scenario: a refused save is sent again by the next approval
- **Key:** `ui:save:a-refused-save-is-sent-again-by-the-next-approval`
- **Layers:** e2e
- **WHEN** the draft's only save is refused and Approve is pressed
- **THEN** the edit is sent again
- **AND** the approval then holds it

### Requirement: A dialog holds the focus from its first control while it is open

The system SHALL open every confirming dialog — Render, Revise, Delete, and New collection or Add sources — and the key
list as a modal dialog, the page behind it inert, the focus on its first control and held inside it, and SHALL return
the focus to where it was when it closes. The Render dialog's first control SHALL be its first photograph's tile, on
which `↵` does nothing, and `Tab` SHALL move on from the tiles in the dialog's order, past each later collection's tick,
to *Keep the volume open*, which `Space` toggles and `↵` leaves alone; with no tile, the checkbox SHALL be first. The
Revise dialog's first control SHALL be its confirm button, and the Delete dialog's its *No*. The key list SHALL stand
centred over most of the window, its keys in columns by scope — everywhere, then the screen's — and `⌃/`, `Esc` and
the backdrop SHALL close it.

A key goes where the eye is. A dialog over a grid that leaves the focus on the grid sends `↵` and `Tab` to what it
covers. The Render dialog asks first which photographs render, so its first focus is on them, the checkbox one stop
after; only `Mod+↵` spends money, so `↵` on a tile or the checkbox never renders.

#### Scenario: the Render dialog opens on its first photograph
- **Key:** `ui:dialogs:the-render-dialog-opens-on-its-first-photograph`
- **Layers:** e2e
- **WHEN** the Render dialog opens on the hub, then `↵`, then `Tab` until the focus has passed every control
- **THEN** the first photograph's tile held the focus first, `↵` rendered nothing, and the focus never left the dialog
- **AND** `Esc` returns the focus to the hub cell it left

#### Scenario: the key list is a dialog
- **Key:** `ui:dialogs:the-key-list-is-a-dialog`
- **Layers:** unit
- **WHEN** `⌃/` opens the key list on a screen
- **THEN** it is a modal dialog holding the focus, the everywhere keys in one column and the screen's in another
- **AND** `⌃/`, `Esc` and a click on the backdrop each close it

#### Scenario: the key list holds the focus in a browser
- **Key:** `ui:dialogs:the-key-list-holds-the-focus-in-a-browser`
- **Layers:** e2e
- **WHEN** the key list opens on Review, then `Tab` and `⇧Tab` are pressed
- **THEN** the focus never reaches the page behind it
- **AND** `⌃/`, `Esc` and a click on the backdrop each close it, the focus returning to where it was

### Requirement: Each command has one key, declared once, and none fires while typing

The system SHALL declare each keyboard command once, with its key and its label, on the screen or overlay that offers
it, and SHALL draw every key hint and the key list from those declarations, the list opening on `⌃/` on every screen
and on the app bar's `?` button; no screen SHALL carry a key bar. It SHALL match a key by the physical key, whatever
the keyboard layout, and SHALL treat Mod as `⌘` on macOS and `Ctrl` elsewhere. An open overlay SHALL take every key
before the screen beneath it, and the screen before the keys offered everywhere. While focus is in a text field, no
command SHALL fire but `Esc`, `Mod+↵`, `Mod+Z`, `⇧Mod+Z`, `Mod+K`, `⌃/` and `⌃;`, Review's `⌃P`, and on macOS Review's
`⌃H` and `⌃L`, which move between its panes, and `⌃J` and `⌃K`, which move between its fields as `↓` and `↑` do, and
in ④'s seed slots `j` `k` `↓` `↑`, which move between the slots; the field SHALL keep its own editing keys. On a grid,
a move between rows SHALL keep the column it is in, held at a shorter row's end. On the hub and in the session drawer,
a focused button or link SHALL keep `↵` and `Space`. An `Esc` that ends an input method's composition SHALL be the
input method's, closing nothing. `Esc` SHALL close an open suggestion list first, then leave the field, then close the
top overlay, then go back on the screen, and SHALL never close a billing alert. On macOS Review's panes SHALL move by
`⌃H` and `⌃L` alone, from a field or not, and `h` `l` and `←` `→` SHALL move within a pane; elsewhere `h` `l` and `←`
`→` SHALL move between the panes. A plain letter SHALL move the focus, and a command SHALL take `⇧` and a letter, but
for `⌫` on a chosen file, which removes it before anything is committed, and `⇧⌫` on a large view, which asks before
it deletes the render. No key SHALL spend money but the Render dialog's `Mod+↵`, which confirms the price it quotes.

A key typed into a field is text, never a command; a list drawn from the declarations cannot disagree with the keys.
Option is the window manager's on Linux and types characters on macOS, and a layout moves letters but not keys.
On Linux `Ctrl+J` is the browser's and `Ctrl+K` is `Mod+K`, so the field moves are macOS's alone. A shifted letter is
not pressed in passing, so it guards what writes.

```
keydown ─▶ in a text field? ─ yes ─▶ Esc · Mod+↵ · Mod+Z · ⇧Mod+Z · Mod+K · ⌃/ · ⌃;, Review's ⌃P,
               │                     on macOS Review's ⌃H ⌃L ⌃J ⌃K, else the field's own
               │ no
               ▼
           top overlay ─▶ screen ─▶ everywhere        the first that declares the key runs
```

#### Scenario: a key is matched by the physical key
- **Key:** `ui:keys:a-key-is-matched-by-the-physical-key`
- **Layers:** unit
- **WHEN** `⇧H` is pressed on a Cyrillic layout
- **THEN** the command declared for `⇧H` runs

#### Scenario: Mod is Command or Control
- **Key:** `ui:keys:mod-is-command-or-control`
- **Layers:** unit
- **WHEN** a command declared for `Mod+K` is offered
- **THEN** `⌘K` and `Ctrl+K` each run it

#### Scenario: no command fires in a text field
- **Key:** `ui:keys:no-command-fires-in-a-text-field`
- **Layers:** unit
- **WHEN** a declared letter is pressed with focus in a text field
- **THEN** no command runs
- **AND** `Esc`, `Mod+↵`, `Mod+Z` and `Mod+K` still do

#### Scenario: a command waits until the field is left
- **Key:** `ui:keys:a-command-waits-until-the-field-is-left`
- **Layers:** e2e
- **WHEN** `⇧H` is typed into a tag field, then `Esc` and `⇧H` are pressed
- **THEN** the field holds the typed text and Review stays open
- **AND** the second `⇧H` opens the hub

#### Scenario: a focused control keeps Enter and Space
- **Key:** `ui:keys:a-focused-control-keeps-enter-and-space`
- **Layers:** unit
- **WHEN** `↵` or `Space` is pressed on the hub or in the session drawer with focus on a button or a link
- **THEN** the control answers it and the cell's command does not run

#### Scenario: an overlay takes the keys first
- **Key:** `ui:keys:an-overlay-takes-the-keys-first`
- **Layers:** unit
- **WHEN** an overlay and the screen beneath it both declare a key
- **THEN** only the overlay's command runs

#### Scenario: a screen takes the keys before everywhere
- **Key:** `ui:keys:a-screen-takes-the-keys-before-everywhere`
- **Layers:** unit
- **WHEN** a screen and the keys offered everywhere both declare a key
- **THEN** only the screen's command runs

#### Scenario: Esc closes the nearest thing first
- **Key:** `ui:keys:esc-closes-the-nearest-thing-first`
- **Layers:** unit
- **WHEN** `Esc` is pressed with a suggestion list open in a field inside an overlay
- **THEN** the list closes, and the next `Esc` leaves the field, and the next closes the overlay

#### Scenario: the key list and the hints come from the declarations
- **Key:** `ui:keys:hints-come-from-the-declarations`
- **Layers:** unit
- **WHEN** a screen declares its commands
- **THEN** its button hints and the key list name each command's key and label
- **AND** no key bar is drawn

#### Scenario: Review moves between its panes
- **Key:** `ui:keys:review-moves-between-its-panes`
- **Layers:** unit
- **WHEN** on macOS `⌃L` is pressed from the rail three times, then `l` once
- **THEN** focus moves through the source pane and the sheet to ④
- **AND** `l` moves within ④, and no pane changes

#### Scenario: a row move keeps the column
- **Key:** `ui:keys:a-row-move-keeps-the-column`
- **Layers:** unit
- **WHEN** `j` is pressed on the cell modal's third image of a row whose next row holds two
- **THEN** the focus moves to that row's second image

#### Scenario: an Esc that ends a composition closes nothing
- **Key:** `ui:keys:an-esc-ending-a-composition-closes-nothing`
- **Layers:** unit
- **WHEN** `Esc` ends an input method's composition in a field inside an overlay
- **THEN** the field keeps the focus and the overlay stays open

#### Scenario: Review's panes move from a field on macOS
- **Key:** `ui:keys:review-panes-move-from-a-field-on-macos`
- **Layers:** unit
- **WHEN** `⌃L` is pressed with focus in a tag field, on macOS and then on Linux
- **THEN** on macOS the next pane takes the focus, and on Linux nothing moves

#### Scenario: the key list opens from a field
- **Key:** `ui:keys:the-key-list-opens-from-a-field`
- **Layers:** unit
- **WHEN** `?` and then `⌃/` are pressed with focus in a text field
- **THEN** `?` is typed into the field and `⌃/` opens the key list

#### Scenario: Review's fields move from a field on macOS
- **Key:** `ui:keys:review-fields-move-from-a-field-on-macos`
- **Layers:** unit
- **WHEN** Review's commands are declared on macOS and then on Linux
- **THEN** on macOS `⌃J` and `⌃K` move to the next and the previous field from a text field
- **AND** on Linux neither is declared

#### Scenario: a letter typed in a tag field is text
- **Key:** `ui:keys:a-letter-typed-in-a-tag-field-is-text`
- **Layers:** e2e
- **WHEN** `h`, `j`, `k` and `l` are typed into a tag field on Review
- **THEN** the field holds them and no pane moves
- **AND** `Esc` closes a suggestion list first, then leaves the field

#### Scenario: the pane keys move the focus in a browser
- **Key:** `ui:keys:the-pane-keys-move-the-focus-in-a-browser`
- **Layers:** e2e
- **WHEN** the pane key — `⌃L` on macOS, `l` outside a field elsewhere — is pressed from the rail three times
- **THEN** the focus moves to the source pane, the sheet and ④
- **AND** the key for the other way returns it to the sheet
