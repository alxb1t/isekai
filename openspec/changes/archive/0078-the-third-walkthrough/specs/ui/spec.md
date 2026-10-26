## MODIFIED Requirements

### Requirement: A folder in the library is a batch when it holds `sources/`

The system SHALL list as a batch every folder in the library that holds `sources/`, SHALL list any other folder as
not a batch and open none of it, and SHALL list no dot-folder. Each batch's row SHALL carry its name, its source
count, the names of its first fifteen sources, whose thumbnails it shows, for each flow the surface offers that is
present the counts approved and rendered out of the sources that have that flow, the count of sources with no flow,
and the time and kind of the newest file written in it. Batches SHALL be ordered by that time, newest first, and
folders that are not batches after them. Home SHALL carry New batch at the right of the library's header row, and on
an empty library below the privacy line. Count labels on the surface SHALL use a singular noun at one and a plural
noun otherwise.

A folder is a batch by its layout alone, so no marker file can disagree with what is on disk, and the row is a
listing read on every request. A folder that is not a batch is shown rather than hidden so the screen matches the
folder, and nothing in the app writes into it. The flows the surface offers are named in its configuration; a flow
approved from another's sheet stays the CLI's. On first start the privacy line is read before the first import.

#### Scenario: a folder with `sources/` is a batch
- **Key:** `ui:batch-folder:a-folder-with-sources-is-a-batch`
- **Layers:** unit
- **WHEN** the library holds a folder with `sources/` and one without
- **THEN** the first is listed as a batch
- **AND** the second is listed as not a batch, and cannot be opened

#### Scenario: a dot-folder is not listed
- **Key:** `ui:batch-folder:a-dot-folder-is-not-listed`
- **Layers:** unit
- **WHEN** the library holds a folder whose name starts with a dot
- **THEN** it is not listed at all

#### Scenario: a flow's counts are of the sources that have it
- **Key:** `ui:batch-folder:a-flows-counts-are-of-its-sources`
- **Layers:** unit
- **WHEN** a batch's sources have different sets of flows
- **THEN** each flow's approved and rendered counts are out of the sources whose runs hold that flow
- **AND** the sources with no flow are counted apart

#### Scenario: batches are ordered by their newest file
- **Key:** `ui:batch-folder:batches-are-ordered-by-their-newest-file`
- **Layers:** unit
- **WHEN** the library holds batches written at different times
- **THEN** they are listed newest first, by the newest file written in each

#### Scenario: no file records a batch
- **Key:** `ui:batch-folder:no-file-records-a-batch`
- **Layers:** unit
- **WHEN** the surface lists the library and opens a batch
- **THEN** no file describing a batch is created anywhere in the library

#### Scenario: a flow the surface does not offer has no count
- **Key:** `ui:batch-folder:an-unoffered-flow-has-no-count`
- **Layers:** unit
- **WHEN** a batch's runs hold a tracked flow the configuration does not offer
- **THEN** its row carries no count for that flow

#### Scenario: count labels use singular at one
- **Key:** `ui:batch-folder:count-labels-use-singular-at-one`
- **Layers:** unit
- **WHEN** a count label is drawn for zero, one and several items
- **THEN** one uses the singular noun and the other counts use the plural noun

#### Scenario: a row names its first sources
- **Key:** `ui:batch-folder:a-row-names-its-first-sources`
- **Layers:** unit
- **WHEN** a batch holds seventeen sources
- **THEN** its row names the first fifteen in the hub's order
- **AND** its source count is seventeen

#### Scenario: first start shows New batch under the privacy line
- **Key:** `ui:batch-folder:first-start-shows-new-batch-under-the-privacy-line`
- **Layers:** e2e
- **WHEN** Home opens on an empty library
- **THEN** New batch sits below the privacy line

### Requirement: The hub shows each source's stage in each offered flow, and a tick assigns it

