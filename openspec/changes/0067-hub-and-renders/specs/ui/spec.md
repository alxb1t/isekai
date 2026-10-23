## MODIFIED Requirements

### Requirement: A folder in the library is a batch when it holds `sources/`

The system SHALL list as a batch every folder in the library that holds `sources/`, SHALL list any other folder as
not a batch and open none of it, and SHALL list no dot-folder. Each batch's row SHALL carry its name, its source
count, the names of its first seven sources, whose thumbnails it shows, for each flow the surface offers that is
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
- **WHEN** a batch holds nine sources
- **THEN** its row names the first seven in the hub's order
- **AND** its source count is nine

#### Scenario: first start shows New batch under the privacy line
- **Key:** `ui:batch-folder:first-start-shows-new-batch-under-the-privacy-line`
- **Layers:** e2e
- **WHEN** Home opens on an empty library
- **THEN** New batch sits below the privacy line

### Requirement: The hub shows each source's stage in each offered flow, and a tick assigns it

The system SHALL show a batch's hub as a grid of its sources by the flows the surface offers, each cell carrying the
stage read from that run's directory — no flow, assigned, tagged, sheet, draft, approved or rendered — and SHALL
ignore any other flow's directory. A cell whose run file cannot be read SHALL show that it is unreadable, with the
refusal the pipeline raised, and the rest of the grid SHALL still be shown. Reading the hub SHALL write nothing; a
tick SHALL write only through the assigning verb, and an untick only while the cell is assigned. A source imported
as it is, still carrying metadata, SHALL be marked on its row. Each source SHALL show its thumbnail and the size read
from its own file, with or without a run. A cell SHALL name its newest image — the newest version holding images,
then its last-written image — and a click or `↵` SHALL follow the cell's stage: tick while unassigned or assigned,
open Review on a sheet or a draft, open the sheet read-only on an approval with no image, and open the newest
image's large view where the cell holds images; a tagged or unreadable cell SHALL do nothing. The header SHALL leave
a 12 px gap between items.

A stage is a directory listing, the rule every stage already follows, so the grid cannot drift from the disk, and a
tick survives a reload. The mark and the size are read from the source itself, so no file records them. An approved
cell can hold an older version's images, so its newest image is named by the server rather than guessed by the page.

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
- **WHEN** a rendered cell is clicked
- **THEN** its newest image's large view opens
- **AND** `Esc` returns to the hub

### Requirement: The page is told of a job as it runs

The system SHALL serve an event stream that, on every connection, sends a snapshot of the job slot and, when a batch
is named, that batch's hub, and then sends each change as the job's stages report it. A running Prepare snapshot
SHALL carry its accepted total, completed count and start time. A hub opened while the slot holds its batch's failed
Prepare SHALL show that job's message until Discard on that batch's hub dismisses it in that page. When the surface
stops, its streams SHALL end before the server's graceful wait expires, without cancellation errors; a terminal
interrupt SHALL exit quietly after cleanup.

A reload or a second tab gets the whole truth at once; a job's progress reaches the page as the verbs report it. A
job outlives its page, so a failure that happened while no page was open is still told.

#### Scenario: a connection starts with a snapshot
- **Key:** `ui:events:a-connection-starts-with-a-snapshot`
- **Layers:** unit
- **WHEN** the stream is opened for a batch
- **THEN** its first event carries the job slot and that batch's hub

#### Scenario: a stage's report reaches the stream
- **Key:** `ui:events:a-stages-report-reaches-the-stream`
- **Layers:** unit
- **WHEN** a running stage reports an item done
- **THEN** the stream sends that cell's new stage

#### Scenario: a reconnect keeps Prepare progress
- **Key:** `ui:events:a-reconnect-keeps-prepare-progress`
- **Layers:** unit
- **WHEN** a connection is opened while Prepare has completed part of its work
- **THEN** its snapshot carries the same fixed total, completed count and start time as the running job

#### Scenario: stopping ends open streams quietly
- **Key:** `ui:events:stopping-ends-open-streams-quietly`
- **Layers:** unit
- **WHEN** the surface receives a terminal interrupt with event streams open
- **THEN** the streams end within the graceful wait and the surface exits with status 130 without cancellation errors
- **AND** a running job is interrupted and its cleanup and recovery messages remain visible

#### Scenario: a hub opened after a failure shows it
- **Key:** `ui:events:a-hub-opened-after-a-failure-shows-it`
- **Layers:** unit
- **WHEN** a hub opens while the slot holds its batch's failed Prepare
- **THEN** the Prepare bar shows the job's message
- **AND** once Discard dismisses it, a hub opened again in that page does not

### Requirement: Render is confirmed in a dialog that quotes what renders, its limit and its price at most

