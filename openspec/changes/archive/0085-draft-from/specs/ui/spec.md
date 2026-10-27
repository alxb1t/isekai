## REMOVED Requirements

### Requirement: Revise starts from an image, and opens Review on its first draft

**Reason**: Revise and *Conjure from this* are one act, a draft from an image for a flow; the same flow is a revision.

**Migration**: *Draft from this* on `⇧D`, its own flow the revision; its scenarios hold under *Draft from this starts
from an image, for any flow the app offers, and opens Review on the draft*.

### Requirement: Conjure from this drafts from an image's approval, and opens Review on it

**Reason**: folded into *Draft from this*, which offers every flow the app offers, not the sheet-alone ones alone.

**Migration**: *Draft from this* on `⇧D`, the target chosen in its dialog; its scenarios hold under the new
requirement.

## ADDED Requirements

### Requirement: Draft from this starts from an image, for any flow the app offers, and opens Review on the draft

The system SHALL offer *Draft from this* on `⇧D` from an image's large view and over a selection in the Renders grid,
opening a dialog that lists every flow the app offers, the image's own first, named *revise*, focused, and the others
after it, assigned or not; `↵` SHALL draft the chosen flow from each image's approval, as the draft verb does — a
revision for the image's own flow, a draft from that approval for another, assigning a target and filling its sheet
from the source's tags where it holds none, the image's seed prefilled and the image recorded — then open Review on the
first draft, the others of its flow in the rail. A target holding a waiting draft with edits of its own SHALL write
nothing for that image and open Review on that draft; one equal to its sheet SHALL be replaced. A selection SHALL be
drafted all or none, refusing by name an image of a flow this build does not track, and refusing a selection that names
a version or a seed no run can hold. On such a draft, draft or approved, Review SHALL show the photograph and the image
the draft records — whatever its seeds became, else, for a revision, the first of its seeds rendered under its approval
— on one line, at equal height under one header row, headed by its flow, version and seed, and offer *Side by side*,
also on `⌃P`, both in one dialog, `⌃P` in it showing the photograph alone and back; it SHALL mark each field that
differs from the approval a revision came from, or from the target's sheet for another flow, naming the source flow and
approval in the sheet's kicker; on a draft it SHALL offer to discard it from the approve bar, deleting it only once the
operator confirms.

```
large view · summon-anime-wai v2 · seed 9423…   ⇧D
  Draft from this
  ▸ summon-anime-wai        revise
    summon-flat-anime-wai
    conjure-anime-wai
  ↵ ─▶ Review on the draft: the photograph │ the image it came from
```

An image the operator approved is where the next draft starts, in its own flow or another: one act, whatever the flows
become. The comparison that matters is the render against the photograph, read against the sheet. A waiting edit is the
work in hand; a draft the operator never touched holds no work. A discard deletes the operator's edits, so one click
never does.

#### Scenario: Revise opens Review on the revision
- **Key:** `ui:revise:revise-opens-review-on-the-revision`
- **Layers:** e2e
- **WHEN** *Draft from this* is drafted into the image's own flow on its large view
- **THEN** Review opens on its draft with the render beside the photograph and the seed prefilled
- **AND** once approved, the render still stands beside the photograph

#### Scenario: a revision keeps its image after its seed changes
- **Key:** `ui:revise:a-revision-keeps-its-image-after-its-seed-changes`
- **Layers:** unit
- **WHEN** Review reads a revision whose seed was changed, draft and then approved
- **THEN** its payload names the image the revision was written from

#### Scenario: an approved revision keeps its image
- **Key:** `ui:revise:an-approved-revision-keeps-its-image`
- **Layers:** unit
- **WHEN** Review reads a revision's approval
- **THEN** its payload names the approval it came from, its image and that approval's fields

#### Scenario: a waiting draft is opened, not refused
- **Key:** `ui:revise:a-waiting-draft-is-opened`
- **Layers:** unit
- **WHEN** a revision is asked for an image whose flow holds a waiting draft with edits of its own
- **THEN** it answers with that draft and writes nothing