The system SHALL show a batch's hub as a grid of its sources by the flows the surface offers, each cell carrying the
stage read from that run's directory — no flow, assigned, tagged, sheet, draft, approved or rendered — and SHALL ignore
any other flow's directory. A cell whose run file cannot be read SHALL show that it is unreadable, with the refusal the
pipeline raised, and the rest of the grid SHALL still be shown. Reading the hub SHALL write nothing; a tick SHALL write
only through the assigning verb, and an untick only while the cell is assigned. A source imported as it is, still
carrying metadata, SHALL be marked on its row. Each source SHALL show its name and its thumbnail, and its row SHALL
carry the size read from its own file, with or without a run, which the viewer's title names. A source's thumbnail and a
cell's images SHALL sit at the foot of their cells, level across the row, whatever text stands above them; a cell's
refusal SHALL stand above its images, and `↵ view photo` SHALL take no line of the source's cell. A cell SHALL name its
newest image — the newest version holding images, then its last-written image — and a click or `↵` SHALL follow the
cell's stage: tick while unassigned or assigned, open Review on a sheet or a draft, open the sheet read-only on an
approval with no image, and open the viewer on the newest of the cell's images where it holds any, stepping through
them, `↵` opening an image's large view; a tagged or unreadable cell SHALL do nothing. A cell holding images SHALL show
every one of them, oldest to newest, each marked with its version. A source's cell SHALL be the grid's first column,
reached by `h` and `←`, and `↵` there SHALL open its photograph in the viewer, stepping through the batch's sources. The
hub SHALL keep its focus across a large view, the Back button and a switch of tabs. The header SHALL leave a 12 px gap
between items.

A stage is a directory listing, the rule every stage already follows, so the grid cannot drift from the disk, and a tick
survives a reload. The mark and the size are read from the source itself, so no file records them. An approved cell can
hold an older version's images, so its newest image is named by the server rather than guessed by the page. A row's
pictures share a foot, so a long name, a mark or a refusal moves only the text above them.

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
- **WHEN** a batch's hub is read
- **THEN** no file in the batch is created, changed or removed

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
- **WHEN** an untick is asked for a cell past assigned
- **THEN** it is refused and no file changes

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
- **THEN** it ticks up to assigned, opens Review on a sheet, a draft or an unrendered approval, and opens an image
- **AND** a tagged or an unreadable cell does nothing

#### Scenario: a rendered cell opens its newest image
- **Key:** `ui:hub:a-rendered-cell-opens-its-newest-image`
- **Layers:** e2e
- **WHEN** a rendered cell is clicked, then `↵` is pressed in the viewer
- **THEN** the viewer opens on its newest image, then that image's large view
- **AND** `Esc` returns to the hub, focused on that cell

#### Scenario: a cell lists its images
- **Key:** `ui:hub:a-cell-lists-its-images`
- **Layers:** unit
- **WHEN** a cell holds images under two versions
- **THEN** the hub carries them oldest to newest, each with its version and seed

#### Scenario: the source cell opens its photograph
- **Key:** `ui:hub:the-source-cell-opens-its-photograph`
- **Layers:** e2e
- **WHEN** `h` is pressed on a row's first flow cell, then `↵`
- **THEN** the row's photograph opens in the viewer
- **AND** while the source cell holds the focus, its thumbnail's foot is level with the row's images' foot

### Requirement: A version says what it was, and Compare shows a seed's two versions

The system SHALL head each image's large view with its approval version, the version it came from, read from its
producer, naming it a revision when its fields differ from that version's and a re-roll when only its count or seeds do,
and the approval's time, count and seeds. A large view whose seed is rendered under an older version of the same source
and flow SHALL offer Compare with the newest such version first, and every large view SHALL offer *Compare with…* any
other image of its source and flow, picked in a dialog of those images as tiles, each named by its version and seed, or
compared at once where the cell holds one other, saying so when the two seeds differ or the two share a sheet, showing
both images at equal size, the older of the two before, the fields that changed, what changed in the count and seeds,
and the tokens before and after. Every large view SHALL offer *Side by side*, the image beside its run's photograph at
equal height.

