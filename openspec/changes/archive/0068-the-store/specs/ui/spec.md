## MODIFIED Requirements

### Requirement: Render is confirmed in a dialog that quotes what renders, its limit and its price at most

The system SHALL offer Render from a bar on a batch's hub and its Renders view that counts the images short of their
approvals' counts, and SHALL show no such bar when none is short and no count is refused, nor on the hub while changes
wait for Prepare. The bar SHALL be disabled, with its reason, when a job runs, when a pod may still be billing, when
no RunPod key is in the surface's environment, and when an approval's count is refused. It SHALL open a dialog
listing per offered flow the images that will render and what is left out, with the reason, the session's estimate
and limit, and its price at most — the limit at the hourly maximum `gpunit.toml` names, with the volume at its
configured rate. Its confirmation SHALL be the only act that rents; the dialog SHALL hold no URL. The confirmation
SHALL carry the limit and the number of images the dialog showed, and SHALL be refused, starting nothing, when the
batch's quote taken again has a longer limit or another number of images. The bar SHALL show the newest offer
asked for, whatever order the answers arrive in.

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

#### Scenario: a stale offer is dropped
- **Key:** `ui:render:a-stale-offer-is-dropped`
- **Layers:** unit
- **WHEN** an older offer request is answered after a newer one
- **THEN** the bar keeps the newer offer

### Requirement: The page is told of a job as it runs

The system SHALL serve an event stream that, on every connection, sends a snapshot of the job slot and, when a batch
is named, that batch's hub, and then sends each change as the job's stages report it. A running Prepare snapshot
SHALL carry its accepted total, completed count and start time. A hub opened while the slot holds its batch's failed
Prepare SHALL show that job's message until Discard on that batch's hub dismisses it in that page. A page SHALL hold
one event stream, naming the batch its screen shows and the import it has open, and SHALL open it again when either
changes. When the surface stops, its streams SHALL end before the server's graceful wait expires, without
cancellation errors; a terminal interrupt SHALL exit quietly after cleanup.

A reload or a second tab gets the whole truth at once; a job's progress reaches the page as the verbs report it. A
job outlives its page, so a failure that happened while no page was open is still told. Every connect brings a
snapshot, so a stream opened again loses nothing, and one connection a page leaves the browser's others free.

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

#### Scenario: one stream follows the batch and the import
- **Key:** `ui:events:one-stream-follows-the-batch-and-the-import`
- **Layers:** unit
- **WHEN** a page opens a batch, then an import inside it
- **THEN** it holds one stream, opened again naming the batch and then the import too
- **AND** the stream it closed is the only other one it opened

### Requirement: Sources are chosen in the file dialog, and each shows its own upload

The system SHALL take sources through the browser's file dialog, sending each file in its own request, and SHALL show
for each its upload's progress, then its reading, then whether it is ready, converted, refused or not cleaned, with
the reason. Import SHALL stay disabled, with its reason, until every chosen file is read, and SHALL commit only the
ready files and those the operator chose to import as they are. Each upload SHALL keep its own state, whatever its
name; an upload SHALL be refused once Import begins committing; and a file whose reading fails SHALL be refused
alone, the next file still read.

Each file's bar answers which one is slow; each reason sits on the file it concerns, so two files of one name are
two uploads. A file that lands while the folder is committed would be dropped from the batch unseen.

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
- **WHEN** Import is pressed on a new batch
- **THEN** the batch's hub opens with every source unassigned

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
- **AND** the committed batch is unchanged by it

#### Scenario: a failed read refuses its file alone
- **Key:** `ui:sheet:a-failed-read-refuses-its-file-alone`
- **Layers:** unit
- **WHEN** reading one uploaded file raises
- **THEN** that file is refused, naming why
- **AND** the next file is still read

### Requirement: The Renders view shows each source's images by flow and version

The system SHALL list a batch's images by source and offered flow, each cell's approval versions newest first, and
SHALL show them as a grid of sources by flows, each cell one row of its images, its versions oldest to newest, each
image marked with its version, and open an image's large view, with the sheet it was rendered from, from any of them.
A cell whose newest approval lacks images of its count SHALL carry the number it lacks, as the render stage counts
it. Each source SHALL show its photograph's thumbnail, upright, opening the photograph in a viewer. `Esc` on a large
view SHALL return to the screen it was opened from. It SHALL mark an approval it cannot read as damaged, naming the
file, and show every image, that version's own among them; and SHALL refuse an address whose version is not `v` and
ASCII digits. It SHALL serve each thumbnail, a render's or a source's, from a cache in the library's `.cache/`, made
on first request and named by the image's own bytes. It SHALL refuse an image it cannot read, one past Pillow's pixel
bound among them, naming the file. It SHALL serve a photograph, a source or a run's copy, as the image its bytes are,
whatever its name ends in, and a source in a format the render does not read as an upright JPEG of it.

The images come back to where the sheets were decided, version by version in the order they were approved; a cache the
library can lose costs only its rebuild. Two batches can hold one source rendered at one seed, so only the bytes say
which image a thumbnail shows. One damaged file costs only its own version, never the batch's page. The count a cell
lacks is the render stage's own, so the page and the render agree on what is ready. A source keeps the name it arrived
with, and one ending `.html` served by its name would run as a page on the surface's own origin; one placed by hand in
another format is still shown, as its thumbnail is.

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

#### Scenario: an image it cannot read is refused
- **Key:** `ui:renders:an-unreadable-image-is-refused`
- **Layers:** unit
- **WHEN** an image past Pillow's pixel bound is read for a thumbnail, or served whole
- **THEN** it is refused, naming the file
