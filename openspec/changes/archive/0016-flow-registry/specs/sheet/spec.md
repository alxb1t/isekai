## REMOVED Requirements

### Requirement: The stage runs once per distinct schema and vocabulary pair
**Reason**: A schema now lives inside its flow, so there is no schema two flows can be said to share
and no selector that could find them. Sharing one fill across flows was worth a mechanism only while a
fill was expensive relative to what a flow costs to run; a caption is $0.0159 per photograph at worst
and $0.0013 cached, against a boot that costs $0.036, so the sharing bought a selector, a digest-keyed
fan-out and a class of silent cross-flow inheritance in exchange for a rounding error. A flow shares
nothing.
**Migration**: None. `sheet:output:sheet-stores-fields-only` continues to hold per flow.

### Requirement: A schema is a declared, versioned document
**Reason**: Both of the things this requirement declared about a schema stop being true. It carries no
version, because inside a frozen flow directory a version protects nothing — the flow's digest proves
the field list byte for byte, and a changed field list is a new flow. And it declares no vocabulary,
because the flow does: where two things could own a declaration the flow owns it. What survives is the
field list, its order and its `scored` flags, restated below with the two scenario keys that still hold.
**Migration**: `sheet:schema:field-order-is-declared-once` and
`sheet:schema:field-names-are-identifier-safe` carry forward unchanged under the requirement added
below. `sheet:schema:unknown-version-is-refused` has no successor at the schema; the equivalent refusal
now belongs to the flow manifest's own format version,
`image-generation:manifest:manifest-declares-its-format-version`.

## ADDED Requirements

### Requirement: A schema is a declared field list inside its flow

The system SHALL read the field list from a schema document inside the flow's own directory that
declares, in order, each field's name, whether it is scored, and the vocabulary suffix convention that
applies to it. The schema SHALL NOT declare a version and SHALL NOT declare a vocabulary.

The schema is data rather than code so that it can be checked without executing anything, and so that a
second schema — a photoreal flow's, say — is a file rather than a branch. It carries no version because
inside a frozen flow directory a version protects nothing: the flow's digest already proves the field
list byte for byte, and a changed field list is a new flow rather than a new schema version. That is
also what makes a schema change measurable, because the old flow and the new one can be rendered over
one cohort and compared. It declares no vocabulary because the flow does: where two things could own a
declaration the flow owns it, since the flow is the unit that is frozen, selected, rendered and
compared, and the vocabulary is provisioned like the models are.

#### Scenario: field order in the schema is the order in the prompt
- **Key:** `sheet:schema:field-order-is-declared-once`
- **Layers:** unit
- **WHEN** a prompt is assembled from a sheet
- **THEN** the fields appear in the order the schema declares
- **AND** no second ordering is defined anywhere else

#### Scenario: field names are usable as structured-output keys
- **Key:** `sheet:schema:field-names-are-identifier-safe`
- **Layers:** unit
- **WHEN** a schema is loaded
- **THEN** every field name is accepted as a JSON schema property key without transformation
- **AND** the name the instructions use is the same name the structure enforces

#### Scenario: the schema is read from the flow's own directory
- **Key:** `sheet:schema:schema-is-read-from-the-flow`
- **Layers:** unit
- **WHEN** a flow's schema is loaded
- **THEN** it is read from that flow's directory
- **AND** no schema is read from outside a flow directory

#### Scenario: the vocabulary is declared once, by the flow
- **Key:** `sheet:schema:vocabulary-is-declared-by-the-flow`
- **Layers:** unit
- **WHEN** a schema document is loaded
- **THEN** it declares no vocabulary
- **AND** the vocabulary the fill is held against is the one the flow declares

### Requirement: The stage takes prose, a schema and a vocabulary, and returns fields

The system SHALL fill a sheet from exactly three inputs — prose, a schema and a vocabulary — and SHALL
store fields only. It SHALL NOT store an assembled prompt in a sheet, and SHALL NOT be told which flow
requested the work.

Storing the assembled prompt in the sheet creates a footgun where a human edits the prompt block and a
rebuild silently overwrites it. Keeping the stage ignorant of flows is what lets the same code serve
every flow without learning that flows exist: the composition root resolves a flow to its schema and
hands the stage a primitive.

#### Scenario: a sheet stores fields and no prompt
- **Key:** `sheet:output:sheet-stores-fields-only`
- **Layers:** unit
- **WHEN** a sheet is written
- **THEN** it carries one entry per schema field
- **AND** it carries no assembled prompt

#### Scenario: an empty field is a legal answer
- **Key:** `sheet:output:empty-field-is-legal`
- **Layers:** unit
- **WHEN** the prose carries nothing a field can be filled from
- **THEN** that field is present and empty
- **AND** the sheet is not rejected for it

#### Scenario: the sheet records the vocabulary it was filled from
- **Key:** `sheet:output:sheet-names-its-vocabulary`
- **Layers:** unit
- **WHEN** a sheet is written
- **THEN** it records the vocabulary's name, revision and digest
- **AND** that record is what a later reader checks the fill against
