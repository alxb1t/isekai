## MODIFIED Requirements

### Requirement: An approved input is read-only on the surface until it is re-opened

The system SHALL present an input whose flow has an approved artifact and no later draft as not editable,
SHALL refuse a draft update against such an input, and SHALL state on the page that the input is approved
and when, naming no file. Where a draft numbered above the approved artifact's `approved_from`
exists, the system SHALL present the input as **re-opened**: editable, its approval still
stated.

`review --flow F --new-version` writes a new numbered draft from the approved copy, and the surface shows that
state as its own rather than as something it is not: re-opened is a third status, and the approved artifact is
never edited in place in either case. The library counts every approval the run directories hold; Review's rail
holds the sheets not yet rendered and the one open, and its footer counts the approved among them.

#### Scenario: a draft update against an approved input is refused
- **Key:** `ui:approval:approved-input-refuses-a-draft-update`
- **Layers:** unit
- **WHEN** a draft update is submitted for an input whose flow is approved and holds no later draft
- **THEN** it is refused
- **AND** no file in the run directory is created, changed or removed

#### Scenario: an input approved in an earlier sitting opens read-only
- **Key:** `ui:approval:approved-input-opens-read-only`
- **Layers:** unit
- **WHEN** the surface serves an input whose flow has an approved artifact and no draft
- **THEN** the sheet it shows is the approved artifact's
- **AND** the input is presented as not editable

#### Scenario: an input re-opened with a new version is editable again
- **Key:** `ui:approval:a-re-opened-input-is-editable`
- **Layers:** unit
- **WHEN** the surface serves an input whose flow has an approved artifact and a draft numbered above the
  version that artifact records as its origin
- **THEN** the sheet it shows is the draft's
- **AND** the input is presented as editable
- **AND** a draft update against it is accepted

#### Scenario: a re-opened input is not counted as approved
- **Key:** `ui:approval:a-re-opened-input-is-not-counted-approved`
- **Layers:** unit
- **WHEN** the collection is read while one of its inputs is re-opened
- **THEN** that input's reported status is neither approved nor a plain draft
- **AND** the collection's approved count agrees with what the run directories hold
- **AND** Review's footer counts the approved among the rail's sheets, the re-opened one included

#### Scenario: a stale lower draft does not re-open an approved input
- **Key:** `ui:approval:a-stale-lower-draft-does-not-reopen`
- **Layers:** unit
- **WHEN** the surface serves an input whose flow has an approved artifact and a draft numbered below it
- **THEN** the sheet it shows is the approved artifact's
- **AND** the input is presented as not editable, naming no draft

#### Scenario: an update that overlaps an approval is refused
- **Key:** `ui:approval:an-update-overlapping-an-approval-is-refused`
- **Layers:** unit
- **WHEN** a draft update is in flight while the same input is approved
- **THEN** the update is refused once the approval has written
- **AND** the approved artifact is the one the approval wrote

### Requirement: Both tag lists are shown beside the prose, read-only, and neither is editable there

The system SHALL show, beside the caption, the scored list the local tagger produced and the
committable tags the hosted tagger offered, and SHALL make neither list a way to change a sheet.

**The two lists are narrowed differently, and the asymmetry is measured rather than chosen.** The local
tagger is scored against the vocabulary it emits, so every tag it returns is committable by
construction and all of them are shown, with the confidence beside each — a wrong tag sorted below a
right one refutes itself. The hosted tagger free-associates: on the acceptance collection roughly nine in
ten of its tags were outside the vocabulary, could not be committed to any field, and the operator's
verdict was that only the marked ones carried any value. So its list is **filtered to what the
vocabulary carries** before it is shown.

**Filtered on the way to the page, never on the way to disk.** The artifact keeps every tag the model
returned — that is `tagging`'s requirement and it is untouched — because narrowing what is *stored*
would make the record disagree with what the model said, and the reason the artifact exists is to be
able to look behind the sorter. What changes is only which of those tags the surface spends the
operator's attention on.

#### Scenario: the local list is shown whole and the hosted list is shown filtered
- **Key:** `ui:source:both-tag-lists-are-shown-raw-and-read-only`
- **Layers:** unit
- **WHEN** an input whose tag artifacts contain tags outside the flow's vocabulary is opened
- **THEN** every tag the local tagger scored is present in the response the surface renders
- **AND** only the hosted tags the vocabulary contains are present in it
- **AND** no interaction on either list writes to a draft

