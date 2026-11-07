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
image, and open the viewer on the newest of the cell's images where it holds any, stepping through them, `⇧↵` opening an
image's large view; an unreadable cell SHALL do nothing. A cell holding images SHALL show every one of them, oldest to
newest, each marked with its version. A source's cell SHALL be the grid's first column, reached by `h` and `←`, and `↵`
there SHALL open its photograph in the viewer, stepping through the collection's sources. The hub SHALL keep its focus
across a large view, the Back button and a switch of tabs, a restored focus scrolled to the window's centre. A key's
move to the first row SHALL scroll the hub to its top, to the last row to its foot, and to any other row only as far as
the row needs. The header SHALL leave a 12 px gap between items. An assigned cell SHALL read tagged from the
photograph's tag list, so a photograph tagged once is tagged in every flow it is assigned to.

A stage is a directory listing, the rule every stage already follows, so the grid cannot drift from the disk, and a tick
survives a reload. A tagged cell holds no sheet: its tag list is the photograph's, so its untick deletes no work, and
the verb's refusal of a directory holding files is the guard. The mark and the size are read from the source itself, so
no file records them. An approved cell can hold an older version's images, so its newest image is named by the server
rather than guessed by the page. A row's pictures share a foot, so a long name, a mark or a refusal moves only the text
above them. *Add sources…* and the flow names sit above the first row, so a move there shows them.

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
- **THEN** it ticks up to tagged, opens Review on a sheet, a draft or an unrendered approval, and opens an image
- **AND** an unreadable cell does nothing

#### Scenario: a rendered cell opens its newest image
- **Key:** `ui:hub:a-rendered-cell-opens-its-newest-image`
- **Layers:** e2e
- **WHEN** a rendered cell is clicked, then `⇧↵` is pressed in the viewer
- **THEN** the viewer opens on its newest image, then that image's large view
- **AND** `Esc` returns to the hub, focused on that cell, and that cell in view

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