#### Scenario: an untracked flow refuses its image
- **Key:** `ui:revise:an-untracked-flow-refuses-its-image`
- **Layers:** unit
- **WHEN** a draft is asked for a selection holding an image of a flow this build does not track
- **THEN** that image is refused naming its flow
- **AND** no draft is written for any image

#### Scenario: an image no run can hold is refused
- **Key:** `ui:revise:an-image-no-run-can-hold-is-refused`
- **Layers:** unit
- **WHEN** a draft is asked for an image whose version or seed no run can hold
- **THEN** the selection is refused
- **AND** no draft is written

#### Scenario: a discard deletes the draft the page read
- **Key:** `ui:revise:a-discard-deletes-the-draft-the-page-read`
- **Layers:** unit
- **WHEN** a discard states the draft on disk
- **THEN** that draft is deleted
- **AND** every approval is unchanged

#### Scenario: Discard asks before it deletes
- **Key:** `ui:revise:discard-asks-before-it-deletes`
- **Layers:** e2e
- **WHEN** Discard is pressed on a revision, then Keep
- **THEN** the draft is still on disk and the sheet still open

#### Scenario: Side by side shows the pair
- **Key:** `ui:revise:side-by-side-shows-the-pair`
- **Layers:** e2e
- **WHEN** `⌃P` is pressed on a revision with focus in a tag field, then `⌃P` again
- **THEN** one dialog shows the photograph and the render at equal height, then the photograph alone
- **AND** `Esc` closes it

#### Scenario: the large view names its targets
- **Key:** `ui:conjure-from:the-large-view-names-its-targets`
- **Layers:** unit
- **WHEN** a summon image's large view is read in a collection where no source is assigned another flow
- **THEN** its targets are every flow the app offers, summon first

#### Scenario: a refused draft writes nothing
- **Key:** `ui:conjure-from:a-refused-draft-writes-nothing`
- **Layers:** unit
- **WHEN** a draft is asked from an approval version the source does not hold
- **THEN** it is refused naming that version
- **AND** no file is written

#### Scenario: a waiting edit is opened
- **Key:** `ui:conjure-from:a-waiting-edit-is-opened`
- **Layers:** unit
- **WHEN** a draft is asked for a target whose waiting draft has edits of its own
- **THEN** it answers with that draft and writes nothing

#### Scenario: an approved draft keeps its marks
- **Key:** `ui:conjure-from:an-approved-draft-keeps-its-marks`
- **Layers:** unit
- **WHEN** Review reads the approval of a draft written from another flow's approval
- **THEN** it names the source flow and approval, and carries the target sheet's fields

#### Scenario: Review reads the draft against the target's sheet
- **Key:** `ui:conjure-from:review-reads-the-draft-against-the-sheet`
- **Layers:** unit
- **WHEN** Review reads a draft written from another flow's approval
- **THEN** it names the source flow and approval, and carries the target sheet's fields

#### Scenario: Conjure from this opens Review on the draft
- **Key:** `ui:conjure-from:conjure-from-this-opens-review`
- **Layers:** e2e
- **WHEN** `⇧D` is pressed on a summon image whose source is not assigned conjure, conjure chosen and `↵` pressed
- **THEN** Review opens on conjure's draft, its kicker naming the summon approval
- **AND** a field summon changed is marked against conjure's sheet
- **AND** its caption pane shows summon's caption, named as summon's, and the summon image stands beside the photograph

#### Scenario: an unedited waiting draft is replaced
- **Key:** `ui:draft-from:an-unedited-waiting-draft-is-replaced`
- **Layers:** unit
- **WHEN** a draft is asked for a target whose waiting draft equals its sheet
- **THEN** the draft from the image is written at that draft's number

#### Scenario: a selection drafts into the flow chosen
- **Key:** `ui:draft-from:a-selection-drafts-into-the-flow-chosen`
- **Layers:** unit
- **WHEN** a selection of two images from different runs is drafted into another flow
- **THEN** each run's target gains a draft from its image's approval, its seed prefilled
