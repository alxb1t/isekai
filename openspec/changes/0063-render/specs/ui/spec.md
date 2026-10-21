## ADDED Requirements

### Requirement: Render is confirmed in a dialog that quotes what renders, its limit and its price at most

The system SHALL open, for a batch, a dialog listing per offered flow the images that will render and what is left
out, with the reason, the session's estimate and limit, and its price at most — the limit at the hourly maximum
`gpunit.toml` names, with the volume at its configured rate. Its confirmation SHALL be the only act that rents; the
dialog SHALL hold no URL. Render SHALL be disabled, with its reason, when nothing is short of its count, when a job
runs, when a pod may still be billing, and when no RunPod key is in the surface's environment.

The quote is what the operator agrees to; gpunit refuses a card above the hourly maximum, so the price is a bound and
not a guess. A reload never reopens a confirmation that spends.

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

#### Scenario: the confirmation starts the render
- **Key:** `ui:render:the-confirmation-starts-the-render`
- **Layers:** e2e
- **WHEN** the dialog's Render is confirmed
- **THEN** the session view opens at `/session`

### Requirement: The render job opens the volume, renders, and closes the volume unless kept

The system SHALL run a render as one job: the volume window opened or extended, then the rendering verb with the
session's limit and its progress, then the window closed unless the operator kept it open. A lost answer from the
window's opening SHALL render nothing and raise the volume alert; a failed close SHALL raise it too. Stop SHALL
interrupt the rendering verb, which tears its pod down.

The volume is the job's to open and to close, so no step depends on the operator remembering one.

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
SHALL serve each image's thumbnail from a cache in the library's `.cache/`, made on first request.

The images come back to where the sheets were decided; a cache the library can lose costs only its rebuild.

#### Scenario: versions are listed newest first
- **Key:** `ui:renders:versions-newest-first`
- **Layers:** unit
- **WHEN** a cell holds images under two approvals
- **THEN** the newer approval's images are listed first

#### Scenario: a thumbnail is made once
- **Key:** `ui:renders:a-thumbnail-is-made-once`
- **Layers:** unit
- **WHEN** an image's thumbnail is asked for twice
- **THEN** the second answer is read from `.cache/` without decoding the image

#### Scenario: the large view shows its sheet
- **Key:** `ui:renders:the-large-view-shows-its-sheet`
- **Layers:** e2e
- **WHEN** an image is opened from the grid
- **THEN** its large view shows the approval it was rendered from
