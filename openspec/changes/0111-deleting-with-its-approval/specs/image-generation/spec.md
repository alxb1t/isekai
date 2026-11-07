## ADDED Requirements

### Requirement: A render is discarded whole, and the newest approval goes with its last render

The system SHALL let the operator discard one render by its image's path: it SHALL delete the image, then its record,
then its outputs group when that leaves the group empty, and SHALL delete no other file of the run. It SHALL refuse a
path that names no render, deleting nothing. A discard that removes the group of the flow's newest approval, with no
draft waiting above it, SHALL then delete that approval's prompt and failure records and cancel the approval back to its
draft. The newest approval a discard leaves short of its count, its group still holding an image, SHALL lack the
discarded image, and the next render SHALL render what it lacks, its listed seeds first. An older approval, and the
newest one under a waiting draft, SHALL be left as they are.

A render is a likeness of a person ([the threat model](../../../THREAT_MODEL.md)), so a failed one is deleted, never
hidden. The image goes first, so a discard cut short leaves a record with no image, which reads as unrendered, as a
render cut short does. An empty group would still read as work made from its approval. An approval with no image left would read as
*approved* and render the same seed again; cancelled, it reads as a draft, its edits kept, and approving it again
undoes the delete. A cancel never replaces a waiting draft, so that draft keeps the approval.

```
outputs/001/  42.png  42.render.json  77.png  77.render.json
   discard 42 ─▶ outputs/001/  77.png  77.render.json
   discard 77 ─▶ outputs/001/ removed ─▶ prompts/001.json gone ─▶ review/001.approved.json back to 001.draft.json
```

#### Scenario: the image and its record are deleted, and nothing else
- **Key:** `image-generation:discard:the-image-and-its-record-are-deleted`
- **Layers:** unit
- **WHEN** one render of a group holding two is discarded
- **THEN** its image and its record are gone
- **AND** the other render, the approval and the prompt are as they were

#### Scenario: an emptied group is removed
- **Key:** `image-generation:discard:an-emptied-group-is-removed`
- **Layers:** unit
- **WHEN** the only render of a group is discarded through the render stage alone
- **THEN** the group's directory is gone
- **AND** the approval and its prompt are as they were

#### Scenario: the approval is left short
- **Key:** `image-generation:discard:the-approval-is-left-short`
- **Layers:** unit
- **WHEN** one render of the newest approval, rendered to its count of two, is discarded
- **THEN** the approval lacks one image

#### Scenario: the newest approval goes with its last render
- **Key:** `image-generation:discard:the-newest-approval-goes-with-its-last-render`
- **Layers:** unit
- **WHEN** the newest approval's group is gone and nothing waits above it
- **THEN** its prompt and failure records are deleted, and the approval is cancelled back to its draft
- **AND** a copy is deleted, as its cancel deletes it

#### Scenario: an older approval stays
- **Key:** `image-generation:discard:an-older-approval-stays`
- **Layers:** unit
- **WHEN** the group of an approval older than the flow's newest is gone
- **THEN** that approval and its prompt are as they were

#### Scenario: a waiting draft keeps the approval
- **Key:** `image-generation:discard:a-waiting-draft-keeps-the-approval`
- **Layers:** unit
- **WHEN** the newest approval's group is gone and a draft waits above it
- **THEN** the approval, its prompt and the draft are as they were

#### Scenario: a path naming no render is refused
- **Key:** `image-generation:discard:a-path-naming-no-render-is-refused`
- **Layers:** unit
- **WHEN** the path given is a sidecar, a prompt, or a file outside an outputs group
- **THEN** the discard is refused, naming the form a render's path takes
- **AND** no file is deleted

### Requirement: A flow renders on another flow's seeds when the operator names it, reading no copy's origin

