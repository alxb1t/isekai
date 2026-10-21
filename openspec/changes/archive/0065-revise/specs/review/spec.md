## ADDED Requirements

### Requirement: A revision is a draft from the approval that made the image, its seed prefilled

The system SHALL write, for a rendered image, the next numbered draft of its flow copied from the approval the image
was rendered under — whether or not that is the newest — naming that approval in its producer, with a count of one
and the image's seed listed. It SHALL refuse, naming why, while the flow holds an unapproved draft.

A revision starts from what the operator looked at, not from what came after it. Keeping the seed puts the edited
sheet on the same composition; the seed stays editable, so a re-roll is the same act.

#### Scenario: a revision copies the image's approval and keeps its seed
- **Key:** `review:revise:a-revision-copies-the-images-approval`
- **Layers:** unit
- **WHEN** an image rendered under approval one is revised after approval two exists
- **THEN** the new draft's fields are approval one's and its producer names approval one
- **AND** its count is one and its seeds are the image's seed

#### Scenario: a waiting draft refuses a revision
- **Key:** `review:revise:a-waiting-draft-refuses`
- **Layers:** unit
- **WHEN** an image is revised while its flow holds an unapproved draft
- **THEN** the revision is refused naming that draft
- **AND** no file is written

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

### Requirement: An unapproved draft can be discarded

The system SHALL delete a flow's highest-numbered draft when asked, only while it is unapproved, and SHALL refuse,
naming the approval, when that number is approved.

A waiting draft blocks a revision; deleting the operator's own unfinished edit is the way out, and the one deletion
review makes.

#### Scenario: a draft is discarded
- **Key:** `review:discard:a-draft-is-discarded`
- **Layers:** unit
- **WHEN** a flow's highest draft is unapproved and is discarded
- **THEN** that draft is gone and every approval is unchanged

#### Scenario: an approval is never discarded
- **Key:** `review:discard:an-approval-is-never-discarded`
- **Layers:** unit
- **WHEN** discarding is asked for a flow whose highest number is approved
- **THEN** it is refused and no file changes
