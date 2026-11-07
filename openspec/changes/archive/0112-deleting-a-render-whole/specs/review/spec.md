## ADDED Requirements

### Requirement: An unapproved draft can be discarded, with its source copy and nothing else

The system SHALL delete a flow's highest-numbered draft when asked, only while it is unapproved, with the source copy
held under its number, and SHALL refuse, naming the approval, when that number is approved. A discard SHALL leave the
flow's sheets and its assignment as they are, whichever way the draft was written.

A waiting draft blocks a revision; deleting the operator's own unfinished edit is the way out, and the one deletion
review makes. A source copy belongs to the draft of its number, so it goes with it; the flow stays, as a draft
discarded leaves nothing that names another flow
([D50](../../../docs/decisions.md#d50--the-last-render-takes-its-approval-and-a-flow-holds-only-its-own-files)).

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

#### Scenario: a drafted draft goes alone
- **Key:** `review:discard:a-drafted-draft-goes-alone`
- **Layers:** unit
- **WHEN** a draft from another flow's image, in a flow holding nothing but it, its source copy and its sheet, is
  discarded
- **THEN** the draft and its source copy are gone
- **AND** the sheet and the flow's directory stay

### Requirement: A draft is written once from another flow's approval, holding its own fields, seeds and image

When the operator names a source flow and one of its approvals, the system SHALL write the target flow's draft whose
every field both flows' schemas declare is the source approval's, and whose every other field the target declares is the
target's newest sheet's, recording the target's sheet and neither the source approval nor any image of the source.
Where the operator names one of that approval's images, the system SHALL copy that image into the target's sources,
under the draft's own number, before the draft is written — the **source copy** — and the draft SHALL have a count of
one and that seed listed; naming no image, it SHALL copy none, and its renders SHALL be the approval's seeds, as a
copy's are. A source copy SHALL never count as one of the target's renders. It SHALL approve that draft as an ordinary
approval of the target, never as a copy. It SHALL refuse, naming the way out: a target holding no sheet; a source
holding no such approval; a named image that approval never rendered, or whose image file is gone; a source that is the
target or no tracked flow; and a waiting draft of the target whose fields differ from its sheet's or that renders
anything but one drawn seed. A waiting draft equal to its sheet, rendering one drawn seed, SHALL be replaced at its own
number. A target approval or waiting draft drafted from a source approval SHALL NOT hold that approval's cancel.

```
source approval vN ──▶ every field both declare ─┐
target newest sheet ──▶ every field it alone has ┴─▶ target draft NNN · its own fields and seeds
source image <seed>.png ──── copied ──────────────▶ target sources/NNN.png
```

The operator corrects a sheet once, in the flow that reads the photograph, and finishes only the fields another flow
adds. A draft the operator never touched holds no work, so replacing it loses nothing; an edited one does, and a
count, a seed or a revision's seed is an edit. A draft from another flow is taken once: it holds its own fields, seeds
and image, so the source approval and its renders can go and leave it whole
([D49](../../../docs/decisions.md#d49--a-control-flow-is-its-subject-with-the-face-chain-at-zero-copied-once),
[D50](../../../docs/decisions.md#d50--the-last-render-takes-its-approval-and-a-flow-holds-only-its-own-files)).

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

#### Scenario: a draft from an image copies it
- **Key:** `review:draft-from:a-draft-from-an-image-copies-it`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval naming one of its images
- **THEN** the target's sources hold that image's bytes under the draft's number
- **AND** the draft records no image, and a draft naming no image copies none

#### Scenario: an image the approval never rendered is refused
- **Key:** `review:draft-from:an-image-the-approval-never-rendered-is-refused`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval naming a seed it rendered no image for, or whose image file is
  gone
- **THEN** it is refused naming that seed and the command that lists the rendered seeds
- **AND** no file is written

#### Scenario: a draft from an image prefills its seed
- **Key:** `review:draft-from:a-draft-from-an-image-prefills-its-seed`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval naming one of its images
- **THEN** its count is one and its seeds are the image's seed

## MODIFIED Requirements

### Requirement: An approval is copied once from another flow's approval, its seeds with it

When the operator names a source flow, the system SHALL write an approval under the target flow whose fields are the
source flow's latest approval's, validated against the target flow's schema and the vocabulary as any approval is, and
whose renders list the source approval's seeds — its listed seeds, then each seed its outputs group holds an image of —
its count raised to their number where it is lower. The copy SHALL name the target's newest sheet, SHALL record whether
its fields differ from that sheet's, and SHALL record that it is a copy and SHALL NOT record the source flow or
approval. The approve verb SHALL first fill a target holding no sheet from the photograph's tag list, as the sheet verb
fills one; asked of a target holding no sheet without that fill, the copy SHALL be refused, naming the sheet verb and
writing nothing. It SHALL refuse a run whose source flow has no approval, naming the way out. It SHALL write nothing
where the target's newest approval is a copy holding the same fields and renders, and SHALL otherwise copy under the
target's next number. It SHALL refuse a source that is the target itself or no tracked flow, before any run is opened.

```
runs/<id>/summon-anime-wai/review/001.approved.json      renders {count 2, seeds []} · outputs/001/ 11.png 12.png
        │  approve --flow control-anime-wai --from summon-anime-wai <run>
        │  control-anime-wai/sheets/ empty? fill 001.json from photo/wd14/ first
        ▼
runs/<id>/control-anime-wai/review/001.approved.json     same fields; renders {count 2, seeds [11, 12]}; a copy;
                                                         sheet 1, control's own
```

Two flows are compared only on one prompt and one noise. A copy by hand carries the source's identifier; a second
approval by hand lets the prompts drift. The target's own validation keeps the copy honest. The seeds travel with the
copy, so control and subject render the same seeds with no later check, and the source's approval can always be
cancelled or deleted with its renders. The copy's sheet is the target's own, so a revision of the copy compares
against a sheet the target holds
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

#### Scenario: the copy names the target's own sheet
- **Key:** `review:copy-from:the-copy-names-the-targets-own-sheet`
- **Layers:** unit
- **WHEN** a target holding a sheet is approved from a source approval
- **THEN** the copy names the target's newest sheet, and whether its fields differ from it
- **AND** a revision of one of the copy's images approves against that sheet
- **AND** a target holding no sheet refuses the copy, naming the sheet verb, and no file is written

#### Scenario: a target with no sheet is filled first
- **Key:** `review:copy-from:a-target-with-no-sheet-is-filled-first`
- **Layers:** unit
- **WHEN** the approve verb copies a source approval into a target holding no sheet
- **THEN** the target's first sheet is filled from the photograph's tag list, and the copy names it

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

## REMOVED Requirements

### Requirement: An unapproved draft can be discarded

**Reason**: a discard no longer undoes the flow a drafting assigned, and takes the draft's source copy with it
([D4](../../changes/0112-deleting-a-render-whole/design.md#d4)).
**Migration**: replaced by *An unapproved draft can be discarded, with its source copy and nothing else*; nothing on
disk moves.

### Requirement: A draft is written once from another flow's approval, its own fields from its own sheet

**Reason**: a named image is now copied into the target's sources rather than recorded
([D2](../../changes/0112-deleting-a-render-whole/design.md#d2)).
**Migration**: replaced by *A draft is written once from another flow's approval, holding its own fields, seeds and
image*; an old draft or approval keeps its recorded image, unread.
