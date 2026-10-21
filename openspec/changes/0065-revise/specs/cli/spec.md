## ADDED Requirements

### Requirement: The revise verb takes image paths, and writes every draft or none

The system SHALL offer a verb that takes the paths of rendered images, reads from each its run, flow, approval and
seed, checks every image before writing anything — the image exists, its flow holds no unapproved draft, and no two
images share a run and flow — and then writes a revision for each, or, when any check fails, writes nothing and names
every image that failed, with its reason.

An image's path names everything a revision needs, so the verb takes nothing else. A selection is revised whole or
not at all, so a retry after a fix does not meet the drafts the first try wrote.

#### Scenario: every image is revised
- **Key:** `cli:revise:every-image-is-revised`
- **Layers:** unit
- **WHEN** the verb is given two images from different runs
- **THEN** each run's flow gains a revision of its image

#### Scenario: one refusal writes nothing
- **Key:** `cli:revise:one-refusal-writes-nothing`
- **Layers:** unit
- **WHEN** one of the images given has its flow's draft waiting
- **THEN** no draft is written for any image
- **AND** the refusal names that image and its reason
