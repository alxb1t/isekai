## MODIFIED Requirements

### Requirement: The hub shows each source's stage in each offered flow, and a tick assigns it

The system SHALL show a collection's hub as a grid of its sources by the flows the surface offers, each cell carrying
the stage read from that run's directory — no flow, assigned, tagged, sheet, draft, approved or rendered — and SHALL
ignore any other flow's directory. A cell whose run file cannot be read SHALL show that it is unreadable, with the
refusal the pipeline raised, and the rest of the grid SHALL still be shown. Reading the hub SHALL write nothing; a tick
SHALL write only through the assigning verb, and an untick only while the cell is assigned. A source imported as it is,
still carrying metadata, SHALL be marked on its row. Each source SHALL show its name and its thumbnail, and its row
SHALL carry the size read from its own file, with or without a run, which the viewer's title names. A source's thumbnail
and a cell's images SHALL sit at the foot of their cells, level across the row, whatever text stands above them; a
cell's refusal SHALL stand above its images, and `↵ view photo` SHALL take no line of the source's cell. A cell SHALL
name its newest image — the newest version holding images, then its last-written image — and a click or `↵` SHALL follow
the cell's stage: tick while unassigned or assigned, open Review on a sheet or a draft, open the sheet read-only on an
approval with no image, and open the viewer on the newest of the cell's images where it holds any, stepping through
them, `⇧↵` opening an image's large view; a tagged or unreadable cell SHALL do nothing. A cell holding images SHALL show
every one of them, oldest to newest, each marked with its version. A source's cell SHALL be the grid's first column,
reached by `h` and `←`, and `↵` there SHALL open its photograph in the viewer, stepping through the collection's
sources. The hub SHALL keep its focus across a large view, the Back button and a switch of tabs, a restored focus
scrolled to the window's centre. A key's move to the first row SHALL scroll the hub to its top, to the last row to its
foot, and to any other row only as far as the row needs. The header SHALL leave a 12 px gap between items.

A stage is a directory listing, the rule every stage already follows, so the grid cannot drift from the disk, and a tick
survives a reload. The mark and the size are read from the source itself, so no file records them. An approved cell can
hold an older version's images, so its newest image is named by the server rather than guessed by the page. A row's
pictures share a foot, so a long name, a mark or a refusal moves only the text above them. *Add sources…* and the flow
names sit above the first row, so a move there shows them.

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

### Requirement: Sources are chosen in the file dialog, and each shows its own upload

The system SHALL take sources through the browser's file dialog, sending each file in its own request, and SHALL show
for each its upload's progress, then its reading, then whether it is ready, converted, refused or not cleaned, with
the reason. Import SHALL stay disabled, with its reason, until every chosen file is read and every removal has
ended, and SHALL commit only the ready files and those the operator chose to import as they are. Each upload SHALL
keep its own state, whatever its name; an upload SHALL be refused once Import begins committing; and a file whose
reading fails SHALL be refused alone, the next file still read. While Import commits, the sheet SHALL take no file,
no second Import and no cancel, by button, by `Esc` or by leaving the screen; a commit refused after the screen is
left SHALL cancel its staged folder. Before Import commits, a read or a skipped file SHALL be removable alone,
unasked — `×` on its tile, or `⌫` with its tile focused — a read file's removal taking it out of the staging folder,
unless a file skipped as its copy is still chosen, which then holds it, and the focus moving to the next tile; a file
still uploading SHALL offer neither, and a second press on a file whose removal is in flight SHALL do nothing. Once
read, the tiles SHALL be a grid that `h j k l` and the arrows move through, the first tile taking the focus unless a
field holds it, and `↵` SHALL open the focused file full size in the viewer. `⇧A` SHALL open the file dialog from the
sheet, whether it names a new collection or adds to one, except while Import commits or a text field holds the focus,
and Add files… SHALL carry its key.

Each file's bar answers which one is slow; each reason sits on the file it concerns, so two files of one name are
two uploads. A file that lands while the folder is committed would be dropped from the collection unseen, and a cancel
then would delete the folder the commit is moving. `⇧A` adds sources on the hub, so pressed again in the sheet it adds
more files.

#### Scenario: each file shows its own progress, then its result
- **Key:** `ui:sheet:each-file-shows-its-progress`
- **Layers:** e2e
- **WHEN** files are chosen in the dialog
- **THEN** each tile shows its upload, then its result
- **AND** a refused file names its reason

