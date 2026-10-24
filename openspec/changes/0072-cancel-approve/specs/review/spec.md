## ADDED Requirements

### Requirement: An approval nothing derives from can be cancelled back to its draft

The system SHALL cancel a flow's newest approval by writing the draft it was approved from — its fields, renders,
sheet, vocabulary, schema document and field map, and its producer without what approval added — and then deleting
the approval, leaving every older approval in place. It SHALL refuse, writing nothing and naming the reason and the
way on, while anything derives from the approval — a prompt, a render group or a failure record numbered for it, or
another flow's approval copied from it — while a later draft exists, and for an approval that is itself a copy. A
cancel interrupted between its writing and its deleting SHALL be finished by running it again.

An approved artifact is never silently replaced: cancelling is an explicit act, and it is refused once anything has
been made from the approval, so no output loses the sheet that made it. A draft written before the delete leaves a
crash reading as still approved, which approving already does.

```
NNN.approved.json ─▶ write NNN.draft.json ─▶ delete NNN.approved.json
                         crash here: both on disk, read as approved; cancel again finishes
```

#### Scenario: a cancel restores the draft
- **Key:** `review:cancel:a-cancel-restores-the-draft`
- **Layers:** unit
- **WHEN** an approval nothing derives from is cancelled
- **THEN** its draft holds the approval's fields and renders, and the approval is gone
- **AND** the flow reads as a draft

#### Scenario: an older approval stays
- **Key:** `review:cancel:an-older-approval-stays`
- **Layers:** unit
- **WHEN** a revision approved over a rendered approval is cancelled
- **THEN** the older approval is unchanged and the flow reads as re-opened

#### Scenario: anything made from it refuses the cancel
- **Key:** `review:cancel:anything-made-from-it-refuses`
- **Layers:** unit
- **WHEN** a cancel is asked while a prompt, a render group or a failure record is numbered for the approval
- **THEN** it is refused naming what derives and the way on
- **AND** no file changes

#### Scenario: a copy taken from it refuses the cancel
- **Key:** `review:cancel:a-copy-taken-from-it-refuses`
- **Layers:** unit
- **WHEN** another flow's approval is copied from the approval
- **THEN** the cancel is refused naming that flow

#### Scenario: a copy and a re-opened sheet are refused
- **Key:** `review:cancel:a-copy-and-a-reopened-sheet-are-refused`
- **Layers:** unit
- **WHEN** a cancel is asked for an approval that is a copy, then for one with a later draft
- **THEN** each is refused naming the way on

#### Scenario: an interrupted cancel finishes when run again
- **Key:** `review:cancel:an-interrupted-cancel-finishes`
- **Layers:** unit
- **WHEN** a flow holds an approval and the draft a cancel wrote beside it
- **THEN** it reads as approved, and cancelling again leaves only the draft
