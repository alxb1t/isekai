# Capability: `sheet`

## Purpose

Stage ② of the pipeline: turning descriptive prose into a sheet of fields filled with canonical
vocabulary tags, using the schema and the standing instructions inside the flow that asked, and knowing
nothing about flows beyond the one directory it reads and writes.

**Source:** `isekai/pipeline/sheet.py`, `isekai/shared/fields.py`, `isekai/shared/vocabulary.py`,
`isekai/boundary/claude_cli.py`, `isekai/foundation/flow.py`, `flows/summon-v1/schema.json`,
`flows/summon-v1/sheet.briefing.md` ·
**Tests:** `tests/test_sheet_schema.py`, `tests/test_sheet_stage.py`,
`tests/test_vocabulary.py`

## Requirements

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

### Requirement: The flow selects the sorter implementation, and the shape constraint travels with it

The system SHALL select the sorter implementation from the string the flow's manifest declares, SHALL
refuse — naming the implementations the build carries — when a flow declares one it does not have, and
SHALL constrain every implementation's output to the schema's field structure regardless of how that
constraint is expressed to the model. A sorter's answer SHALL be read whether it arrives as a separate
structured field or as the body of the response.

The shape constraint is what keeps a malformed answer classified as permanent rather than transient: the
structure was stated in the request, so a response that does not carry it will not carry it on the next
attempt either, and another attempt would spend for nothing. That classification is a property of the
constraint being enforced server-side, not of which transport carries it — an implementation that merely
asked politely for the right shape would flip that row to transient and quietly turn a wasted attempt
into three. Reading the answer from either place is what lets one stage serve implementations that differ
in nothing the stage cares about: the cascade that canonicalises the phrases, the validation that refuses
a non-vocabulary tag, and the rule that an empty field is a legal answer are all downstream of this seam
and all unchanged by which implementation filled it.

#### Scenario: the declared implementation is the one that runs
- **Key:** `sheet:selection:the-flow-names-the-implementation`
- **Layers:** unit
- **WHEN** a flow declaring an implementation is sorted
- **THEN** the sheet's producer names that implementation
- **AND** no other implementation was constructed

#### Scenario: an implementation this build does not carry is refused naming the ones it does
- **Key:** `sheet:selection:unknown-implementation-is-refused`
- **Layers:** unit
- **WHEN** a flow declares a sorter implementation the build does not carry
- **THEN** the command refuses naming the implementations it does carry
- **AND** no sheet is written and no attempt is recorded

#### Scenario: the field structure is required of every implementation
- **Key:** `sheet:selection:structure-is-required-of-every-implementation`
- **Layers:** unit
- **WHEN** any implementation is called
- **THEN** it is required to return exactly the schema's fields
- **AND** the requirement is expressed to the model rather than checked only after the fact

#### Scenario: an answer carried in the response body is read
- **Key:** `sheet:selection:answer-in-the-body-is-read`
- **Layers:** unit
- **WHEN** an implementation returns the schema's fields as the body of its response rather than as a
  separate structured field
- **THEN** the sheet is filled from it
- **AND** the stage does not record a failure for the difference

#### Scenario: a truncated answer is permanent and says why
- **Key:** `sheet:selection:truncation-is-permanent-and-named`
- **Layers:** unit
- **WHEN** an implementation's answer is cut short before the fields are complete and the host reports
  that it ran out of output budget
- **THEN** the failure is recorded as permanent
- **AND** the record distinguishes it from an answer that was malformed for another reason
