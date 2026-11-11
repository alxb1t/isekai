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
a failed save leaves the draft pending only when no later save of the sheet waits.

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

### Requirement: The hub shows each source's stage in each offered flow, and a tick assigns it

The system SHALL show a collection's hub as a grid of its sources by the flows the surface offers, each cell carrying
the stage read from that run's directory — no flow, assigned, tagged, sheet, draft, approved or rendered — and SHALL
ignore any other flow's directory. A cell whose run file cannot be read SHALL show that it is unreadable, with the
refusal the pipeline raised, and the rest of the grid SHALL still be shown. Reading the hub SHALL write nothing; a tick
SHALL write only through the assigning verb, and an untick, by the tick or by Discard, only while the cell is assigned
or tagged, the verb refusing a flow directory that holds work. A source imported as it is, still carrying metadata,
SHALL be marked on its row. Each source SHALL show its name and its thumbnail, and its row SHALL carry the size read
from its own file, with or without a run, which the viewer's title names. A source's thumbnail and a cell's images SHALL
sit at the foot of their cells, level across the row, whatever text stands above them; a cell's refusal SHALL stand
above its images, and `↵ view photo` SHALL take no line of the source's cell. A cell SHALL name its newest image — the
newest version holding images, then its last-written image — and a click or `↵` SHALL follow the cell's stage: tick
while unassigned, assigned or tagged, open Review on a sheet or a draft, open the sheet read-only on an approval with no
image, and open the cell modal on the cell's newest image where it holds any; an unreadable cell SHALL do nothing. The
cell modal SHALL show every image of the cell as one grid, versions oldest first, each version's seeds in numeric
order, at most three to a row, its rows balanced — ⌈n/3⌉ rows of ⌈n/rows⌉ images, the last row holding the rest — each
image badged with its version, as on the hub, and captioned with its seed, marked `⇄` when that seed was rendered
under another version too. Up to three rows SHALL show whole, each image at twice a thumbnail's size or scaled down to
fit the window, and more rows SHALL scroll. The arrows and `h j k l` SHALL move it, a move between rows keeping the
column, held at a shorter row's last image, `l` at a row's end going on to the next row's first and `h` at a row's
start back to the previous row's last; `↵` or a click SHALL open the focused image's large view, and `Esc` SHALL close
it. A cell holding images SHALL show every one of them in that order, each marked with its version, a click on one
opening the cell modal on it, and last, while its newest approval lacks images of its count, a tile naming the number it
lacks, as the render stage counts it. A source's cell SHALL be the grid's first column, reached by `h` and `←`, and `↵`
there SHALL open its photograph in the viewer, stepping through the collection's sources. The hub SHALL keep its focus
across the Back button and a switch of tabs, a restored focus scrolled to the window's centre. A key's move to the first
row SHALL scroll the hub to its top, to the last row to its foot, and to any other row only as far as the row needs. The
header SHALL leave a 12 px gap between items. An assigned cell SHALL read tagged from the photograph's tag list, so a
photograph tagged once is tagged in every flow it is assigned to.

A stage is a directory listing, the rule every stage already follows, so the grid cannot drift from the disk, and a tick
survives a reload. A tagged cell holds no sheet: its tag list is the photograph's, so its untick deletes no work, and
the verb's refusal of a directory holding files is the guard. The mark and the size are read from the source itself, so
no file records them. An approved cell can hold an older version's images, so its newest image is named by the server
rather than guessed by the page. A row's pictures share a foot, so a long name, a mark or a refusal moves only the text
above them. *Add sources…* and the flow names sit above the first row, so a move there shows them. The cell modal
shows a cell's renders together, as large as the window lets them be, in the order every screen walks, so a render
keeps its place from the cell to the large view; balanced rows of at most three keep a cell's few renders one set. The
pending count is the render stage's own.

#### Scenario: a cell's stage comes from its run's directory
- **Key:** `ui:hub:a-cells-stage-comes-from-its-run`
- **Layers:** unit
- **WHEN** a run holds a flow's approved sheet and no render
- **THEN** that cell's stage is approved

#### Scenario: a flow the surface does not offer is ignored
- **Key:** `ui:hub:an-untracked-flow-is-ignored`
- **Layers:** unit
- **WHEN** a run holds a directory for a flow the surface does not offer
- **THEN** the hub shows no column and no refusal for it

#### Scenario: an unreadable run file marks its cell alone
- **Key:** `ui:hub:an-unreadable-file-marks-its-cell`
- **Layers:** unit
- **WHEN** one cell's run file cannot be read
- **THEN** that cell is unreadable, with the pipeline's refusal
- **AND** every other cell shows its stage

#### Scenario: the hub writes nothing
- **Key:** `ui:hub:the-hub-writes-nothing`
- **Layers:** unit
- **WHEN** a collection's hub is read
- **THEN** no file in the collection is created, changed or removed

#### Scenario: a tick assigns the flow
- **Key:** `ui:hub:a-tick-assigns-the-flow`
- **Layers:** e2e
- **WHEN** an unassigned cell is ticked
- **THEN** the cell reads assigned
- **AND** it still reads assigned after a reload
- **AND** the header keeps a 12 px gap between its items

#### Scenario: a prepared cell's tick stays
- **Key:** `ui:hub:a-prepared-tick-stays`
- **Layers:** unit
- **WHEN** an untick is asked for a cell whose flow directory holds work
- **THEN** it is refused and no file changes

#### Scenario: a tagged cell with no work unticks
- **Key:** `ui:hub:a-tagged-cell-with-no-work-unticks`
- **Layers:** unit
- **WHEN** a tagged cell whose flow directory is empty is unticked, by its tick or by Discard
- **THEN** its flow directory is removed and the cell reads no flow
- **AND** the photograph's tag list stays

