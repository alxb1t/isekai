## REMOVED Requirements

### Requirement: The revise verb takes image paths, and writes every draft or none

**Reason**: one verb drafts any flow from images; its own flow is a revision.

**Migration**: `isekai draft --flow <the image's flow> <image>…`; the scenarios hold under *The draft verb drafts a flow
from image paths, and writes every draft or none*.

### Requirement: The review verb drafts from another flow's approval with `--from`

**Reason**: a draft from another flow starts from an image, as the page's does.

**Migration**: `isekai draft --flow <target> <image>…` takes the image's approval; `review` keeps `--new-version` and
`--discard`.

## ADDED Requirements

### Requirement: The draft verb drafts a flow from image paths, and writes every draft or none

The system SHALL offer `isekai draft --flow FLOW <image>…`, which reads from each image path its run, flow, approval and
seed, checks every image before writing anything — the image exists, its approval can be read, the target holds no
waiting draft with edits of its own, and no two images share a run and target — and then writes, through the review
stage, a revision where `FLOW` is the image's own flow and a draft from its approval where it is another, assigning a
target with no sheet and filling its sheet from the source's tags; when any check fails it SHALL write nothing and name
every image that failed, with its reason. It SHALL tell two images' runs apart by the identity of their directories,
never by the text of their paths.

An image's path names everything a draft needs but its target, so the verb takes nothing else. A selection is drafted
whole or not at all, so a retry after a fix does not meet the drafts the first try wrote. A target with no sheet needs
no Prepare: the source's tags are the target's.

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
- **THEN** the target is assigned, its sheet filled from the source's tag list, and its draft written
- **AND** no caption or tag list is written for the target

#### Scenario: another flow is drafted from the image
- **Key:** `cli:draft:another-flow-is-drafted-from-the-image`
- **Layers:** unit
- **WHEN** the verb is given a summon image and another flow
- **THEN** the target's draft holds the image's approval's shared fields, its seed and its image