#### Scenario: filtering the panel does not filter the artifact
- **Key:** `ui:source:the-artifact-keeps-what-the-panel-drops`
- **Layers:** unit
- **WHEN** a hosted tag outside the vocabulary is withheld from the payload
- **THEN** that tag is still present in the stored artifact, unchanged

### Requirement: A missing caption is shown with the command that writes it

The system SHALL, when an input's flow holds no caption, show in the source pane the caption of the flow its
sheet's tags came from, named as that flow's, and else that there is none and the command that writes it, naming
the flow, the run and the runs root. It SHALL NOT refuse to open the surface for
the absence.

**The prose is the one artifact a skipped verb leaves missing on a page under review.** The tag lists keep
their silence: a list is missing because a tagger failed, because the run predates it, or because the flow
declares no tagger. Skipping `tag` never reaches review, because the sheet refuses without a tag list the
flow declares.

The caption is now its own verb and nothing downstream needs it, so an input can reach review having never
been read. A blank pane cannot be told from a photograph with nothing to say, and the one-verb design kept
the caption bundled for exactly that reason; naming the command keeps the reason without the bundle.

The server builds the command, as it builds every other command a refusal prints, and it names the run and its
runs root so it works when pasted: a collection's runs root in the library is never the default.

#### Scenario: an input with no caption names the command that writes it
- **Key:** `ui:source:a-missing-caption-names-its-command`
- **Layers:** unit
- **WHEN** an input whose flow holds no caption is opened
- **THEN** the payload carries no prose and the command that writes it, naming the flow, the run and the runs root
- **AND** the surface serves the input without a refusal

#### Scenario: a sheet filled from another flow's tags shows that flow's caption
- **Key:** `ui:source:a-borrowed-sheet-shows-its-sources-caption`
- **Layers:** unit
- **WHEN** an input is opened whose flow holds no caption and whose sheet names another flow's tags
- **THEN** the payload carries that flow's caption prose and names that flow
- **AND** it carries no command

### Requirement: The surface serves one library, from a verb that takes no arguments

The system SHALL serve the browser surface from a subcommand that takes no flow, no input and no runs root, over one
library directory named by `ISEKAI_LIBRARY` and defaulting to `~/isekai`, creating it when absent. It SHALL refuse,
before binding a port, a library inside the repository's working tree that is not under the ignored data root, and a
library it cannot create, naming the remedy.

