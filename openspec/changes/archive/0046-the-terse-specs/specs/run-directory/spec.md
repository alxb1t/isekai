## MODIFIED Requirements

### Requirement: Every artifact declares its schema and what produced it

The system SHALL write every artifact with a schema name and version and a producer record, and SHALL
record in the producer which upstream artifact version the work was derived from.

A producer that names only a model cannot explain its result. The instruction text shapes what comes back, so its
digest is recorded beside the model that read it. Instructions fixed by this build rather than by a flow have
bytes to hash and no path, and a record that invented a path would assert a location that does not exist.

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

### Requirement: A run root is under the ignored root or outside the repository

The system SHALL refuse a run root inside the repository's working tree unless it is under the ignored
data root, and SHALL accept one outside the repository. It SHALL decide containment by the identity of
the directories, never by comparing the text of their paths.

A run holds a copy of the photograph, so a run root git can reach is one `git add` from publishing a
likeness ([D18](../../../docs/decisions.md#d18--runs-stay-out-of-what-git-tracks)). Two spellings of
one directory are one directory, and only its identity says so.

#### Scenario: a run root inside the working tree and outside the ignored root is refused
- **Key:** `run-directory:containment:in-tree-run-root-is-refused`
- **Layers:** unit
- **WHEN** a run root resolves to a path inside the repository working tree that is not under the
  ignored data root
- **THEN** the invocation is refused before any run is created
- **AND** the message names the path given and what would be accepted

#### Scenario: a differently-spelled name for a directory inside the tree is still inside it
- **Key:** `run-directory:containment:containment-is-decided-by-identity`
- **Layers:** unit
- **WHEN** a run root names a directory inside the working tree by a spelling the filesystem treats as
  the same directory but a textual comparison does not
- **THEN** the invocation is refused exactly as the plainly-spelled path would be

#### Scenario: a run root outside the repository is accepted
- **Key:** `run-directory:containment:external-run-root-is-accepted`
- **Layers:** unit
- **WHEN** a run root resolves to a path outside the repository working tree
- **THEN** it is accepted and runs are created under it
- **AND** no containment check applies to it

#### Scenario: the default run root is under the ignored root
- **Key:** `run-directory:containment:default-is-the-ignored-root`
- **Layers:** unit
- **WHEN** no run root is given
- **THEN** runs are created under the repository's ignored data root

### Requirement: The run directory is input above, flow below, and every artifact is a flow's own

The system SHALL place the input and its frame at the root of a run, and SHALL place every artifact any
stage produces under a directory named for the flow that produced it. It SHALL NOT place any stage's
artifacts above the flow level, and SHALL NOT let one flow read another flow's artifacts.

```
runs/<input-id>/
├── run.json, the photograph      shared by every flow, copied once
└── <flow-id>/                    one subtree per flow
    └── captions/ wd14/ tags/ sheets/ review/ prompts/ outputs/
```

Above the split sits the one thing every flow shares, the input. A flow adds one subtree, and retiring one flow's
work for one input removes one directory ([D17](../../../docs/decisions.md#d17--input-above-flow-below)). A caption
written under one flow's briefing can never be picked up by another flow, because the two never name the same
directory, and a stage directory that is absent records that the flow did not declare what would fill it.

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

### Requirement: A resume check asks the flow what it produces rather than assuming an image

The system SHALL determine which of a flow's outputs are already produced from filenames alone, using
the output form that flow declares, and SHALL NOT assume any particular image format.

A listing with an image extension written into it would report a non-image flow's finished work as missing and
render it again, on the one stage that costs money on every pass.

#### Scenario: the completed-output check is not tied to one format
- **Key:** `run-directory:listings:resume-does-not-assume-an-image-format`
- **Layers:** unit
- **WHEN** the set of already-produced outputs is computed for a flow
- **THEN** it is derived from the output form that flow declares
- **AND** no image format is named in the predicate

### Requirement: Inspection reads the flows root it was given, and refuses before it prints

The system SHALL resolve a run's flows through the flows root the invocation supplies rather than a
default, and SHALL refuse a run holding a directory no flow answers for before any line of the report is
printed.

A verb that takes an injected root and reads another is a seam that is not one: a run captured under another root
cannot be inspected, and inspection's whole job is reading a run in any state. The report streams, so a refusal
after output begins leaves a partial account with no way to tell which lines were complete.

#### Scenario: inspection reads the flows root it is given
- **Key:** `run-directory:inspection:the-injected-flows-root-is-used`
- **Layers:** unit
- **WHEN** a run is inspected with a flows root supplied by the invocation
- **THEN** the flows it reports are resolved through that root

#### Scenario: a directory no flow answers for refuses before any line is printed
- **Key:** `run-directory:inspection:an-unanswerable-directory-refuses-first`
- **Layers:** unit
- **WHEN** a run holds a directory no tracked flow answers for
- **THEN** the invocation is refused
- **AND** no line of the report has been printed
