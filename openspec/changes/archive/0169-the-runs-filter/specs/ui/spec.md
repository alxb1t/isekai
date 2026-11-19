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

#### Scenario: a folder that is no run is ignored
- **Key:** `ui:hub:a-folder-that-is-no-run-is-ignored`
- **Layers:** unit
- **WHEN** a collection's runs folder holds a folder whose name is no run's and which cannot be read
- **THEN** the hub shows its grid with no cell and no refusal for it
- **AND** a run beside it shows its stage

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