#### Scenario: a source imported as it is is marked
- **Key:** `ui:hub:an-uncleaned-source-is-marked`
- **Layers:** unit
- **WHEN** a source still carries metadata
- **THEN** its row is marked not cleaned

#### Scenario: a source is sized from its file
- **Key:** `ui:hub:a-source-is-sized-from-its-file`
- **Layers:** unit
- **WHEN** the hub is read for a source that has no run
- **THEN** its row carries the width and height of its file

#### Scenario: a cell names its newest image
- **Key:** `ui:hub:a-cell-names-its-newest-image`
- **Layers:** unit
- **WHEN** an approved cell holds images only under an older version
- **THEN** it names that version and its last-written image

#### Scenario: a click follows the cell's stage
- **Key:** `ui:hub:a-click-follows-the-cells-stage`
- **Layers:** unit
- **WHEN** a cell is clicked at each stage
- **THEN** it ticks up to tagged, opens Review on a sheet, a draft or an unrendered approval, and opens the cell modal
- **AND** an unreadable cell does nothing

#### Scenario: a rendered cell opens its newest image
- **Key:** `ui:hub:a-rendered-cell-opens-its-newest-image`
- **Layers:** e2e
- **WHEN** a rendered cell is clicked, then `↵` is pressed in the cell modal
- **THEN** the cell modal opens on its newest image, then that image's large view
- **AND** `Esc` returns to the hub, focused on that cell, and that cell in view

#### Scenario: a cell lists its images
- **Key:** `ui:hub:a-cell-lists-its-images`
- **Layers:** unit
- **WHEN** a cell holds images under two versions
- **THEN** the hub carries them oldest to newest, each with its version and seed

#### Scenario: the cell modal moves by version and seed
- **Key:** `ui:hub:the-cell-modal-moves-by-version-and-seed`
- **Layers:** unit
- **WHEN** the cell modal opens on an image of a cell holding seeds 9 then 2 under v1, and seeds 4, 6 and 8 under v2
- **THEN** its rows hold v1 seed 2, v1 seed 9 and v2 seed 4, then v2 seeds 6 and 8, as the cell's thumbnails stand,
  the focus on that image
- **AND** `l` at a row's end moves to the next row's first image, `h` back, and `j` onto a missing image lands on the
  last

#### Scenario: the cell modal balances its rows
- **Key:** `ui:hub:the-cell-modal-balances-its-rows`
- **Layers:** unit
- **WHEN** the cell modal opens on cells holding one to ten images
- **THEN** its rows hold 1; 2; 3; 2 and 2; 3 and 2; 3 and 3; 3, 3 and 1; 3, 3 and 2; 3, 3 and 3; and 3, 3, 3 and 1

#### Scenario: a seed under two versions is marked
- **Key:** `ui:hub:a-seed-under-two-versions-is-marked`
- **Layers:** unit
- **WHEN** a cell holds seed 7 under v1 and v2, and seed 5 under v2 alone
- **THEN** the cell modal marks seed 7 `⇄` and leaves seed 5 unmarked

#### Scenario: a thumbnail opens the cell modal on it
- **Key:** `ui:hub:a-thumbnail-opens-the-cell-modal-on-it`
- **Layers:** e2e
- **WHEN** a cell's older thumbnail is clicked
- **THEN** the cell modal opens focused on that image, its tiles in one row at twice a thumbnail's width, each badged
  with its version
- **AND** each tile of a seed rendered under both versions is marked `⇄`
- **AND** in a window too short for that, its tiles shrink to fit and the grid does not scroll

#### Scenario: a cell of ten renders scrolls its grid
- **Key:** `ui:hub:a-cell-of-ten-renders-scrolls-its-grid`
- **Layers:** e2e
- **WHEN** the cell modal opens on a cell of ten renders in a 1280×768 window
- **THEN** its four rows keep their height, and none scrolls on its own
- **AND** the grid scrolls to the fourth row

#### Scenario: a cell shows what is ready
- **Key:** `ui:hub:a-cell-shows-what-is-ready`
- **Layers:** unit
- **WHEN** a cell's newest approval lacks two images of its count
- **THEN** the cell's last tile reads `ready · 2 images`
- **AND** a cell lacking none, or unapproved, draws no such tile

#### Scenario: the hub keeps its focus
- **Key:** `ui:hub:the-hub-keeps-its-focus`
- **Layers:** unit
- **WHEN** a collection's hub focus is moved, then its hub is opened again
- **THEN** the focus is where it was left, or on the first spot when that one is gone
- **AND** another collection's hub starts from the first spot

#### Scenario: the source cell opens its photograph
- **Key:** `ui:hub:the-source-cell-opens-its-photograph`
- **Layers:** e2e
- **WHEN** `h` is pressed on a row's first flow cell, then `↵`
- **THEN** the row's photograph opens in the viewer
- **AND** while the source cell holds the focus, its thumbnail's foot is level with the row's images' foot

#### Scenario: a key's move to an edge row shows the hub's head
- **Key:** `ui:hub:an-edge-row-shows-the-head`
- **Layers:** e2e
- **WHEN** in a window shorter than the grid, `j` moves the focus to the last row, then `k` back to the first
- **THEN** Add sources… is out of view on the last row
- **AND** it is in view again on the first

#### Scenario: a photograph tagged once is tagged in every flow
- **Key:** `ui:hub:a-tagged-photograph-is-tagged-in-every-flow`
- **Layers:** unit
- **WHEN** a photograph's tag list is written and two flows are assigned to it, neither with a sheet
- **THEN** both cells read tagged

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

