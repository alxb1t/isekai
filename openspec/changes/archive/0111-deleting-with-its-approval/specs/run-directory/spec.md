## MODIFIED Requirements

### Requirement: Artifacts are append-only and numbered, and re-running a command is a no-op

The system SHALL number each stage's artifacts within that stage's own directory, SHALL never overwrite
a written artifact, and SHALL make a command whose artifact already exists do nothing — write nothing,
call nothing — unless a new version is explicitly requested. It SHALL delete a render's image and
record only when the operator discards that render, and SHALL delete an approval, its prompt and its
failure records with the newest approval's last render.

Idempotence is what makes resume ordinary: there is no special mode and no state machine, because
running every command again is the whole of it. It is also the only defence against a shell loop
retrying after a network blip and silently burning a call. A render is a likeness, so the one way it
leaves a run is the operator's ask; an approval with nothing left made from it goes with it, so the
Hub reads a draft rather than an approval short of the image just deleted.

#### Scenario: re-running a completed command changes nothing
- **Key:** `run-directory:idempotence:rerun-is-a-no-op`
- **Layers:** unit
- **WHEN** a command runs against a run whose artifact for that stage already exists
- **THEN** no file in the run directory changes
- **AND** no call is made to any external service

#### Scenario: a new version is an explicit act
- **Key:** `run-directory:idempotence:new-version-must-be-asked-for`
- **Layers:** unit
- **WHEN** a command is asked explicitly for a new version
- **THEN** the next number is written
- **AND** the previous version is left exactly as it was

#### Scenario: numbering is per directory and linked by provenance
- **Key:** `run-directory:numbering:each-directory-counts-its-own`
- **Layers:** unit
- **WHEN** two stages each write artifacts for the same run
- **THEN** each stage's numbers are assigned within its own directory
- **AND** the link between them is the producer record, not a shared counter

#### Scenario: approving an approved flow writes nothing
- **Key:** `run-directory:idempotence:approving-an-approved-flow-writes-nothing`
- **Layers:** unit
- **WHEN** approval is asked for a flow that is already approved and still holds a draft numbered below its approval
- **THEN** no file in the run directory changes
- **AND** the command reports the stage as already complete

#### Scenario: the newest approval goes with its last render
- **Key:** `run-directory:idempotence:the-newest-approval-goes-with-its-last-render`
- **Layers:** unit
- **WHEN** the operator discards the only render of a flow's newest approval
- **THEN** that approval, its prompt and its failure records are gone, and its draft is back
- **AND** every other file of the run is as it was

### Requirement: The run directory is the input and its photograph's description above, and each flow's work below

The system SHALL place the input, its frame and the photograph's description at the root of a run — the caption and
both tag lists, under `photo/` — and SHALL place every other artifact a stage produces under a directory named for the
flow that produced it. Every flow SHALL read the one description under `photo/`. It SHALL NOT let one flow read another
flow's artifacts, except where the operator names a source flow; then a render SHALL record the source, and a copied
approval or a draft from it SHALL hold its own fields and seeds, reading the source no more. It SHALL
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
names is not a flow reaching into another on its own. A copy is taken once and holds what it took, so the source's
approval can always go
([D49](../../../docs/decisions.md#d49--a-control-flow-is-its-subject-with-the-face-chain-at-zero-copied-once)).

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
- **WHEN** a flow renders on the seeds of another flow the operator named as its source
- **THEN** each render's record names the source flow
- **AND** the source flow's artifacts are unchanged

#### Scenario: photo is no flow
- **Key:** `run-directory:layout:photo-is-no-flow`
- **Layers:** unit
- **WHEN** a run holding `photo/` is asked for its flows
- **THEN** `photo` is not among them
- **AND** assigning a flow named `photo` is refused, naming the name reserved
