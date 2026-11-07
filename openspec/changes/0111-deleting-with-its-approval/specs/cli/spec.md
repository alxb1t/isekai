## MODIFIED Requirements

### Requirement: The discard verb deletes a render named by its image path

The system SHALL offer `isekai discard <image>`, which reads the run, flow, approval and seed from the image's path,
deletes the image's own thumbnail from the cache of the library whose collection holds the run, discards the render
through the render stage, then, where that removed the group of the flow's newest approval with no draft waiting above
it, deletes that approval's prompt and failure records and cancels it back to its draft; it prints each path it
deleted, a run's file from its runs root and a thumbnail from its library. A path that names no render SHALL be refused, naming the form a render's path takes, the verb exiting 1 and
deleting nothing.

The hand path stays ([D3](../../../docs/decisions.md#d3--the-hand-path-stays)): the page's Delete is this verb's act,
run in the server's process. An image's path names everything a discard needs, so the verb takes nothing else.

#### Scenario: the render and its thumbnail are deleted
- **Key:** `cli:discard:the-render-and-its-thumbnail-are-deleted`
- **Layers:** unit
- **WHEN** the verb is given the path of a render in a collection's run whose thumbnail is cached
- **THEN** the image, its record and the thumbnail are deleted
- **AND** each deleted path is printed, and the verb exits 0

#### Scenario: the last render takes its approval with it
- **Key:** `cli:discard:the-last-render-takes-its-approval`
- **Layers:** unit
- **WHEN** the verb is given the path of the only render of the flow's newest approval, its prompt assembled
- **THEN** the group, the prompt and the approval are deleted, each printed, and the draft is back
- **AND** another collection's thumbnail of the same photograph and seed stays

#### Scenario: a path naming no render is refused
- **Key:** `cli:discard:a-path-naming-no-render-is-refused`
- **Layers:** unit
- **WHEN** the verb is given a path that is no render
- **THEN** it exits 1, naming the path and the form a render's path takes
- **AND** no file is deleted
