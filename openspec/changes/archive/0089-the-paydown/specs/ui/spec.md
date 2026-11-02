## MODIFIED Requirements

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
