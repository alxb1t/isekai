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
scrolled to the window's centre. The header SHALL leave a 12 px gap between items.

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

### Requirement: Sources are chosen in the file dialog, and each shows its own upload

The system SHALL take sources through the browser's file dialog, sending each file in its own request, and SHALL show
for each its upload's progress, then its reading, then whether it is ready, converted, refused or not cleaned, with
the reason. Import SHALL stay disabled, with its reason, until every chosen file is read, and SHALL commit only the
ready files and those the operator chose to import as they are. Each upload SHALL keep its own state, whatever its
name; an upload SHALL be refused once Import begins committing; and a file whose reading fails SHALL be refused
alone, the next file still read. While Import commits, the sheet SHALL take no file, no second Import and no
cancel, by button, by `Esc` or by leaving the screen; a commit refused after the screen is left SHALL cancel its
staged folder. Before Import commits, a read or a skipped file SHALL be removable alone, unasked — `×` on its tile, or
`⌫` with its tile focused — a read file's removal taking it out of the staging folder, and the focus moving to the next
tile; a file still uploading SHALL offer neither. Once read, the tiles SHALL be a grid that `h j k l` and the arrows
move through, the first tile taking the focus unless a field holds it, and `↵` SHALL open the focused file full size in
the viewer.

Each file's bar answers which one is slow; each reason sits on the file it concerns, so two files of one name are
two uploads. A file that lands while the folder is committed would be dropped from the collection unseen, and a cancel
then would delete the folder the commit is moving.

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

#### Scenario: the tiles take the keys once read
- **Key:** `ui:sheet:the-tiles-take-the-keys`
- **Layers:** unit
- **WHEN** every chosen file is read and no field holds the focus
- **THEN** the first tile takes the focus, `h j k l` move it, and `⌫` removes the focused file
- **AND** `↵` opens it full size in the viewer

### Requirement: Prepare runs what changed as one job, and refuses before it starts when Ollama does not answer

The system SHALL run Prepare as one job over every assigned cell with no sheet: for each flow, the tagging, reading and
sheet stages, each one invocation of the pipeline's own verb over that flow's cells. One job of each kind, a Prepare and
a render, SHALL run at a time, the two side by side in any collections; a job SHALL keep running when its page closes;
Stop SHALL interrupt the current stage of the job it names and start no other, leaving the other job running; stopping
the surface SHALL interrupt every running job; each line a job's verbs write to the collection's log SHALL name its job;
and a stage that fails having reported nothing SHALL end the job as failed, naming the collection's log, and start no
other. Before any stage starts, the surface SHALL check that the local model server answers, and SHALL refuse with its
message, starting nothing, when it does not. While Prepare runs, the job strip and Prepare bar SHALL show each stage's
completed cells out of its asked total — `tag 6 of 6 · caption 3 of 6 · sheet 0 of 6 · 00:35` — the bar as wide as the
stages done over the stages asked; each total SHALL stay fixed, a cell SHALL count once per stage it completes and a
refused one in none, and elapsed time SHALL tick every second. Before it runs, the Prepare bar SHALL name how many
photographs it prepares in its collection, `2 photographs to prepare in <collection>`, its button the changes.

The pipeline's verb is the one path, so Prepare is exactly what the verbs do. Prepare runs on the local models and a
render on a rented GPU, and they write no file in common, so neither waits for the other. A refusal before the start
leaves every cell assigned, so pressing Prepare again is the whole fix.

#### Scenario: Prepare runs each stage over the assigned cells
- **Key:** `ui:prepare:prepare-runs-the-assigned-cells`
- **Layers:** e2e
- **WHEN** Prepare is pressed with cells assigned
- **THEN** each cell reaches sheet
- **AND** no cell outside the assignment changes
- **AND** while it runs, the strip and bar show matching totals and ticking elapsed time across a reload, and Render
  is offered beside it

#### Scenario: a second job is refused while one runs
- **Key:** `ui:prepare:one-job-at-a-time`
- **Layers:** unit
- **WHEN** a job is asked for while another of its kind runs
- **THEN** it is refused naming the running job

