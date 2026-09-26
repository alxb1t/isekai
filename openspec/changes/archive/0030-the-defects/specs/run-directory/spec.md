## MODIFIED Requirements

### Requirement: Artifacts are append-only and numbered, and re-running a command is a no-op

The system SHALL number each stage's artifacts within that stage's own directory, SHALL never overwrite
a written artifact, and SHALL make a command whose artifact already exists do nothing — write nothing,
call nothing — unless a new version is explicitly requested.

Idempotence is what makes resume ordinary: there is no special mode and no state machine, because
running every command again is the whole of it. It is also the only defence against a shell loop
retrying after a network blip and silently burning a call.

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

### Requirement: An unknown schema version is refused, naming the fix

The system SHALL refuse to read an artifact whose schema version it does not know, and SHALL name what
the operator can do about it rather than parsing the artifact as best it can.

A best-effort parse of a format you do not know produces numbers that look fine and mean nothing. This
is the same posture the evaluator already takes when an optional dependency is absent: refuse, and say
what would fix it.

#### Scenario: an artifact from a newer version is refused
- **Key:** `run-directory:schema:unknown-version-is-refused`
- **Layers:** unit
- **WHEN** an artifact declares a schema version this build does not know
- **THEN** the read is refused naming the file, the version it declares and the version this build reads
- **AND** no field of the artifact is interpreted

#### Scenario: the refusal states the remedy
- **Key:** `run-directory:schema:refusal-names-the-fix`
- **Layers:** unit
- **WHEN** an unknown schema version is refused
- **THEN** the message tells the operator what action would resolve it
- **AND** it does not suggest an action this build cannot perform

#### Scenario: an unreadable artifact is refused by name
- **Key:** `run-directory:schema:an-unreadable-artifact-is-refused-by-name`
- **Layers:** unit
- **WHEN** an artifact is not valid JSON, is not a JSON object, or carries a schema block that is not an object
- **THEN** the read is refused naming the file
- **AND** no field of the artifact is interpreted
- **AND** the remedy names an action this build can perform
