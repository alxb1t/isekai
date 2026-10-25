## ADDED Requirements

### Requirement: A draft is written from another flow's approval, its own fields from its own sheet

When the operator names a source flow and one of its approvals, the system SHALL write the target flow's draft whose
every field both flows' schemas declare is the source approval's, and whose every other field the target declares is
the target's newest sheet's, recording the target's sheet and the source flow and approval it was drafted from. It
SHALL approve that draft as an ordinary approval of the target, never as a copy. It SHALL refuse, naming the way out:
a target holding no sheet; a source holding no such approval; a source that is the target or no tracked flow; and a
waiting draft of the target whose fields differ from its sheet's or that renders anything but one drawn seed. A
waiting draft equal to its sheet, rendering one drawn seed, SHALL be replaced at its own number. The system SHALL
refuse cancelling a source approval while a target approval or waiting draft drafted from it stands, naming the
target's cancel or the command that discards that draft.

```
source approval vN ──▶ every field both declare ─┐
target newest sheet ──▶ every field it alone has ┴─▶ target draft · drafted from source vN
```

The operator corrects a sheet once, in the flow that reads the photograph, and finishes only the fields another flow
adds. A draft the operator never touched holds no work, so replacing it loses nothing; an edited one does, and a
count, a seed or a revision's seed is an edit. A target draft or approval names the source approval it was drafted
from, so that approval stands while the record does, as a copy's source does.

#### Scenario: the shared fields come from the source and the rest from the sheet
- **Key:** `review:draft-from:the-shared-fields-come-from-the-source`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval
- **THEN** each field both flows declare holds the source approval's tags
- **AND** each field only the target declares holds its sheet's tags

#### Scenario: the draft names where it came from
- **Key:** `review:draft-from:the-draft-names-where-it-came-from`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval
- **THEN** its record names the target's sheet, the source flow and the source approval's version

#### Scenario: its approval is an ordinary approval
- **Key:** `review:draft-from:its-approval-is-an-ordinary-approval`
- **Layers:** unit
- **WHEN** a draft written from a source approval that differs from the target's sheet is approved
- **THEN** the approval is written, recorded as edited
- **AND** its record names no copy
- **AND** cancelling it restores the draft, still naming where it came from

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

#### Scenario: what is drafted from it refuses the source's cancel
- **Key:** `review:draft-from:what-is-drafted-from-it-refuses-the-sources-cancel`
- **Layers:** unit
- **WHEN** a cancel is asked for a source approval a target approval or waiting draft was drafted from
- **THEN** it is refused naming the target's cancel, or its draft's discard, and no file changes
- **AND** once the target's approval is cancelled and its draft discarded, the source's cancel succeeds
