## MODIFIED Requirements

### Requirement: A revision is a draft from the approval that made the image, its seed prefilled

The system SHALL write, for a rendered image, the next numbered draft of its flow copied from the approval the image was
rendered under — whether or not that is the newest — naming that approval in its producer, with a count of one and the
image's seed listed, and recording the image itself — its flow, version and seed — which the approval keeps. It SHALL
refuse, naming why, while the flow holds an unapproved draft.

A revision starts from what the operator looked at, not from what came after it. Keeping the seed puts the edited sheet
on the same composition; the seed stays editable, so a re-roll is the same act. The image is recorded apart from the
seeds, so an edited seed never loses it.

#### Scenario: a revision copies the image's approval and keeps its seed
- **Key:** `review:revise:a-revision-copies-the-images-approval`
- **Layers:** unit
- **WHEN** an image rendered under approval one is revised after approval two exists
- **THEN** the new draft's fields are approval one's and its producer names approval one
- **AND** its count is one and its seeds are the image's seed

#### Scenario: a revision records its image, and its approval keeps it
- **Key:** `review:revise:a-revision-records-its-image`
- **Layers:** unit
- **WHEN** an image is revised, its seed changed, and the draft approved
- **THEN** the draft and the approval record the image's flow, version and seed

#### Scenario: a waiting draft refuses a revision
- **Key:** `review:revise:a-waiting-draft-refuses`
- **Layers:** unit
- **WHEN** an image is revised while its flow holds an unapproved draft
- **THEN** the revision is refused naming that draft
- **AND** no file is written

### Requirement: A draft is written from another flow's approval, its own fields from its own sheet

When the operator names a source flow and one of its approvals, the system SHALL write the target flow's draft whose
every field both flows' schemas declare is the source approval's, and whose every other field the target declares is the
target's newest sheet's, recording the target's sheet and the source flow and approval it was drafted from, and, where
the operator names one of that approval's images, the image itself — its flow, version and seed. It SHALL approve that
draft as an ordinary approval of the target, never as a copy. It SHALL refuse, naming the way out: a target holding no
sheet; a source holding no such approval; a named image that approval never rendered; a source that is the target or
no tracked flow; and a waiting draft of the target whose fields differ from its sheet's or that renders anything but one
drawn seed. A waiting draft equal to its
sheet, rendering one drawn seed, SHALL be replaced at its own number. The system SHALL refuse cancelling a source
approval while a target approval or waiting draft drafted from it stands, naming the target's cancel or the command that
discards that draft.

```
source approval vN ──▶ every field both declare ─┐
target newest sheet ──▶ every field it alone has ┴─▶ target draft · drafted from source vN
```

The operator corrects a sheet once, in the flow that reads the photograph, and finishes only the fields another flow
adds. A draft the operator never touched holds no work, so replacing it loses nothing; an edited one does, and a
count, a seed or a revision's seed is an edit. A target draft or approval names the source approval it was drafted
from, so that approval stands while the record does, as a copy's source does.

#### Scenario: the shared fields come from the source and the rest from the sheet
- **Key:** `review:draft-from:the-shared-fields-come-from-the-source`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval
- **THEN** each field both flows declare holds the source approval's tags
- **AND** each field only the target declares holds its sheet's tags

#### Scenario: the draft names where it came from
- **Key:** `review:draft-from:the-draft-names-where-it-came-from`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval
- **THEN** its record names the target's sheet, the source flow and the source approval's version

#### Scenario: its approval is an ordinary approval
- **Key:** `review:draft-from:its-approval-is-an-ordinary-approval`
- **Layers:** unit
- **WHEN** a draft written from a source approval that differs from the target's sheet is approved
- **THEN** the approval is written, recorded as edited
- **AND** its record names no copy
- **AND** cancelling it restores the draft, still naming where it came from

#### Scenario: a target with no sheet is refused
- **Key:** `review:draft-from:a-target-with-no-sheet-is-refused`
- **Layers:** unit
- **WHEN** the target holds no sheet
- **THEN** it is refused naming the command that assigns the target, then Prepare
- **AND** no file is written

#### Scenario: a missing source approval is refused
- **Key:** `review:draft-from:a-missing-source-approval-is-refused`
- **Layers:** unit
- **WHEN** the source holds no approval of the version named
- **THEN** it is refused naming the source flow and that version

#### Scenario: an unedited waiting draft is replaced
- **Key:** `review:draft-from:an-unedited-waiting-draft-is-replaced`
- **Layers:** unit
- **WHEN** the target's waiting draft holds its sheet's fields
- **THEN** a draft from the source approval is written at that draft's number

#### Scenario: an edited waiting draft is refused
- **Key:** `review:draft-from:an-edited-waiting-draft-is-refused`
- **Layers:** unit
- **WHEN** the target's waiting draft differs from its sheet, lists seeds, or asks for more than one image
- **THEN** it is refused naming that draft and the command that discards it
- **AND** the draft is unchanged

#### Scenario: what is drafted from it refuses the source's cancel
- **Key:** `review:draft-from:what-is-drafted-from-it-refuses-the-sources-cancel`
- **Layers:** unit
- **WHEN** a cancel is asked for a source approval a target approval or waiting draft was drafted from
- **THEN** it is refused naming the target's cancel, or its draft's discard, and no file changes
- **AND** once the target's approval is cancelled and its draft discarded, the source's cancel succeeds

#### Scenario: a draft from an image records it
- **Key:** `review:draft-from:a-draft-from-an-image-records-it`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval naming one of its images
- **THEN** the draft records that image's flow, version and seed
- **AND** a draft naming no image records none

#### Scenario: an image the approval never rendered is refused
- **Key:** `review:draft-from:an-image-the-approval-never-rendered-is-refused`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval naming a seed it rendered no image for
- **THEN** it is refused naming that seed and the command that lists the rendered seeds
- **AND** no file is written
