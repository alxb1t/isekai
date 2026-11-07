## ADDED Requirements

### Requirement: A render is discarded whole, and its approval goes with its last render

The system SHALL let the operator discard one render by its image's path: it SHALL delete the image, then its record,
then its outputs group when that leaves the group empty. It SHALL refuse a path that names no render, deleting nothing.
A discard that removes an approval's group SHALL then delete that approval, its prompt, its failure records and its
source copy; every older approval of the flow with no group SHALL go the same way, and, where the approval was the
flow's newest, so SHALL the draft waiting above it and that draft's source copy. Nothing SHALL be cancelled back to a
draft. A flow left with no approval SHALL lose every file under its sheets, reviews, prompts and sources and those
directories, and its outputs directory when empty, keeping its own empty directory, which is its assignment; the
photograph's caption and tag lists SHALL stay. An approval whose group still holds an image SHALL stay, lacking the
discarded image, and the next render SHALL render what it lacks, its listed seeds first. A newer approval with no
group, and every outputs group no approval going names, SHALL stay.

A render is a likeness of a person ([the threat model](../../../THREAT_MODEL.md)), so a failed one is deleted, never
hidden. The image goes first, so a discard cut short leaves a record with no image, which reads as unrendered, as a
render cut short does. An approval with no image left would read as *approved* and render the same seed again, and a
draft or a sheet left behind would offer the deleted work for review again: the operator deleted it to be rid of it
([D50](../../../docs/decisions.md#d50--the-last-render-takes-its-approval-and-a-flow-holds-only-its-own-files)). A
newer approval with no render yet is waiting for its render, not left by one.

```
outputs/001/ 42.png 42.render.json 77.png 77.render.json   review/ 001.approved.json   sheets/ 001.json
   discard 42 ─▶ outputs/001/ 77.png 77.render.json         001 stays, short of one
   discard 77 ─▶ outputs/001/ removed ─▶ prompts/001.json, review/001.approved.json gone
              ─▶ no approval left ─▶ sheets/ review/ prompts/ outputs/ gone ─▶ <flow>/ empty: assigned
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

#### Scenario: the approval goes with its last render
- **Key:** `image-generation:discard:the-approval-goes-with-its-last-render`
- **Layers:** unit
- **WHEN** the newest approval's group is gone, a draft waits above it, and an older approval still holds an image
- **THEN** the approval, its prompt, its failure records and its source copy are deleted, and so is the waiting draft
- **AND** no draft is written, and the older approval and its group are as they were

#### Scenario: older approvals with no render go
- **Key:** `image-generation:discard:older-render-less-approvals-go`
- **Layers:** unit
- **WHEN** an approval's group is gone, an older approval has no group and the oldest still holds an image
- **THEN** the approval and the older one with no group are deleted
- **AND** the oldest stays, and an approval whose group holds an image is never deleted

#### Scenario: a flow with no approval left keeps only its assignment
- **Key:** `image-generation:discard:a-flow-with-no-approval-keeps-its-assignment`
- **Layers:** unit
- **WHEN** the group of a flow's only approval is gone
- **THEN** the flow's directory is empty, and the photograph's caption and tag lists are as they were
- **AND** an outputs group no approval names, holding an image, stays with its outputs directory

#### Scenario: a path naming no render is refused
- **Key:** `image-generation:discard:a-path-naming-no-render-is-refused`
- **Layers:** unit
- **WHEN** the path given is a sidecar, a prompt, or a file outside an outputs group
- **THEN** the discard is refused, naming the form a render's path takes
- **AND** no file is deleted

## REMOVED Requirements

### Requirement: A render is discarded whole, and the newest approval goes with its last render

**Reason**: an approval's last render now deletes it, with older ones holding no render and, once none is left, the
flow's sheets, rather than cancelling the newest back to its draft
([D1](../../changes/0112-deleting-a-render-whole/design.md#d1)).
**Migration**: replaced by *A render is discarded whole, and its approval goes with its last render*; nothing on disk
moves. The leftovers of the old delete are swept by a one-off after release.
