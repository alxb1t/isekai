## MODIFIED Requirements

### Requirement: The review verb drafts from another flow's approval with `--from`

The system SHALL take `--from FLOW` on `isekai review`, drafting each named flow of each named run from that flow's
approval through the review stage, first assigning a named flow that holds no sheet and filling its sheet from the
source's tag list, of the version `--version N` names, else the source's newest approval. It SHALL
answer each run on its own, and SHALL refuse, before any run is read, `--from` beside `--discard` or
`--new-version`, `--version` without `--from`, and a source that is a named flow or no tracked flow.

The draft is the review stage's act, so the verb composes it and decides nothing. The newest approval is the one the
operator just finished, so it needs no number. A target with no sheet needs no Prepare: the source's tags are
the target's.

#### Scenario: each flow is drafted from the source's newest approval
- **Key:** `cli:review-from:each-flow-is-drafted-from-the-newest-approval`
- **Layers:** unit
- **WHEN** `review --from` names a source holding two approvals and no `--version`
- **THEN** each named flow's draft is drafted from the source's newest approval
- **AND** with `--version 1` it is drafted from approval one

#### Scenario: a target with no sheet is assigned and filled first
- **Key:** `cli:review-from:a-target-with-no-sheet-is-filled-first`
- **Layers:** unit
- **WHEN** `review --from` names a target the run is not assigned to
- **THEN** the target is assigned, its sheet filled from the source's tag list, and its draft written
- **AND** no caption or tag list is written for the target

#### Scenario: a conflicting option is refused before any run is read
- **Key:** `cli:review-from:a-conflicting-option-is-refused`
- **Layers:** unit
- **WHEN** `review --from` is given beside `--discard`, or `--version` without `--from`
- **THEN** it is refused naming the options
- **AND** no run is read
