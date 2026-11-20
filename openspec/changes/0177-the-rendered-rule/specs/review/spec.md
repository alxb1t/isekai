## MODIFIED Requirements

### Requirement: A revision is a draft from the approval that made the image, its seed prefilled

The system SHALL write, for a rendered image, the next numbered draft of its flow copied from the approval the image was
rendered under — whether or not that is the newest — naming that approval in its producer, with a count of one and the
image's seed listed, and recording the image itself — its flow, version and seed — which the approval keeps. It SHALL
refuse, naming why, while the flow holds a waiting draft with edits of its own, and SHALL replace one equal to its
sheet at its own number.

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
- **WHEN** an image is revised while its flow holds a waiting draft with edits of its own
- **THEN** the revision is refused naming that draft
- **AND** no file is written

#### Scenario: an unedited waiting draft is replaced
- **Key:** `review:revise:an-unedited-waiting-draft-is-replaced`
- **Layers:** unit
- **WHEN** an image is revised while its flow's waiting draft equals its sheet
- **THEN** the revision is written at that draft's number

#### Scenario: a seed with a record and no image is refused
- **Key:** `review:revise:a-record-without-its-image-is-refused`
- **Layers:** unit
- **WHEN** a seed is revised whose record is in its approval's group and whose image is not
- **THEN** the revision is refused naming that seed
- **AND** no file is written

#### Scenario: a seed with an image and no record is revised
- **Key:** `review:revise:an-image-without-its-record-is-revised`
- **Layers:** unit
- **WHEN** a seed is revised whose image is in its approval's group and whose record is not
- **THEN** the revision is written with a count of one and that seed listed

### Requirement: Approval refuses a revision that would reproduce its images

The system SHALL refuse approval of a draft copied from an approval when its fields are that approval's and every
image it would render is of a seed that approval lists or rendered, naming the images it would reproduce.

An unchanged revision renders images that already exist, so refusing costs nothing and rendering costs money. A seed
the approval neither lists nor rendered is a change, and so is a count above the listed seeds, which draws new ones.

#### Scenario: an unchanged revision is refused
- **Key:** `review:revise:an-unchanged-revision-is-refused`
- **Layers:** unit
- **WHEN** approval is asked for a revision with its approval's fields and only seeds that approval lists or rendered
- **THEN** it is refused naming the images it would reproduce

#### Scenario: new seeds alone are a change
- **Key:** `review:revise:new-seeds-alone-are-a-change`
- **Layers:** unit
- **WHEN** approval is asked for a revision whose only difference is a seed its approval neither lists nor rendered
- **THEN** it is approved

#### Scenario: a seed with a record and no image is a change
- **Key:** `review:revise:a-seed-with-a-record-and-no-image-is-a-change`
- **Layers:** unit
- **WHEN** approval is asked for a revision whose only difference is a seed its approval does not list and holds a
  record of, with no image
- **THEN** it is approved

#### Scenario: a seed with an image and no record is reproduced
- **Key:** `review:revise:a-seed-with-an-image-and-no-record-is-reproduced`
- **Layers:** unit
- **WHEN** approval is asked for a revision whose only difference is a seed its approval does not list and holds an
  image of, with no record
- **THEN** it is refused naming the images it would reproduce

### Requirement: A draft is written once from another flow's approval, holding its own fields, seeds and image

When the operator names a source flow and one of its approvals, the system SHALL write the target flow's draft whose
every field both flows' schemas declare is the source approval's, and whose every other field the target declares is the
target's newest sheet's, recording the target's sheet and neither the source approval nor any image of the source.
Where the operator names one of that approval's images, the system SHALL copy that image into the target's sources,
under the draft's own number, before the draft is written — the **source copy** — and the draft SHALL have a count of
one and that seed listed; naming no image, it SHALL copy none, and its renders SHALL be the approval's seeds, as a
copy's are. A source copy SHALL never count as one of the target's renders. It SHALL approve that draft as an ordinary
approval of the target, never as a copy. It SHALL refuse, naming the way out: a target holding no sheet; a source
holding no such approval; a named image that approval never rendered, or whose image file is gone; a source that is the
target or no tracked flow; and a waiting draft of the target whose fields differ from its sheet's or that renders
anything but one drawn seed. A waiting draft equal to its sheet, rendering one drawn seed, SHALL be replaced at its own
number. A target approval or waiting draft drafted from a source approval SHALL NOT hold that approval's cancel.

