## MODIFIED Requirements

### Requirement: The reader takes a photograph and returns prose, for one flow

The system SHALL pass a reader exactly one input — the photograph — and SHALL accept exactly one output:
descriptive prose. It SHALL NOT pass a schema, a field list, a vocabulary or a flow identifier to the
reader, and SHALL NOT accept tags into the caption. A caption SHALL be written inside the flow that
asked for it, and SHALL NOT be read by any other flow.

Pressing a reader into a schema is measured to make it invent. Instructed never to leave a field blank,
a reader manufactured nineteen identity marks across seven of ten subjects and its score fell from
0.518 to 0.307. That is a rule about what reaches the reader, and it is unchanged: the reader still
receives the photograph and its standing instructions and nothing else. What changes is who the answer
belongs to. A caption used to be written once per run and reused by any flow added later, which meant a
second flow silently inherited a reading written to answer a different question — its briefing is part
of its frozen directory, so two flows asking different questions were sharing one answer. Reuse was
worth that risk only while a reading was expensive: it costs $0.0159 per photograph at worst and $0.0013
cached and batched, against a boot that costs $0.036. Two flows over one input now read it twice, and
the class of error disappears rather than being checked for.

**The prohibition on tags is scoped to this artifact rather than to the run.** A separate stage produces
tag lists for the same photograph, into its own directories, from models given the photograph and
nothing else — and that stage exists precisely because asking one call for prose and tags at once would
rewrite the instruction the prose was measured under. What this requirement forbids is unchanged in
substance: a caption is prose, a reader is not asked for structure, and nothing about the tag stage
sends a schema or a field list to any model.

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

#### Scenario: a caption belongs to the flow that asked for it
- **Key:** `caption:output:caption-belongs-to-one-flow`
- **Layers:** unit
- **WHEN** a second flow is added to a run that already has a caption
- **THEN** the added flow produces its own caption
- **AND** the existing flow's caption is neither read nor changed

#### Scenario: the reader's standing instructions come from the flow
- **Key:** `caption:inputs:briefing-comes-from-the-flow`
- **Layers:** unit
- **WHEN** a caption is produced for a flow
- **THEN** the standing instructions are read from that flow's own directory
- **AND** the caption records the digest of the instructions it was produced under
