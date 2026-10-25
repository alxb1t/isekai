## ADDED Requirements

### Requirement: The review verb drafts from another flow's approval with `--from`

The system SHALL take `--from FLOW` on `isekai review`, drafting each named flow of each named run from that flow's
approval through the review stage, of the version `--version N` names, else the source's newest approval. It SHALL
answer each run on its own, and SHALL refuse, before any run is read, `--from` beside `--discard` or
`--new-version`, `--version` without `--from`, and a source that is a named flow or no tracked flow.

The draft is the review stage's act, so the verb composes it and decides nothing. The newest approval is the one the
operator just finished, so it needs no number.

#### Scenario: each flow is drafted from the source's newest approval
- **Key:** `cli:review-from:each-flow-is-drafted-from-the-newest-approval`
- **Layers:** unit
- **WHEN** `review --from` names a source holding two approvals and no `--version`
- **THEN** each named flow's draft is drafted from the source's newest approval
- **AND** with `--version 1` it is drafted from approval one

#### Scenario: a conflicting option is refused before any run is read
- **Key:** `cli:review-from:a-conflicting-option-is-refused`
- **Layers:** unit
- **WHEN** `review --from` is given beside `--discard`, or `--version` without `--from`
- **THEN** it is refused naming the options
- **AND** no run is read