When the operator names a source flow, the system SHALL render one image per seed of that flow's latest
render group for the same run, reading the seeds from filenames alone, and SHALL record the source flow on
each render. It SHALL refuse a run whose source flow has no render before any endpoint is acquired, SHALL
refuse a flow named as its own source, and SHALL accept neither a count nor an explicit seed beside a source.
It SHALL NOT read the flow's approval for where it came from: a copy holds
its own fields and seeds ([D49](../../../docs/decisions.md#d49--a-control-flow-is-its-subject-with-the-face-chain-at-zero-copied-once)).

```
isekai render <runs> S=1 T=S
   free pass: assemble S and T
   pod: render S into its latest approval's group, then T on those seeds
```

A render on the same seed starts from the same noise, so two flows differ only in what the operator changed
between them; a fresh seed would add a difference of its own as large as the one measured.

#### Scenario: one render per source seed
- **Key:** `image-generation:seeds-from:one-render-per-source-seed`
- **Layers:** unit
- **WHEN** a flow is rendered with a source flow named and the source holds renders for the run
- **THEN** the flow renders exactly the source's latest group's seeds
- **AND** each render's record names the source flow

#### Scenario: a run without a source render is refused before the session
- **Key:** `image-generation:seeds-from:no-source-render-is-refused-first`
- **Layers:** unit
- **WHEN** a source flow is named and a run holds no render of it
- **THEN** the run is refused naming the source flow and the command that renders it
- **AND** no endpoint is contacted

#### Scenario: a flow is not its own source
- **Key:** `image-generation:seeds-from:a-flow-is-not-its-own-source`
- **Layers:** unit
- **WHEN** the source flow named is one of the flows being rendered
- **THEN** the invocation is refused naming the flow

#### Scenario: a source excludes a count and explicit seeds
- **Key:** `image-generation:seeds-from:excludes-count-and-seeds`
- **Layers:** unit
- **WHEN** a source flow is named beside a count or an explicit seed
- **THEN** the invocation is refused before any run is opened

## MODIFIED Requirements

### Requirement: A control flow equals its subject flow but for the dials it zeroes

The system SHALL hold a control flow equal to its subject flow: the graph and the schema byte for byte,
and the manifest equal once the identifier and the face dials are set aside, with those
dials at zero. A difference anywhere else SHALL fail the suite naming the file.

```
flows/summon-anime-wai/                    flows/control-anime-wai/
  flow.json   ip_weight 0.9, cn 0.8   ──▶    flow.json   the identifier; ip_weight 0, cn 0
  graph.json                          ══▶    graph.json           byte-identical
  schema.json                         ══▶    schema.json          byte-identical
```

A control is a floor only while it differs from its subject in exactly the thing under test. Each flow is
pinned by its own digest, so a drift in the subject is caught by its pin and by the control's equality,
and the two move together or not at all
([D49](../../../docs/decisions.md#d49--a-control-flow-is-its-subject-with-the-face-chain-at-zero-copied-once)).

#### Scenario: the control's files equal the subject's
- **Key:** `image-generation:control:files-equal-the-subject`
- **Layers:** unit
- **WHEN** the control flow's graph and schema are compared with the subject's
- **THEN** each is byte-identical

#### Scenario: the manifests differ only in the identifier and the face dials
- **Key:** `image-generation:control:manifest-differs-only-in-the-face-dials`
- **Layers:** unit
- **WHEN** the two manifests are compared with the identifier and the face dials set aside
- **THEN** they are equal
- **AND** the control's face dials are zero

## REMOVED Requirements

### Requirement: A render is discarded whole, and its approval is left short

**Reason**: the newest approval now goes with its last render ([D1](../../changes/0111-deleting-with-its-approval/design.md#d1)).
**Migration**: replaced by *A render is discarded whole, and the newest approval goes with its last render*; nothing on
disk moves.

### Requirement: A flow renders on another flow's seeds when the operator names it

**Reason**: the checks of a copy against its source go; a copy holds its own seeds
([D5](../../changes/0111-deleting-with-its-approval/design.md#d5)).
**Migration**: replaced by *A flow renders on another flow's seeds when the operator names it, reading no copy's
origin*; `--in-step-with` is deleted, and `render` runs no check before the pod for a source it renders first.
