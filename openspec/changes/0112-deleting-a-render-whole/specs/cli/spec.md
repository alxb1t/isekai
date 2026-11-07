## MODIFIED Requirements

### Requirement: The discard verb deletes a render named by its image path

The system SHALL offer `isekai discard <image>`, which reads the run, flow, approval and seed from the image's path,
deletes the image's own thumbnail from the cache of the library whose collection holds the run, discards the render
through the render stage, then, where that removed an approval's group, deletes that approval and what goes with it,
as the render stage's discard says — older approvals with no render, the newest's waiting draft and, once no approval
is left, the flow's sheets — writing no draft; it prints each path it deleted, a run's file from its runs root and a
thumbnail from its library. A path that names no render SHALL be refused, naming the form a render's path takes, the
verb exiting 1 and deleting nothing; so SHALL a discard while a render session holds the image's collection, as the
app's delete is.

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
- **WHEN** the verb is given the path of the only render of the flow's only approval, its prompt assembled
- **THEN** the group, the prompt, the approval, the sheet and the emptied directories are deleted, each printed
- **AND** no draft is written, and the flow's directory is left empty
- **AND** another collection's thumbnail of the same photograph and seed stays

#### Scenario: a running render refuses it
- **Key:** `cli:discard:a-running-render-refuses-it`
- **Layers:** unit
- **WHEN** the verb is given the path of a render in a collection whose render session holds its record's lock
- **THEN** it exits 1, saying a render session is running
- **AND** the image, its record and its thumbnail are not deleted

#### Scenario: a path naming no render is refused
- **Key:** `cli:discard:a-path-naming-no-render-is-refused`
- **Layers:** unit
- **WHEN** the verb is given a path that is no render
- **THEN** it exits 1, naming the path and the form a render's path takes
- **AND** no file is deleted

### Requirement: The draft verb drafts a flow from image paths, and writes every draft or none

The system SHALL offer `isekai draft --flow FLOW <image>…`, which reads from each image path its run, flow, approval and
seed, checks every image before writing anything — the image exists, its approval can be read, the target holds no
waiting draft with edits of its own, and no two images share a run and target — and then writes, through the review
stage, a revision where `FLOW` is the image's own flow and a draft from its approval where it is another, assigning a
target with no sheet and filling its sheet from the photograph's tags, and copying another flow's image into the
target's sources; when any check fails it SHALL write nothing and name every image that failed, with its reason. It SHALL tell two images' runs apart by the identity of their
directories, never by the text of their paths.

An image's path names everything a draft needs but its target, so the verb takes nothing else. A selection is drafted
whole or not at all, so a retry after a fix does not meet the drafts the first try wrote. A target with no sheet needs
no Prepare: the photograph's tags are every flow's.

#### Scenario: every image is revised
- **Key:** `cli:revise:every-image-is-revised`
- **Layers:** unit
- **WHEN** the verb is given two images from different runs and their own flow
- **THEN** each run's flow gains a revision of its image

#### Scenario: one refusal writes nothing
- **Key:** `cli:revise:one-refusal-writes-nothing`
- **Layers:** unit
- **WHEN** one image given has its target's edited draft waiting, an unreadable approval, or another's run and target
- **THEN** no draft is written for any image
- **AND** the refusal names that image and its reason

#### Scenario: a target with no sheet is assigned and filled first
- **Key:** `cli:review-from:a-target-with-no-sheet-is-filled-first`
- **Layers:** unit
- **WHEN** `draft --flow` names a target an image's run is not assigned to
- **THEN** the target is assigned, its sheet filled from the photograph's tag list, and its draft written
- **AND** no caption or tag list is written for the target

#### Scenario: another flow is drafted from the image
- **Key:** `cli:draft:another-flow-is-drafted-from-the-image`
- **Layers:** unit
- **WHEN** the verb is given a summon image and another flow
- **THEN** the target's draft holds the image's approval's shared fields and its seed, and records no image
- **AND** the target's sources hold a copy of the image under the draft's number
