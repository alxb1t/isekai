## MODIFIED Requirements

### Requirement: A folder in the library is a batch when it holds `sources/`

The system SHALL list as a batch every folder in the library that holds `sources/`, SHALL list any other folder as
not a batch and open none of it, and SHALL list no dot-folder. Each batch's row SHALL carry its name, its source
count, for each flow the surface offers that is present the counts approved and rendered out of the sources that have
that flow, the count of sources with no flow, and the time and kind of the newest file written in it. Batches SHALL be
ordered by that time, newest first, and folders that are not batches after them.

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

## REMOVED Requirements

### Requirement: The hub shows each source's stage in each tracked flow, read from the run directory

**Reason:** the hub's columns are now the flows the surface offers, and a tick writes; a requirement's title and its
claim that the hub writes nothing both change.

**Migration:** see *The hub shows each source's stage in each offered flow, and a tick assigns it*, which keeps every
scenario key.

## ADDED Requirements

### Requirement: The hub shows each source's stage in each offered flow, and a tick assigns it

The system SHALL show a batch's hub as a grid of its sources by the flows the surface offers, each cell carrying the
stage read from that run's directory — no flow, assigned, tagged, sheet, draft, approved or rendered — and SHALL
ignore any other flow's directory. A cell whose run file cannot be read SHALL show that it is unreadable, with the
refusal the pipeline raised, and the rest of the grid SHALL still be shown. Reading the hub SHALL write nothing; a
tick SHALL write only through the assigning verb, and an untick only while the cell is assigned. A source imported
as it is, still carrying metadata, SHALL be marked on its row.

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

### Requirement: Prepare runs what changed as one job, and refuses before it starts when Ollama does not answer

The system SHALL run Prepare as one job over every assigned cell with no sheet: for each flow, the tagging, reading
and sheet stages, each one invocation of the pipeline's own verb over that flow's cells. Only one job SHALL run at a
time; a job SHALL keep running when its page closes; Stop SHALL interrupt the current stage and start no other; and
stopping the surface SHALL interrupt a running job. Before any stage starts, the surface SHALL check that the local
model server answers, and SHALL refuse with its message, starting nothing, when it does not.

The pipeline's verb is the one path, so Prepare is exactly what the verbs do. A refusal before the start leaves every
cell assigned, so pressing Prepare again is the whole fix.

#### Scenario: Prepare runs each stage over the assigned cells
- **Key:** `ui:prepare:prepare-runs-the-assigned-cells`
- **Layers:** e2e
- **WHEN** Prepare is pressed with cells assigned
- **THEN** each cell reaches sheet
- **AND** no cell outside the assignment changes

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

### Requirement: The page is told of a job as it runs

The system SHALL serve an event stream that, on every connection, sends a snapshot of the job slot and, when a batch
is named, that batch's hub, and then sends each change as the job's stages report it.

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
