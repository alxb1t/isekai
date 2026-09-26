## REMOVED Requirements

### Requirement: The stage takes a tag list, a schema, a vocabulary and a field map, and returns fields

**Reason**: A flow may now declare that it needs no tagger, and such a flow has no tag list; the title said
every sheet takes one. The requirement that replaces it keeps every rule this one held for a flow that
declares the tagger, and adds the empty fill for a flow that declares none.

**Migration**: None for either tracked flow — both declare the tagger, so their fill is unchanged. The
refusal for an absent tag list names `tag` rather than `caption`.

## ADDED Requirements

### Requirement: The stage fills fields from the tag list of a flow that declares the tagger, and leaves them empty for a flow that declares none

The system SHALL fill a sheet from a schema, a vocabulary, a field map and — for a flow that declares the
tagger — its local tag list, and SHALL store fields only. It SHALL NOT store an assembled prompt in a sheet,
SHALL NOT be told which flow requested the work beyond whether a tag list is expected, and SHALL NOT read
prose. For a flow that declares the tagger it SHALL refuse naming the verb that produces the tag list when
that list is absent. For a flow that declares none it SHALL write every field empty, and the sheet's
producer SHALL record that no tag list and no model filled it.

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

**For a flow that declares the tagger, the tag list is a prerequisite rather than an aid, and the refusal
is what says so.** A sheet with every
field empty is legal and therefore silent, so producing one when the tagger never ran would hide the one
thing the operator needs told. The rule that an absent tag artifact is an absent aid holds for a tagger that
contributes nothing to a sheet; it cannot hold for the one the sheet is filled from.

**A flow that declares no tagger gets empty fields, and that is not the silence the refusal guards
against.** The refusal exists because an empty sheet would hide a tagger that never ran; for a flow that
declares none, no tagger was going to run, so there is nothing to hide. The person fills the sheet on the
review surface and approves it, and approval still gates the render.

The stage learns only whether a tag list is expected — a boolean the composition root reads from the
manifest — so it stays ignorant of flows.

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
