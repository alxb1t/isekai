## MODIFIED Requirements

### Requirement: Artifacts are append-only and numbered, and re-running a command is a no-op

The system SHALL number each stage's artifacts within that stage's own directory, SHALL never overwrite
a written artifact, and SHALL make a command whose artifact already exists do nothing — write nothing,
call nothing — unless a new version is explicitly requested. It SHALL delete a render's image and
record only when the operator discards that render.

Idempotence is what makes resume ordinary: there is no special mode and no state machine, because
running every command again is the whole of it. It is also the only defence against a shell loop
retrying after a network blip and silently burning a call. A render is a likeness, so the one way it
leaves a run is the operator's ask.

#### Scenario: re-running a completed command changes nothing
- **Key:** `run-directory:idempotence:rerun-is-a-no-op`
- **Layers:** unit
- **WHEN** a command runs against a run whose artifact for that stage already exists
- **THEN** no file in the run directory changes
- **AND** no call is made to any external service

#### Scenario: a new version is an explicit act
- **Key:** `run-directory:idempotence:new-version-must-be-asked-for`
- **Layers:** unit
- **WHEN** a command is asked explicitly for a new version
- **THEN** the next number is written
- **AND** the previous version is left exactly as it was

#### Scenario: numbering is per directory and linked by provenance
- **Key:** `run-directory:numbering:each-directory-counts-its-own`
- **Layers:** unit
- **WHEN** two stages each write artifacts for the same run
- **THEN** each stage's numbers are assigned within its own directory
- **AND** the link between them is the producer record, not a shared counter

#### Scenario: approving an approved flow writes nothing
- **Key:** `run-directory:idempotence:approving-an-approved-flow-writes-nothing`
- **Layers:** unit
- **WHEN** approval is asked for a flow that is already approved and still holds a draft numbered below its approval
- **THEN** no file in the run directory changes
- **AND** the command reports the stage as already complete

