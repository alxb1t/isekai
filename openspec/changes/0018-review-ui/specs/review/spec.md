## ADDED Requirements

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
