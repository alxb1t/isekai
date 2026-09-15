## Purpose

Stage ② of the pipeline: turning descriptive prose into a sheet of fields filled with canonical
vocabulary tags, using a declared schema and a provisioned tag list, and knowing nothing about which
flow asked or how many will read the result.

## ADDED Requirements

### Requirement: A schema is a declared, versioned document

The system SHALL read the field list from a versioned schema document that declares, in order, each
field's name, whether it is scored, and the vocabulary suffix convention that applies to it. The schema
SHALL declare the vocabulary it is written against.

The schema is data rather than code so that it can be checked without executing anything, and so that a
second schema — a photoreal flow's, say — is a file rather than a branch. Declaring the vocabulary is
what makes a per-field suffix honest: expecting a hair-colour field to hold tags ending in "hair" is a
statement about a particular tag list, not about the field.

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

#### Scenario: an unknown schema version is refused
- **Key:** `sheet:schema:unknown-version-is-refused`
- **Layers:** unit
- **WHEN** a schema document declares a version this build does not know
- **THEN** it is refused naming the file and both versions
- **AND** no field of it is interpreted

### Requirement: The stage takes prose, a schema and a vocabulary, and returns fields

The system SHALL fill a sheet from exactly three inputs — prose, a schema and a vocabulary — and SHALL
store fields only. It SHALL NOT store an assembled prompt in a sheet, and SHALL NOT be told which flow
requested the work.

Storing the assembled prompt in the sheet creates a footgun where a human edits the prompt block and a
rebuild silently overwrites it. Keeping the stage ignorant of flows is what lets one filled sheet serve
every flow that shares a schema and a vocabulary.

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
- **AND** a sheet filled from a different vocabulary is distinguishable from the record alone

### Requirement: No absence clause and no out-of-vocabulary tag survives this stage

The system SHALL drop any phrase that asserts an attribute is absent, and SHALL emit no tag that is not
in the vocabulary.

A positive prompt has no negation, so an absence clause passed through becomes a presence instruction —
a sheet stating that no tattoos were visible produced a render with tattoos. An invented tag that
merely looks canonical is worse than an obviously invalid one, because it passes every later check on
its way into the prompt.

#### Scenario: an absence clause produces nothing
- **Key:** `sheet:purity:absence-clause-is-dropped`
- **Layers:** unit
- **WHEN** the prose states that an attribute is absent
- **THEN** no tag is emitted for it
- **AND** the field is left empty rather than filled with a negation

#### Scenario: every emitted tag is in the vocabulary
- **Key:** `sheet:purity:no-tag-outside-the-vocabulary`
- **Layers:** unit
- **WHEN** a sheet is written
- **THEN** every tag in every field is present in the vocabulary
- **AND** a phrase that maps to nothing contributes no tag at all

### Requirement: The mapping from phrase to canonical tag is deterministic and ordered

The system SHALL map a free-text phrase onto canonical tags by a fixed cascade — an exact match, then a
per-field suffix convention, then a curated synonym pass that consumes the span it matched and
continues, then a containment pass that requires every word of a candidate tag to appear in the phrase —
and SHALL return an empty result when nothing matches.

Each rule in that order is a recorded correction. Returning on the first curated hit lost concepts from
multi-concept phrases. Scoring by word-overlap ratio let a tag win while containing a word the phrase
never had. Requiring every word of the tag removes that without needing a threshold.

#### Scenario: a phrase already in the vocabulary maps to itself
- **Key:** `sheet:mapping:exact-match-wins-first`
- **Layers:** unit
- **WHEN** a phrase is already a canonical tag
- **THEN** it is returned unchanged
- **AND** no later pass alters it

#### Scenario: a field's suffix convention completes a bare value
- **Key:** `sheet:mapping:suffix-completes-a-bare-value`
- **Layers:** unit
- **WHEN** a field declares a suffix and the phrase plus that suffix is a canonical tag
- **THEN** the completed tag is returned
- **AND** the suffix comes from the schema rather than from the mapper

#### Scenario: a curated match consumes its span and the rest continues
- **Key:** `sheet:mapping:curated-pass-consumes-and-continues`
- **Layers:** unit
- **WHEN** a phrase contains a curated synonym alongside other content
- **THEN** the synonym's tag is emitted and its words are removed from the phrase
- **AND** the remaining words are still considered

#### Scenario: containment requires every word of the candidate
- **Key:** `sheet:mapping:containment-requires-every-word`
- **Layers:** unit
- **WHEN** a candidate tag contains a word the phrase does not
- **THEN** that tag is not emitted
- **AND** a candidate whose every word appears in the phrase may be

#### Scenario: an empty result is a real answer
- **Key:** `sheet:mapping:no-match-emits-nothing`
- **Layers:** unit
- **WHEN** a phrase carries nothing the generator can draw
- **THEN** no tag is emitted for it
- **AND** the mapper does not substitute a nearest neighbour

### Requirement: The stage runs once per distinct schema and vocabulary pair

The system SHALL fill a sheet once for each distinct combination of schema and vocabulary, and SHALL
write the result to every flow that declares that combination.

Flows that share a schema and a vocabulary start from identical sheets and diverge only when a human
edits them. Filling once and copying is what makes adding a flow cheap, and it follows from the stage
not being told which flow asked.

#### Scenario: flows sharing a schema and vocabulary cost one fill
- **Key:** `sheet:sharing:one-fill-serves-every-matching-flow`
- **Layers:** unit
- **WHEN** two flows declare the same schema and vocabulary
- **THEN** the stage fills a sheet once
- **AND** the result is written to both flows' sheet directories

### Requirement: The model is an injectable seam and its structure is constrained, not its content

The system SHALL reach the model through an interface a test double satisfies, SHALL constrain the
model's output to the schema's field structure, and SHALL NOT constrain the model's word choice to the
vocabulary at generation time.

Constraining generation to the vocabulary was measured and rejected: token-prefix masking lands on the
nearest tag sharing a prefix rather than the one the model meant, which turns a visible failure into an
invisible one — a phrase meaning "tucked into jeans" became a valid, unrelated tag that passes every
guard and gets rendered. Generating freely and mapping afterwards scored 0.482 against 0.316 for the
constrained arm.

#### Scenario: the suite fills a sheet with no network
- **Key:** `sheet:seam:offline-double-satisfies-the-interface`
- **Layers:** unit
- **WHEN** the stage runs with the test double in place
- **THEN** a sheet is written
- **AND** no network call is attempted

#### Scenario: the structure is enforced and the wording is free
- **Key:** `sheet:seam:structure-constrained-content-free`
- **Layers:** unit
- **WHEN** the model is called
- **THEN** it is required to return exactly the schema's fields
- **AND** it is not restricted to vocabulary terms while generating

#### Scenario: a response that does not match the field structure is a permanent failure
- **Key:** `sheet:failure:structural-mismatch-is-permanent`
- **Layers:** unit
- **WHEN** the model's response does not carry the schema's fields
- **THEN** the failure is recorded as permanent
- **AND** no sheet is written
