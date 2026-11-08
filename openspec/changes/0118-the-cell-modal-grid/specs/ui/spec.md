## MODIFIED Requirements

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
it. A cell holding images SHALL show every one of them in that order, each marked with its version, a click on one opening the cell modal on it,
and last, while its newest approval lacks images of its count, a tile naming the number it lacks, as the render stage
counts it. A source's cell SHALL be the grid's first column, reached by `h` and `←`, and `↵` there SHALL open its
photograph in the viewer, stepping through the collection's sources. The hub SHALL keep its focus across the Back button
and a switch of tabs, a restored focus scrolled to the window's centre. A key's move to the first row SHALL scroll the
hub to its top, to the last row to its foot, and to any other row only as far as the row needs. The header SHALL leave a
12 px gap between items. An assigned cell SHALL read tagged from the photograph's tag list, so a photograph tagged once
is tagged in every flow it is assigned to.

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

### Requirement: Render is confirmed in a dialog that quotes what renders, its limit and its price at most

The system SHALL offer Render from a bar on a collection's hub that counts the images short of
their approvals' counts, its collection's and, as `+n in other collections`, every other collection's, and SHALL show no
such bar when no collection is short and no count is refused, nor on the hub while changes wait for Prepare. While a
render runs the bar SHALL show the session's totals and *Session* in place of the count and Render, and name the images
short that the session does not render as waiting for the next session. The bar SHALL be disabled, with its reason, when
a pod may still be billing, when no RunPod key is in the surface's environment, and when an approval's count is refused.
It SHALL open a dialog listing a row per collection short of images, in the Library's order, each ticked, and in each
row per offered flow the photographs that will render, as tiles grouped by flow, and none that is left out; unticking a
row SHALL quote the rest again; the session's estimate and limit, and its price at most — the limit at the hourly
maximum `gpunit.toml` names, with the volume at its configured rate; an estimate past the ceiling `gpunit.toml` names
SHALL disable the confirmation, saying so. A tile's `×`, or `⌫` while the tile holds the focus, SHALL take its
photograph's flow out of the session and quote the rest again, show the next photograph past the cap, and move the focus
to the next tile; a refused count SHALL show no tile. A row whose every tile is taken out SHALL read *all removed*,
unticked, and leave the confirmation, and with every row so emptied the confirmation SHALL be disabled, saying *Nothing
left to render.* The tiles SHALL be one stop in the `Tab` order: `h` and `l` SHALL move the focus along a flow's tiles,
`j` and `k` to the next and the previous flow's, its place held at the shorter's end, and a key's move SHALL scroll the
focused tile to the centre of the list where the scroll allows, the first flow's to the list's top and the last's to its
foot. Its confirmation SHALL be the only act that rents; the dialog SHALL hold no URL, and SHALL close when its page is
left, and the confirmation SHALL close it and open the session drawer over the page. The confirmation SHALL carry the
ticked collections, the limit, the number of images the dialog showed and the photographs taken out, which the session
SHALL not render, and SHALL be refused, starting nothing, when the ticked collections' quote taken again has a longer
limit or another number of images, or names a photograph that is not one of a quoted collection's runs. The bar SHALL
show the newest offer asked for, whatever order the answers arrive in.

