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

### Requirement: Review opens a collection at its own address, lists every unrendered sheet, and Approve stays on the sheet

The system SHALL open a collection's Review on a chooser when two or more flows hold sheets to review: a row per flow,
its name, how many wait to be approved and how many lack images, and up to fifteen of its waiting photographs, then
`+n`; `j` `k` and the arrows SHALL move between rows, `↵` or a click on a row SHALL open that flow's head, and a click
on a photograph that sheet. With one such flow it SHALL open that flow's head: its first unapproved sheet in the hub's
order, else its first approved sheet whose newest approval lacks images of its count, read-only; with none, a page
saying no sheet waits for review, with the way to the hub. `Esc` on Review, with no overlay open and outside a field,
SHALL return to the chooser. The hub SHALL carry for each cell the number of images its newest approval lacks, as the
render stage counts it. Review's rail SHALL list every sheet of the flow that is unapproved or lacks images, each
marked untouched, edited, approved or re-opened, and its footer SHALL count the approved among them; the Review tab
SHALL count the unapproved, every flow's, and the rail's head SHALL name each other flow holding some, with how many
and the key to the chooser. Approve SHALL leave the sheet open and read-only, the approve bar naming the approval it
shows, offering *Cancel approve* while the review stage can cancel it, else the reason beside it, and while no render
runs for the collection; a cancel SHALL leave the sheet open on what the flow is left on: its draft, editable, or for
a copy the draft open above what lies beneath, else the approval beneath it, read-only. Opening a sheet that has no
draft SHALL write one through the review stage's own function, and opening it again SHALL write no second draft; a
failure after approval SHALL be shown in the approve bar, never dropped. ④ SHALL show one slot per image, a set seed
or random, beside the sheet rows; its count's `−` and `+` and its slots SHALL be one grid for the keys, `−` `+` a row
and each slot a row below, and a control that disables SHALL pass its focus to the nearest enabled one in its row.
`⇧J` and `⇧K` SHALL step the rail's sheets, the focused one scrolled into view, centred. `⌃P` SHALL open the
photograph in the viewer — on a revision or a draft from an image, *Side by side* — from any pane and from a field,
stepping through the rail's sheets, and `Esc` SHALL return the focus where it was.

A sheet is done when its images are, not when it is approved, so the rail keeps it until then; the count is the
render stage's own. Approving is an act, not a navigation, and a copy's cancel takes back only the copy. A slot per
image says what the next render draws before it is approved. The operator chooses the flow to review; the page
does not choose it for them.

```
two or more flows waiting ─▶ the chooser ─↵─▶ that flow's head
one flow waiting          ─▶ its head: first unapproved ─▶ else first approved and short
none                      ─▶ "No sheet waits for review"
```

#### Scenario: a collection's Review opens its head
- **Key:** `ui:review:a-batch-opens-its-head`
- **Layers:** unit
- **WHEN** a collection's one flow holds an approved, short sheet and an unapproved one, then neither
- **THEN** its Review opens the unapproved sheet, then the approved one
- **AND** with no sheet left it opens none

#### Scenario: two flows waiting open the chooser
- **Key:** `ui:review:two-flows-waiting-open-the-chooser`
- **Layers:** unit
- **WHEN** a collection's two flows each hold an unapproved sheet
- **THEN** its Review is a row per flow, each naming its count and its waiting photographs

#### Scenario: the chooser opens a flow
- **Key:** `ui:review:the-chooser-opens-a-flow`
- **Layers:** e2e
- **WHEN** the Review tab opens on two waiting flows, `j` then `↵` are pressed
- **THEN** Review opens on the second flow's first waiting sheet
- **AND** `Esc` returns to the chooser, its second row focused

#### Scenario: a cell counts what its newest approval lacks
- **Key:** `ui:review:a-cell-counts-what-it-lacks`
- **Layers:** unit
- **WHEN** a cell's newest approval holds one image of a count of three
- **THEN** the hub carries two for that cell

#### Scenario: the rail holds every sheet not yet rendered
- **Key:** `ui:review:the-rail-holds-every-unrendered-sheet`
- **Layers:** unit
- **WHEN** a flow holds an unapproved sheet, an approved short one and an approved one with all its images
- **THEN** the rail lists the first two, marked by their state