The origin is already on disk, so nothing new records it. Same seed, same composition: the difference left is the edit.
A pick reads as a choice when every choice is in view. The grid carries the images; the large view, which carries the
sheet, carries what the version was.

#### Scenario: a version is named a revision or a re-roll
- **Key:** `ui:compare:a-version-is-named-by-what-changed`
- **Layers:** unit
- **WHEN** one version changes a field of the version it came from and another changes only its seeds
- **THEN** the first's large view is headed a revision and the second's a re-roll

#### Scenario: Compare pairs a seed with its newest older version
- **Key:** `ui:compare:a-seed-pairs-with-its-newest-older-version`
- **Layers:** unit
- **WHEN** a seed is rendered under versions one, two and three
- **THEN** version three's large view compares with version two

#### Scenario: Compare shows the pair and the changed fields
- **Key:** `ui:compare:compare-shows-the-pair-and-the-change`
- **Layers:** e2e
- **WHEN** Compare is opened on a revised image
- **THEN** both images and the changed fields are shown
- **AND** a pick of another seed's image compares it, saying the seeds differ

#### Scenario: Side by side sets the image beside its photograph
- **Key:** `ui:compare:side-by-side-sets-the-image-beside-its-photograph`
- **Layers:** e2e
- **WHEN** *Side by side* is opened on an image's large view
- **THEN** one dialog shows the run's photograph and the image at equal height

#### Scenario: Compare takes any two images of a cell
- **Key:** `ui:compare:any-two-images-of-a-cell`
- **Layers:** unit
- **WHEN** Compare is asked for an image of v4 against an image of v2 with another seed
- **THEN** it serves both, the changed fields and that the seeds differ
- **AND** v2 is before, whichever of the two is named

#### Scenario: one other image is compared at once
- **Key:** `ui:compare:one-other-image-is-compared-at-once`
- **Layers:** unit
- **WHEN** *Compare with…* is asked on an image whose cell holds one other image, then three
- **THEN** the first compares with that image at once
- **AND** the second opens the pick, on the newest older version of its seed

### Requirement: Every command has one key, declared once, and none fires while typing

The system SHALL declare each keyboard command once, with its key and its label, on the screen or overlay that offers
it, and SHALL draw every key hint and the key list from those declarations, the list opening on `⌃/` on every screen and
on the app bar's `?` button; no screen SHALL carry a key bar. It SHALL match a key by the physical key, whatever the
keyboard layout, and SHALL treat Mod as `⌘` on macOS and `Ctrl` elsewhere. An open overlay SHALL take every key before
the screen beneath it, and the screen before the keys offered everywhere. While focus is in a text field, no command
SHALL fire but `Esc`, `Mod+↵`, `Mod+Z`, `⇧Mod+Z`, `Mod+K` and `⌃/`, Review's `⌃P`, and on macOS Review's `⌃H` and `⌃L`,
which move between its panes, and `⌃J` and `⌃K`, which move between its fields as `↓` and `↑` do; the field SHALL keep
its own editing keys. On a grid, a move between rows SHALL keep the column it is in, held at a shorter row's end. On the
hub and on a session's page, a focused button or link SHALL keep `↵` and `Space`. An `Esc` that ends an input method's
composition SHALL be the input method's, closing nothing. `Esc` SHALL close an open suggestion list first, then leave
the field, then close the top overlay, then go back on the screen, and SHALL never close a billing alert. On the large
view and on Renders a command that writes SHALL take a shifted letter and one that only looks a plain one. No key SHALL
spend money but the Render dialog's `Mod+↵`, which confirms the price it quotes.

A key typed into a field is text, never a command; a list drawn from the declarations cannot disagree with the keys.
Option is the window manager's on Linux and types characters on macOS, and a layout moves letters but not keys.
On Linux `Ctrl+J` is the browser's and `Ctrl+K` is `Mod+K`, so the field moves are macOS's alone. A shifted letter is
not pressed in passing, so it guards what writes.