#### Scenario: another batch's Prepare is disabled while one runs
- **Key:** `ui:prepare:another-batchs-prepare-is-disabled`
- **Layers:** unit
- **WHEN** a hub has changes waiting while a Prepare runs for another collection
- **THEN** its Prepare is disabled, naming the collection that runs

#### Scenario: Prepare refuses when Ollama does not answer
- **Key:** `ui:prepare:refused-when-ollama-does-not-answer`
- **Layers:** unit
- **WHEN** Prepare is asked for and the local model server does not answer
- **THEN** it is refused with the reader's message
- **AND** no stage starts

#### Scenario: Stop interrupts the job
- **Key:** `ui:prepare:stop-interrupts-the-job`
- **Layers:** unit
- **WHEN** Stop is asked for during a stage
- **THEN** that stage is interrupted and no later stage starts
- **AND** cells already at sheet stay at sheet

#### Scenario: a stage that fails before it reports ends the job
- **Key:** `ui:prepare:a-silent-failure-ends-the-job`
- **Layers:** unit
- **WHEN** a stage exits in failure having reported no item
- **THEN** the job ends as failed, naming the collection's log
- **AND** no later stage starts

#### Scenario: totals count cells rather than stage reports
- **Key:** `ui:prepare:totals-count-cells-not-stages`
- **Layers:** unit
- **WHEN** assigned cells report tagging, reading, sheet completion and a refusal
- **THEN** each stage's count grows once per cell completing it, against that stage's fixed total
- **AND** a refused cell counts in no stage, and a repeated completion never increments a count again

#### Scenario: a render runs beside a Prepare
- **Key:** `ui:prepare:a-render-runs-beside-a-prepare`
- **Layers:** unit
- **WHEN** a render is asked for while a Prepare runs
- **THEN** both run, and Stop of the render leaves the Prepare running

#### Scenario: stopping the surface interrupts both jobs
- **Key:** `ui:prepare:stopping-the-surface-interrupts-both`
- **Layers:** unit
- **WHEN** the surface stops while a Prepare and a render run
- **THEN** both are interrupted, and the render's window closes before the surface exits

#### Scenario: the log names each job
- **Key:** `ui:prepare:the-log-names-each-job`
- **Layers:** unit
- **WHEN** a Prepare and a render write to one collection's log
- **THEN** each line begins with its job's name

#### Scenario: the Prepare bar names its photographs
- **Key:** `ui:prepare:the-bar-names-its-photographs`
- **Layers:** unit
- **WHEN** two photographs are assigned to two flows each
- **THEN** the bar reads `2 photographs to prepare in <collection>`
- **AND** its button reads `4 changes · Prepare`

### Requirement: Every command has one key, declared once, and none fires while typing

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
for `⌫` on a chosen file, which removes it before anything is committed. No key SHALL spend money but the Render
dialog's `Mod+↵`, which confirms the price it quotes.

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

#### Scenario: Renders moves by cell and by image
- **Key:** `ui:keys:renders-moves-by-cell-and-by-image`
- **Layers:** unit
- **WHEN** `l` and then `→` are pressed on a cell's last image of the Renders grid
- **THEN** each moves to the next image, crossing into the next cell, and `h` at a row's start reaches its source

#### Scenario: Review moves between its panes
- **Key:** `ui:keys:review-moves-between-its-panes`
- **Layers:** unit
- **WHEN** on macOS `⌃L` is pressed from the rail three times, then `l` once
- **THEN** focus moves through the source pane and the sheet to ④
- **AND** `l` moves within ④, and no pane changes

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
- **WHEN** `?` and then `⌃/` are pressed with focus in a text field
- **THEN** `?` is typed into the field and `⌃/` opens the key list

#### Scenario: Review's fields move from a field on macOS
- **Key:** `ui:keys:review-fields-move-from-a-field-on-macos`
- **Layers:** unit
- **WHEN** Review's commands are declared on macOS and then on Linux
- **THEN** on macOS `⌃J` and `⌃K` move to the next and the previous field from a text field
- **AND** on Linux neither is declared

### Requirement: A dialog holds the focus while it is open

