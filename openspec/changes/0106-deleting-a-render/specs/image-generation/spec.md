## ADDED Requirements

### Requirement: A render is discarded whole, and its approval is left short

The system SHALL let the operator discard one render by its image's path: it SHALL delete the image, then its record,
then its outputs group when that leaves the group empty, and SHALL delete no other file of the run. It SHALL refuse a
path that names no render, deleting nothing. The newest approval a discard leaves short of its count SHALL lack the
discarded image, and the next render SHALL render what it lacks as for any short approval, its listed seeds first; an
older approval SHALL be left as it is, since only the newest renders.

A render is a likeness of a person ([the threat model](../../../THREAT_MODEL.md)), so a failed one is deleted, never
hidden. The image goes first, so a discard cut short leaves a record with no image, which reads as unrendered, as a
render cut short does. An empty group would still read as work made from its approval.

```
outputs/001/  42.png  42.render.json  77.png  77.render.json
   discard 42 ─▶ outputs/001/  77.png  77.render.json
   discard 77 ─▶ outputs/001/ removed
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
- **WHEN** the only render of a group is discarded
- **THEN** the group's directory is gone
- **AND** the approval and its prompt are as they were

#### Scenario: the approval is left short
- **Key:** `image-generation:discard:the-approval-is-left-short`
- **Layers:** unit
- **WHEN** one render of the newest approval, rendered to its count, is discarded
- **THEN** the approval lacks one image

#### Scenario: a path naming no render is refused
- **Key:** `image-generation:discard:a-path-naming-no-render-is-refused`
- **Layers:** unit
- **WHEN** the path given is a sidecar, a prompt, or a file outside an outputs group
- **THEN** the discard is refused, naming the form a render's path takes
- **AND** no file is deleted