The system SHALL offer Render from a bar on a batch's hub and its Renders view that counts the images short of their
approvals' counts, and SHALL show no such bar when none is short and no count is refused, nor on the hub while changes
wait for Prepare. The bar SHALL be disabled, with its reason, when a job runs, when a pod may still be billing, when
no RunPod key is in the surface's environment, and when an approval's count is refused. It SHALL open a dialog
listing per offered flow the images that will render and what is left out, with the reason, the session's estimate
and limit, and its price at most — the limit at the hourly maximum `gpunit.toml` names, with the volume at its
configured rate. Its confirmation SHALL be the only act that rents; the dialog SHALL hold no URL. The confirmation
SHALL carry the limit and the number of images the dialog showed, and SHALL be refused, starting nothing, when the
batch's quote taken again has a longer limit or another number of images.

The quote is what the operator agrees to; gpunit refuses a card above the hourly maximum, so the price is a bound and
not a guess. A reload never reopens a confirmation that spends; a changed image total or longer limit requires
a fresh confirmation, even where the limit sits at its floor or cap. An equal-total change of sources or approvals
is outside that comparison. A bar that is absent needs no reason, and one forward action holds the screen's accent;
a refused count keeps the bar, so the refusal is never silent.

#### Scenario: the dialog lists what renders per flow
- **Key:** `ui:render:the-dialog-lists-what-renders`
- **Layers:** unit
- **WHEN** a batch's quote is asked for with approvals short of their count in two flows
- **THEN** it lists each flow's images and what is left out, with the reason
- **AND** it carries the estimate, the limit and the price at most

#### Scenario: without a key Render is disabled
- **Key:** `ui:render:without-a-key-render-is-disabled`
- **Layers:** unit
- **WHEN** the surface's environment holds no RunPod key
- **THEN** Render is disabled, naming the fix

#### Scenario: nothing short disables Render
- **Key:** `ui:render:nothing-short-disables-render`
- **Layers:** unit
- **WHEN** every approval in a batch already has its count of images
- **THEN** the batch's Render offer counts no image
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
- **WHEN** a batch's only approval short of its count holds a count no render takes
- **THEN** its Render offer counts no image and carries the refusal, naming the file
- **AND** the Render bar shows, disabled, with its reason

#### Scenario: the confirmation starts the render
- **Key:** `ui:render:the-confirmation-starts-the-render`
- **Layers:** e2e
- **WHEN** the dialog's Render is confirmed
- **THEN** the session view opens at `/session`

#### Scenario: a quote that has grown is refused
- **Key:** `ui:render:a-grown-quote-is-refused`
- **Layers:** unit
- **WHEN** Render is confirmed with a shorter limit, or fewer images, than the batch's quote now gives
- **THEN** the confirmation is refused, naming that the quote changed
- **AND** no job starts

### Requirement: The Renders view shows each source's images by flow and version

The system SHALL list a batch's images by source and offered flow, each cell's approval versions newest first, and
SHALL show them as a grid of sources by flows, each cell one row of its images from oldest to newest, each image
marked with its version, and open an image's large view, with the
sheet it was rendered from, from any of them. A cell whose newest approval lacks images of its count SHALL carry the
number it lacks, as the render stage counts it. Each source SHALL show its photograph's thumbnail, upright, opening
the photograph in a viewer. `Esc` on a large view SHALL return to the screen it was opened from. It SHALL mark an
approval it cannot read as damaged, naming the file, and show every image, that version's own among them; and SHALL
refuse an address whose version is not `v` and ASCII digits. It SHALL serve each thumbnail, a render's or a source's,
from a cache in the library's `.cache/`, made on first request and named by the image's own bytes. It SHALL serve a
photograph, a source or a run's copy, as the image its bytes are, whatever its name ends in, and a source in a format
the render does not read as an upright JPEG of it.

The images come back to where the sheets were decided, in the order they were made; a cache the library can lose
costs only its rebuild. Two batches can hold one source rendered at one seed, so only the bytes say which image a
thumbnail shows. One damaged file costs only its own version, never the batch's page. The count a cell lacks is the
render stage's own, so the page and the render agree on what is ready. A source keeps the name it arrived with, and
one ending `.html` served by its name would run as a page on the surface's own origin; one placed by hand in another
format is still shown, as its thumbnail is.

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
- **WHEN** two batches hold different images of one source, flow, version and seed
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

### Requirement: A version says what it was, and Compare shows a seed's two versions

The system SHALL head each image's large view with its approval version, the version it came from, read from its
producer, naming it a revision when its fields differ from that version's and a re-roll when only its count or seeds
do, and the approval's time, count and seeds. A large view whose seed is rendered under an older version of the same
source and flow SHALL offer Compare with the newest such version, showing both images at equal size, the fields that
changed, what changed in the count and seeds, and the tokens before and after.

The origin is already on disk, so nothing new records it. Same seed, same composition: the difference left is the
edit. The grid carries the images; the large view, which carries the sheet, carries what the version was.

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