The system SHALL open every confirming dialog — Render, Revise, and New collection or Add sources — and the key list as
a modal dialog,
the page behind it inert, the focus on its first control and held inside it, and SHALL return the focus to where it
was when it closes. The Render dialog's first control SHALL be *Keep the volume open*, which `Space` toggles and
`↵` leaves alone; the Revise dialog's SHALL be its confirm button. The key list
SHALL stand centred over most of the window, its keys in columns by scope — everywhere, then the screen's — and `⌃/`,
`Esc` and the backdrop SHALL close it.

A key goes where the eye is. A dialog over a grid that leaves the focus on the grid sends `↵` and `Tab` to what it
covers; and only `Mod+↵` spends money, so `↵` on the checkbox never renders.

#### Scenario: the Render dialog opens on its checkbox
- **Key:** `ui:dialogs:the-render-dialog-opens-on-its-checkbox`
- **Layers:** e2e
- **WHEN** the Render dialog opens on the hub, then `Tab` is pressed until the focus has passed every control
- **THEN** *Keep the volume open* held the focus first, and the focus never left the dialog
- **AND** `Esc` returns the focus to the hub cell it left

#### Scenario: the key list is a dialog
- **Key:** `ui:dialogs:the-key-list-is-a-dialog`
- **Layers:** unit
- **WHEN** `⌃/` opens the key list on a screen
- **THEN** it is a modal dialog holding the focus, the everywhere keys in one column and the screen's in another
- **AND** `⌃/`, `Esc` and a click on the backdrop each close it

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

```
any screen ──⌃; or ●──▶ the drawer, half the window ──↵──▶ the viewer over it
                         esc / ⌃; / the backdrop ◀──esc── closes one layer
```

A running render bills by the minute wherever the operator is, so it is the app's, not a collection's: it is glanced at,
not gone to. A session is the record the render wrote, so the drawer and the terminal agree; once it ends its images are
on Renders.

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

#### Scenario: the drawer fits its widest grid
- **Key:** `ui:sessions:the-drawer-fits-its-widest-grid`
- **Layers:** e2e
- **WHEN** the drawer holds a session whose grid is wider than half the window
- **THEN** the drawer is as wide as that grid, short of the window by 100 px at most
- **AND** a refusal's text does not widen it

#### Scenario: one progress for the Render bar and the drawer
- **Key:** `ui:sessions:one-progress-for-the-bar-and-the-drawer`
- **Layers:** unit
- **WHEN** a session has rendered three of four images
- **THEN** the Render bar and the drawer's bar are each three quarters full
- **AND** with no plan the bar slides, sized by nothing

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

### Requirement: A version says what it was, and Compare sets an image beside any image of its source

The system SHALL head each image's large view with its approval version, the version it came from, read from its
producer, naming it a revision when its fields differ from that version's and a re-roll when only its count or seeds
do, and the approval's time, count and seeds. `⇧C` on a large view SHALL open a pick of its source's images: the
photograph's row on top, then a row per flow holding images of the source, each row its images oldest to newest, each
captioned by its version, the image compare started from marked, the pick's head naming the focused image's flow,
version and seed on two lines, `Compare <the image started from>` and `with <the focused image>`, each cut at its end;
the pick SHALL be as wide as its longest row, its images 20 px apart, at least 480 px and at most the window less 96
px, a longer row scrolling inside it, whatever is focused; the focus SHALL start on the newest older version of its
seed, else the image before it, else the photograph; `h j k l` and the arrows SHALL move it, keeping the column, held
at a shorter row's end, `↵` SHALL compare the image picked and `Esc` close the pick. Compare SHALL set the image
picked on the left and the image compare started from on the right, at equal size, each headed by its flow, version
and seed, and nothing else: the pair as tall as the window less the app bar and the heads, centred. The large view
SHALL offer no *Side by side*.

```
large view · summon v2 · seed 9423  ⇧C ─▶  photo                  [▣]
                                           summon-anime-wai       [v1][v2·][v3]
                                           summon-flat-anime-wai  [v1]
                                       ↵ ─▶ Compare: the image picked │ summon v2 · seed 9423
```

