## MODIFIED Requirements

### Requirement: Review opens a batch at its own address, lists every unrendered sheet, and Approve stays on the sheet

The system SHALL open a batch's Review on a chooser when two or more flows hold sheets to review: a row per flow, its
name, how many wait to be approved and how many lack images, and up to fifteen of its waiting photographs, then `+n`;
`j` `k` and the arrows SHALL move between rows, `↵` or a click on a row SHALL open that flow's head, and a click on a
photograph that sheet. With one such flow it SHALL open that flow's head: its first unapproved sheet in the hub's order,
else its first approved sheet whose newest approval lacks images of its count, read-only; with none, a page saying no
sheet waits for review, with the way to the hub. `Esc` on Review, with no overlay open and outside a field, SHALL return
to the chooser. The hub SHALL carry for each cell the number of images its newest approval lacks, as the render stage
counts it. Review's rail SHALL list every sheet of the flow that is unapproved or lacks images, each marked untouched,
edited, approved or re-opened, and its footer SHALL count the approved among them; the Review tab SHALL count the
unapproved, every flow's, and the rail's head SHALL name each other flow holding some, with how many and the key to the
chooser. Approve SHALL leave the sheet open and read-only, the approve bar naming the approval it shows, offering
*Cancel approve* while the review stage can cancel it, else the reason beside it, and while no render runs for the
batch; a cancel SHALL leave the sheet open on what the flow is left on: its draft, editable, or for a copy the draft
open above what lies beneath, else the approval beneath it, read-only. Opening a sheet that has no draft SHALL write one
through the review stage's own function, and opening it again SHALL write no second draft; a failure after approval
SHALL be shown in the approve bar, never dropped. ④ SHALL show one slot per image, a set seed or random, beside the
sheet rows. `⌃P` SHALL open the photograph in the viewer — on a revision or a draft from an image, *Side by side* — from
any pane and from a field, stepping through the rail's sheets, and `Esc` SHALL return the focus where it was.

A sheet is done when its images are, not when it is approved, so the rail keeps it until then; the count is the
render stage's own. Approving is an act, not a navigation, and a copy's cancel takes back only the copy. A slot per
image says what the next render draws before it is approved. The operator chooses the flow to review; the page
does not choose it for them.

```
two or more flows waiting ─▶ the chooser ─↵─▶ that flow's head
one flow waiting          ─▶ its head: first unapproved ─▶ else first approved and short
none                      ─▶ "No sheet waits for review"
```

#### Scenario: a batch's Review opens its head
- **Key:** `ui:review:a-batch-opens-its-head`
- **Layers:** unit
- **WHEN** a batch's one flow holds an approved, short sheet and an unapproved one, then neither
- **THEN** its Review opens the unapproved sheet, then the approved one
- **AND** with no sheet left it opens none

#### Scenario: two flows waiting open the chooser
- **Key:** `ui:review:two-flows-waiting-open-the-chooser`
- **Layers:** unit
- **WHEN** a batch's two flows each hold an unapproved sheet
- **THEN** its Review is a row per flow, each naming its count and its waiting photographs

#### Scenario: the chooser opens a flow
- **Key:** `ui:review:the-chooser-opens-a-flow`
- **Layers:** e2e
- **WHEN** the Review tab opens on two waiting flows, `j` then `↵` are pressed
- **THEN** Review opens on the second flow's first waiting sheet
- **AND** `Esc` returns to the chooser, its second row focused

#### Scenario: a cell counts what its newest approval lacks
- **Key:** `ui:review:a-cell-counts-what-it-lacks`
- **Layers:** unit
- **WHEN** a cell's newest approval holds one image of a count of three
- **THEN** the hub carries two for that cell

#### Scenario: the rail holds every sheet not yet rendered
- **Key:** `ui:review:the-rail-holds-every-unrendered-sheet`
- **Layers:** unit
- **WHEN** a flow holds an unapproved sheet, an approved short one and an approved one with all its images
- **THEN** the rail lists the first two, marked by their state

#### Scenario: Approve stays on the sheet
- **Key:** `ui:review:approve-stays-on-the-sheet`
- **Layers:** e2e
- **WHEN** a sheet is approved
- **THEN** the same sheet stays open, read-only, and its rail mark reads approved
- **AND** the approve bar names its approval

#### Scenario: opening a sheet with no draft writes one
- **Key:** `ui:review:opening-a-sheet-writes-its-draft`
- **Layers:** unit
- **WHEN** Review opens a sheet whose flow has a sheet and no draft
- **THEN** a draft is written through the review stage
- **AND** opening it again writes no second draft

#### Scenario: a failure after approval is shown
- **Key:** `ui:review:a-failure-after-approval-is-shown`
- **Layers:** e2e
- **WHEN** an approval succeeds and reading the batch again fails
- **THEN** the approve bar shows the refusal

#### Scenario: each image has a slot
- **Key:** `ui:review:each-image-has-a-slot`
- **Layers:** unit
- **WHEN** a draft renders four images with seed 144 listed
- **THEN** ④ shows four slots, the first holding 144 and three random
- **AND** removing a slot takes a random one first

