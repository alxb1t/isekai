## ADDED Requirements

### Requirement: The reader takes a photograph and its briefing, and returns the photograph's prose

The system SHALL pass a reader exactly the photograph and the briefing the caption config names, and SHALL
accept exactly one output: descriptive prose. It SHALL NOT pass a schema, a field list, a vocabulary or a flow
identifier to the reader, and SHALL NOT accept tags into the caption. A caption SHALL be written once per photograph,
under `photo/`, and every flow SHALL read that one caption.

Pressing a reader into a schema makes it invent: told never to leave a field blank, a reader manufactures identity
marks. Every flow is read under one briefing, the caption config's, on one model, so the prose is the photograph's and a
second reading would say the same ([D17](../../../docs/decisions.md#d17--input-above-flow-below)). The prohibition on
tags is scoped to this artifact: the tag stage writes tag lists for the same photograph, into its own directories, from
models given the photograph alone ([D1](../../../docs/decisions.md#d1--stage--is-two-independent-verbs)).

#### Scenario: the reader is given the photograph and nothing else
- **Key:** `caption:inputs:only-the-photograph-is-passed`
- **Layers:** unit
- **WHEN** a caption is produced
- **THEN** the reader receives the photograph and its standing instructions
- **AND** it receives no schema, no field list, no vocabulary and no flow identifier

#### Scenario: the artifact holds prose, not tags
- **Key:** `caption:output:artifact-is-prose`
- **Layers:** unit
- **WHEN** the caption artifact is written
- **THEN** its content is a single block of descriptive prose
- **AND** no structured field or tag list is stored inside the caption artifact

#### Scenario: every flow reads the one caption
- **Key:** `caption:output:every-flow-reads-one-caption`
- **Layers:** unit
- **WHEN** a photograph already captioned is captioned again, as a second flow's Prepare does
- **THEN** no second caption is written
- **AND** the run holds its one caption under `photo/`

#### Scenario: the reader's standing instructions come from the caption config
- **Key:** `caption:inputs:briefing-comes-from-the-config`
- **Layers:** unit
- **WHEN** a caption is produced
- **THEN** the standing instructions are read from the briefing the caption config names
- **AND** the caption records the digest of the instructions it was produced under

## REMOVED Requirements

### Requirement: The reader takes a photograph and its briefing, and returns prose for one flow

**Reason**: a caption is the photograph's, written once under `photo/` and read by every flow.

**Migration**: *The reader takes a photograph and its briefing, and returns the photograph's prose* replaces it; its
other keys stay, and `caption:output:caption-belongs-to-one-flow` gives way to
`caption:output:every-flow-reads-one-caption`.