The quote is what the operator agrees to; gpunit refuses a card above the hourly maximum, so the price is a bound and
not a guess. A reload never reopens a confirmation that spends; a changed image total or longer limit requires a fresh
confirmation, even where the limit sits at its floor or cap. An equal-total change of sources or approvals is outside
that comparison. A bar that is absent needs no reason, and one forward action holds the screen's accent; a refused count
keeps the bar, so the refusal is never silent. A photograph is known by sight, so the dialog shows it rather than its
file name, and is taken out where it is seen; the dialog shows only what renders, as that is what the operator agrees
to. A removal is the render verb's `--without`, so the page's session is one the terminal can run
([D3](../../../docs/decisions.md#d3--the-hand-path-stays)).

#### Scenario: the dialog lists what renders per flow
- **Key:** `ui:render:the-dialog-lists-what-renders`
- **Layers:** unit
- **WHEN** a collection's quote is asked for with approvals short of their count in two flows, and a draft in one
- **THEN** it lists each flow's images, each photograph with its run, and nothing left out
- **AND** it carries the estimate, the limit and the price at most

#### Scenario: the dialog shows each photograph as a thumbnail by flow
- **Key:** `ui:render:the-dialog-shows-thumbnails-by-flow`
- **Layers:** unit
- **WHEN** a collection's quote holds photographs to render in a flow
- **THEN** each flow shows its photographs' thumbnails, 15 and then `+n`, each counted only above one image

#### Scenario: a photograph taken out leaves the quote and the session
- **Key:** `ui:render:a-photograph-taken-out-leaves-the-quote`
- **Layers:** unit
- **WHEN** the quote and the confirmation name one run's flow taken out of a collection short in two runs
- **THEN** the quote counts the other run's images alone
- **AND** the render job's verb carries a `--without` for the run's flow

#### Scenario: a photograph no quoted run holds is refused
- **Key:** `ui:render:a-photograph-not-quoted-is-refused`
- **Layers:** unit
- **WHEN** the quote names a photograph taken out whose run is not one of the collection's runs
- **THEN** the quote is refused, naming that the dialog must be opened again

#### Scenario: taking a photograph out shows the next past the cap
- **Key:** `ui:render:taking-out-shows-the-next`
- **Layers:** unit
- **WHEN** a flow holds more photographs than the cap and one of its shown photographs is taken out
- **THEN** the next photograph past the cap shows
- **AND** `+n` counts one fewer

#### Scenario: a tile is taken out by its key and by its ×
- **Key:** `ui:render:a-tile-is-taken-out-by-its-key`
- **Layers:** e2e
- **WHEN** a flow's first tile holds the focus, then `l` and `⌫` are pressed, then each tile left is taken out by
  its `×`
- **THEN** `l` moved the focus to the second tile, `⌫` took it out of the row and its quote, the focus on the next
- **AND** the row reads *all removed* and is unticked

#### Scenario: with every row taken out nothing is left to render
- **Key:** `ui:render:nothing-left-disables-render`
- **Layers:** unit
- **WHEN** every tile of every row is taken out
- **THEN** each row reads *all removed*
- **AND** the confirmation is disabled, saying *Nothing left to render.*

#### Scenario: the tiles move by flow
- **Key:** `ui:render:the-tiles-move-by-flow`
- **Layers:** unit
- **WHEN** `h`, `l`, `j` and `k` move the focus over a flow of three tiles and a flow of two
- **THEN** `h` and `l` step along a flow's tiles and stay at its ends
- **AND** `j` and `k` move to the next and the previous flow's, held at the shorter's end

#### Scenario: a key's move centres the focused tile
- **Key:** `ui:render:a-key-move-centres-the-tile`
- **Layers:** unit
- **WHEN** a key moves the focus to a middle flow's tile, then to the first flow's, then to the last's
- **THEN** the middle tile scrolls to the list's centre
- **AND** the first scrolls the list to its top, and the last to its foot

#### Scenario: without a key Render is disabled
- **Key:** `ui:render:without-a-key-render-is-disabled`
- **Layers:** unit
- **WHEN** the surface's environment holds no RunPod key
- **THEN** Render is disabled, naming the fix

#### Scenario: nothing short disables Render
- **Key:** `ui:render:nothing-short-disables-render`
- **Layers:** unit
- **WHEN** every approval in a collection already has its count of images
- **THEN** the collection's Render offer counts no image
- **AND** it names why

#### Scenario: Prepare takes the bar first
- **Key:** `ui:render:prepare-takes-the-bar-first`
- **Layers:** unit
- **WHEN** a hub has images short and changes waiting for Prepare
- **THEN** the Prepare bar shows and the Render bar does not
- **AND** with nothing waiting the Render bar shows, and with nothing short neither does

#### Scenario: a refused count is shown
- **Key:** `ui:render:a-refused-count-is-shown`
- **Layers:** unit
- **WHEN** a collection's only approval short of its count holds a count no render takes
- **THEN** its Render offer counts no image and carries the refusal, naming the file
- **AND** the Render bar shows, disabled, with its reason

#### Scenario: the confirmation starts the render
- **Key:** `ui:render:the-confirmation-starts-the-render`
- **Layers:** e2e
- **WHEN** the dialog's Render is confirmed
- **THEN** the session drawer opens over the hub, which keeps its URL
- **AND** the dialog is closed

#### Scenario: a quote that has grown is refused
- **Key:** `ui:render:a-grown-quote-is-refused`
- **Layers:** unit
- **WHEN** Render is confirmed with a shorter limit, or fewer images, than the collection's quote now gives
- **THEN** the confirmation is refused, naming that the quote changed
- **AND** no job starts

#### Scenario: a stale offer is dropped
- **Key:** `ui:render:a-stale-offer-is-dropped`
- **Layers:** unit
- **WHEN** an older offer request is answered after a newer one
- **THEN** the bar keeps the newer offer

#### Scenario: the dialog quotes every collection
- **Key:** `ui:render:the-dialog-quotes-every-collection`
- **Layers:** unit
- **WHEN** two collections are short of images and the quote is asked for both, then for one
- **THEN** the first quote lists both, with one estimate and one limit
- **AND** the second lists the one alone

#### Scenario: past the ceiling disables Render
- **Key:** `ui:render:past-the-ceiling-disables-render`
- **Layers:** unit
- **WHEN** the ticked collections' estimate passes the configured ceiling
- **THEN** the quote's confirmation is disabled, naming the ceiling

#### Scenario: a running session shows its totals
- **Key:** `ui:render:a-running-session-shows-its-totals`
- **Layers:** unit
- **WHEN** the bar is read while a session renders three images and a fourth is short outside it
- **THEN** it shows the session's totals and *Session*, and one image waiting for the next session
- **AND** it shows no count ready to render and no Render

### Requirement: The running render opens in a drawer every screen offers

The system SHALL show the running render in a session drawer: a modal dialog as wide as its widest grid, at least half
the window and 480 px, at most the window less 100 px, a wider grid scrolling inside it, on the right, over a dark
backdrop, holding no URL. `⌃;` SHALL open and close it on every screen, from a field too, and the running render's
link SHALL open it; confirming a render SHALL open it, and a render started from the terminal SHALL open nothing. Its
bar and the Render bar SHALL show one progress, the images done over the images asked, from one function, the drawer
keeping the time against the limit as text. It SHALL read the running render's record, live while it runs, with the
volume steps and Stop the job adds; after it ends it SHALL show that session's outcome, its images and its time until
the app reloads or another render starts; with neither it SHALL say no render runs. Its images SHALL be a grid per
collection the session renders, stacked in its recorded collection order, retaining scan order for older records
without it, each headed by its name: a column for each photograph the session was asked to render, a row for each
flow, the photographs' row at the foot, a cell holding that flow's images of that photograph and a waiting tile for
each still to come, drawn at a thumbnail's size and moved through by `h j k l` and the arrows, `j` `↓` on a
grid's last row moving into the first row of the grid below and `k` `↑` back, keeping the column, held at a shorter
row's end. `↵` SHALL open the focused row in the viewer over the drawer, which SHALL follow its list when it changes
while open; `⇧H` SHALL close the drawer and open the focused image's collection's hub, as *View in Hub* does. A click on the backdrop,
`⌃;` and `Esc` SHALL close it, `Esc` closing the viewer first.
A key's move to the first row SHALL scroll the drawer to its top, to the last row to its foot, and to any other row
only as far as the row needs, a grid's first row also bringing its collection's name into view.

```
any screen ──⌃; or ●──▶ the drawer, half the window ──↵──▶ the viewer over it
                         esc / ⌃; / the backdrop ◀──esc── closes one layer
```

A running render bills by the minute wherever the operator is, so it is the app's, not a collection's: it is glanced at,
not gone to. A session is the record the render wrote, so the drawer and the terminal agree; once it ends its images are
on the hub.
The session's head sits above the first row, Stop below the last, and each collection's name above its own first
row, so a move there shows them.

#### Scenario: the drawer holds the render
- **Key:** `ui:sessions:the-drawer-holds-the-render`
- **Layers:** e2e
- **WHEN** a render is confirmed, `↵` is pressed on its image, then `Esc` twice, then `⌃;`
- **THEN** the drawer shows the render over the hub, the viewer its image, then the drawer again, then the page alone
- **AND** `⌃;` opens the drawer again on the finished session's outcome

#### Scenario: the drawer keeps the last session
- **Key:** `ui:sessions:the-drawer-keeps-the-last-session`
- **Layers:** unit
- **WHEN** a running render ends, then another starts
- **THEN** the drawer shows the first's outcome until the second starts, then the second

#### Scenario: the viewer closes for a replacement session
- **Key:** `ui:sessions:the-viewer-closes-for-a-replacement-session`
- **Layers:** unit
- **WHEN** another terminal render starts while the finished session's photograph viewer is open
- **THEN** the viewer closes while the drawer waits for the replacement record
- **AND** the drawer shows the replacement session without an error

#### Scenario: a session's page reads its record
- **Key:** `ui:sessions:a-session-reads-its-record`
- **Layers:** unit
- **WHEN** a session is asked for by its id
- **THEN** its record's images, steps and outcome are served
- **AND** an id no record holds is refused, naming the id

#### Scenario: a terminal render stays live
- **Key:** `ui:sessions:a-terminal-render-stays-live`
- **Layers:** unit
- **WHEN** a terminal render runs across collections in reverse name order without an app job slot
- **THEN** its records read running and the global running-session read carries their id and complete traversal order
- **AND** after its process releases ownership without an outcome the record reads ended without an outcome

#### Scenario: the selected record keeps the newest response
- **Key:** `ui:sessions:the-selected-record-keeps-the-newest-response`
- **Layers:** unit
- **WHEN** an older record read answers after a newer read of the same session
- **THEN** the selected record keeps the newer outcome and images

#### Scenario: the viewer follows image identity
- **Key:** `ui:sessions:the-viewer-follows-image-identity`
- **Layers:** unit
- **WHEN** an open viewer's list shrinks, reorders, grows or becomes empty
- **THEN** it keeps the selected image by identity while present, otherwise a valid neighbour
- **AND** an empty list closes the viewer

#### Scenario: the session grid holds each flow over the originals
- **Key:** `ui:sessions:the-grid-holds-each-flow-over-the-originals`
- **Layers:** unit
- **WHEN** a record plans two images of one photograph in summon and one of another in conjure
- **THEN** the grid has a column per photograph, a row per flow over the photographs' row, and three waiting tiles
- **AND** a record without a plan places its landed images and no waiting tiles

#### Scenario: the session grid moves by photograph and by row
- **Key:** `ui:sessions:the-grid-moves-by-photograph-and-row`
- **Layers:** unit
- **WHEN** `l` and then `j` are pressed on the grid's first render
- **THEN** `l` moves to the next photograph's column and `j` to the row below, held at the photographs' row

#### Scenario: the grids stack by collection
- **Key:** `ui:sessions:the-grids-stack-by-collection`
- **Layers:** unit
- **WHEN** `j` is pressed on the first grid's last row, then `k`
- **THEN** the focus moves into the second grid's first row, in the same column, then back

#### Scenario: one progress for the Render bar and the drawer
- **Key:** `ui:sessions:one-progress-for-the-bar-and-the-drawer`
- **Layers:** unit
- **WHEN** a session has rendered three of four images
- **THEN** the Render bar and the drawer's bar are each three quarters full
- **AND** with no plan the bar slides, sized by nothing

#### Scenario: the drawer fits its widest grid
- **Key:** `ui:sessions:the-drawer-fits-its-widest-grid`
- **Layers:** e2e
- **WHEN** the drawer holds a session whose grid is wider than half the window
- **THEN** the drawer is as wide as that grid, short of the window by 100 px at most

#### Scenario: a key's move to an edge row shows the drawer's head
- **Key:** `ui:sessions:an-edge-row-shows-the-head`
- **Layers:** e2e
- **WHEN** in a window holding the head and the first row, not the foot, `j` moves to the last row, then `k` back
- **THEN** the timer is out of view on the last row
- **AND** View in Hub is in view there
- **AND** the timer is in view again on the first

### Requirement: Draft from this starts from an image, for any flow the app offers, and opens Review on the draft

The system SHALL offer *Draft from this* on `⇧D` from an image's large view,
opening a dialog that lists every flow the app offers, the image's own first, named *revise*, focused, and the others
after it, assigned or not; `↵` SHALL draft the chosen flow from each image's approval, as the draft verb does — a
revision for the image's own flow, a draft from that approval for another, assigning a target and filling its sheet from
the photograph's tags where it holds none, the image's seed prefilled and, for another flow, the image copied into the
target's sources — then open Review on the first draft, the others of its flow in the rail. A target holding a waiting
draft with edits of its own SHALL write nothing for that image and open Review on that draft; one equal to its sheet
SHALL be replaced. A selection SHALL be drafted all or none, refusing by name an image of a flow this build does not
track, and refusing a selection that names a version or a seed no run can hold. On such a draft, draft or approved,
Review SHALL show the photograph and, for a revision, while its file exists, the image the draft records — whatever its
seeds became, else the first of its seeds rendered under its approval — headed by its seed, or, for a draft from another
flow, its source copy, headed *the image it was drafted from* and naming no flow, version or seed; on one line, at equal
height under one header row, and offer *Side by side*, also on `⌃P`, both in one dialog, `⌃P` in it showing the
photograph alone and back; it SHALL mark each field that differs from the approval a revision came from, or from the
target's sheet for another flow; on a draft it SHALL offer to discard it from the approve bar, deleting it only once the
operator confirms.

```
large view · summon-anime-wai v2 · seed 9423…   ⇧D
  Draft from this
  ▸ summon-anime-wai           revise
    summon-semireal-anime-wai
    summon-flat-anime-wai
    summon-vivid-anime-wai
    conjure-anime-wai
  ↵ ─▶ Review on the draft: the photograph │ the image it came from
```

An image the operator approved is where the next draft starts, in its own flow or another: one act, whatever the flows
become. The comparison that matters is the render against the photograph, read against the sheet. A waiting edit is the
work in hand; a draft the operator never touched holds no work. A discard deletes the operator's edits, so one click
never does. A draft from another flow holds its own fields and its own copy of the image, so deleting the image it
came from, or the whole source flow, leaves it as it was
([D50](../../../docs/decisions.md#d50--the-last-render-takes-its-approval-and-a-flow-holds-only-its-own-files)).

#### Scenario: Revise opens Review on the revision
- **Key:** `ui:revise:revise-opens-review-on-the-revision`
- **Layers:** e2e
- **WHEN** *Draft from this* is drafted into the image's own flow on its large view
- **THEN** Review opens on its draft with the render beside the photograph and the seed prefilled
- **AND** once approved, the render still stands beside the photograph

#### Scenario: a revision keeps its image after its seed changes
- **Key:** `ui:revise:a-revision-keeps-its-image-after-its-seed-changes`
- **Layers:** unit
- **WHEN** Review reads a revision whose seed was changed, draft and then approved
- **THEN** its payload names the image the revision was written from

#### Scenario: an approved revision keeps its image
- **Key:** `ui:revise:an-approved-revision-keeps-its-image`
- **Layers:** unit
- **WHEN** Review reads a revision's approval
- **THEN** its payload names the approval it came from, its image and that approval's fields

#### Scenario: a waiting draft is opened, not refused
- **Key:** `ui:revise:a-waiting-draft-is-opened`
- **Layers:** unit
- **WHEN** a revision is asked for an image whose flow holds a waiting draft with edits of its own
- **THEN** it answers with that draft and writes nothing

#### Scenario: an untracked flow refuses its image
- **Key:** `ui:revise:an-untracked-flow-refuses-its-image`
- **Layers:** unit
- **WHEN** a draft is asked for a selection holding an image of a flow this build does not track
- **THEN** that image is refused naming its flow
- **AND** no draft is written for any image

#### Scenario: an image no run can hold is refused
- **Key:** `ui:revise:an-image-no-run-can-hold-is-refused`
- **Layers:** unit
- **WHEN** a draft is asked for an image whose version or seed no run can hold
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

#### Scenario: the large view names its targets
- **Key:** `ui:conjure-from:the-large-view-names-its-targets`
- **Layers:** unit
- **WHEN** a summon image's large view is read in a collection where no source is assigned another flow
- **THEN** its targets are every flow the app offers, summon first

#### Scenario: a refused draft writes nothing
- **Key:** `ui:conjure-from:a-refused-draft-writes-nothing`
- **Layers:** unit
- **WHEN** a draft is asked from an approval version the source does not hold
- **THEN** it is refused naming that version
- **AND** no file is written

#### Scenario: a waiting edit is opened
- **Key:** `ui:conjure-from:a-waiting-edit-is-opened`
- **Layers:** unit
- **WHEN** a draft is asked for a target whose waiting draft has edits of its own
- **THEN** it answers with that draft and writes nothing

#### Scenario: an approved draft keeps its marks
- **Key:** `ui:conjure-from:an-approved-draft-keeps-its-marks`
- **Layers:** unit
- **WHEN** Review reads the approval of a draft written from another flow's approval
- **THEN** it carries the target sheet's fields and the number of its source copy

#### Scenario: Review reads the draft against the target's sheet
- **Key:** `ui:conjure-from:review-reads-the-draft-against-the-sheet`
- **Layers:** unit
- **WHEN** Review reads a draft written from another flow's approval
- **THEN** it carries the target sheet's fields and the number of its source copy, naming no source approval
- **AND** the source copy is served at that number, and still is once the source image's file is gone

#### Scenario: Conjure from this opens Review on the draft
- **Key:** `ui:conjure-from:conjure-from-this-opens-review`
- **Layers:** e2e
- **WHEN** `⇧D` is pressed on a summon image whose source is not assigned conjure, conjure chosen and `↵` pressed
- **THEN** Review opens on conjure's draft, its kicker naming no summon approval, the image headed *the image it was
  drafted from*
- **AND** a field summon changed is marked against conjure's sheet
- **AND** its caption pane shows the photograph's caption, naming no flow, and the summon image stands beside the
  photograph
- **AND** once summon's only render is deleted, summon's cell reads *tagged* and conjure's draft still opens, showing
  the photograph and its source copy

#### Scenario: an unedited waiting draft is replaced
- **Key:** `ui:draft-from:an-unedited-waiting-draft-is-replaced`
- **Layers:** unit
- **WHEN** a draft is asked for a target whose waiting draft equals its sheet
- **THEN** the draft from the image is written at that draft's number

#### Scenario: a selection drafts into the flow chosen
- **Key:** `ui:draft-from:a-selection-drafts-into-the-flow-chosen`
- **Layers:** unit
- **WHEN** a selection of two images from different runs is drafted into another flow
- **THEN** each run's target gains a draft from its image's approval, its seed prefilled

## REMOVED Requirements

### Requirement: The Renders view shows each source's images by flow, and a large view walks the photograph's row

**Reason:** Renders is deleted: the hub's cells show every image and the pending tile, the cell modal sets a cell's
renders side by side, and every large view goes back to the hub. Its large view, thumbnail and serving rules stand, as
*An image's large view shows its sheet and walks the photograph's row, and its thumbnail is made once*.

**Migration:** Open images from the hub — `↵` or a click on a cell opens the cell modal, `↵` there the large view. The
`/c/<collection>/renders` page is gone; the large view's and Compare's `/renders/…` addresses keep their names. The
scenarios *versions are listed newest first*, *a cell counts what is ready*, *a source opens in the viewer* and *a
damaged version's images are drawn* go with the page; *a grid keeps its focus* is the hub's, as *the hub keeps its
focus*; every other scenario keeps its key under the added requirement.

### Requirement: Every command has one key, declared once, and none fires while typing

**Reason:** Its scenario *Renders moves by cell and by image* goes with Renders, and `openspec validate --strict`
refuses a MODIFIED block that drops a scenario.

**Migration:** Read *Each command has one key, declared once, and none fires while typing*: the same rule, every other scenario and key kept, *a row move keeps the column* read
on the cell modal.

## ADDED Requirements

### Requirement: An image's large view shows its sheet and walks the photograph's row, and its thumbnail is made once

The system SHALL open an image's large view, with the sheet it was rendered from, from the hub's cell modal. `h` `l` and
the arrows on a large view SHALL walk the photograph's row — its flows in the hub's column order, each version oldest
first, each version's seeds in numeric order — replacing its address, held at either end, its head naming the step, `2
of 5`. `Esc` and *Back to Hub* on a large view SHALL open the hub focused on the cell of the image it closed, scrolled
to the window's centre, whatever opened the view. The large view of an image whose approval no hand can read SHALL be
headed damaged, naming the file, and count nothing. It SHALL refuse an address whose version is not `v` and ASCII
digits. It SHALL serve each thumbnail, a render's or a source's, from a cache in the library's `.cache/`, made on first
request and named by the image's own bytes, a source's upright. It SHALL refuse an image it cannot read, one past
Pillow's pixel bound among them, naming the file. It SHALL serve a photograph, a source or a run's copy, as the image
its bytes are, whatever its name ends in, and a source in a format the render does not read as an upright JPEG of it.

A cache the library can lose costs only its rebuild. Two collections can hold one source rendered at one seed, so only
the bytes say which image a thumbnail shows. One damaged file costs only its own image's heading. A source keeps the
name it arrived with, and one ending `.html` served by its name would run as a page on the surface's own origin; one
placed by hand in another format is still shown, as its thumbnail is. One order on every screen keeps a render's place,
and the image a large view closes may be another flow's than the one it opened on, so the hub lands on that image's
cell; the hub is the one screen of images, so a pasted address goes back there too.

#### Scenario: an address naming no version is refused
- **Key:** `ui:renders:an-address-naming-no-version-is-refused`
- **Layers:** unit
- **WHEN** an image is asked for at a version spelled in digits outside ASCII
- **THEN** the request is refused naming the version, never failed

#### Scenario: a thumbnail is made once
- **Key:** `ui:renders:a-thumbnail-is-made-once`
- **Layers:** unit
- **WHEN** an image's thumbnail is asked for twice
- **THEN** the second answer is read from `.cache/` without decoding the image

#### Scenario: a thumbnail is its own image's
- **Key:** `ui:renders:a-thumbnail-is-its-own-images`
- **Layers:** unit
- **WHEN** two collections hold different images of one source, flow, version and seed
- **THEN** each image's thumbnail is made from that image

#### Scenario: a source's thumbnail is upright
- **Key:** `ui:renders:a-source-thumbnail-is-upright`
- **Layers:** unit
- **WHEN** a source's thumbnail is asked for and its file declares a turning orientation
- **THEN** the thumbnail is drawn upright
- **AND** a second request reads it from `.cache/`

#### Scenario: the large view shows its sheet
- **Key:** `ui:renders:the-large-view-shows-its-sheet`
- **Layers:** e2e
- **WHEN** an image is opened from the cell modal
- **THEN** its large view shows the approval it was rendered from
- **AND** `Esc` returns to the hub focused on that image's cell, and that cell in view

#### Scenario: a damaged approval marks its own version
- **Key:** `ui:renders:a-damaged-approval-marks-its-version`
- **Layers:** unit
- **WHEN** one of a cell's two approvals holds a count no render takes
- **THEN** its image's large view is headed damaged, naming the file, and counts nothing
- **AND** the other version's large view is not damaged

#### Scenario: a photograph is served as the image its bytes are
- **Key:** `ui:renders:a-photograph-is-served-as-its-bytes`
- **Layers:** unit
- **WHEN** a source whose name ends `.html` holds a PNG and is asked for whole
- **THEN** it is served as `image/png`, and the browser is told not to guess another type
- **AND** a run's photograph is served the same way
- **AND** a source in another format is served as an upright JPEG of it

#### Scenario: an image it cannot read is refused
- **Key:** `ui:renders:an-unreadable-image-is-refused`
- **Layers:** unit
- **WHEN** an image past Pillow's pixel bound is read for a thumbnail, or served whole
- **THEN** it is refused, naming the file

#### Scenario: the large view walks the photograph's row
- **Key:** `ui:renders:the-large-view-walks-the-photographs-row`
- **Layers:** unit
- **WHEN** `l` is pressed on the large view of a source's first image
- **THEN** it shows the row's next image, then the next flow's first image, in the hub's column order
- **AND** at the last image `l` holds

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
