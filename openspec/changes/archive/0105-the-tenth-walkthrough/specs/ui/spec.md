## MODIFIED Requirements

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
each still to come, drawn at the tile size Renders draws and moved through by `h j k l` and the arrows, `j` `↓` on a
grid's last row moving into the first row of the grid below and `k` `↑` back, keeping the column, held at a shorter
row's end. `↵` SHALL open the focused row in the viewer over the drawer, which SHALL follow its list when it changes
while open; `⇧I` SHALL close the drawer and open the focused image's collection's Renders. A click on the backdrop,
`⌃;` and `Esc` SHALL close it, `Esc` closing the viewer first.
A key's move to the first row SHALL scroll the drawer to its top, to the last row to its foot, and to any other row
only as far as the row needs, a grid's first row also bringing its collection's name into view.

```
any screen ──⌃; or ●──▶ the drawer, half the window ──↵──▶ the viewer over it
                         esc / ⌃; / the backdrop ◀──esc── closes one layer
```

A running render bills by the minute wherever the operator is, so it is the app's, not a collection's: it is glanced at,
not gone to. A session is the record the render wrote, so the drawer and the terminal agree; once it ends its images are
on Renders.
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
- **AND** View in Renders is in view there
- **AND** the timer is in view again on the first

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
A key's move to the tiles' first row SHALL scroll the sheet's body to its top, to the last row to its foot, and to
any other row only as far as the row needs.

Each file's bar answers which one is slow; each reason sits on the file it concerns, so two files of one name are
two uploads. A file that lands while the folder is committed would be dropped from the collection unseen, and a cancel
then would delete the folder the commit is moving. `⇧A` adds sources on the hub, so pressed again in the sheet it adds
more files.
The sources' label sits above the first row, so a move there shows it.

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

#### Scenario: a key's move to an edge row shows the sources' label
- **Key:** `ui:sheet:an-edge-row-shows-the-head`
- **Layers:** e2e
- **WHEN** in a window holding the label and the first row, not the foot, `j` moves to the last row, then `k` back
- **THEN** the sources' label above the tiles is out of view on the last row
- **AND** it is in view again on the first