#### Scenario: import waits for every file to be read
- **Key:** `ui:sheet:import-waits-for-reading`
- **Layers:** e2e
- **WHEN** a chosen file is still being read
- **THEN** Import is disabled, naming how many are read

#### Scenario: an imported batch opens its hub
- **Key:** `ui:sheet:an-import-opens-the-hub`
- **Layers:** e2e
- **WHEN** Import is pressed on a new collection
- **THEN** the collection's hub opens with every source unassigned

#### Scenario: a staged file serves its preview
- **Key:** `ui:sheet:a-staged-file-serves-its-preview`
- **Layers:** unit
- **WHEN** a staged file's preview is asked for
- **THEN** a downscaled JPEG of it is served
- **AND** nothing of it is kept

#### Scenario: the stream reports each file's reading
- **Key:** `ui:sheet:the-stream-reports-each-files-reading`
- **Layers:** unit
- **WHEN** an uploaded file is read
- **THEN** the import's stream reports it waiting, then converting, then its result

#### Scenario: an upload is answered before it is read
- **Key:** `ui:sheet:an-upload-is-answered-before-reading`
- **Layers:** unit
- **WHEN** a file's bytes have all arrived
- **THEN** its request is answered before the file is read
- **AND** the files are read one at a time, in the order their uploads ended

#### Scenario: two uploads of one name keep their own states
- **Key:** `ui:sheet:two-uploads-of-one-name-keep-their-own-states`
- **Layers:** unit
- **WHEN** two files of one name are uploaded to one import, and one is refused
- **THEN** each upload is reported under its own id
- **AND** only the refused one carries the refusal

#### Scenario: an upload after Import is pressed is refused
- **Key:** `ui:sheet:an-upload-after-import-is-refused`
- **Layers:** unit
- **WHEN** a file is uploaded once Import has begun committing
- **THEN** the upload is refused, naming the way to add it
- **AND** the committed collection is unchanged by it

#### Scenario: a failed read refuses its file alone
- **Key:** `ui:sheet:a-failed-read-refuses-its-file-alone`
- **Layers:** unit
- **WHEN** reading one uploaded file raises
- **THEN** that file is refused, naming why
- **AND** the next file is still read

#### Scenario: a commit in flight holds the sheet
- **Key:** `ui:sheet:a-commit-in-flight-holds-the-sheet`
- **Layers:** e2e
- **WHEN** Import's commit is in flight
- **THEN** Add files…, Import and Cancel are disabled, and no file can be removed
- **AND** `Esc` leaves the sheet open

#### Scenario: leaving the screen mid-commit keeps the staged folder
- **Key:** `ui:sheet:leaving-mid-commit-keeps-the-folder`
- **Layers:** unit
- **WHEN** the sheet closes while Import's commit is in flight
- **THEN** its staging folder is not cancelled
- **AND** a commit refused after it closes cancels the folder

#### Scenario: a chosen file is removed alone
- **Key:** `ui:sheet:a-chosen-file-is-removed-alone`
- **Layers:** unit
- **WHEN** a read file and a skipped file are each removed before Import
- **THEN** the read file leaves the staging folder and the skipped one only the sheet
- **AND** every other file stays, and Import commits the rest
- **AND** while a removal is in flight, Import is disabled, naming it

#### Scenario: a removed file's copy keeps the photograph
- **Key:** `ui:sheet:a-removed-files-copy-keeps-it`
- **Layers:** unit
- **WHEN** a read file is removed while a file skipped as its copy is still chosen
- **THEN** the copy holds the staged file, which stays in the staging folder, and Import commits it
- **AND** with no copy chosen, the removal takes the file out of the staging folder
- **AND** a copy heard as skipped only as its file is removed is sent again, so it stages its own bytes and Import
  commits it

#### Scenario: the tiles take the keys once read
- **Key:** `ui:sheet:the-tiles-take-the-keys`
- **Layers:** unit
- **WHEN** every chosen file is read and no field holds the focus
- **THEN** the first tile takes the focus, `h j k l` move it, and `⌫` removes the focused file
- **AND** `↵` opens it full size in the viewer

#### Scenario: ⇧A opens the file dialog from the sheet
- **Key:** `ui:sheet:shift-a-opens-the-file-dialog`
- **Layers:** e2e
- **WHEN** `⇧A` is pressed in the open sheet, no field holding the focus
- **THEN** the browser's file dialog opens, and the files chosen in it join the sheet
- **AND** Add files… carries `⇧A`

### Requirement: A folder in the library is a collection when it holds `sources/`

