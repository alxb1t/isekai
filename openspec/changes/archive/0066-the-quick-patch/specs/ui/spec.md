## MODIFIED Requirements

### Requirement: A folder in the library is a batch when it holds `sources/`

The system SHALL list as a batch every folder in the library that holds `sources/`, SHALL list any other folder as
not a batch and open none of it, and SHALL list no dot-folder. Each batch's row SHALL carry its name, its source
count, for each flow the surface offers that is present the counts approved and rendered out of the sources that have
that flow, the count of sources with no flow, and the time and kind of the newest file written in it. Batches SHALL be
ordered by that time, newest first, and folders that are not batches after them. Count labels on the surface SHALL
use a singular noun at one and a plural noun otherwise.

A folder is a batch by its layout alone, so no marker file can disagree with what is on disk, and the row is a
listing read on every request. A folder that is not a batch is shown rather than hidden so the screen matches the
folder, and nothing in the app writes into it. The flows the surface offers are named in its configuration; a flow
approved from another's sheet stays the CLI's.

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

### Requirement: The hub shows each source's stage in each offered flow, and a tick assigns it

The system SHALL show a batch's hub as a grid of its sources by the flows the surface offers, each cell carrying the
stage read from that run's directory — no flow, assigned, tagged, sheet, draft, approved or rendered — and SHALL
ignore any other flow's directory. A cell whose run file cannot be read SHALL show that it is unreadable, with the
refusal the pipeline raised, and the rest of the grid SHALL still be shown. Reading the hub SHALL write nothing; a
tick SHALL write only through the assigning verb, and an untick only while the cell is assigned. A source imported
as it is, still carrying metadata, SHALL be marked on its row. The header SHALL leave a 12 px gap between items.

A stage is a directory listing, the rule every stage already follows, so the grid cannot drift from the disk, and a
tick survives a reload. The mark is read from the source itself, so no file records it.

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

### Requirement: Sources are chosen in the file dialog, and each shows its own upload

The system SHALL take sources through the browser's file dialog, sending each file in its own request, and SHALL show
for each its upload's progress, then its reading, then whether it is ready, converted, refused or not cleaned, with
the reason. Import SHALL stay disabled, with its reason, until every chosen file is read, and SHALL commit only the
ready files and those the operator chose to import as they are.

Each file's bar answers which one is slow; each reason sits on the file it concerns.

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

### Requirement: Prepare runs what changed as one job, and refuses before it starts when Ollama does not answer

The system SHALL run Prepare as one job over every assigned cell with no sheet: for each flow, the tagging, reading
and sheet stages, each one invocation of the pipeline's own verb over that flow's cells. Only one job SHALL run at a
time; a job SHALL keep running when its page closes; Stop SHALL interrupt the current stage and start no other;
stopping the surface SHALL interrupt a running job; and a stage that fails having reported nothing SHALL end the job
as failed, naming the batch's log, and start no other. Before any stage starts, the surface SHALL check that the
local model server answers, and SHALL refuse with its message, starting nothing, when it does not. While Prepare
runs, the job strip and Prepare bar SHALL show completed cells out of the accepted total and elapsed time; the total
SHALL stay fixed, a cell SHALL count as completed only at sheet, and elapsed time SHALL tick every second.

The pipeline's verb is the one path, so Prepare is exactly what the verbs do. A refusal before the start leaves every
cell assigned, so pressing Prepare again is the whole fix.

#### Scenario: Prepare runs each stage over the assigned cells
- **Key:** `ui:prepare:prepare-runs-the-assigned-cells`
- **Layers:** e2e
- **WHEN** Prepare is pressed with cells assigned
- **THEN** each cell reaches sheet
- **AND** no cell outside the assignment changes
- **AND** while it runs, the strip and bar show matching totals and ticking elapsed time across a reload

#### Scenario: a second job is refused while one runs
- **Key:** `ui:prepare:one-job-at-a-time`
- **Layers:** unit
- **WHEN** a job is asked for while another runs
- **THEN** it is refused naming the running job

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
- **THEN** the job ends as failed, naming the batch's log
- **AND** no later stage starts

#### Scenario: totals count cells rather than stage reports
- **Key:** `ui:prepare:totals-count-cells-not-stages`
- **Layers:** unit
- **WHEN** assigned cells report tagging, reading, sheet completion and a refusal
- **THEN** each cell counts once in the fixed total and only cells reaching sheet count as completed
- **AND** a repeated completion never increments the count again

### Requirement: The page is told of a job as it runs

The system SHALL serve an event stream that, on every connection, sends a snapshot of the job slot and, when a batch
is named, that batch's hub, and then sends each change as the job's stages report it. A running Prepare snapshot
SHALL carry its accepted total, completed count and start time. When the surface stops, its streams SHALL end before
the server's graceful wait expires, without cancellation errors; a terminal interrupt SHALL exit quietly after cleanup.

