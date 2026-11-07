## ADDED Requirements

### Requirement: An approval is copied once from another flow's approval, its seeds with it

When the operator names a source flow, the system SHALL write an approval under the target flow whose fields are the
source flow's latest approval's, validated against the target flow's schema and the vocabulary as any approval is, and
whose renders list the source approval's seeds — its listed seeds, then each seed its outputs group holds an image of —
its count raised to their number where it is lower. The copy SHALL record that it is a copy and SHALL NOT record the
source flow or approval. It SHALL refuse a run whose source flow has no approval, naming the way out. It SHALL write
nothing where the target's newest approval is a copy holding the same fields and renders, and SHALL otherwise copy under
the target's next number. It SHALL refuse a source that is the target itself or no tracked flow, before any run is
opened.

```
runs/<id>/summon-anime-wai/review/001.approved.json      renders {count 2, seeds []} · outputs/001/ 11.png 12.png
        │  approve --flow control-anime-wai --from summon-anime-wai <run>
        ▼
runs/<id>/control-anime-wai/review/001.approved.json     same fields; renders {count 2, seeds [11, 12]}; a copy
```

Two flows are compared only on one prompt and one noise. A copy by hand carries the source's identifier; a second
approval by hand lets the prompts drift. The target's own validation keeps the copy honest. The seeds travel with the
copy, so control and subject render the same seeds with no later check, and the source's approval can always be
cancelled or deleted with its renders
([D49](../../../docs/decisions.md#d49--a-control-flow-is-its-subject-with-the-face-chain-at-zero-copied-once)).

#### Scenario: the fields are copied and validated against the target
- **Key:** `review:copy-from:fields-are-copied-and-validated`
- **Layers:** unit
- **WHEN** a target flow is approved from a source flow's approval
- **THEN** the target's approval carries the source's fields
- **AND** a field the target's schema does not declare refuses the copy naming it

#### Scenario: the copy carries the source's seeds and names no source
- **Key:** `review:copy-from:the-copy-carries-the-seeds`
- **Layers:** unit
- **WHEN** a target flow is approved from a source approval whose group holds images
- **THEN** the approval's identifier is the target flow's, and its renders list the source's listed seeds, then each
  seed rendered
- **AND** its record says it is a copy and names neither the source flow nor its approval

#### Scenario: no source approval refuses the copy
- **Key:** `review:copy-from:no-source-approval-is-refused`
- **Layers:** unit
- **WHEN** the source flow holds no approval for the run
- **THEN** the copy is refused naming the source flow and the command that approves it

#### Scenario: an equal copy writes nothing
- **Key:** `review:copy-from:an-approved-target-writes-nothing`
- **Layers:** unit
- **WHEN** the target's newest approval is a copy holding the fields and renders the copy would hold
- **THEN** nothing is written
- **AND** the existing approval is unchanged

#### Scenario: a changed source approval is copied again
- **Key:** `review:copy-from:a-newer-source-approval-is-copied-again`
- **Layers:** unit
- **WHEN** the source's latest approval differs from what the target's newest approval holds, or that is no copy
- **THEN** the source's latest is copied under the target's next number
- **AND** the target's earlier approval is unchanged

#### Scenario: the source is a tracked flow other than the target
- **Key:** `review:copy-from:the-source-is-another-tracked-flow`
- **Layers:** unit
- **WHEN** the source named is the target itself or no tracked flow
- **THEN** the invocation is refused naming it
- **AND** no run is opened

### Requirement: An approval nothing of its own flow derives from can be cancelled back to its draft

The system SHALL cancel a flow's newest approval by writing the draft it was approved from — its fields, renders,
sheet, vocabulary, schema document and field map, and its producer without what approval added — and then deleting the
approval, leaving every older approval in place, and SHALL cancel an approval that is itself a copy by deleting it,
naming what the flow is left on: the draft open above what lies beneath, else the approval beneath, which stays
approved. It SHALL refuse, writing nothing and naming the reason and a way on that succeeds, while anything derives
from the approval — a prompt, a render group or a failure record numbered for it — and while a later draft exists,
naming a waiting draft rather than its discard while anything derives. A cancel interrupted between its writing and
its deleting SHALL be finished by running it again. A cancel asked of a flow with no approval SHALL change nothing:
with a draft open it SHALL say the flow is at its draft, and with none it SHALL refuse naming `review`. Another flow's
copy of the approval, an approval drafted from it and a waiting draft drafted from it SHALL NOT hold the cancel.

An approved artifact is never silently replaced: cancelling is an explicit act, and it is refused once anything has
been made from the approval, so no output loses the sheet that made it. What another flow took holds its own copy, so
it holds nothing here. A copy has no draft of its own, and `approve --from` copies the source's newest approval
again; deleting it takes back only the copy, so what it was written over stands. A draft written before the delete
leaves a crash reading as still approved, which approving already does.

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

#### Scenario: what another flow took holds no cancel
- **Key:** `review:cancel:what-another-flow-took-holds-no-cancel`
- **Layers:** unit
- **WHEN** another flow holds a copy of the approval, an approval drafted from it, or a waiting draft drafted from it
- **THEN** the cancel restores the approval's draft
- **AND** the other flow's files are as they were

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

#### Scenario: a flow with no approval has nothing to cancel
- **Key:** `review:cancel:a-flow-with-no-approval-has-nothing-to-cancel`
- **Layers:** unit
- **WHEN** a cancel is asked for a flow with a draft and no approval, then for a flow with neither
- **THEN** the first changes nothing and says the flow is at its draft
- **AND** the second is refused naming `review`, and no file changes

### Requirement: A draft is written once from another flow's approval, its own fields from its own sheet

When the operator names a source flow and one of its approvals, the system SHALL write the target flow's draft whose
every field both flows' schemas declare is the source approval's, and whose every other field the target declares is the
target's newest sheet's, recording the target's sheet and not the source approval, and, where the operator names one of
that approval's images, the image itself — its flow, version and seed — with a count of one and that seed listed;
naming no image, its renders are the approval's seeds, as a copy's are. It SHALL approve that
draft as an ordinary approval of the target, never as a copy. It SHALL refuse, naming the way out: a target holding no
sheet; a source holding no such approval; a named image that approval never rendered; a source that is the target or
no tracked flow; and a waiting draft of the target whose fields differ from its sheet's or that renders anything but one
drawn seed. A waiting draft equal to its
sheet, rendering one drawn seed, SHALL be replaced at its own number. A target approval or waiting draft drafted from a
source approval SHALL NOT hold that approval's cancel.

```
source approval vN ──▶ every field both declare ─┐
target newest sheet ──▶ every field it alone has ┴─▶ target draft · its own fields and seeds
```

The operator corrects a sheet once, in the flow that reads the photograph, and finishes only the fields another flow
adds. A draft the operator never touched holds no work, so replacing it loses nothing; an edited one does, and a
count, a seed or a revision's seed is an edit. A draft from another flow is taken once: it holds its own fields and
seeds, so the source approval can go
([D49](../../../docs/decisions.md#d49--a-control-flow-is-its-subject-with-the-face-chain-at-zero-copied-once)).

#### Scenario: the shared fields come from the source and the rest from the sheet
- **Key:** `review:draft-from:the-shared-fields-come-from-the-source`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval
- **THEN** each field both flows declare holds the source approval's tags
- **AND** each field only the target declares holds its sheet's tags

#### Scenario: the draft records its sheet and no source approval
- **Key:** `review:draft-from:the-draft-records-no-source-approval`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval
- **THEN** its record names the target's sheet
- **AND** it names neither the source flow nor the source approval's version

#### Scenario: a draft from no image carries the approval's seeds
- **Key:** `review:draft-from:a-draft-from-no-image-carries-the-seeds`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval naming no image, and that approval's group holds images
- **THEN** its renders list the approval's listed seeds, then each seed rendered

#### Scenario: its approval is an ordinary approval
- **Key:** `review:draft-from:its-approval-is-an-ordinary-approval`
- **Layers:** unit
- **WHEN** a draft written from a source approval that differs from the target's sheet is approved
- **THEN** the approval is written, recorded as edited
- **AND** its record names no copy
- **AND** cancelling it restores the draft as it was written

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

#### Scenario: what is drafted from it holds no source cancel
- **Key:** `review:draft-from:what-is-drafted-from-it-holds-no-source-cancel`
- **Layers:** unit
- **WHEN** a cancel is asked for a source approval a target approval and a target waiting draft were drafted from
- **THEN** the source's draft is restored
- **AND** the target's files are as they were

#### Scenario: a draft from an image records it
- **Key:** `review:draft-from:a-draft-from-an-image-records-it`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval naming one of its images
- **THEN** the draft records that image's flow, version and seed
- **AND** a draft naming no image records none

#### Scenario: an image the approval never rendered is refused
- **Key:** `review:draft-from:an-image-the-approval-never-rendered-is-refused`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval naming a seed it rendered no image for
- **THEN** it is refused naming that seed and the command that lists the rendered seeds
- **AND** no file is written

#### Scenario: a draft from an image prefills its seed
- **Key:** `review:draft-from:a-draft-from-an-image-prefills-its-seed`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval naming one of its images
- **THEN** its count is one and its seeds are the image's seed

## REMOVED Requirements

### Requirement: An approval is copied from another flow's approval, recording where it came from

**Reason**: a copy no longer records the approval it came from, and no longer checks it again
([D3](../../changes/0111-deleting-with-its-approval/design.md#d3)).
**Migration**: replaced by *An approval is copied once from another flow's approval, its seeds with it*; an existing
copy's `copied_from` is left as it is, and its value is never read.

### Requirement: An approval nothing derives from can be cancelled back to its draft

**Reason**: what another flow took no longer holds the cancel
([D2](../../changes/0111-deleting-with-its-approval/design.md#d2)).
**Migration**: replaced by *An approval nothing of its own flow derives from can be cancelled back to its draft*.

### Requirement: A draft is written from another flow's approval, its own fields from its own sheet

**Reason**: a draft from another flow no longer records the approval it came from, nor holds its cancel
([D4](../../changes/0111-deleting-with-its-approval/design.md#d4)).
**Migration**: replaced by *A draft is written once from another flow's approval, its own fields from its own sheet*;
an existing draft's `drafted_from` is left as it is, and its value is never read.
