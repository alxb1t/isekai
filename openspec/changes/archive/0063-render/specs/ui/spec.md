## ADDED Requirements

### Requirement: Render is confirmed in a dialog that quotes what renders, its limit and its price at most

The system SHALL open, for a batch, a dialog listing per offered flow the images that will render and what is left
out, with the reason, the session's estimate and limit, and its price at most — the limit at the hourly maximum
`gpunit.toml` names, with the volume at its configured rate. Its confirmation SHALL be the only act that rents; the
dialog SHALL hold no URL. The confirmation SHALL carry the limit and the number of images the dialog showed, and SHALL
be refused, starting nothing, when the batch's quote taken again has a longer limit or another number of images.
Render SHALL be disabled, with its reason, when nothing is short of its count, when a job runs, when a pod may still
be billing, and when no RunPod key is in the surface's environment.

The quote is what the operator agrees to; gpunit refuses a card above the hourly maximum, so the price is a bound and
not a guess. A reload never reopens a confirmation that spends, and an approval made while the dialog is open never
renders what the operator did not see, even where the limit already sits at its floor or its cap.

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
on its terminal as the wait begins; a wait that runs out with the window not closed SHALL name the command that
closes it. An interrupt at the surface's terminal SHALL reach no child of the job.

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
- **WHEN** the surface stops mid-render and the pod's teardown outlasts the wait
- **THEN** the surface names the command that closes the window

#### Scenario: a verb that cannot start fails the job
- **Key:** `ui:render-job:a-verb-that-cannot-start-fails-the-job`
- **Layers:** unit
- **WHEN** the rendering verb cannot be started after the window opens
- **THEN** the job ends failed, naming the batch's log
- **AND** the window is closed

### Requirement: Billing state is read from gpunit's own records

The system SHALL show a pod as possibly billing when gpunit holds a pod record or a pending create while no session
runs, SHALL ask gpunit for its status only on start, every half minute while a session runs or an alert is open, and
on Check again, and SHALL clear an alert only when gpunit confirms the pod or volume gone. It SHALL show an open
volume as a quiet item until the end gpunit recorded for its window, and as the alert band after it.

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

### Requirement: The Renders view shows each source's images by flow and version

The system SHALL show a batch's images as a grid of sources by offered flows, each cell's approval versions newest
first with their images, and open an image's large view, with the sheet it was rendered from, from any of them. It
SHALL mark an approval it cannot read as damaged, naming the file, and show every other image; and SHALL refuse an
address whose version is not `v` and ASCII digits. It SHALL serve each image's thumbnail from a cache in the library's
`.cache/`, made on first request and named by the image's own bytes.

The images come back to where the sheets were decided; a cache the library can lose costs only its rebuild. Two
batches can hold one source rendered at one seed, so only the bytes say which image a thumbnail shows. One damaged
file costs only its own version, never the batch's page.

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

#### Scenario: the large view shows its sheet
- **Key:** `ui:renders:the-large-view-shows-its-sheet`
- **Layers:** e2e
- **WHEN** an image is opened from the grid
- **THEN** its large view shows the approval it was rendered from
