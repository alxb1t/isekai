## MODIFIED Requirements

### Requirement: An approved input is read-only on the surface until it is re-opened

The system SHALL present an input whose flow has an approved artifact and no later draft as not editable,
SHALL refuse a draft update against such an input, and SHALL state on the page that the input is approved
and name the artifact that holds it. Where a draft numbered above the approved artifact's `approved_from`
exists, the system SHALL present the input as **re-opened**: editable, with its approved artifact still
named.

**The previous wording assumed a state the pipeline can produce.** It read *"Approval deletes the draft
and opening the surface again writes no replacement, because a new version is an explicit act — so there
is nothing on disk for an edit after approval to be written into."* The second clause is true and the
inference from it is not: `review --flow F --new-version` is exactly that explicit act, and
`review:copy:second-review-appends` requires it to write a new numbered draft from the approved copy. Two
capabilities described one state and disagreed about it.

**`review` is the one that was right.** `--new-version` exists for this and is older and tested; the
surface is what had no way to show its result. `v0.22.1` closed the disagreement in the other direction
because that fix needed no spec delta, and said so in the refusal it shipped — *"this page keeps showing
the input approved and read-only either way, because the re-opened state is v0.22.2's."* This is that
version.

**Re-opened is a third status, not a second meaning for an existing one.** An input with an approved
artifact and no newer draft is finished and stays read-only; the approved artifact is never edited in
place in either case. What changes is that a deliberately re-opened input stops being reported as
something it is not.

#### Scenario: a draft update against an approved input is refused
- **Key:** `ui:approval:approved-input-refuses-a-draft-update`
- **Layers:** unit
- **WHEN** a draft update is submitted for an input whose flow is approved and holds no later draft
- **THEN** it is refused
- **AND** no file in the run directory is created, changed or removed

#### Scenario: an input approved in an earlier sitting opens read-only
- **Key:** `ui:approval:approved-input-opens-read-only`
- **Layers:** unit
- **WHEN** the surface serves an input whose flow has an approved artifact and no draft
- **THEN** the sheet it shows is the approved artifact's
- **AND** the input is presented as not editable

#### Scenario: an input re-opened with a new version is editable again
- **Key:** `ui:approval:a-re-opened-input-is-editable`
- **Layers:** unit
- **WHEN** the surface serves an input whose flow has an approved artifact and a draft numbered above the
  version that artifact records as its origin
- **THEN** the sheet it shows is the draft's
- **AND** the input is presented as editable
- **AND** a draft update against it is accepted

#### Scenario: a re-opened input is not counted as approved
- **Key:** `ui:approval:a-re-opened-input-is-not-counted-approved`
- **Layers:** unit
- **WHEN** the batch is read while one of its inputs is re-opened
- **THEN** that input's reported status is neither approved nor a plain draft
- **AND** the batch's approved count agrees with what the run directories hold

#### Scenario: a stale lower draft does not re-open an approved input
- **Key:** `ui:approval:a-stale-lower-draft-does-not-reopen`
- **Layers:** unit
- **WHEN** the surface serves an input whose flow has an approved artifact and a draft numbered below it
- **THEN** the sheet it shows is the approved artifact's
- **AND** the input is presented as not editable, naming no draft

#### Scenario: an update that overlaps an approval is refused
- **Key:** `ui:approval:an-update-overlapping-an-approval-is-refused`
- **Layers:** unit
- **WHEN** a draft update is in flight while the same input is approved
- **THEN** the update is refused once the approval has written
- **AND** the approved artifact is the one the approval wrote
