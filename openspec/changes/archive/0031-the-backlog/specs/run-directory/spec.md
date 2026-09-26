## MODIFIED Requirements

### Requirement: An unknown schema version is refused, naming the fix

The system SHALL refuse to read an artifact whose schema version it does not know, and SHALL name what
the operator can do about it rather than parsing the artifact as best it can.

A best-effort parse of a format this build does not know produces numbers that look fine and mean nothing. This
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
