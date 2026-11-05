## MODIFIED Requirements

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
