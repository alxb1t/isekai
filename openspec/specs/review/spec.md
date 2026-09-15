# Capability: `review`

Stage ③ of the pipeline: the operator's correction of a filled sheet — an editable copy taken into a
directory of its own, validated against the vocabulary, and approved by a rename, so that the
machine-written sheet it came from is never altered.

**Source:** `isekai/review.py` ·
**Tests:** `tests/test_review.py`

## Requirements

### Requirement: The machine's sheet is never edited; review works on a copy

The system SHALL take the sheet into a separate directory before any edit is possible, and SHALL NOT
provide any path by which the stage that filled the sheet has its output altered.

The machine's raw sheet is the baseline the correction is worth measuring against: the unreviewed route
carries 0.568 of the sheet's attributes into the render and the reviewed one carries 0.917. Editing in
place destroys that baseline permanently, on every run. Separating the directories makes the guarantee
a property of the layout rather than a rule a tool is trusted to follow.

#### Scenario: review copies rather than edits
- **Key:** `review:copy:review-writes-to-its-own-directory`
- **Layers:** unit
- **WHEN** review is invoked for a run and a flow
- **THEN** an editable copy is written into the review directory
- **AND** no file in the sheet directory is created, changed or removed

#### Scenario: review takes the highest available sheet
- **Key:** `review:copy:highest-sheet-is-copied`
- **Layers:** unit
- **WHEN** more than one sheet version exists for a flow
- **THEN** the highest-numbered one is copied
- **AND** the copy records which sheet version it came from

#### Scenario: reviewing again appends rather than replaces
- **Key:** `review:copy:second-review-appends`
- **Layers:** unit
- **WHEN** review is invoked for a flow that already has an approved copy
- **THEN** a new numbered draft is written from the approved one
- **AND** the existing approved copy is left exactly as it was

### Requirement: Saving is not approving

The system SHALL treat an edited but unapproved copy as a draft, SHALL leave it editable for as long as
the operator wants, and SHALL make approval a separate, explicit act.

A sheet must be parkable half-edited, because the whole reason the two directories exist is that sheets
diverge under human editing over minutes or days. Approval being its own act is also what lets the
directory listing answer whether the stage is finished.

#### Scenario: a draft is not treated as complete
- **Key:** `review:approval:draft-is-not-done`
- **Layers:** unit
- **WHEN** a draft exists and has not been approved
- **THEN** the stage is reported as not complete
- **AND** downstream stages refuse to proceed from it

#### Scenario: approval renames rather than rewrites
- **Key:** `review:approval:approve-validates-then-renames`
- **Layers:** unit
- **WHEN** a draft is approved
- **THEN** the artifact's bytes are unchanged and its name declares it approved
- **AND** approval is decidable from the filename alone

#### Scenario: the approved artifact is never silently replaced
- **Key:** `review:approval:approved-is-not-overwritten`
- **Layers:** unit
- **WHEN** an approved artifact exists for a flow
- **THEN** no command overwrites it
- **AND** producing a corrected version means writing the next number

### Requirement: Approval validates every tag against the vocabulary and refuses on an unknown one

The system SHALL check every tag in every field against the vocabulary at approval, SHALL refuse
approval naming each tag that is not in it, and SHALL state the reason honestly — that the tag is not
in the vocabulary's prediction set, rather than that it is not a real tag.

A tag that merely looks canonical passes every later check on its way into the prompt, so approval is
the last place it can be caught. The honest wording matters: the vocabulary is the set the tag list
predicts, which is a subset of the wider tag corpus, so calling an absent tag unreal overclaims.

#### Scenario: an unknown tag refuses approval
- **Key:** `review:validation:unknown-tag-refuses-approval`
- **Layers:** unit
- **WHEN** a draft contains a tag absent from the vocabulary
- **THEN** approval is refused naming that tag and its field
- **AND** the draft is left untouched for the operator to correct

#### Scenario: the refusal does not overclaim
- **Key:** `review:validation:message-states-the-prediction-set`
- **Layers:** unit
- **WHEN** approval is refused for an unknown tag
- **THEN** the message says the tag is not in the vocabulary's prediction set
- **AND** it does not assert that the tag does not exist

#### Scenario: a missing field refuses approval
- **Key:** `review:validation:missing-field-refuses-approval`
- **Layers:** unit
- **WHEN** a draft does not carry every field the schema declares
- **THEN** approval is refused naming the missing fields
- **AND** an empty field is not treated as missing

### Requirement: Approval warns when the assembled prompt exceeds the encoder's window

The system SHALL estimate the assembled prompt's token count at approval and SHALL warn — not refuse —
when it exceeds the text encoder's window.

Sheets already run well past that window and nothing currently says so, which means every one is being
silently chunked and averaged. It is a warning rather than a refusal because the sheet is the ground
truth for what the render was asked to contain; deleting fields to fit would make the question of
whether a criterion survived unanswerable at the moment it is asked.

#### Scenario: an over-long prompt warns and still approves
- **Key:** `review:budget:over-window-warns-not-refuses`
- **Layers:** unit
- **WHEN** the assembled prompt's estimated tokens exceed the encoder's window
- **THEN** a warning states the estimate and the window
- **AND** approval still succeeds

### Requirement: The approved artifact records whether a human changed anything

The system SHALL record on the approved artifact whether its content differs from the sheet it was
copied from.

Whether a sheet was actually corrected is the difference between the 0.568 route and the 0.917 one, and
without this it is an assumption rather than a fact on disk. It is also what lets the machine's raw
draft be rendered deliberately as a control — approved unedited, and recorded as such.

#### Scenario: an untouched copy is recorded as unedited
- **Key:** `review:provenance:unedited-copy-is-declared`
- **Layers:** unit
- **WHEN** a draft is approved without having been changed
- **THEN** the artifact records that it was not edited
- **AND** it records the sheet version it came from

#### Scenario: a changed copy is recorded as edited
- **Key:** `review:provenance:edited-copy-is-declared`
- **Layers:** unit
- **WHEN** a draft's content differs from its source sheet
- **THEN** the artifact records that it was edited
- **AND** the record does not depend on the operator having said so

### Requirement: This stage refuses to the operator and writes no error record

The system SHALL report a refusal from review or approval to the operator and exit with a failure
status, and SHALL NOT write an error record or consume a retry budget for it.

Error records exist so that a batch of twenty photographs does not halt on one item's failure. This
stage has no batch and no unattended retry — the operator is present by definition, and a refusal here
is a message to them rather than state for a later resume to reason about.

#### Scenario: a refusal is reported and leaves no error record
- **Key:** `review:refusal:no-error-record-is-written`
- **Layers:** unit
- **WHEN** review or approval refuses
- **THEN** the reason is reported and the command exits with a failure status
- **AND** no error record is written into the run directory