```
keydown ─▶ in a text field? ─ yes ─▶ Esc · Mod+↵ · Mod+Z · ⇧Mod+Z · Mod+K · ⌃/, Review's ⌃P,
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
- **WHEN** `↵` or `Space` is pressed on the hub or a session's page with focus on a button or a link
- **THEN** the control answers it and the cell's command does not run

#### Scenario: an overlay takes the keys first
- **Key:** `ui:keys:an-overlay-takes-the-keys-first`
- **Layers:** unit
- **WHEN** an overlay and the screen beneath it both declare a key
- **THEN** only the overlay's command runs

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

#### Scenario: Renders moves by cell and by image
- **Key:** `ui:keys:renders-moves-by-cell-and-by-image`
- **Layers:** unit
- **WHEN** `l` and then `→` are pressed on a cell's last image of the Renders grid
- **THEN** each moves to the next image, crossing into the next cell, and `h` at a row's start reaches its source

#### Scenario: Review moves between its panes
- **Key:** `ui:keys:review-moves-between-its-panes`
- **Layers:** unit
- **WHEN** `l` is pressed from the rail three times
- **THEN** focus moves through the source pane and the sheet to ④

#### Scenario: a row move keeps the column
- **Key:** `ui:keys:a-row-move-keeps-the-column`
- **Layers:** unit
- **WHEN** `j` is pressed on the Renders grid's third image of a row whose next row holds two
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
- **WHEN** `⌃/` and then `?` are pressed with focus in a text field
- **THEN** `⌃/` opens the key list and `?` is typed into the field

#### Scenario: Review's fields move from a field on macOS
- **Key:** `ui:keys:review-fields-move-from-a-field-on-macos`
- **Layers:** unit
- **WHEN** Review's commands are declared on macOS and then on Linux
- **THEN** on macOS `⌃J` and `⌃K` move to the next and the previous field from a text field
- **AND** on Linux neither is declared

### Requirement: Review opens a batch at its own address, lists every unrendered sheet, and Approve stays on the sheet

The system SHALL open a batch's Review on a chooser when two or more flows hold sheets to review: a row per flow, its
name, how many wait to be approved and how many lack images, and up to fifteen of its waiting photographs, then `+n`;
`j` `k` and the arrows SHALL move between rows, `↵` or a click on a row SHALL open that flow's head, and a click on a
photograph that sheet. With one such flow it SHALL open that flow's head: its first unapproved sheet in the hub's order,
else its first approved sheet whose newest approval lacks images of its count, read-only; with none, a page saying no
sheet waits for review, with the way to the hub. `Esc` on Review, with no overlay open and outside a field, SHALL return
to the chooser. The hub SHALL carry for each cell the number of images its newest approval lacks, as the render stage
counts it. Review's rail SHALL list every sheet of the flow that is unapproved or lacks images, each marked untouched,
edited, approved or re-opened, and its footer SHALL count the approved among them; the Review tab SHALL count the
unapproved, every flow's, and the rail's head SHALL name each other flow holding some, with how many and the key to the
chooser. Approve SHALL leave the sheet open and read-only, the approve bar naming the approval it shows, offering
*Cancel approve* while the review stage can cancel it, else the reason beside it, and while no render runs for the
batch; a cancel SHALL leave the sheet open on what the flow is left on: its draft, editable, or for a copy the draft
open above what lies beneath, else the approval beneath it, read-only. Opening a sheet that has no draft SHALL write one
through the review stage's own function, and opening it again SHALL write no second draft; a failure after approval
SHALL be shown in the approve bar, never dropped. ④ SHALL show one slot per image, a set seed or random, beside the
sheet rows. `⌃P` SHALL open the photograph in the viewer — on a revision, *Side by side* — from any pane and from a
field, stepping through the rail's sheets, and `Esc` SHALL return the focus where it was.

A sheet is done when its images are, not when it is approved, so the rail keeps it until then; the count is the
render stage's own. Approving is an act, not a navigation, and a copy's cancel takes back only the copy. A slot per
image says what the next render draws before it is approved. The operator chooses the flow to review; the page
does not choose it for them.

```
two or more flows waiting ─▶ the chooser ─↵─▶ that flow's head
one flow waiting          ─▶ its head: first unapproved ─▶ else first approved and short
none                      ─▶ "No sheet waits for review"
```

#### Scenario: a batch's Review opens its head
- **Key:** `ui:review:a-batch-opens-its-head`
- **Layers:** unit
- **WHEN** a batch's one flow holds an approved, short sheet and an unapproved one, then neither
- **THEN** its Review opens the unapproved sheet, then the approved one
- **AND** with no sheet left it opens none

#### Scenario: two flows waiting open the chooser
- **Key:** `ui:review:two-flows-waiting-open-the-chooser`
- **Layers:** unit
- **WHEN** a batch's two flows each hold an unapproved sheet
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
- **WHEN** an approval succeeds and reading the batch again fails
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

#### Scenario: the rail names the other flows' waiting sheets
- **Key:** `ui:review:the-rail-names-the-other-flows-waiting`
- **Layers:** unit
- **WHEN** Review is open on one flow and another flow holds one unapproved sheet
- **THEN** the rail's head names that flow and one waiting

### Requirement: Revise starts from an image, and opens Review on its first draft

The system SHALL offer Revise from an image's large view and over a selection in the Renders grid, SHALL show what it
will write before writing, and SHALL then open Review on the first draft it wrote, the others of its flow
in the rail. An image whose flow holds a waiting draft SHALL write nothing: Revise from its large view SHALL open
Review on that draft, and a selection SHALL leave such images out, the confirm naming them. It SHALL
write a selection's drafts all or none, refusing by name an image of a flow this build does not track, and refusing a
selection that names a version or a seed no run can hold. On a revision, draft or approved, Review SHALL show the
photograph and the image being revised on one line, at equal height under one header row, mark each field that
differs from its approval, and offer *Side by side*, also on `⌃P`, both in one dialog, `⌃P` in it showing the photograph
alone and back; on a draft it SHALL offer to discard it from the approve bar, deleting it only once the operator
confirms.

The comparison that matters on a revision is the render against the photograph, read against the sheet. A discard
deletes the operator's edits, so one click never does. A waiting draft is the work in hand, so Revise goes to it;
the comparison still matters once the revision is approved.

#### Scenario: Revise opens Review on the revision
- **Key:** `ui:revise:revise-opens-review-on-the-revision`
- **Layers:** e2e
- **WHEN** Revise is confirmed on an image's large view
- **THEN** Review opens on its draft with the render beside the photograph and the seed prefilled
- **AND** once approved, the render still stands beside the photograph

#### Scenario: an approved revision keeps its image
- **Key:** `ui:revise:an-approved-revision-keeps-its-image`
- **Layers:** unit
- **WHEN** Review reads a revision's approval
- **THEN** its payload names the approval it came from, its image and that approval's fields

#### Scenario: a waiting draft is opened, not refused
- **Key:** `ui:revise:a-waiting-draft-is-opened`
- **Layers:** unit
- **WHEN** Revise is asked for an image whose flow holds a waiting draft
- **THEN** it answers with that draft and writes nothing

#### Scenario: an untracked flow refuses its image
- **Key:** `ui:revise:an-untracked-flow-refuses-its-image`
- **Layers:** unit
- **WHEN** Revise is asked for a selection holding an image of a flow this build does not track
- **THEN** that image is refused naming its flow
- **AND** no draft is written for any image

#### Scenario: an image no run can hold is refused
- **Key:** `ui:revise:an-image-no-run-can-hold-is-refused`
- **Layers:** unit
- **WHEN** Revise is asked for an image whose version or seed no run can hold
- **THEN** the selection is refused
- **AND** no draft is written

#### Scenario: a discard deletes the draft the page read
- **Key:** `ui:revise:a-discard-deletes-the-draft-the-page-read`
- **Layers:** unit
- **WHEN** a discard states the draft on disk
- **THEN** that draft is deleted
- **AND** every approval is unchanged

#### Scenario: Discard asks before it deletes
- **Key:** `ui:revise:discard-asks-before-it-deletes`
- **Layers:** e2e
- **WHEN** Discard is pressed on a revision, then Keep
- **THEN** the draft is still on disk and the sheet still open

#### Scenario: Side by side shows the pair
- **Key:** `ui:revise:side-by-side-shows-the-pair`
- **Layers:** e2e
- **WHEN** `⌃P` is pressed on a revision with focus in a tag field, then `⌃P` again
- **THEN** one dialog shows the photograph and the render at equal height, then the photograph alone
- **AND** `Esc` closes it

### Requirement: Conjure from this drafts from an image's approval, and opens Review on it

The system SHALL offer, on an image's large view, one action per target — each flow of the batch that reads a sheet
alone, other than the image's own — named *Conjure from this* for `conjure-anime-wai`, the first on `⇧F`. It SHALL
draft the target of the image's run from the approval the image was rendered under, then open Review on that draft;
a refusal SHALL show on the large view, and write nothing. On such a draft, Review SHALL mark each field that differs
from the target's sheet, name the source flow and approval in the sheet's kicker, and offer *Discard draft*.

```
large view · summon-anime-wai v1 · seed 7     [ Conjure from this ⇧F ]
        │ drafts conjure-anime-wai from summon-anime-wai v1
        ▼
