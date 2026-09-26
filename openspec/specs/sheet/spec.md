# Capability: `sheet`

## Purpose

Stage ② of the pipeline: filling a sheet's fields with canonical vocabulary tags from the WD14 tag list,
through the field map, against the schema inside the flow that asked — or leaving them empty for a flow
that declares no tagger — and knowing nothing about flows beyond the one directory it reads and writes
and whether a tag list is expected.

**Source:** `isekai/pipeline/sheet.py`, `isekai/shared/fields.py`, `isekai/shared/vocabulary.py`,
`isekai/shared/field_map.py`, `isekai/foundation/flow.py`, `flows/summon-anime-wai/schema.json` ·
**Tests:** `tests/test_sheet_schema.py`, `tests/test_sheet_stage.py`,
`tests/test_vocabulary.py`

## Requirements

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

### Requirement: The stage takes a tag list, a schema, a vocabulary and a field map, and returns fields

The system SHALL fill a sheet from exactly four inputs — a tag list, a schema, a vocabulary and a field map
— and SHALL store fields only. It SHALL NOT store an assembled prompt in a sheet, SHALL NOT be told which
flow requested the work, SHALL NOT read prose, and SHALL refuse naming the verb that produces the tag list
when that list is absent.

Storing the assembled prompt in the sheet creates a footgun where a human edits the prompt block and a
rebuild silently overwrites it. Keeping the stage ignorant of flows is what lets the same code serve every
flow without learning that flows exist: the composition root resolves a flow to its schema and hands the
stage a primitive.

**The input changes from prose to a tag list because of what the two producers can be wrong about.** A
reader asked for a field structure can invent a tag that merely looks canonical, and it did: `light` and
`dark` reached an assembled prompt as bare tags meaning *lighting* and *darkness*, past every guard, and one
sheet lost its subject count entirely. A tagger whose output layer **is** the vocabulary cannot make that
class of error, because naming a tag outside the list is not something it can express. It can be wrong about
the photograph, and that is the operator's to correct on the surface — which he does to every sheet
regardless, so sheet fidelity was never the metric. Prose remains a reading aid for the operator and stops
being a machine input, so a failed reader no longer blocks a sheet it does not feed.

**The tag list is a prerequisite rather than an aid, and the refusal is what says so.** A sheet with every
field empty is legal and therefore silent, so producing one when the tagger never ran would hide the one
thing the operator needs told. The rule that an absent tag artifact is an absent aid holds for a tagger that
contributes nothing to a sheet; it cannot hold for the one the sheet is filled from.

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
- **WHEN** a sheet is asked for an input whose local tagger's artifact is absent
- **THEN** the stage refuses, naming the verb that would produce it
- **AND** no sheet is written

### Requirement: Every tag in a sheet is in the vocabulary

The system SHALL emit no tag that is not in the vocabulary.

An invented tag that merely looks canonical is worse than an obviously invalid one, because it passes every
later check on its way into the prompt. **After this change the property holds by construction rather than
by filtering**: the tagger's output layer is the vocabulary, and the router emits only tags it was given.
The requirement stays because it is what a later reader checks a fill against, and because it is the
invariant any future producer would have to satisfy to be allowed near a sheet.

#### Scenario: every emitted tag is in the vocabulary
- **Key:** `sheet:purity:no-tag-outside-the-vocabulary`
- **Layers:** unit
- **WHEN** a sheet is written
- **THEN** every tag in every field is present in the vocabulary
- **AND** a tag the field map does not place contributes nothing at all
