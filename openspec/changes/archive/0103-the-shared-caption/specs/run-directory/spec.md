## ADDED Requirements

### Requirement: The run directory is the input and its photograph's description above, and each flow's work below

The system SHALL place the input, its frame and the photograph's description at the root of a run — the caption and
both tag lists, under `photo/` — and SHALL place every other artifact a stage produces under a directory named for the
flow that produced it. Every flow SHALL read the one description under `photo/`. It SHALL NOT let one flow read another
flow's artifacts, except where the operator names a source flow; then what is written SHALL record the source. It SHALL
NOT count `photo/` among a run's flows, and SHALL refuse to assign a flow named `photo`.

```
runs/<input-id>/
├── run.json, the photograph      shared by every flow, copied once
├── photo/                        the photograph's description, read by every flow
│   └── captions/ wd14/ tags/
└── <flow-id>/                    one subtree per flow
    └── sheets/ review/ prompts/ outputs/
```

Every flow reads a photograph under one briefing, one model, one pinned tagger and one prompt, so the description is the
photograph's rather than a flow's, and it is written once. A flow adds one subtree, and retiring one flow's work for one
input removes one directory ([D17](../../../docs/decisions.md#d17--input-above-flow-below)). A source flow the operator
names is not a flow reaching into another on its own, and the record of it is what keeps the two flows comparable
([D38](../../../docs/decisions.md#d38--a-control-flow-is-its-subject-with-the-face-chain-at-zero)).

#### Scenario: each flow's work is under the flow, and the description under photo/
- **Key:** `run-directory:layout:stage-artifacts-live-under-the-flow`
- **Layers:** unit
- **WHEN** a run has been carried through every stage for a flow
- **THEN** that flow's sheets, reviews, prompts and outputs are all under one directory named for the flow
- **AND** the only entries above it are the input, its frame and `photo/`, which holds the caption and tag lists

#### Scenario: every flow reads the one description
- **Key:** `run-directory:layout:every-flow-reads-the-description`
- **Layers:** unit
- **WHEN** two flows are carried through a run
- **THEN** `photo/` holds one caption and one list of each tagger's
- **AND** neither flow's directory holds a caption or a tag list

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
- **AND** the input, its frame and `photo/` remain

#### Scenario: a named source is the one crossing, and it is recorded
- **Key:** `run-directory:layout:a-named-source-is-recorded`
- **Layers:** unit
- **WHEN** a stage writes under one flow from another flow the operator named as its source
- **THEN** the artifact written records the source flow
- **AND** the source flow's artifacts are unchanged

#### Scenario: photo is no flow
- **Key:** `run-directory:layout:photo-is-no-flow`
- **Layers:** unit
- **WHEN** a run holding `photo/` is asked for its flows
- **THEN** `photo` is not among them
- **AND** assigning a flow named `photo` is refused, naming the name reserved

### Requirement: A run whose description sits under its flows is refused until it is migrated

The system SHALL refuse to read or write a run's description when a flow's directory in that run holds a caption, a
WD14 list or a hosted tag list and `photo/` holds none of that kind, naming the run and the command that migrates it,
and writing nothing. Inspection SHALL read such a run as it reads any other.

A run written before the description was shared keeps it under its flows. Reading `photo/` alone would treat it as
never tagged, and reading both would keep a second path alive for good; the refusal names the one fix, which copies
the description once.

#### Scenario: an unmigrated run is refused by name
- **Key:** `run-directory:migration:an-unmigrated-run-is-refused`
- **Layers:** unit
- **WHEN** a stage reads or writes the description of a run whose flow holds a caption or a tag list `photo/` lacks
- **THEN** it is refused, naming the run and `isekai migrate`
- **AND** nothing is written

#### Scenario: a migrated run is read from photo/
- **Key:** `run-directory:migration:a-migrated-run-reads-photo`
- **Layers:** unit
- **WHEN** a run's flows still hold their old copies and `photo/` holds each kind they hold
- **THEN** every stage reads the description from `photo/`
- **AND** the old copies are neither read nor changed

## MODIFIED Requirements

### Requirement: A failure is recorded as an attempt, never as a completion

The system SHALL record a stage's failure as a sibling of the artifact it failed to produce, SHALL
carry the attempt's ordinal and its kind in that file's name, and SHALL NOT consume the artifact's
version number with a failure.
The sheet stage SHALL record a damaged tag list and a tag outside the vocabulary as permanent failures, and
SHALL record nothing when the photograph has no tag list.

Two stages take their version number from an upstream artifact rather than counting their own, so
"a retry writes the next number" has no next number to write there. Putting the kind and the ordinal in
the name is what keeps the retry decision a directory listing, which is the same rule the completion
tests are held to. The sheet stage is deterministic, so what fails once fails again
([D21](../../../docs/decisions.md#d21--retries-follow-what-can-fail)); an absent tag list is fixed by running
`tag`, and a record would bar the sheet that follows.

#### Scenario: an error file names the artifact it stands in for
- **Key:** `run-directory:failure:error-is-a-sibling-of-its-artifact`
- **Layers:** unit
- **WHEN** a stage fails
- **THEN** an error record is written beside where its artifact would have gone
- **AND** the artifact's version number is still available to a later successful attempt

#### Scenario: the attempt's kind and ordinal are in the filename
- **Key:** `run-directory:failure:kind-and-attempt-are-in-the-filename`
- **Layers:** unit
- **WHEN** an error record is written
- **THEN** its filename carries the attempt's ordinal and whether the failure was transient or permanent
- **AND** counting attempts requires no file to be opened

#### Scenario: a failed attempt is kept when a later one succeeds
- **Key:** `run-directory:failure:failed-attempts-survive-the-fix`
- **Layers:** unit
- **WHEN** a stage succeeds after an earlier failure
- **THEN** the earlier error record is still present
- **AND** the artifact is written under the number the failure did not take

#### Scenario: a sheet's failure is recorded as permanent
- **Key:** `run-directory:failure:a-sheet-failure-is-permanent`
- **Layers:** unit
- **WHEN** the sheet stage refuses a damaged tag list or a tag outside the vocabulary
- **THEN** a permanent error record is written beside the sheet it failed to produce
- **AND** the refusal names the record and its deletion

#### Scenario: an absent tag list leaves no record
- **Key:** `run-directory:failure:an-absent-tag-list-leaves-no-record`
- **Layers:** unit
- **WHEN** the sheet stage refuses a flow that declares the tagger, for a photograph that holds no tag list
- **THEN** no error record is written

## REMOVED Requirements

### Requirement: The run directory is input above, flow below, and every artifact is a flow's own

**Reason**: the caption and both tag lists are the photograph's, written once under `photo/` and read by every flow.

**Migration**: *The run directory is the input and its photograph's description above, and each flow's work below*
replaces it, with the same keys and `run-directory:layout:every-flow-reads-the-description` and
`run-directory:layout:photo-is-no-flow` added; `isekai migrate` copies a run's per-flow description into `photo/`.