#### Scenario: the photograph opens in the viewer
- **Key:** `ui:review:the-photograph-opens-in-the-viewer`
- **Layers:** e2e
- **WHEN** `⌃P` is pressed in a tag field, then `→`
- **THEN** the viewer shows the photograph fitted, then the next sheet's photograph
- **AND** `Esc` returns the focus to the field

#### Scenario: Cancel approve opens the sheet again
- **Key:** `ui:review:cancel-approve-opens-the-sheet-again`
- **Layers:** e2e
- **WHEN** a sheet is approved, then *Cancel approve* is pressed
- **THEN** the same sheet is editable again

#### Scenario: an approved sheet says why it cannot be cancelled
- **Key:** `ui:review:the-sheet-says-why-it-cannot-be-cancelled`
- **Layers:** unit
- **WHEN** Review reads an approved sheet whose prompt is assembled
- **THEN** its payload carries the review stage's reason

#### Scenario: the rail names the other flows' waiting sheets
- **Key:** `ui:review:the-rail-names-the-other-flows-waiting`
- **Layers:** unit
- **WHEN** Review is open on one flow and another flow holds one unapproved sheet
- **THEN** the rail's head names that flow and one waiting

### Requirement: Revise starts from an image, and opens Review on its first draft

The system SHALL offer Revise from an image's large view and over a selection in the Renders grid, SHALL show what it
will write before writing, and SHALL then open Review on the first draft it wrote, the others of its flow
in the rail. An image whose flow holds a waiting draft SHALL write nothing: Revise from its large view SHALL open
Review on that draft, and a selection SHALL leave such images out, the confirm naming them. It SHALL
write a selection's drafts all or none, refusing by name an image of a flow this build does not track, and refusing a
selection that names a version or a seed no run can hold. On a revision, draft or approved, Review SHALL show the
photograph and the image being revised — the one the revision records, whatever its seeds became, else the first of
its seeds rendered under its approval — on one line, at equal height under one header row, mark each field that
differs from its approval, and offer *Side by side*, also on `⌃P`, both in one dialog, `⌃P` in it showing the photograph
alone and back; on a draft it SHALL offer to discard it from the approve bar, deleting it only once the operator
confirms.

The comparison that matters on a revision is the render against the photograph, read against the sheet. A discard
deletes the operator's edits, so one click never does. A waiting draft is the work in hand, so Revise goes to it;
the comparison still matters once the revision is approved.

#### Scenario: Revise opens Review on the revision
- **Key:** `ui:revise:revise-opens-review-on-the-revision`
- **Layers:** e2e
- **WHEN** Revise is confirmed on an image's large view
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
- **WHEN** Revise is asked for an image whose flow holds a waiting draft
- **THEN** it answers with that draft and writes nothing

#### Scenario: an untracked flow refuses its image
- **Key:** `ui:revise:an-untracked-flow-refuses-its-image`
- **Layers:** unit
- **WHEN** Revise is asked for a selection holding an image of a flow this build does not track
- **THEN** that image is refused naming its flow
- **AND** no draft is written for any image

#### Scenario: an image no run can hold is refused
- **Key:** `ui:revise:an-image-no-run-can-hold-is-refused`
- **Layers:** unit
- **WHEN** Revise is asked for an image whose version or seed no run can hold
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

### Requirement: Conjure from this drafts from an image's approval, and opens Review on it

The system SHALL offer, on an image's large view, one action per target — each flow the surface offers that reads a
sheet alone, other than the image's own, assigned or not — named *Conjure from this* for `conjure-anime-wai`, the first
on `⇧F`. It SHALL draft the target of the image's run from the approval the image was rendered under, naming the image,
as the review verb's `--from` does — assigning it and filling its sheet first where it holds none — then open Review on
that draft; where the target holds a waiting draft with edits of its own, it SHALL write nothing and open Review on that
draft; a refusal SHALL show on the large view, and write nothing. On such a draft, approved or not, Review SHALL show
the image it records beside the photograph as it shows a revision's, headed by its flow, version and seed, mark each
field that differs from the target's sheet and name the source flow and approval in the sheet's kicker, and on the draft
offer *Discard draft*.

```
large view · summon-anime-wai v1 · seed 7     [ Conjure from this ⇧F ]
        │ drafts conjure-anime-wai from summon-anime-wai v1
        ▼
Review · conjure-anime-wai   ③ SHEET — FROM SUMMON-ANIME-WAI V1   hair_colour  was …
```

The image the operator approved is where the next flow starts. A flow that reads a photograph has its own sheet of
the person, so it is no target. The press assigns, so no tick and no Prepare come first; an edited draft is the
work in hand. The marks show what the source changed, so the operator reads only the fields the
target adds.

#### Scenario: the large view names its targets
- **Key:** `ui:conjure-from:the-large-view-names-its-targets`
- **Layers:** unit
- **WHEN** a summon image's large view is read in a batch where no source is assigned conjure
- **THEN** its targets are conjure alone

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
- **WHEN** `⇧F` is pressed on a summon image whose source is not assigned conjure
- **THEN** Review opens on conjure's draft, its kicker naming the summon approval
- **AND** a field summon changed is marked against conjure's sheet
- **AND** its caption pane shows summon's caption, named as summon's, and the summon image stands beside the photograph
