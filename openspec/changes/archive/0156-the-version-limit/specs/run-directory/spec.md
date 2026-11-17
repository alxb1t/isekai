## MODIFIED Requirements

### Requirement: Artifacts are append-only and numbered, and re-running a command is a no-op

The system SHALL number each stage's artifacts within that stage's own directory, SHALL never overwrite
a written artifact, and SHALL make a command whose artifact already exists do nothing — write nothing,
call nothing — unless a new version is explicitly requested. It SHALL delete a render's image and
record only when the operator discards that render, SHALL delete an approval, its prompt, its failure
records and its source copy with its last render, and SHALL delete a flow's sheets only when that
leaves the flow with no approval; nothing SHALL go back to a draft.

Idempotence is what makes resume ordinary: there is no special mode and no state machine, because
running every command again is the whole of it. It is also the only defence against a shell loop
retrying after a network blip and silently burning a call. A render is a likeness, so the one way it
leaves a run is the operator's ask; an approval with no render left goes with it, and a flow with no
approval left keeps only its assignment, so neither the Hub nor Review offers what was just deleted
([D50](../../../docs/decisions.md#d50--the-last-render-takes-its-approval-and-a-flow-holds-only-its-own-files)).

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

#### Scenario: the newest approval goes with its last render
- **Key:** `run-directory:idempotence:the-newest-approval-goes-with-its-last-render`
- **Layers:** unit
- **WHEN** the operator discards the only render of a flow's newest approval, an older approval still holding an image
- **THEN** that approval, its prompt and its failure records are gone, and no draft is written
- **AND** every other file of the run is as it was

#### Scenario: a full directory refuses a new version
- **Key:** `run-directory:numbering:a-full-directory-refuses-a-new-version`
- **Layers:** unit
- **WHEN** a stage asks for the next number of a directory that holds version 999, the last a three-digit name can spell
- **THEN** it refuses, naming the directory and that the way out is to move the whole run that holds it out of
  its runs root and start that photograph again as a new run, so a flow's approvals, prompts and renders stay
  together
- **AND** no file in the directory changes