The library is where the app keeps every collection, so the operator never types a path. Its collections hold copies of
photographs, so the rule that keeps a runs root out of what git tracks holds for the library too
([D18](../../../docs/decisions.md#d18--runs-stay-out-of-what-git-tracks)).

```
~/isekai/                      the library
  <collection>/ sources/ runs/ log.txt
  .staging/                    a dot-folder: never listed
```

#### Scenario: the verb takes no arguments
- **Key:** `ui:library:the-verb-takes-no-arguments`
- **Layers:** unit
- **WHEN** the surface's subcommand is given a flow, an input or a runs root
- **THEN** the invocation is refused at parse time

#### Scenario: an absent library is created
- **Key:** `ui:library:an-absent-library-is-created`
- **Layers:** unit
- **WHEN** the surface starts and the library directory does not exist
- **THEN** it is created before the address is printed

#### Scenario: a library git can reach is refused
- **Key:** `ui:library:a-library-git-can-reach-is-refused`
- **Layers:** unit
- **WHEN** the library resolves inside the working tree and outside the ignored data root
- **THEN** the surface refuses before binding a port
- **AND** the message names the variable that moves it

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
them, `↵` opening an image's large view; a tagged or unreadable cell SHALL do nothing. A cell holding images SHALL show
every one of them, oldest to newest, each marked with its version. A source's cell SHALL be the grid's first column,
reached by `h` and `←`, and `↵` there SHALL open its photograph in the viewer, stepping through the collection's
sources. The hub SHALL keep its focus across a large view, the Back button and a switch of tabs. The header SHALL leave
a 12 px gap between items.

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
- **WHEN** a rendered cell is clicked, then `↵` is pressed in the viewer
- **THEN** the viewer opens on its newest image, then that image's large view
- **AND** `Esc` returns to the hub, focused on that cell

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
staged folder.

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
- **THEN** Add files…, Import and Cancel are disabled
- **AND** `Esc` leaves the sheet open

#### Scenario: leaving the screen mid-commit keeps the staged folder
- **Key:** `ui:sheet:leaving-mid-commit-keeps-the-folder`
- **Layers:** unit
- **WHEN** the sheet closes while Import's commit is in flight
- **THEN** its staging folder is not cancelled
- **AND** a commit refused after it closes cancels the folder

### Requirement: Prepare runs what changed as one job, and refuses before it starts when Ollama does not answer

The system SHALL run Prepare as one job over every assigned cell with no sheet: for each flow, the tagging, reading and
sheet stages, each one invocation of the pipeline's own verb over that flow's cells. One job of each kind, a Prepare and
a render, SHALL run at a time, the two side by side in any collections; a job SHALL keep running when its page closes;
Stop SHALL interrupt the current stage of the job it names and start no other, leaving the other job running; stopping
the surface SHALL interrupt every running job; each line a job's verbs write to the collection's log SHALL name its job;
and a stage that fails having reported nothing SHALL end the job as failed, naming the collection's log, and start no
other. Before any stage starts, the surface SHALL check that the local model server answers, and SHALL refuse with its
message, starting nothing, when it does not. While Prepare runs, the job strip and Prepare bar SHALL show completed
cells out of the accepted total and elapsed time; the total SHALL stay fixed, a cell SHALL count as completed only at
sheet, and elapsed time SHALL tick every second.

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
- **THEN** each cell counts once in the fixed total and only cells reaching sheet count as completed
- **AND** a repeated completion never increments the count again

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

### Requirement: The page is told of a job as it runs

The system SHALL serve an event stream that, on every connection, sends a snapshot of both job slots, the Prepare and
the render, and, when a collection is named, that collection's hub, and then sends each change as the job's stages
report it. A running Prepare snapshot SHALL carry its accepted total, completed count and start time. A hub opened while
the slot holds its collection's failed Prepare SHALL show that job's message until Discard on that collection's hub
dismisses it in that page. A page SHALL hold one event stream, naming the collection its screen shows and the import it
has open, and SHALL open it again when either changes. When the surface stops, its streams SHALL end before the server's
graceful wait expires, without cancellation errors; a terminal interrupt SHALL exit quietly after cleanup.

A reload or a second tab gets the whole truth at once; a job's progress reaches the page as the verbs report it. A
job outlives its page, so a failure that happened while no page was open is still told. Every connect brings a
snapshot, so a stream opened again loses nothing, and one connection a page leaves the browser's others free.

#### Scenario: a connection starts with a snapshot
- **Key:** `ui:events:a-connection-starts-with-a-snapshot`
- **Layers:** unit
- **WHEN** the stream is opened for a collection
- **THEN** its first event carries both job slots and that collection's hub

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
- **WHEN** a hub opens while the slot holds its collection's failed Prepare
- **THEN** the Prepare bar shows the job's message
- **AND** once Discard dismisses it, a hub opened again in that page does not

#### Scenario: one stream follows the batch and the import
- **Key:** `ui:events:one-stream-follows-the-batch-and-the-import`
- **Layers:** unit
- **WHEN** a page opens a collection, then an import inside it
- **THEN** it holds one stream, opened again naming the collection and then the import too
- **AND** the stream it closed is the only other one it opened

#### Scenario: a job event fills its kind's slot
- **Key:** `ui:events:a-job-event-fills-its-kinds-slot`
- **Layers:** unit
- **WHEN** a render's event arrives while a Prepare runs
- **THEN** the page holds both jobs, each in its own slot

### Requirement: Render is confirmed in a dialog that quotes what renders, its limit and its price at most

The system SHALL offer Render from a bar on a collection's hub and its Renders view that counts the images short of
their approvals' counts, and SHALL show no such bar when none is short and no count is refused, nor on the hub while
changes wait for Prepare. The bar SHALL be disabled, with its reason, when a render runs, when a pod may still be
billing, when no RunPod key is in the surface's environment, and when an approval's count is refused. It SHALL open a
dialog listing per offered flow the images that will render and what is left out, with the reason, the session's
estimate and limit, and its price at most — the limit at the hourly maximum `gpunit.toml` names, with the volume at its
configured rate. Its confirmation SHALL be the only act that rents; the dialog SHALL hold no URL, and SHALL close when
its page is left, and the confirmation SHALL close it and open the session drawer over the page. The confirmation SHALL
carry the limit and the number of images the dialog showed, and SHALL be refused, starting nothing, when the
collection's quote taken again has a longer limit or another number of images. The bar SHALL show the newest offer asked
for, whatever order the answers arrive in.

The quote is what the operator agrees to; gpunit refuses a card above the hourly maximum, so the price is a bound and
not a guess. A reload never reopens a confirmation that spends; a changed image total or longer limit requires
a fresh confirmation, even where the limit sits at its floor or cap. An equal-total change of sources or approvals
is outside that comparison. A bar that is absent needs no reason, and one forward action holds the screen's accent;
a refused count keeps the bar, so the refusal is never silent.

#### Scenario: the dialog lists what renders per flow
- **Key:** `ui:render:the-dialog-lists-what-renders`
- **Layers:** unit
- **WHEN** a collection's quote is asked for with approvals short of their count in two flows
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
- **WHEN** every approval in a collection already has its count of images
- **THEN** the collection's Render offer counts no image
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
- **WHEN** a collection's only approval short of its count holds a count no render takes
- **THEN** its Render offer counts no image and carries the refusal, naming the file
- **AND** the Render bar shows, disabled, with its reason

#### Scenario: the confirmation starts the render
- **Key:** `ui:render:the-confirmation-starts-the-render`
- **Layers:** e2e
- **WHEN** the dialog's Render is confirmed
- **THEN** the session drawer opens over the hub, which keeps its URL
- **AND** the dialog is closed

#### Scenario: a quote that has grown is refused
- **Key:** `ui:render:a-grown-quote-is-refused`
- **Layers:** unit
- **WHEN** Render is confirmed with a shorter limit, or fewer images, than the collection's quote now gives
- **THEN** the confirmation is refused, naming that the quote changed
- **AND** no job starts

#### Scenario: a stale offer is dropped
- **Key:** `ui:render:a-stale-offer-is-dropped`
- **Layers:** unit
- **WHEN** an older offer request is answered after a newer one
- **THEN** the bar keeps the newer offer

### Requirement: The render job opens the volume, renders, and closes the volume unless kept

The system SHALL run a render as one job: the volume window opened or extended, then the rendering verb with the
session's limit, its id and its progress, then the window closed unless the operator kept it open. A lost answer from
the window's opening SHALL render nothing and raise the volume alert, and an opening that raises SHALL mark its step
failed; a failed close SHALL raise it too. A job whose verb cannot be started SHALL end failed, naming the collection's
log, and still close the window. Stop SHALL interrupt the rendering verb, which tears its pod down. The surface
stopping SHALL do the same, and SHALL wait for the pod's teardown and the window's close before it exits, for at most
the teardown's estimate and one volume verb, saying so on its terminal as the wait begins. After that wait, a window
not kept whose close has failed or remains unfinished SHALL cause the terminal to name the command that closes it,
even when the worker has ended; kept and successfully closed windows SHALL need no close remedy. An interrupt at the
surface's terminal SHALL reach no child of the job.

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
- **THEN** the job ends failed, naming the collection's log
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

#### Scenario: an opening that raises fails its step
- **Key:** `ui:render-job:an-opening-that-raises-fails-its-step`
- **Layers:** unit
- **WHEN** opening the window raises
- **THEN** the job ends failed and the volume step reads failed

### Requirement: The Renders view shows each source's images by flow and version

The system SHALL list a collection's images by source and offered flow, each cell's approval versions newest first, and
SHALL show them as a grid of sources by flows, each cell one row of its images, its versions oldest to newest, each
image marked with its version, and open an image's large view, with the sheet it was rendered from, from any of them.
A cell whose newest approval lacks images of its count SHALL carry the number it lacks, as the render stage counts
it. Each source SHALL show its photograph's thumbnail, upright, opening the photograph in a viewer, its cell the
grid's first column, reached by the keys and opened by `↵`. `Esc` on a large
view SHALL return to the screen it was opened from, focused on the image it closed, and Renders SHALL keep its focus
across the Back button and a switch of tabs. It SHALL mark an approval it cannot read as damaged, naming the
file, and show every image, that version's own among them; and SHALL refuse an address whose version is not `v` and
ASCII digits. It SHALL serve each thumbnail, a render's or a source's, from a cache in the library's `.cache/`, made
on first request and named by the image's own bytes. It SHALL refuse an image it cannot read, one past Pillow's pixel
bound among them, naming the file. It SHALL serve a photograph, a source or a run's copy, as the image its bytes are,
whatever its name ends in, and a source in a format the render does not read as an upright JPEG of it.

The images come back to where the sheets were decided, version by version in the order they were approved; a cache the
library can lose costs only its rebuild. Two collections can hold one source rendered at one seed, so only the bytes say
which image a thumbnail shows. One damaged file costs only its own version, never the collection's page. The count a
cell lacks is the render stage's own, so the page and the render agree on what is ready. A source keeps the name it
arrived with, and one ending `.html` served by its name would run as a page on the surface's own origin; one placed by
hand in another format is still shown, as its thumbnail is.

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
- **AND** `Esc` returns to the grid focused on that image
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

### Requirement: Conjure from this drafts from an image's approval, and opens Review on it

The system SHALL offer, on an image's large view, one action per target — each flow the surface offers that reads a
sheet alone, other than the image's own, assigned or not — named *Conjure from this* for `conjure-anime-wai`, the first
on `⇧F`. It SHALL draft the target of the image's run from the approval the image was rendered under, naming the image,
as the review verb's `--from` does — assigning it and filling its sheet first where it holds none — then open Review on
that draft; where the target holds a waiting draft with edits of its own, it SHALL write nothing and open Review on that
draft; a refusal SHALL show on the large view, and write nothing. On such a draft, approved or not, Review SHALL show
the image it records beside the photograph as it shows a revision's, headed by its flow, version and seed, mark each
field that differs from the target's sheet and name the source flow and approval in the sheet's kicker, and on the draft
offer *Discard draft*.

```
large view · summon-anime-wai v1 · seed 7     [ Conjure from this ⇧F ]
        │ drafts conjure-anime-wai from summon-anime-wai v1
        ▼
Review · conjure-anime-wai   ③ SHEET — FROM SUMMON-ANIME-WAI V1   hair_colour  was …
```

The image the operator approved is where the next flow starts. A flow that reads a photograph has its own sheet of
the person, so it is no target. The press assigns, so no tick and no Prepare come first; an edited draft is the
work in hand. The marks show what the source changed, so the operator reads only the fields the
target adds.

#### Scenario: the large view names its targets
- **Key:** `ui:conjure-from:the-large-view-names-its-targets`
- **Layers:** unit
- **WHEN** a summon image's large view is read in a collection where no source is assigned conjure
- **THEN** its targets are conjure alone

#### Scenario: a refused draft writes nothing
- **Key:** `ui:conjure-from:a-refused-draft-writes-nothing`
- **Layers:** unit
- **WHEN** a draft is asked from an approval version the source does not hold
- **THEN** it is refused naming that version
- **AND** no file is written

#### Scenario: a waiting edit is opened
- **Key:** `ui:conjure-from:a-waiting-edit-is-opened`
- **Layers:** unit
- **WHEN** a draft is asked for a target whose waiting draft has edits of its own
- **THEN** it answers with that draft and writes nothing

#### Scenario: an approved draft keeps its marks
- **Key:** `ui:conjure-from:an-approved-draft-keeps-its-marks`
- **Layers:** unit
- **WHEN** Review reads the approval of a draft written from another flow's approval
- **THEN** it names the source flow and approval, and carries the target sheet's fields

#### Scenario: Review reads the draft against the target's sheet
- **Key:** `ui:conjure-from:review-reads-the-draft-against-the-sheet`
- **Layers:** unit
- **WHEN** Review reads a draft written from another flow's approval
- **THEN** it names the source flow and approval, and carries the target sheet's fields

#### Scenario: Conjure from this opens Review on the draft
- **Key:** `ui:conjure-from:conjure-from-this-opens-review`
- **Layers:** e2e
- **WHEN** `⇧F` is pressed on a summon image whose source is not assigned conjure
- **THEN** Review opens on conjure's draft, its kicker naming the summon approval
- **AND** a field summon changed is marked against conjure's sheet
- **AND** its caption pane shows summon's caption, named as summon's, and the summon image stands beside the photograph

### Requirement: A dialog holds the focus while it is open

The system SHALL open every confirming dialog — Render, Revise, and New collection or Add sources — as a modal dialog,
the page behind it inert, the focus on its first control and held inside it, and SHALL return the focus to where it
was when it closes. The Render dialog's first control SHALL be *Keep the volume open*, which `Space` toggles and
`↵` leaves alone; the Revise dialog's SHALL be its confirm button.

A key goes where the eye is. A dialog over a grid that leaves the focus on the grid sends `↵` and `Tab` to what it
covers; and only `Mod+↵` spends money, so `↵` on the checkbox never renders.

#### Scenario: the Render dialog opens on its checkbox
- **Key:** `ui:dialogs:the-render-dialog-opens-on-its-checkbox`
- **Layers:** e2e
- **WHEN** the Render dialog opens on the hub, then `Tab` is pressed until the focus has passed every control
- **THEN** *Keep the volume open* held the focus first, and the focus never left the dialog
- **AND** `Esc` returns the focus to the hub cell it left

### Requirement: The running render opens in a drawer every screen offers

The system SHALL show the running render in a session drawer: a modal dialog over half the window, at least 480 px wide,
on the right, over a dark backdrop, holding no URL. `⌃;` SHALL open and close it on every screen, from a field too, and
the running render's link SHALL open it; confirming a render SHALL open it, and a render started from the terminal SHALL
open nothing. It SHALL read the running render's record, live while it runs, with the volume steps and Stop the job
adds; after it ends it SHALL show that session's outcome, its images and its time until the app reloads or another
render starts; with neither it SHALL say no render runs. Its images SHALL be a grid: a column for each photograph the
session was asked to render, a row for each flow, the photographs' row at the foot, a cell holding that flow's images of
that photograph and a waiting tile for each still to come, drawn at the tile size Renders draws and moved through by `h
j k l` and the arrows. `↵` SHALL open the focused row in the viewer over the drawer, which SHALL follow its list when it
changes while open; `⇧I` SHALL close the drawer and open its collection's Renders. A click on the backdrop, `⌃;` and
`Esc` SHALL close it, `Esc` closing the viewer first.

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
- **WHEN** a terminal render runs without an app job slot
- **THEN** its record reads running and the global running-session read names its collection and id
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

## REMOVED Requirements

### Requirement: A folder in the library is a batch when it holds `sources/`

**Reason**: a library folder is a collection; the requirement is renamed in that word.

**Migration**: the requirement holds, unchanged but for the word, under its new title, *A folder in the library is a collection when it holds `sources/`*.

### Requirement: Every screen has a URL naming its batch and its run

**Reason**: a library folder is a collection; the requirement is renamed in that word.

**Migration**: the requirement holds, unchanged but for the word, under its new title, *Every screen has a URL naming its collection and its run*.

### Requirement: Review opens a batch at its own address, lists every unrendered sheet, and Approve stays on the sheet

**Reason**: a library folder is a collection; the requirement is renamed in that word.

**Migration**: the requirement holds, unchanged but for the word, under its new title, *Review opens a collection at its own address, lists every unrendered sheet, and Approve stays on the sheet*.

## ADDED Requirements

### Requirement: A folder in the library is a collection when it holds `sources/`

The system SHALL list as a collection every folder in the library that holds `sources/`, SHALL list any other folder as
not a collection and open none of it, and SHALL list no dot-folder. Each collection's row SHALL carry its name, its
source count, the names of its first fifteen sources, whose thumbnails it shows, for each flow the surface offers that
is present the counts approved and rendered out of the sources that have that flow, the count of sources with no flow,
and the time and kind of the newest file written in it. Collections SHALL be ordered by that time, newest first, and
folders that are not collections after them. Home SHALL carry New collection at the right of the library's header row,
and on an empty library below the privacy line. Count labels on the surface SHALL use a singular noun at one and a
plural noun otherwise.

A folder is a collection by its layout alone, so no marker file can disagree with what is on disk, and the row is a
listing read on every request. A folder that is not a collection is shown rather than hidden so the screen matches the
folder, and nothing in the app writes into it. The flows the surface offers are named in its configuration; a flow
approved from another's sheet stays the CLI's. On first start the privacy line is read before the first import.

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

#### Scenario: first start shows New collection under the privacy line
- **Key:** `ui:batch-folder:first-start-shows-new-batch-under-the-privacy-line`
- **Layers:** e2e
- **WHEN** Home opens on an empty library
- **THEN** New collection sits below the privacy line

### Requirement: Every screen has a URL naming its collection and its run

The system SHALL give Home, a collection's hub, a collection's Review, a review of a source in a flow and the billing
alert's way out each its own URL, the session drawer holding none, SHALL name the collection in every URL inside one,
and SHALL name a run by the twelve-character digest its identifier begins with. A collection's Review SHALL open the
sheet Review starts from and put that sheet's URL in its place. It SHALL answer any of them on a fresh load, and SHALL
refuse one naming a collection or a run the library does not hold, naming the way back.

A reload, a second tab or a bookmark then lands where it was, never on whatever the server last held open. A run's
short name is a sanitised filename and can repeat; its digest cannot.

```
/                                       Home
/c/<collection>/hub                     the hub
/c/<collection>/review                  the head of Review, replaced by its sheet's URL
/c/<collection>/review/<digest>/<flow>  Review
/billing                                the billing alert's way out
```

#### Scenario: a reload lands on the same screen
- **Key:** `ui:routes:a-reload-lands-on-the-same-screen`
- **Layers:** e2e
- **WHEN** a hub, a review or a collection's Review address is loaded again
- **THEN** the same collection, source and flow are shown
- **AND** a collection's Review address is replaced by its head's sheet URL
- **AND** a collection with no sheet waiting says none waits

#### Scenario: a run is named by its digest
- **Key:** `ui:routes:a-run-is-named-by-its-digest`
- **Layers:** unit
- **WHEN** a review URL names a run
- **THEN** the run is the one whose identifier begins with that digest

#### Scenario: an unknown collection is refused with the way back
- **Key:** `ui:routes:an-unknown-batch-is-refused`
- **Layers:** e2e
- **WHEN** a URL names a collection the library does not hold
- **THEN** the page refuses, naming the collection
- **AND** it offers the way back to Home

### Requirement: Review opens a collection at its own address, lists every unrendered sheet, and Approve stays on the sheet

The system SHALL open a collection's Review on a chooser when two or more flows hold sheets to review: a row per flow,
its name, how many wait to be approved and how many lack images, and up to fifteen of its waiting photographs, then
`+n`; `j` `k` and the arrows SHALL move between rows, `↵` or a click on a row SHALL open that flow's head, and a click
on a photograph that sheet. With one such flow it SHALL open that flow's head: its first unapproved sheet in the hub's
order, else its first approved sheet whose newest approval lacks images of its count, read-only; with none, a page
saying no sheet waits for review, with the way to the hub. `Esc` on Review, with no overlay open and outside a field,
SHALL return to the chooser. The hub SHALL carry for each cell the number of images its newest approval lacks, as the
render stage counts it. Review's rail SHALL list every sheet of the flow that is unapproved or lacks images, each marked
untouched, edited, approved or re-opened, and its footer SHALL count the approved among them; the Review tab SHALL count
the unapproved, every flow's, and the rail's head SHALL name each other flow holding some, with how many and the key to
the chooser. Approve SHALL leave the sheet open and read-only, the approve bar naming the approval it shows, offering
*Cancel approve* while the review stage can cancel it, else the reason beside it, and while no render runs for the
collection; a cancel SHALL leave the sheet open on what the flow is left on: its draft, editable, or for a copy the
draft open above what lies beneath, else the approval beneath it, read-only. Opening a sheet that has no draft SHALL
write one through the review stage's own function, and opening it again SHALL write no second draft; a failure after
approval SHALL be shown in the approve bar, never dropped. ④ SHALL show one slot per image, a set seed or random, beside
the sheet rows. `⌃P` SHALL open the photograph in the viewer — on a revision or a draft from an image, *Side by side* —
from any pane and from a field, stepping through the rail's sheets, and `Esc` SHALL return the focus where it was.

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