The system SHALL list as a collection every folder in the library that holds `sources/`, SHALL list any other folder as
not a collection and open none of it, and SHALL list no dot-folder. Each collection's row SHALL carry its name, its
source count, the names of its first fifteen sources, whose thumbnails it shows, for each flow the surface offers that
is present the counts approved and rendered out of the sources that have that flow, the count of sources with no flow,
and the time and kind of the newest file written in it; Home SHALL draw the row with no count per flow, which the
payload alone carries. Collections SHALL be ordered by that time, newest first, and folders that are not collections
after them. Home SHALL carry New collection at the right of the library's header row, and on an empty library below the
privacy line. A key's move to the first collection SHALL scroll Home to its top, to the last to its foot, and to any
other only as far as the row needs. Count labels on the surface SHALL use a singular noun at one and a plural noun
otherwise.

A folder is a collection by its layout alone, so no marker file can disagree with what is on disk, and the row is a
listing read on every request. A folder that is not a collection is shown rather than hidden so the screen matches the
folder, and nothing in the app writes into it. The flows the surface offers are named in its configuration; a flow
approved from another's sheet stays the CLI's. The per-flow counts are read where an approval is counted, and the row
on screen keeps to the collection's name, its sources and its newest activity. On first start the privacy line is read
before the first import. New collection sits above the first row, so a move there shows it.

#### Scenario: a folder with `sources/` is a collection
- **Key:** `ui:batch-folder:a-folder-with-sources-is-a-batch`
- **Layers:** unit
- **WHEN** the library holds a folder with `sources/` and one without
- **THEN** the first is listed as a collection
- **AND** the second is listed as not a collection, and cannot be opened

#### Scenario: a dot-folder is not listed
- **Key:** `ui:batch-folder:a-dot-folder-is-not-listed`
- **Layers:** unit
- **WHEN** the library holds a folder whose name starts with a dot
- **THEN** it is not listed at all

#### Scenario: a flow's counts are of the sources that have it
- **Key:** `ui:batch-folder:a-flows-counts-are-of-its-sources`
- **Layers:** unit
- **WHEN** a collection's sources have different sets of flows
- **THEN** each flow's approved and rendered counts are out of the sources whose runs hold that flow
- **AND** the sources with no flow are counted apart

#### Scenario: collections are ordered by their newest file
- **Key:** `ui:batch-folder:batches-are-ordered-by-their-newest-file`
- **Layers:** unit
- **WHEN** the library holds collections written at different times
- **THEN** they are listed newest first, by the newest file written in each

#### Scenario: no file records a collection
- **Key:** `ui:batch-folder:no-file-records-a-batch`
- **Layers:** unit
- **WHEN** the surface lists the library and opens a collection
- **THEN** no file describing a collection is created anywhere in the library

#### Scenario: a flow the surface does not offer has no count
- **Key:** `ui:batch-folder:an-unoffered-flow-has-no-count`
- **Layers:** unit
- **WHEN** a collection's runs hold a tracked flow the configuration does not offer
- **THEN** its row carries no count for that flow

#### Scenario: count labels use singular at one
- **Key:** `ui:batch-folder:count-labels-use-singular-at-one`
- **Layers:** unit
- **WHEN** a count label is drawn for zero, one and several items
- **THEN** one uses the singular noun and the other counts use the plural noun

#### Scenario: a row names its first sources
- **Key:** `ui:batch-folder:a-row-names-its-first-sources`
- **Layers:** unit
- **WHEN** a collection holds seventeen sources
- **THEN** its row names the first fifteen in the hub's order
- **AND** its source count is seventeen

#### Scenario: the row Home draws shows no count per flow
- **Key:** `ui:batch-folder:the-row-draws-no-count-per-flow`
- **Layers:** e2e
- **WHEN** Home lists a collection that holds an approval
- **THEN** its row shows no flow's approved or rendered count

#### Scenario: first start shows New collection under the privacy line
- **Key:** `ui:batch-folder:first-start-shows-new-batch-under-the-privacy-line`
- **Layers:** e2e
- **WHEN** Home opens on an empty library
- **THEN** New collection sits below the privacy line

#### Scenario: a key's move to an edge row shows Home's head
- **Key:** `ui:batch-folder:an-edge-row-shows-the-head`
- **Layers:** unit
- **WHEN** a key moves the focus to the first collection, to the last, or to one between
- **THEN** Home scrolls to its top, to its foot, or only as far as the row needs

