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
cell modal SHALL show the cell's images as a row per version, oldest first, each row's seeds in numeric order, each
image at twice a thumbnail's size, a seed rendered under more than one version marked `⇄`; the arrows and `h j k l`
SHALL move it, `↵` or a click SHALL open the focused image's large view, and `Esc` SHALL close it. A cell holding images
SHALL show every one of them in that order, each marked with its version, a click on one opening the cell modal on it,
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
shows a cell's renders together, at a size to compare them, in the order every screen walks, so a render keeps its place
from the cell to the large view. The pending count is the render stage's own, the one Renders shows.

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
- **WHEN** the cell modal opens on an image of a cell holding seeds 9 then 2 under v1, and seed 4 under v2
- **THEN** its rows are v1 holding 2 then 9, then v2, as the cell's thumbnails stand, the focus on that image
- **AND** a row move keeps the column, held at a shorter row's end

#### Scenario: a seed under two versions is marked
- **Key:** `ui:hub:a-seed-under-two-versions-is-marked`
- **Layers:** unit
- **WHEN** a cell holds seed 7 under v1 and v2, and seed 5 under v2 alone
- **THEN** the cell modal marks seed 7 `⇄` and leaves seed 5 unmarked

#### Scenario: a thumbnail opens the cell modal on it
- **Key:** `ui:hub:a-thumbnail-opens-the-cell-modal-on-it`
- **Layers:** e2e
- **WHEN** a cell's older thumbnail is clicked
- **THEN** the cell modal opens focused on that image, its tiles at twice a thumbnail's width
- **AND** each tile of a seed rendered under both versions is marked `⇄`

#### Scenario: a cell shows what is ready
- **Key:** `ui:hub:a-cell-shows-what-is-ready`
- **Layers:** unit
- **WHEN** a cell's newest approval lacks two images of its count
- **THEN** the cell's last tile reads `ready · 2 images`
- **AND** a cell lacking none, or unapproved, draws no such tile

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

## ADDED Requirements

### Requirement: The Renders view shows each source's images by flow, and a large view walks the photograph's row

The system SHALL list a collection's images by source and offered flow, each cell's approval versions newest first, and
SHALL show them as a grid of sources by flows, each cell one row of its images, its versions oldest to newest, each
image marked with its version, and open an image's large view, with the sheet it was rendered from, from any of them. A
cell whose newest approval lacks images of its count SHALL carry the number it lacks, as the render stage counts it.
Each source SHALL show its photograph's thumbnail, upright, opening the photograph in a viewer, its cell the grid's
first column, reached by the keys and opened by `↵`. `h` `l` and the arrows on a large view SHALL walk the
photograph's row wherever it was opened — its flows in the hub's column order, each version oldest first, each
version's seeds in numeric order — replacing its address, held at either end, its head naming the step, `2 of 5`. `Esc`
and the back button on a large view SHALL return to the screen it was opened from — the hub focused on the cell of the
image it closed, Renders focused on that image — scrolled to the window's centre, and Renders SHALL keep its focus
across the Back button and a switch of tabs. It SHALL mark an approval it cannot read as damaged, naming the
file, and show every image, that version's own among them; and SHALL refuse an address whose version is not `v` and
ASCII digits. It SHALL serve each thumbnail, a render's or a source's, from a cache in the library's `.cache/`, made on
first request and named by the image's own bytes. It SHALL refuse an image it cannot read, one past Pillow's pixel bound
among them, naming the file. It SHALL serve a photograph, a source or a run's copy, as the image its bytes are, whatever
its name ends in, and a source in a format the render does not read as an upright JPEG of it.

The images come back to where the sheets were decided, version by version in the order they were approved; a cache the
library can lose costs only its rebuild. Two collections can hold one source rendered at one seed, so only the bytes say
which image a thumbnail shows. One damaged file costs only its own version, never the collection's page. The count a
cell lacks is the render stage's own, so the page and the render agree on what is ready. A source keeps the name it
arrived with, and one ending `.html` served by its name would run as a page on the surface's own origin; one placed by
hand in another format is still shown, as its thumbnail is. One order on every screen keeps a render's place, and the
image a large view closes may be another flow's than the one it opened on, so the hub lands on that image's cell.

#### Scenario: versions are listed newest first
- **Key:** `ui:renders:versions-newest-first`
- **Layers:** unit
- **WHEN** a cell holds images under two approvals
- **THEN** the newer approval's images are listed first

#### Scenario: a damaged approval marks its own version
- **Key:** `ui:renders:a-damaged-approval-marks-its-version`
- **Layers:** unit
- **WHEN** one of a cell's two approvals holds a count no render takes
- **THEN** its version is marked damaged, naming the file
- **AND** the other version and every image are still listed

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

#### Scenario: a cell counts what is ready
- **Key:** `ui:renders:a-cell-counts-what-is-ready`
- **Layers:** unit
- **WHEN** a cell's newest approval holds fewer images than its count
- **THEN** the cell carries the number of images it lacks

#### Scenario: the large view shows its sheet
- **Key:** `ui:renders:the-large-view-shows-its-sheet`
- **Layers:** e2e
- **WHEN** an image is opened from the grid
- **THEN** its large view shows the approval it was rendered from
- **AND** `Esc` returns to the grid focused on that image, and that image in view
- **AND** `h` from a row's first image reaches its source, and `↵` there opens its photograph

#### Scenario: a source opens in the viewer
- **Key:** `ui:renders:a-source-opens-in-the-viewer`
- **Layers:** e2e
- **WHEN** a source's thumbnail is clicked in the Renders view
- **THEN** its photograph opens in a dialog, fitted to the window
- **AND** `Esc` closes the dialog and leaves the address unchanged

#### Scenario: a damaged version's images are drawn
- **Key:** `ui:renders:a-damaged-versions-images-are-drawn`
- **Layers:** e2e
- **WHEN** the Renders view opens on a cell whose one approval is damaged
- **THEN** that version's images are drawn beside its damaged mark
- **AND** the first of them holds the focus

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

#### Scenario: a grid keeps its focus
- **Key:** `ui:renders:a-grid-keeps-its-focus`
- **Layers:** unit
- **WHEN** a collection's grid focus is moved, then its view is opened again
- **THEN** the focus is where it was left, or on the first spot when that one is gone

#### Scenario: the large view walks the photograph's row
- **Key:** `ui:renders:the-large-view-walks-the-photographs-row`
- **Layers:** unit
- **WHEN** `l` is pressed on the large view of a source's first image, the hub its opener
- **THEN** it shows the row's next image, then the next flow's first image, in the hub's column order
- **AND** at the last image `l` holds

## REMOVED Requirements

### Requirement: The Renders view shows each source's images by flow and version

**Reason**: its scenario *the large view steps through its screen's order* is false once a large view walks the
photograph's row wherever it was opened; a MODIFIED block may not drop a scenario title, so the requirement is removed
and added under a new title.

**Migration**: *The Renders view shows each source's images by flow, and a large view walks the photograph's row*
carries every scenario; `ui:renders:the-large-view-steps-its-screens-order` is
`ui:renders:the-large-view-walks-the-photographs-row`, and every other `ui:renders:` key keeps its key.
