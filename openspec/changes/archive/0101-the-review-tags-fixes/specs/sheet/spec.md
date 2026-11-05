## MODIFIED Requirements

### Requirement: Every tag in a sheet is in the vocabulary

The system SHALL emit no tag that is not in the vocabulary, and SHALL refuse to prepare a sheet holding a tag on the
field map's excluded list, naming the tag and its field.

An invented tag that looks canonical passes every later check on its way into the prompt. The tagger's output layer
is the vocabulary and the router emits only tags it was given, so this holds by construction
([D2](../../../docs/decisions.md#d2--a-table-fills-the-sheet)); the requirement is what a later reader checks a fill
against, and what any future producer must meet.

The excluded check holds by construction too, since no group holds an excluded tag; preparation checks it so a
producer that does not route through the table meets it as well.

#### Scenario: every emitted tag is in the vocabulary
- **Key:** `sheet:purity:no-tag-outside-the-vocabulary`
- **Layers:** unit
- **WHEN** a sheet is written
- **THEN** every tag in every field is present in the vocabulary
- **AND** a tag the field map does not place contributes nothing at all

#### Scenario: a sheet holding an excluded tag is refused
- **Key:** `sheet:purity:an-excluded-tag-is-refused`
- **Layers:** unit
- **WHEN** a sheet being prepared holds a tag on the field map's excluded list
- **THEN** preparation is refused naming the tag and its field
- **AND** no sheet is written
