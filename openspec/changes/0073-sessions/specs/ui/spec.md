## ADDED Requirements

### Requirement: Each batch's render sessions are listed and shown from their records

The system SHALL list a batch's render sessions from its records, the running one first and the rest newest first,
each with its start, its duration against its limit, its outcome and its images, and SHALL show one session's page
from its record, live while it runs, with the volume steps and Stop the job adds. A Sessions tab SHALL sit beside the
hub, Review and Renders. While a render runs, every screen SHALL show it running, with its clock, linking to its
session's page. A finished image SHALL open in the viewer, and the batch's source photographs SHALL show on the page,
each opening in the viewer; images and photographs SHALL be drawn at the tile size Renders draws. The viewer SHALL
follow its list when it changes while open.

A session is the record the render wrote, so the page, the list and the terminal agree, and a finished session can
be found again. A running render is the one thing on the surface that bills by the minute.

#### Scenario: a batch lists its sessions
- **Key:** `ui:sessions:a-batch-lists-its-sessions`
- **Layers:** unit
- **WHEN** a batch holds a running record and two finished ones
- **THEN** its sessions are listed running first, then newest first

#### Scenario: a session's page reads its record
- **Key:** `ui:sessions:a-session-reads-its-record`
- **Layers:** unit
- **WHEN** a session is asked for by its id
- **THEN** its record's images, steps and outcome are served
- **AND** an id no record holds is refused, naming the batch's sessions

#### Scenario: the list shows a finished session
- **Key:** `ui:sessions:the-list-shows-a-finished-session`
- **Layers:** e2e
- **WHEN** the Sessions tab is opened on a batch holding a finished record
- **THEN** the session is listed with its images, and its page opens from it

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
- **THEN** the session's page opens at `/b/<batch>/sessions/<id>`

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


### Requirement: The render job opens the volume, renders, and closes the volume unless kept

The system SHALL run a render as one job: the volume window opened or extended, then the rendering verb with the
session's limit, its id and its progress, then the window closed unless the operator kept it open. A lost answer from
the window's opening SHALL render nothing and raise the volume alert, and an opening that raises SHALL mark its step
failed; a failed close SHALL raise it too. A job whose verb cannot be started SHALL end failed, naming the batch's
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

#### Scenario: an opening that raises fails its step
- **Key:** `ui:render-job:an-opening-that-raises-fails-its-step`
- **Layers:** unit
- **WHEN** opening the window raises
- **THEN** the job ends failed and the volume step reads failed


### Requirement: Billing state is read from gpunit's own records

The system SHALL show a pod as possibly billing when gpunit holds a pod record or a pending create while no session
runs, SHALL ask gpunit for its status only on start, every half minute while a session runs or an alert is open, and
on Check again, and SHALL clear an alert only when gpunit confirms the pod or volume gone. It SHALL offer the alert's
way out on its own page, `/billing`, which the alert band opens. It SHALL show an open volume as a quiet item until
the end gpunit recorded for its window, and as the alert band after it.

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

#### Scenario: a volume past its window takes the band
- **Key:** `ui:billing:a-volume-past-its-window-takes-the-band`
- **Layers:** unit
- **WHEN** gpunit's window record ends in the past and the volume is still recorded
- **THEN** the alert band is shown in place of the quiet item


### Requirement: Every screen has a URL naming its batch and its run

The system SHALL give Home, a batch's hub, a batch's Review, a review of a source in a flow, a batch's sessions,
one session and the billing alert's way out each its own URL,
SHALL name the batch in every URL inside one, and SHALL name a run by the twelve-character digest its identifier
begins with. A batch's Review SHALL open the sheet Review starts from and put that sheet's URL in its place. It SHALL
answer any of them on a fresh load, and SHALL refuse one naming a batch or a run the library does not hold, naming
the way back.

A reload, a second tab or a bookmark then lands where it was, never on whatever the server last held open. A run's
short name is a sanitised filename and can repeat; its digest cannot.

```
/                                  Home
/b/<batch>/hub                     the hub
/b/<batch>/review                  the head of Review, replaced by its sheet's URL
/b/<batch>/review/<digest>/<flow>  Review
/b/<batch>/sessions                the batch's sessions
/b/<batch>/sessions/<id>           one session
/billing                           the billing alert's way out
```

#### Scenario: a reload lands on the same screen
- **Key:** `ui:routes:a-reload-lands-on-the-same-screen`
- **Layers:** e2e
- **WHEN** a hub, a review or a batch's Review address is loaded again
- **THEN** the same batch, source and flow are shown
- **AND** a batch's Review address is replaced by its head's sheet URL
- **AND** a batch with no sheet waiting says none waits

#### Scenario: a run is named by its digest
- **Key:** `ui:routes:a-run-is-named-by-its-digest`
- **Layers:** unit
- **WHEN** a review URL names a run
- **THEN** the run is the one whose identifier begins with that digest

#### Scenario: an unknown batch is refused with the way back
- **Key:** `ui:routes:an-unknown-batch-is-refused`
- **Layers:** e2e
- **WHEN** a URL names a batch the library does not hold
- **THEN** the page refuses, naming the batch
- **AND** it offers the way back to Home


### Requirement: Review opens a batch at its own address, lists every unrendered sheet, and Approve stays on the sheet

The system SHALL open a batch's Review on its head: the first unapproved sheet of the first flow that has one, in the
hub's order; else the first approved sheet whose newest approval lacks images of its count, read-only; else a page
saying no sheet waits for review, with the way to the hub. The hub SHALL carry for each cell the number of images its
newest approval lacks, as the render stage counts it. Review's rail SHALL list every sheet of the flow that is
unapproved or lacks images, each marked untouched, edited, approved or re-opened, and its footer SHALL count the
approved among them; the Review tab SHALL count the unapproved. Approve SHALL leave the sheet open and read-only, the
approve bar naming the approval it shows, offering *Cancel approve* while the review stage can cancel it, else the
reason beside it, and while no render runs for the batch; a cancel SHALL leave the sheet open on what the flow is
left on: its draft, editable, or for a copy the draft open above what lies beneath, else the approval beneath it,
read-only. Opening a sheet that has no draft SHALL write one through the review stage's own function, and opening it
again SHALL write no second draft; a failure after approval SHALL be shown in the approve bar, never dropped. ④ SHALL
show one slot per image, a set seed or random, beside the sheet rows. The photograph SHALL open in the viewer,
stepping through the rail's sheets.

A sheet is done when its images are, not when it is approved, so the rail keeps it until then; the count is the
render stage's own. Approving is an act, not a navigation, and a copy's cancel takes back only the copy. A slot per
image says what the next render draws before it is approved.

```
the head:  first unapproved ─▶ else first approved and short ─▶ else "No sheet waits for review"
```

#### Scenario: a batch's Review opens its head
- **Key:** `ui:review:a-batch-opens-its-head`
- **Layers:** unit
- **WHEN** a batch holds an approved, short sheet and an unapproved one, then neither
- **THEN** its Review opens the unapproved sheet, then the approved one
- **AND** with no sheet left it opens none

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
- **WHEN** an approval succeeds and reading the batch again fails
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
- **WHEN** the photograph is opened, then `→` is pressed
- **THEN** the viewer shows it fitted, then the next sheet's photograph

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

