## MODIFIED Requirements

### Requirement: Inspection prints the run directory with its provenance

The system SHALL provide a command that prints a run's artifacts, which version is active for each
stage, and what produced each one. It SHALL list every failure record under the stage or render group that
holds it, and SHALL name every file or directory below a flow's directory that it does not read.

A filename carries only what resume decides on, which leaves a directory that is precise and unreadable.
This command is what a person reads instead — and it is also the answer to "where is this run", which is
why no progress file is needed before something other than a human is watching. It reads a run in any
state, so a failure it hides, or a name it skips, is a run it describes as other than it is.

#### Scenario: inspection names the active version for each stage
- **Key:** `cli:show:active-version-is-marked`
- **Layers:** unit
- **WHEN** a run is inspected
- **THEN** each stage's versions are listed and the active one is marked
- **AND** approval is shown where the concept applies

#### Scenario: inspection reports what produced each artifact
- **Key:** `cli:show:producers-are-reported`
- **Layers:** unit
- **WHEN** a run is inspected
- **THEN** each artifact's producer is shown
- **AND** artifacts produced by different implementations are distinguishable in the output

#### Scenario: a frame it cannot read is marked
- **Key:** `cli:show:an-unreadable-frame-is-marked`
- **Layers:** unit
- **WHEN** a run's frame is unreadable, declares an unknown version, or lacks its photograph
- **THEN** the report marks the frame with its refusal in place of the photograph line
- **AND** it lists the run's flows and artifacts as it would otherwise

#### Scenario: failure records are listed under their stage
- **Key:** `cli:show:failure-records-are-listed`
- **Layers:** unit
- **WHEN** a stage or a render group holds failure records
- **THEN** each record is listed under it with its version, its attempt and its kind
- **AND** a stage whose only content is failure records is not reported as empty

#### Scenario: a name it does not read is named
- **Key:** `cli:show:an-unread-name-is-named`
- **Layers:** unit
- **WHEN** a flow's directory, a stage directory or the render outputs hold a file or directory the report does not read
- **THEN** the report names it as not read
- **AND** it lists the run's artifacts as it would otherwise
