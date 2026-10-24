## ADDED Requirements

### Requirement: An approval nothing derives from can be cancelled back to its draft

The system SHALL cancel a flow's newest approval by writing the draft it was approved from — its fields, renders,
sheet, vocabulary, schema document and field map, and its producer without what approval added — and then deleting
the approval, leaving every older approval in place, and SHALL cancel an approval that is itself a copy by deleting
it, naming what the flow is left on: the draft open above what lies beneath, else the approval beneath, which stays
approved. It SHALL refuse, writing nothing and naming the reason and a way on that succeeds, while anything derives
from the approval — a prompt, a render group or a failure record numbered for it, or another flow's approval copied
from it — and while a later draft exists, naming a waiting draft rather than its discard while anything derives. A
cancel interrupted between its writing and its deleting SHALL be finished by running it again.

An approved artifact is never silently replaced: cancelling is an explicit act, and it is refused once anything has
been made from the approval, so no output loses the sheet that made it. A copy has no draft of its own, and
`approve --from` writes it again; deleting it takes back only the copy, so what it was written over stands. A draft
written before the delete leaves a crash reading as still approved, which approving already does.

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
- **AND** with a draft waiting above it, that draft is named rather than its discard

#### Scenario: a copy taken from it refuses the cancel
- **Key:** `review:cancel:a-copy-taken-from-it-refuses`
- **Layers:** unit
- **WHEN** another flow's approval is copied from the approval
- **THEN** the cancel is refused naming that flow's cancel
- **AND** once that copy is cancelled, the cancel succeeds

#### Scenario: a copy is deleted, and a re-opened sheet is refused
- **Key:** `review:cancel:a-copy-is-deleted-and-a-reopened-sheet-refused`
- **Layers:** unit
- **WHEN** a cancel is asked for an approval with a later draft, then for a copy over the flow's own approval
- **THEN** the first is refused naming its draft's discard, and the copy alone is deleted
- **AND** the cancel names the approval beneath, and the flow reads as approved
- **AND** copying again writes the same copy

#### Scenario: an interrupted cancel finishes when run again
- **Key:** `review:cancel:an-interrupted-cancel-finishes`
- **Layers:** unit
- **WHEN** a flow holds an approval and the draft a cancel wrote beside it
- **THEN** it reads as approved, and cancelling again leaves only the draft