```
source approval vN ──▶ every field both declare ─┐
target newest sheet ──▶ every field it alone has ┴─▶ target draft NNN · its own fields and seeds
source image <seed>.png ──── copied ──────────────▶ target sources/NNN.png
```

The operator corrects a sheet once, in the flow that reads the photograph, and finishes only the fields another flow
adds. A draft the operator never touched holds no work, so replacing it loses nothing; an edited one does, and a
count, a seed or a revision's seed is an edit. A draft from another flow is taken once: it holds its own fields, seeds
and image, so the source approval and its renders can go and leave it whole
([D49](../../../docs/decisions.md#d49--a-control-flow-is-its-subject-with-the-face-chain-at-zero-copied-once),
[D50](../../../docs/decisions.md#d50--the-last-render-takes-its-approval-and-a-flow-holds-only-its-own-files)).

#### Scenario: the shared fields come from the source and the rest from the sheet
- **Key:** `review:draft-from:the-shared-fields-come-from-the-source`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval
- **THEN** each field both flows declare holds the source approval's tags
- **AND** each field only the target declares holds its sheet's tags

#### Scenario: the draft records its sheet and no source approval
- **Key:** `review:draft-from:the-draft-records-no-source-approval`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval
- **THEN** its record names the target's sheet
- **AND** it names neither the source flow nor the source approval's version

#### Scenario: a draft from no image carries the approval's seeds
- **Key:** `review:draft-from:a-draft-from-no-image-carries-the-seeds`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval naming no image, and that approval's group holds images
- **THEN** its renders list the approval's listed seeds, then each seed rendered

#### Scenario: its approval is an ordinary approval
- **Key:** `review:draft-from:its-approval-is-an-ordinary-approval`
- **Layers:** unit
- **WHEN** a draft written from a source approval that differs from the target's sheet is approved
- **THEN** the approval is written, recorded as edited
- **AND** its record names no copy
- **AND** cancelling it restores the draft as it was written

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

#### Scenario: what is drafted from it holds no source cancel
- **Key:** `review:draft-from:what-is-drafted-from-it-holds-no-source-cancel`
- **Layers:** unit
- **WHEN** a cancel is asked for a source approval a target approval and a target waiting draft were drafted from
- **THEN** the source's draft is restored
- **AND** the target's files are as they were

#### Scenario: a draft from an image copies it
- **Key:** `review:draft-from:a-draft-from-an-image-copies-it`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval naming one of its images
- **THEN** the target's sources hold that image's bytes under the draft's number
- **AND** the draft records no image, and a draft naming no image copies none

#### Scenario: an image the approval never rendered is refused
- **Key:** `review:draft-from:an-image-the-approval-never-rendered-is-refused`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval naming a seed it rendered no image for, or whose image file is
  gone
- **THEN** it is refused naming that seed and the command that lists the rendered seeds
- **AND** no file is written

#### Scenario: a draft from an image prefills its seed
- **Key:** `review:draft-from:a-draft-from-an-image-prefills-its-seed`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval naming one of its images
- **THEN** its count is one and its seeds are the image's seed

#### Scenario: an image with no record is drafted from
- **Key:** `review:draft-from:an-image-without-its-record-is-drafted-from`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval naming a seed whose image is in the approval's group and whose
  record is not
- **THEN** the target's sources hold that image's bytes under the draft's number
- **AND** its count is one and its seeds are the image's seed