#### Scenario: Approve stays on the sheet
- **Key:** `ui:review:approve-stays-on-the-sheet`
- **Layers:** e2e
- **WHEN** a sheet is approved
- **THEN** the same sheet stays open, read-only, and its rail mark reads approved
- **AND** the approve bar names its approval

#### Scenario: opening a sheet with no draft writes one
- **Key:** `ui:review:opening-a-sheet-writes-its-draft`
- **Layers:** unit
- **WHEN** Review opens a sheet whose flow has a sheet and no draft
- **THEN** a draft is written through the review stage
- **AND** opening it again writes no second draft

#### Scenario: a failure after approval is shown
- **Key:** `ui:review:a-failure-after-approval-is-shown`
- **Layers:** e2e
- **WHEN** an approval succeeds and reading the collection again fails
- **THEN** the approve bar shows the refusal

#### Scenario: a refused save is shown in the approve bar
- **Key:** `ui:review:a-refused-save-is-shown`
- **Layers:** unit
- **WHEN** a save of the open sheet is refused
- **THEN** the sheet holds the refusal's words, which the approve bar shows
- **AND** the next save that lands clears them

#### Scenario: a sheet that cannot be read says so
- **Key:** `ui:review:a-sheet-that-cannot-be-read-says-so`
- **Layers:** unit
- **WHEN** Review reads a sheet and the read fails
- **THEN** the sheet holds the refusal's words and stops loading
- **AND** no sheet is shown in its place

#### Scenario: each image has a slot
- **Key:** `ui:review:each-image-has-a-slot`
- **Layers:** unit
- **WHEN** a draft renders four images with seed 144 listed
- **THEN** ④ shows four slots, the first holding 144 and three random
- **AND** removing a slot takes a random one first

#### Scenario: the photograph opens in the viewer
- **Key:** `ui:review:the-photograph-opens-in-the-viewer`
- **Layers:** e2e
- **WHEN** `⌃P` is pressed in a tag field, then `→`
- **THEN** the viewer shows the photograph fitted, then the next sheet's photograph
- **AND** `Esc` returns the focus to the field

#### Scenario: Cancel approve opens the sheet again
- **Key:** `ui:review:cancel-approve-opens-the-sheet-again`
- **Layers:** e2e
- **WHEN** a sheet is approved, then *Cancel approve* is pressed
- **THEN** the same sheet is editable again

#### Scenario: an approved sheet says why it cannot be cancelled
- **Key:** `ui:review:the-sheet-says-why-it-cannot-be-cancelled`
- **Layers:** unit
- **WHEN** Review reads an approved sheet whose prompt is assembled
- **THEN** its payload carries the review stage's reason

#### Scenario: Cancel approve follows the render
- **Key:** `ui:review:the-cancel-follows-the-render`
- **Layers:** unit
- **WHEN** a render running for the collection starts or ends while an approved sheet is open
- **THEN** Review reads the sheet again, so *Cancel approve* follows the render
- **AND** a render that starts or ends beside a sheet that is not approved leaves it unread

#### Scenario: a render that moves during the read is read again once it lands
- **Key:** `ui:review:a-render-that-moves-during-the-read-is-read-again`
- **Layers:** unit
- **WHEN** a render running for the collection starts or ends while the sheet is read, and the sheet lands approved
- **THEN** Review reads the sheet once more when the read lands, so *Cancel approve* follows the render
- **AND** a sheet that lands editable is not read again

#### Scenario: the rail names the other flows' waiting sheets
- **Key:** `ui:review:the-rail-names-the-other-flows-waiting`
- **Layers:** unit
- **WHEN** Review is open on one flow and another flow holds one unapproved sheet
- **THEN** the rail's head names that flow and one waiting

#### Scenario: ④ is one grid for the keys
- **Key:** `ui:review:four-is-one-grid-for-the-keys`
- **Layers:** unit
- **WHEN** on macOS `l` is pressed on `−`, then `j` twice, then `k` twice, and `−` is pressed down to one image
- **THEN** the focus moves to `+`, to the first slot, the second, and back to `+`
- **AND** once `−` disables, the focus is on `+`

#### Scenario: a stepped sheet stays in view
- **Key:** `ui:review:a-stepped-sheet-stays-in-view`
- **Layers:** unit
- **WHEN** `⇧J` steps the rail past its visible end
- **THEN** the focused sheet is scrolled into view, centred

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

