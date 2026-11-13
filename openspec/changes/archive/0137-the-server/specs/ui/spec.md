## MODIFIED Requirements

### Requirement: A damaged run file or a malformed draft update is refused, never failed

The system SHALL answer a request that reads a run file lacking a key it needs, or holding one in the wrong shape,
with a refusal naming the file and its fix: the command that rewrites it, naming the runs root the surface serves
when that is not the default, or -- for an approved sheet, which no command rewrites -- the file to restore. It SHALL
refuse a draft update whose fields are not an object of lists of strings, naming the field, and SHALL NOT store a value
it did not accept. It SHALL NOT answer either with a server error.

The stages already refuse the same damage by name. A server error names nothing and offers no remedy, and a string
saved as its letters corrupts a draft without a word.

#### Scenario: a damaged file is refused by name
- **Key:** `ui:damage:a-damaged-file-is-refused-by-name`
- **Layers:** unit
- **WHEN** a draft, an approved sheet, a caption or a tag list the surface reads lacks a key it needs or holds it in
  the wrong shape
- **THEN** the request is refused naming the file and the command that rewrites it under the surface's runs root, or
  for an approved sheet the file to restore
- **AND** the surface keeps serving

#### Scenario: a malformed draft update is refused naming the field
- **Key:** `ui:damage:a-malformed-update-is-refused-naming-the-field`
- **Layers:** unit
- **WHEN** a draft update sends a field whose value is not a list of strings
- **THEN** the update is refused naming the field
- **AND** the draft on disk is unchanged

#### Scenario: a body of the wrong shape is refused naming what it lacks
- **Key:** `ui:damage:a-body-of-the-wrong-shape-is-refused-naming-what-it-lacks`
- **Layers:** unit
- **WHEN** a request to a route that reads a body sends one of the wrong shape, as a name that is no list or a
  count that is no object
- **THEN** it is refused naming what the body lacks, and not answered with a server error
- **AND** nothing is written or started for it

### Requirement: Prepare runs what changed as one job, and refuses before it starts when Ollama does not answer

