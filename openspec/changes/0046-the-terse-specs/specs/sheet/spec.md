## MODIFIED Requirements

### Requirement: A schema is a declared field list inside its flow

The system SHALL read the field list from a schema document inside the flow's own directory that
declares, in order, each field's name, whether it is scored, and the vocabulary suffix convention that
applies to it. The schema SHALL NOT declare a version and SHALL NOT declare a vocabulary.

The schema is data, so it is checked without running anything, and a second schema is a file rather than a branch.
It carries no version: the flow's digest proves the field list byte for byte, and a changed field list is a new
flow, compared with the old one over one cohort. It declares no vocabulary because the flow does — the flow is the
unit that is frozen, selected, rendered and compared
([D14](../../../docs/decisions.md#d14--a-flow-is-one-flat-directory)).

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

### Requirement: Every tag in a sheet is in the vocabulary

The system SHALL emit no tag that is not in the vocabulary.

An invented tag that looks canonical passes every later check on its way into the prompt. The tagger's output layer
is the vocabulary and the router emits only tags it was given, so this holds by construction
([D2](../../../docs/decisions.md#d2--a-table-fills-the-sheet)); the requirement is what a later reader checks a fill
against, and what any future producer must meet.

#### Scenario: every emitted tag is in the vocabulary
- **Key:** `sheet:purity:no-tag-outside-the-vocabulary`
- **Layers:** unit
- **WHEN** a sheet is written
- **THEN** every tag in every field is present in the vocabulary
- **AND** a tag the field map does not place contributes nothing at all

### Requirement: The stage fills fields from the tag list of a flow that declares the tagger, and leaves them empty for a flow that declares none

The system SHALL fill a sheet from a schema, a vocabulary, a field map and — for a flow that declares the
tagger — its local tag list, and SHALL store fields only. It SHALL NOT store an assembled prompt in a sheet,
SHALL NOT be told which flow requested the work beyond whether a tag list is expected and the flow's digest
it records, and SHALL NOT read prose. For a flow that declares the tagger it SHALL refuse naming the verb that
produces the tag list when that list is absent. For a flow that declares none it SHALL write every field empty,
and the sheet's producer SHALL record that no tag list and no model filled it. Every sheet SHALL record the digest
of the flow it was filled for, and SHALL carry the tag list's confidence floor into its producer where the list
records one.

```
flow declares the tagger? ──yes──▶ local tag list present? ──yes──▶ fill through the field map
         │                                  │
         no                                 no ──▶ refuse, naming the verb that produces it
         ▼
every field empty; the producer names no tag list and no model
```

A prompt stored in the sheet would be edited by a person and silently overwritten by a rebuild. The stage learns
only whether a tag list is expected and the flow's digest, which it records and never reads, so one stage serves
every flow; the digest ties a sheet to the schema it was filled against across a re-pin. It reads a tag list, not
prose, because a tagger whose output layer is the vocabulary cannot name a tag outside it
([D2](../../../docs/decisions.md#d2--a-table-fills-the-sheet)). An empty sheet is legal and so silent: for a tagged
flow it would hide a tagger that never ran, and for a flow that declares none there is nothing to hide — a person
fills it, and approval still gates the render
([D31](../../../docs/decisions.md#d31--a-flow-declares-whether-it-is-tagged)).

#### Scenario: a sheet stores fields and no prompt
- **Key:** `sheet:output:sheet-stores-fields-only`
- **Layers:** unit
- **WHEN** a sheet is written
- **THEN** it carries one entry per schema field
- **AND** it carries no assembled prompt

#### Scenario: an empty field is a legal answer
- **Key:** `sheet:output:empty-field-is-legal`
- **Layers:** unit
- **WHEN** the tag list carries nothing a field can be filled from
- **THEN** that field is present and empty
- **AND** the sheet is not rejected for it

#### Scenario: the sheet records the vocabulary it was filled from
- **Key:** `sheet:output:sheet-names-its-vocabulary`
- **Layers:** unit
- **WHEN** a sheet is written
- **THEN** it records the vocabulary's name, revision and digest
- **AND** that record is what a later reader checks the fill against

#### Scenario: the sheet records the field map it was routed by
- **Key:** `sheet:output:sheet-names-its-field-map`
- **Layers:** unit
- **WHEN** a sheet is written
- **THEN** it records the field map's name, revision and digest beside the vocabulary's
- **AND** two sheets routed by different revisions of the table are distinguishable from the record alone

#### Scenario: the stage reads the tag list and not the prose
- **Key:** `sheet:output:the-stage-reads-the-tag-list`
- **Layers:** unit
- **WHEN** a sheet is filled for an input that has both a caption and a local tagger's list
- **THEN** the fields are filled from the tag list
- **AND** the caption is not read

#### Scenario: an absent tag list is a refusal naming the verb that fills it
- **Key:** `sheet:output:an-absent-tag-list-is-refused`
- **Layers:** unit
- **WHEN** a sheet is asked, for a flow that declares the tagger, for an input whose local tagger's artifact
  is absent
- **THEN** the stage refuses, naming the verb that would produce it
- **AND** no sheet is written

#### Scenario: a flow that declares no tagger gets a sheet with every field empty
- **Key:** `sheet:output:a-flow-without-a-tagger-gets-empty-fields`
- **Layers:** unit
- **WHEN** a sheet is asked for an input of a flow that declares no tagger
- **THEN** a sheet is written with every schema field present and empty
- **AND** its producer names no tag list and no model

#### Scenario: a sheet records the digest of the flow it was filled for
- **Key:** `sheet:output:sheet-names-its-flow-digest`
- **Layers:** unit
- **WHEN** a sheet is written, from a tag list or empty
- **THEN** it records the digest of the flow's directory
- **AND** two sheets filled for a flow before and after a re-pin are distinguishable from the record alone

#### Scenario: a sheet carries the tag list's floor
- **Key:** `sheet:output:sheet-carries-the-floor`
- **Layers:** unit
- **WHEN** a sheet is filled from a tag list whose producer records a confidence floor
- **THEN** the sheet's producer records the same floor
- **AND** a tag list that records none yields a sheet that records none