Review · conjure-anime-wai   ③ SHEET — FROM SUMMON-ANIME-WAI V1   hair_colour  was …
```

The image the operator approved is where the next flow starts. A flow that reads a photograph has its own sheet of
the person, so it is no target. The marks show what the source changed, so the operator reads only the fields the
target adds.

#### Scenario: the large view names its targets
- **Key:** `ui:conjure-from:the-large-view-names-its-targets`
- **Layers:** unit
- **WHEN** a summon image's large view is read in a batch assigning conjure
- **THEN** its targets are conjure alone

#### Scenario: a refused draft writes nothing
- **Key:** `ui:conjure-from:a-refused-draft-writes-nothing`
- **Layers:** unit
- **WHEN** a draft is asked for a target holding no sheet
- **THEN** it is refused naming the way out
- **AND** no file is written

#### Scenario: Review reads the draft against the target's sheet
- **Key:** `ui:conjure-from:review-reads-the-draft-against-the-sheet`
- **Layers:** unit
- **WHEN** Review reads a draft written from another flow's approval
- **THEN** it names the source flow and approval, and carries the target sheet's fields

#### Scenario: Conjure from this opens Review on the draft
- **Key:** `ui:conjure-from:conjure-from-this-opens-review`
- **Layers:** e2e
- **WHEN** `⇧F` is pressed on a summon image's large view
- **THEN** Review opens on conjure's draft, its kicker naming the summon approval
- **AND** a field summon changed is marked against conjure's sheet

## ADDED Requirements

### Requirement: A dialog holds the focus while it is open

The system SHALL open every confirming dialog — Render, Revise, and New batch or Add sources — as a modal dialog,
the page behind it inert, the focus on its first control and held inside it, and SHALL return the focus to where it
was when it closes. The Render dialog's first control SHALL be *Keep the volume open*, which `Space` toggles and
`↵` leaves alone; the Revise dialog's SHALL be its confirm button.

A key goes where the eye is. A dialog over a grid that leaves the focus on the grid sends `↵` and `Tab` to what it
covers; and only `Mod+↵` spends money, so `↵` on the checkbox never renders.

#### Scenario: the Render dialog opens on its checkbox
- **Key:** `ui:dialogs:the-render-dialog-opens-on-its-checkbox`
- **Layers:** e2e
- **WHEN** the Render dialog opens on the hub, then `Tab` is pressed until the focus has passed every control
- **THEN** *Keep the volume open* held the focus first, and the focus never left the dialog
- **AND** `Esc` returns the focus to the hub cell it left