The system SHALL run Prepare as one job over every assigned cell with no sheet: one invocation of the pipeline's own
`prepare` verb over those cells, which takes each photograph in turn through tagging, only when it is assigned a flow
that declares the tagger, then reading, then the sheet stage of each of its cells, so a photograph's cells reach sheet
while later photographs wait. One job of each kind, a Prepare and a render, SHALL run at a time, the two side by side
in any collections; a job SHALL keep running when its page closes; Stop SHALL interrupt the current stage of the job it
names and start no other, leaving the other job running; stopping the surface SHALL interrupt every running job; each
line a job's verb writes to the collection's log SHALL name its job; and a job whose verb fails having reported nothing
SHALL end as failed, naming the collection's log. Before any stage starts, the surface SHALL check that the local model
server answers, and SHALL refuse with its message, starting nothing, when it does not. While Prepare runs, the job
strip and Prepare bar SHALL show each stage's completed photographs or cells out of its asked total — `tag 3 of 3 ·
caption 2 of 3 · sheet 0 of 6 · 00:35` — the bar as wide as the stages done over the stages asked; each total SHALL
stay fixed, a photograph or a cell SHALL count once per stage it completes and a refused one in none, a cell unticked
while the job runs among them, and elapsed time SHALL tick every second. Before it runs, the Prepare bar SHALL name how
many photographs it prepares in its collection, `2 photographs to prepare in <collection>`, its button the changes.

The pipeline's verb is the one path, so Prepare is exactly what the verbs do. A photograph's description is every
flow's, so it is tagged and read once, whatever flows it is assigned to, and one already described costs its verbs
nothing. Each photograph is taken end to end, so its sheet is ready for review while the rest prepare; no route waits
on Prepare. Prepare runs on the local models and a render on a rented GPU, and they write no file in common, so
neither waits for the other. A refusal before the start leaves every cell assigned, so pressing Prepare again is the
whole fix.

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

#### Scenario: a job of a kind is accepted once the one before it has ended
- **Key:** `ui:prepare:a-job-follows-an-ended-one`
- **Layers:** unit
- **WHEN** a job is asked for after the job before it of its kind has ended
- **THEN** it starts and runs

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
- **WHEN** the job's verb exits in failure having reported no item
- **THEN** the job ends as failed, naming the collection's log
- **AND** no later stage starts

#### Scenario: totals count cells rather than stage reports
- **Key:** `ui:prepare:totals-count-cells-not-stages`
- **Layers:** unit
- **WHEN** assigned photographs report tagging and reading, their cells sheet completion, and one a refusal
- **THEN** tagging and reading count once per photograph and the sheet once per cell, against fixed totals
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

#### Scenario: a photograph is described once
- **Key:** `ui:prepare:a-photograph-is-described-once`
- **Layers:** unit
- **WHEN** Prepare is planned over a photograph assigned two flows
- **THEN** the job is one invocation of `prepare` naming each of its cells once
- **AND** tagging and reading are each asked once for it, and each flow's sheet stage once

#### Scenario: each photograph in turn
- **Key:** `ui:prepare:each-photograph-in-turn`
- **Layers:** unit
- **WHEN** Prepare is planned over two photographs, the second assigned a flow the first is not
- **THEN** its one invocation names every cell of the first photograph before any cell of the second

#### Scenario: Prepare takes the cells with no sheet and no other
- **Key:** `ui:prepare:prepare-takes-the-cells-with-no-sheet`
- **Layers:** unit
- **WHEN** Prepare is planned over a hub whose cells are assigned, tagged, sheeted and unreadable
- **THEN** it names the assigned and the tagged cells
- **AND** it names no sheeted cell and no unreadable one

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
snapshot of the slots and the hub, so a stream opened again loses no job and no cell's stage; a cell's running mark
and its refusal arrive only as they happen, so a stream opened after them lacks them until that cell next changes.
One connection a page leaves the browser's others free.

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

#### Scenario: a stream sends only its collection's cells
- **Key:** `ui:events:a-stream-sends-only-its-collections-cells`
- **Layers:** unit
- **WHEN** a stream is open for a collection and a cell of another collection changes
- **THEN** the stream does not send that cell
- **AND** it sends the job and the cells of its own collection that follow

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
surface's terminal SHALL reach no child of the job. A window opening or a rendering verb that gpunit refuses for no
card in stock or no card that fits SHALL end the job failed, its message leading with that kind, then quoting gpunit's
`refused:` line and naming the collection's log.

The volume is the job's to open and to close, so no step depends on the operator remembering one, and a surface that
exits mid-render leaves no window billing that was not kept. The wait is bounded so a hung verb cannot hold the
surface forever; a stop that says nothing looks hung, and the kill it invites is the one exit that leaves a window
open. gpunit's exit says the kind and its `refused:` line says why, so the message tells a wait for stock from a
configuration to edit, and the log holds each card gpunit skipped.

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

#### Scenario: a failed close raises the volume alert
- **Key:** `ui:render-job:a-failed-close-raises-the-volume-alert`
- **Layers:** unit
- **WHEN** a render ends and closing the window fails
- **THEN** the volume alert is raised
- **AND** the job's volume down step reads failed

#### Scenario: the verb's lines are the session's steps and images
- **Key:** `ui:render-job:the-verbs-lines-are-the-sessions-steps`
- **Layers:** unit
- **WHEN** the rendering verb prints a step line and an image line, then exits in failure
- **THEN** the session holds that step's state and that image's digest, flow, version and seed
- **AND** the job ends failed, its message naming the verb's exit and the collection's log

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

#### Scenario: a refusal for stock or fit names its kind and gpunit's reason
- **Key:** `ui:render-job:a-refusal-names-its-kind-and-reason`
- **Layers:** unit
- **WHEN** opening the window, or the rendering verb, is refused for no card in stock or no card that fits
- **THEN** the job ends failed, its message leading with that kind and quoting gpunit's `refused:` line
- **AND** the message names the collection's log

### Requirement: Billing state is read from gpunit's own records

The system SHALL show a pod as possibly billing when gpunit holds a pod record or a pending create while no session
runs, SHALL ask gpunit for its status only on start, every half minute while a session runs or an alert is open, and
on Check again, and SHALL clear an alert only when gpunit confirms the pod or volume gone. It SHALL offer the alert's
way out on its own page, `/billing`, which the alert band opens. It SHALL show an open volume as a quiet item until
the end gpunit recorded for its window, and as the alert band after it. The page SHALL show unknown billing while
its first snapshot is pending and an open volume while one is recorded; it SHALL say nothing is billing only when
both pod and volume are known absent.

gpunit already records what it created; reading those records adds no state to disagree with them. Idle, the surface
reaches nothing.

#### Scenario: a pod record without a session is an alert
- **Key:** `ui:billing:a-pod-record-is-an-alert`
- **Layers:** unit
- **WHEN** gpunit holds a pod record and no session runs
- **THEN** the pod alert is shown
- **AND** Render is disabled

#### Scenario: an alert clears only on gpunit's word
- **Key:** `ui:billing:an-alert-clears-on-evidence`
- **Layers:** unit
- **WHEN** Check again is asked for and gpunit still reports the pod
- **THEN** the alert stays

#### Scenario: gpunit is asked while a session runs or an alert is open
- **Key:** `ui:billing:gpunit-is-asked-while-a-session-or-an-alert-is-open`
- **Layers:** unit
- **WHEN** the surface starts, and then a session runs, and then an alert is open, and then neither
- **THEN** gpunit is asked once on start, and again at each interval while a session runs or an alert is open
- **AND** it is asked no more once neither holds, or once the surface stops

#### Scenario: a volume past its window takes the band
- **Key:** `ui:billing:a-volume-past-its-window-takes-the-band`
- **Layers:** unit
- **WHEN** gpunit's window record ends in the past and the volume is still recorded
- **THEN** the alert band is shown in place of the quiet item

#### Scenario: billing clearance requires known absence
- **Key:** `ui:billing:clearance-requires-known-absence`
- **Layers:** unit
- **WHEN** billing is unknown, a volume is open, or both resources are known absent
- **THEN** the page respectively shows pending state, the open volume, or nothing billing