A reload or a second tab gets the whole truth at once; a job's progress reaches the page as the verbs report it.

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

### Requirement: Render is confirmed in a dialog that quotes what renders, its limit and its price at most

The system SHALL open, for a batch, a dialog listing per offered flow the images that will render and what is left
out, with the reason, the session's estimate and limit, and its price at most — the limit at the hourly maximum
`gpunit.toml` names, with the volume at its configured rate. Its confirmation SHALL be the only act that rents; the
dialog SHALL hold no URL. The confirmation SHALL carry the limit and the number of images the dialog showed, and SHALL
be refused, starting nothing, when the batch's quote taken again has a longer limit or another number of images.
Render SHALL be disabled, with its reason, when nothing is short of its count, when a job runs, when a pod may still
be billing, and when no RunPod key is in the surface's environment.

The quote is what the operator agrees to; gpunit refuses a card above the hourly maximum, so the price is a bound and
not a guess. A reload never reopens a confirmation that spends; a changed image total or longer limit requires
a fresh confirmation, even where the limit sits at its floor or cap. An equal-total change of sources or approvals
is outside that comparison.

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
- **THEN** Render is disabled, naming why

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

### Requirement: The render job opens the volume, renders, and closes the volume unless kept

The system SHALL run a render as one job: the volume window opened or extended, then the rendering verb with the
session's limit and its progress, then the window closed unless the operator kept it open. A lost answer from the
window's opening SHALL render nothing and raise the volume alert; a failed close SHALL raise it too. A job whose verb
cannot be started SHALL end failed, naming the batch's log, and still close the window. Stop SHALL interrupt the
rendering verb, which tears its pod down. The surface stopping SHALL do the same, and SHALL wait for the pod's
teardown and the window's close before it exits, for at most the teardown's estimate and one volume verb, saying so
on its terminal as the wait begins. After that wait, a window not kept whose close has failed or remains unfinished
SHALL cause the terminal to name the command that closes it, even when the worker has ended; kept and successfully
closed windows SHALL need no close remedy. An interrupt at the surface's terminal SHALL reach no child of the job.

The volume is the job's to open and to close, so no step depends on the operator remembering one, and a surface that
exits mid-render leaves no window billing that was not kept. The wait is bounded so a hung verb cannot hold the
surface forever; a stop that says nothing looks hung, and the kill it invites is the one exit that leaves a window
open.

#### Scenario: a render job opens, renders and closes
- **Key:** `ui:render-job:opens-renders-and-closes`
- **Layers:** unit
- **WHEN** a render job runs to its end with keep open unticked
- **THEN** the window is opened, the verb runs with the limit, and the window is closed, in that order

#### Scenario: a lost window opening renders nothing
- **Key:** `ui:render-job:a-lost-opening-renders-nothing`
- **Layers:** unit
- **WHEN** opening the window answers that the create's answer was lost
- **THEN** the rendering verb does not run
- **AND** the volume alert is raised

#### Scenario: a surface stopped mid-render still closes the window
- **Key:** `ui:render-job:a-stopped-surface-closes-the-window`
- **Layers:** unit
- **WHEN** the surface stops while a render job runs with keep open unticked
- **THEN** the window is closed after the pod's teardown, before the surface exits
- **AND** no gpunit verb shares the terminal's interrupt
- **AND** the surface says it waits, naming how long

#### Scenario: a stop that outlasts its wait names the fix
- **Key:** `ui:render-job:an-outlasted-stop-names-the-fix`
- **Layers:** unit
- **WHEN** the surface stops mid-render with its window not kept and teardown outlasts the wait
- **THEN** the surface names the command that closes the window

#### Scenario: a verb that cannot start fails the job
- **Key:** `ui:render-job:a-verb-that-cannot-start-fails-the-job`
- **Layers:** unit
- **WHEN** the rendering verb cannot be started after the window opens
- **THEN** the job ends failed, naming the batch's log
- **AND** the window is closed

#### Scenario: a failed close at stop names the fix
- **Key:** `ui:render-job:a-failed-close-at-stop-names-the-fix`
- **Layers:** unit
- **WHEN** the surface stops mid-render and the window close fails before the wait ends
- **THEN** the terminal names the command that closes the window even though its worker has ended

#### Scenario: a kept window needs no close remedy
- **Key:** `ui:render-job:a-kept-window-needs-no-close-remedy`
- **Layers:** unit
- **WHEN** the surface stops mid-render with the window kept
- **THEN** the pod is torn down and the window is left open without a close-remedy warning
