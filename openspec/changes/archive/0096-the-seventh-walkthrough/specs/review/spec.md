## MODIFIED Requirements

### Requirement: An unapproved draft can be discarded

The system SHALL delete a flow's highest-numbered draft when asked, only while it is unapproved, and SHALL refuse,
naming the approval, when that number is approved. A discarded draft drafted from another flow's approval, in a flow
holding nothing but that draft and the sheet drafting wrote, SHALL take the sheet and the flow's assignment with it,
leaving the cell unassigned.

A waiting draft blocks a revision; deleting the operator's own unfinished edit is the way out, and the one deletion
review makes, with the flow a drafting assigned when that draft was all it held.

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

#### Scenario: a drafted draft is undone whole
- **Key:** `review:discard:a-drafted-draft-is-undone-whole`
- **Layers:** unit
- **WHEN** a draft drafted into a flow that held nothing before is discarded
- **THEN** the draft, the sheet drafting wrote and the flow's directory are gone
- **AND** a draft in a flow with its own tagged sheet is discarded alone
