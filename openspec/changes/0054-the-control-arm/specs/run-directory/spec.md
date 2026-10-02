## MODIFIED Requirements

### Requirement: The run directory is input above, flow below, and every artifact is a flow's own

The system SHALL place the input and its frame at the root of a run, and SHALL place every artifact any
stage produces under a directory named for the flow that produced it. It SHALL NOT place any stage's
artifacts above the flow level, and SHALL NOT let one flow read another flow's artifacts, except where the
operator names a source flow; then what is written SHALL record the source.

```
runs/<input-id>/
├── run.json, the photograph      shared by every flow, copied once
└── <flow-id>/                    one subtree per flow
    └── captions/ wd14/ tags/ sheets/ review/ prompts/ outputs/
```

Above the split sits the one thing every flow shares, the input. A flow adds one subtree, and retiring one flow's
work for one input removes one directory ([D17](../../../../docs/decisions.md#d17--input-above-flow-below)). A caption
written under one flow's briefing can never be picked up by another flow, because the two never name the same
directory, and a stage directory that is absent records that the flow did not declare what would fill it. A
source flow the operator names is not a flow reaching into another on its own, and the record of it is what keeps
the two flows comparable
([D38](../../../../docs/decisions.md#d38--a-control-flow-is-its-subject-with-the-face-chain-at-zero)).

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

#### Scenario: a named source is the one crossing, and it is recorded
- **Key:** `run-directory:layout:a-named-source-is-recorded`
- **Layers:** unit
- **WHEN** a stage writes under one flow from another flow the operator named as its source
- **THEN** the artifact written records the source flow
- **AND** the source flow's artifacts are unchanged
