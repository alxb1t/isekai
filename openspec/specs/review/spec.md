# Capability: `review`

## Purpose

Stage ③ of the pipeline: the operator's correction of a filled sheet — an editable copy taken into a
directory of its own, validated against the vocabulary, and approved by a rename, so that the
machine-written sheet it came from is never altered.

**Source:** `isekai/pipeline/review.py` ·
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
### Requirement: A draft is updated in place by one function, and a changed field set is refused

The system SHALL provide one way to replace a draft's field values in place, SHALL leave the draft's
version number and the sheet it records as its source unchanged, and SHALL refuse an update whose set of
field names differs from the set the draft already carries.

Until now a draft was written once and then edited by hand, so nothing owned the update and the envelope
was only ever built at creation. A second writer arriving without a single owner is how two envelopes
drift apart in the same directory. The field-set refusal is what makes that owner load-bearing rather
than clerical: two of the four ways a sheet can be invalid at approval are a missing field and a field
the schema does not have, and checking the set at the one write point turns both from a property the
editing surface is trusted to have into a property of the pipeline — at the cost of one comparison,
without opening the validator or changing what it means.

#### Scenario: an update replaces the values and keeps the version
- **Key:** `review:draft-update:values-are-replaced-in-place`
- **Layers:** unit
- **WHEN** a draft's field values are updated
- **THEN** the draft keeps its version number and the sheet version it records
- **AND** no new artifact is created in the review directory

#### Scenario: an update that adds or drops a field is refused
- **Key:** `review:draft-update:a-changed-field-set-is-refused`
- **Layers:** unit
- **WHEN** an update is submitted whose field names differ from the draft's
- **THEN** it is refused
- **AND** the draft on disk is unchanged

#### Scenario: an update against a flow with no draft is refused
- **Key:** `review:draft-update:no-draft-refuses-the-update`
- **Layers:** unit
- **WHEN** an update is submitted for a flow whose review directory holds no draft
- **THEN** it is refused
- **AND** nothing in the review directory is created

### Requirement: The token budget is counted over the prompt the renderer reads

The system SHALL report a sheet's token cost as a count over the assembled positive prompt — the flow's
prefix, the sheet's tags and the flow's trailer, joined as the renderer joins them — and SHALL report
alongside it each field's own share of that count and the fixed overhead that is not any field's.

The number exists to be steered by while a sheet is being corrected, which is when tags are added and
when the budget is crossed. A count that omits the prefix and trailer understates what the text encoder
will read by about nineteen tokens against a window of seventy-seven, so a sheet reported comfortably
inside the budget is in fact past it and silently chunked. Reporting the per-field shares and the
overhead from the same call is what makes the number act on: the shares sum into the total, the overhead
is the remainder, and the operator's question is never *how many tokens* but *which tag goes*.

#### Scenario: the total is the assembled prompt's, not the tags' alone
- **Key:** `review:budget:count-covers-the-assembled-prompt`
- **Layers:** unit
- **WHEN** a sheet's token budget is reported for a flow
- **THEN** the total accounts for the flow's prompt prefix and trailer as well as the sheet's tags

#### Scenario: the per-field shares and the overhead reconcile with the total
- **Key:** `review:budget:shares-and-overhead-sum-to-the-total`
- **Layers:** unit
- **WHEN** a sheet's token budget is reported
- **THEN** the per-field shares and the stated overhead sum to the total
- **AND** a field with no tags contributes nothing

#### Scenario: a field absent from the sheet does not fail the count
- **Key:** `review:budget:an-absent-field-is-counted-as-empty`
- **Layers:** unit
- **WHEN** a token budget is reported for a sheet that is missing one of the schema's fields
- **THEN** the count succeeds
- **AND** the absent field contributes nothing to the total
