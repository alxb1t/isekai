## MODIFIED Requirements

### Requirement: Every artifact declares its schema and what produced it

The system SHALL write every artifact with a schema name and version and a producer record, and SHALL
record in the producer which upstream artifact version the work was derived from.

A producer that names only a model cannot explain its own result. The instruction text given to a
reader is the variable with the largest measured effect on what comes back — one briefing change moved
a reader's score from 0.518 to 0.307 and manufactured nineteen identity marks that were not in the
photographs — so the digest of that text is recorded beside the model that read it. Instruction text
does not always come from a file: a producer whose instructions are fixed by this build rather than by
a flow has bytes to hash and no path to name, and a record that invented a path for it would assert a
location that does not exist.

#### Scenario: an artifact carries its schema name and version
- **Key:** `run-directory:provenance:artifact-declares-its-schema`
- **Layers:** unit
- **WHEN** any artifact is written
- **THEN** it carries a schema name and an integer version
- **AND** a reader handed an unknown version refuses rather than parsing it

#### Scenario: a producer records the instruction text it was given
- **Key:** `run-directory:provenance:producer-records-the-briefing`
- **Layers:** unit
- **WHEN** a stage that is given instruction text writes its artifact
- **THEN** the producer records that text's digest, and its path where the text has one
- **AND** two artifacts written under different instructions are distinguishable from the record alone

#### Scenario: a producer records which upstream version it came from
- **Key:** `run-directory:provenance:producer-records-its-source`
- **Layers:** unit
- **WHEN** an artifact is derived from an earlier stage's artifact
- **THEN** its producer names that artifact's version number
- **AND** the chain from the render back to the photograph is traceable without a second numbering scheme

#### Scenario: an unpinnable producer says so rather than claiming a pin
- **Key:** `run-directory:provenance:unpinned-producer-is-declared`
- **Layers:** unit
- **WHEN** the producer is a hosted service that exposes no immutable revision
- **THEN** the record declares that it is not pinned
- **AND** it does not carry a revision or digest field that would be untrue

### Requirement: The run directory is input above, flow below, and every artifact is a flow's own

The system SHALL place the input and its frame at the root of a run, and SHALL place every artifact any
stage produces under a directory named for the flow that produced it. It SHALL NOT place any stage's
artifacts above the flow level, and SHALL NOT let one flow read another flow's artifacts.

The layout is a picture of the coupling rather than a filing convention: above the flow split sits what
every flow shares, and after this change the only thing every flow shares is the input itself, copied
once however many flows run. Nesting stage-first meant adding a flow scattered four entries across four
stage directories; nesting flow-first means adding a flow adds one subtree, and retiring one flow's work
for one input is removing one directory. Keeping captions below the split is what makes a flow's
briefing binding: a caption written under one flow's instructions can never be picked up by a flow whose
instructions differ, because the two never name the same directory. The same holds for every artifact a
photograph yields, including those a flow cannot produce at all: a stage directory that is simply absent
is how a run records that a flow did not declare what it would take to fill it.

#### Scenario: every stage writes under the flow
- **Key:** `run-directory:layout:stage-artifacts-live-under-the-flow`
- **Layers:** unit
- **WHEN** a run has been carried through every stage for a flow
- **THEN** that flow's captions, tag lists, sheets, reviews, prompts and outputs are all under one
  directory named for the flow
- **AND** the only entries above it are the input and its frame

#### Scenario: a second flow adds one subtree
- **Key:** `run-directory:layout:a-second-flow-adds-one-subtree`
- **Layers:** unit
- **WHEN** a second flow is carried through a run that already holds one
- **THEN** exactly one new directory appears, named for that flow
- **AND** the first flow's artifacts are unchanged

#### Scenario: the input is copied once however many flows run
- **Key:** `run-directory:layout:the-input-is-copied-once`
- **Layers:** unit
- **WHEN** several flows are run over one input
- **THEN** the run holds exactly one copy of the input
- **AND** its frame is written once

#### Scenario: removing one flow's work leaves the others intact
- **Key:** `run-directory:layout:one-flow-s-work-is-one-directory`
- **Layers:** unit
- **WHEN** one flow's directory is removed from a run
- **THEN** every other flow's artifacts remain readable
- **AND** the input and its frame remain