The origin is already on disk, so nothing new records it. A pick reads as a choice when every choice is in view; one
source's images are every comparison the operator makes for one person. The eye returns to where it came from, on the
right. The images are what is compared, so they take the room.

#### Scenario: a version is named a revision or a re-roll
- **Key:** `ui:compare:a-version-is-named-by-what-changed`
- **Layers:** unit
- **WHEN** one version changes a field of the version it came from and another changes only its seeds
- **THEN** the first's large view is headed a revision and the second's a re-roll

#### Scenario: Compare pairs a seed with its newest older version
- **Key:** `ui:compare:a-seed-pairs-with-its-newest-older-version`
- **Layers:** unit
- **WHEN** a seed is rendered under versions one, two and three
- **THEN** version three's pick opens focused on version two

#### Scenario: Compare shows the pair and the changed fields
- **Key:** `ui:compare:compare-shows-the-pair-and-the-change`
- **Layers:** e2e
- **WHEN** `⇧C` is pressed on a revised image, then `↵`
- **THEN** the older version is on the left and the revised image on the right, each under its head alone
- **AND** a pick of another flow's image compares it, saying the seeds differ

#### Scenario: the photograph's pick sets it beside the image
- **Key:** `ui:compare:side-by-side-sets-the-image-beside-its-photograph`
- **Layers:** e2e
- **WHEN** `⇧C` is pressed on an image's large view, then `k` to the photograph's row and `↵`
- **THEN** the photograph is on the left and the image on the right, at equal height, with no fields

#### Scenario: Compare takes any two images of a source
- **Key:** `ui:compare:any-two-images-of-a-cell`
- **Layers:** unit
- **WHEN** Compare is asked for a summon image of v4 against a flat summon image of v1 with another seed
- **THEN** it serves both images' heads, and no changed field
- **AND** the image picked is on the left, the image compare started from on the right

#### Scenario: the pick moves by row and column
- **Key:** `ui:compare:the-pick-moves-by-row-and-column`
- **Layers:** unit
- **WHEN** `j` is pressed on the photograph's row, then `l` twice, then `j` onto a shorter row
- **THEN** the focus moves to the first flow's first image, then its third, then the shorter row's last

#### Scenario: the pick names the focused tile
- **Key:** `ui:compare:the-pick-names-the-focused-tile`
- **Layers:** unit
- **WHEN** the focus moves to the second of two seeds of one version
- **THEN** its caption reads the version alone, and the pick's head names its flow, version and seed

#### Scenario: the pick holds its width
- **Key:** `ui:compare:the-pick-holds-its-width`
- **Layers:** e2e
- **WHEN** the focus moves in the pick from an image with a long name to the photograph
- **THEN** the pick's width does not change
- **AND** its head takes two lines, each cut at its end

## ADDED Requirements

### Requirement: The viewer shows an image fitted or at full size, by the mouse or the keys

The system SHALL show an image in the viewer fitted to the window, and SHALL toggle it to full size and back by a
click or `↵`; at full size `j` `k` and `↓` `↑` SHALL scroll it, `h` `l` and the arrows SHALL step to the next image,
fitted, and `Esc` SHALL close the viewer. On a pair, which is fitted alone, `↵` SHALL do nothing.

```
fitted ──click or ↵──▶ full size ──j k ↓ ↑──▶ scrolled
   ▲                       │
   └──click or ↵ · h l ────┘          Esc closes either
```

Whether a likeness holds is read at full size, and a hand that left the mouse should not need it back.

#### Scenario: ↵ toggles full size
- **Key:** `ui:viewer:enter-toggles-full-size`
- **Layers:** unit
- **WHEN** `↵` is pressed on a fitted image, then again
- **THEN** the image shows at full size, then fitted
- **AND** on a pair `↵` changes nothing

#### Scenario: full size scrolls by the keys
- **Key:** `ui:viewer:full-size-scrolls-by-the-keys`
- **Layers:** unit
- **WHEN** `j` is pressed on an image at full size, then `l`
- **THEN** the image scrolls down, then the next image shows fitted
