## MODIFIED Requirements

### Requirement: The machine's sheet is never edited; review works on a copy

The system SHALL take the sheet into a separate directory before any edit is possible, and SHALL NOT
provide any path by which the stage that filled the sheet has its output altered.

```
sheet directory ──review──▶ review directory: draft ──approve, a rename──▶ approved
(never edited)               (edited in place)                          (never overwritten)
```

The machine's sheet is the baseline the correction is measured against, and editing it in place destroys that
baseline on every run. Separate directories make the guarantee a property of the layout, not a rule a tool is
trusted to follow.

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

### Requirement: Approval warns when the assembled prompt exceeds the encoder's window

The system SHALL estimate the assembled prompt's token count at approval and SHALL warn — not refuse —
when it exceeds the text encoder's window.

A prompt past the window is silently chunked and averaged, so the operator is told. It is a warning, not a
refusal, because the sheet is the truth of what the render was asked to contain; deleting fields to fit would hide
whether a criterion survived.

#### Scenario: an over-long prompt warns and still approves
- **Key:** `review:budget:over-window-warns-not-refuses`
- **Layers:** unit
- **WHEN** the assembled prompt's estimated tokens exceed the encoder's window
- **THEN** a warning states the estimate and the window
- **AND** approval still succeeds

### Requirement: The approved artifact records whether a human changed anything

The system SHALL record on the approved artifact whether its content differs from the sheet it was
copied from.

Whether a sheet was corrected decides which route a render measures, and without this record it is an assumption
rather than a fact on disk. It also lets the machine's draft be rendered as a control — approved unedited, and
recorded as such.

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

Error records keep a batch from halting on one photograph. Review has no batch and no unattended retry: the
operator is present, and a refusal is a message to them, not state for a later resume.

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

A second writer without a single owner is how two envelopes drift apart in one directory. Checking the field set at
the one write point turns a missing field and a field the schema lacks from a property the editing surface is
trusted to have into a property of the pipeline, at the cost of one comparison.

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

The count is steered by while a sheet is corrected, when tags are added and the budget is crossed. A count that
omits the prefix and trailer understates what the text encoder reads, so a sheet reported inside the budget can be
past it and silently chunked. The shares and the overhead come from the same call, so they sum to the total and
answer the operator's real question: which tag goes.

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
