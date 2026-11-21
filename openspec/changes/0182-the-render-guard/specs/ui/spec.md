## MODIFIED Requirements

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

#### Scenario: an approved sheet says a session of another process renders
- **Key:** `ui:review:the-sheet-names-a-session-another-process-holds`
- **Layers:** unit
- **WHEN** Review reads an approved sheet while a render session of another process holds the collection, and the app's render slot is empty
- **THEN** its payload's reason says a render session is running

#### Scenario: a cancel is refused while a session of another process renders
- **Key:** `ui:review:the-cancel-is-refused-while-another-process-renders`
- **Layers:** unit
- **WHEN** *Cancel approve* is posted for an approved sheet while a render session of another process holds the collection, and the app's render slot is empty
- **THEN** the cancel is refused, saying a render session is running
- **AND** the approval stays

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

### Requirement: The large view deletes its render after asking, and the Hub opens on its cell

The system SHALL offer *Delete* on a render's large view, on `⇧⌫`, after *Compare with…*, opening a modal dialog,
*Delete this render?*, whose *No* comes first and holds the focus; `h` `l` and `←` `→` SHALL move between *No* and
*Yes*, `↵` SHALL press the focused one, and `Esc` SHALL answer *No*. *Yes* SHALL delete the render's own thumbnails from
the library's cache, discard the render through the render stage — its approval going with its last render, and a flow
left with no approval keeping only its assignment — and open the Hub focused on the render's cell, from whichever screen
opened the view. The server SHALL refuse the delete while a render session runs for the collection, deleting nothing,
and the dialog SHALL show the refusal.

A failed render is deleted where it is seen. *No* first makes a stray `↵` harmless, and a write beside a running session
is refused, as *Cancel approve* is. The cell is where the delete shows: one image fewer, an older approval's images once
the newest's last image goes, or *tagged* once the flow's last approval goes, with nothing to review. A thumbnail is
told from another collection's of the same photograph and seed by its image's digest, so only the render's own goes.

```
large view ──⇧⌫──▶ Delete this render?  [No] [Yes]
                     │ Esc · No              │ Yes
                     ▼                       ▼
                 large view           thumbnails ─▶ discard ─▶ its approval, if emptied ─▶ the Hub on the cell
```

#### Scenario: the dialog opens on No
- **Key:** `ui:delete-render:the-dialog-opens-on-no`
- **Layers:** e2e
- **WHEN** `⇧⌫` is pressed on a large view, then `l`, `h` and `Esc`
- **THEN** *Delete this render?* opens with *No* focused, `l` focusing *Yes* and `h` *No*
- **AND** `Esc` closes it, the image still shown

#### Scenario: Yes deletes the render and opens the Hub on its cell
- **Key:** `ui:delete-render:yes-opens-the-hub-on-the-cell`
- **Layers:** e2e
- **WHEN** `⇧⌫`, `l` and `↵` are pressed on the large view of a cell's only image, opened at its address
- **THEN** the Hub opens focused on that cell, reading *tagged*
- **AND** the image, its approval's prompt and the flow's sheet are gone from the run

#### Scenario: the Hub opens without the deleted render
- **Key:** `ui:delete-render:the-hub-opens-without-the-deleted-render`
- **Layers:** e2e
- **WHEN** `⇧⌫`, `l` and `↵` are pressed on the large view of a cell's only image
- **THEN** the Hub is read again before it opens, and no thumbnail of the deleted render is asked for

#### Scenario: the route deletes the render and its thumbnail
- **Key:** `ui:delete-render:the-route-deletes-the-render-and-its-thumbnail`
- **Layers:** unit
- **WHEN** a render whose thumbnail is cached is deleted at its address
- **THEN** its image, its record and its thumbnail are gone
- **AND** the other render and its thumbnail stay, and so does another collection's thumbnail of the same photograph
  and seed

#### Scenario: the delete is refused while a render runs
- **Key:** `ui:delete-render:refused-while-a-render-runs`
- **Layers:** unit
- **WHEN** a render is deleted while a render session runs for its collection
- **THEN** the delete is refused, saying a render session is running
- **AND** no file is deleted

#### Scenario: the delete is refused while a session of another process renders
- **Key:** `ui:delete-render:refused-while-another-process-renders`
- **Layers:** unit
- **WHEN** a render is deleted while a render session of another process holds its collection, and the app's render slot is empty
- **THEN** the delete is refused, saying a render session is running
- **AND** no file is deleted, and a session held in another collection refuses nothing

#### Scenario: a reload that lands after leaving moves nothing
- **Key:** `ui:delete-render:a-reload-that-lands-after-leaving-moves-nothing`
- **Layers:** unit
- **WHEN** a render is deleted, the operator leaves the large view, and the Hub's read that followed the deletion ends
- **THEN** the Hub is not opened, whether that read was answered or refused
- **AND** a read that ends while the view stays opens the Hub on the render's cell

#### Scenario: a dismissed dialog still opens the Hub
- **Key:** `ui:delete-render:a-dismissed-dialog-still-opens-the-hub`
- **Layers:** unit
- **WHEN** *Yes* is pressed, the dialog is dismissed before the deletion answers, and the deletion succeeds
- **THEN** the Hub is read again and opens on the render's cell
- **AND** a deletion that is refused opens nothing

