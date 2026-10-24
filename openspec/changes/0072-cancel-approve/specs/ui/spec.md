## MODIFIED Requirements

### Requirement: Review opens a batch at its own address, lists every unrendered sheet, and Approve stays on the sheet

The system SHALL open a batch's Review on its head: the first unapproved sheet of the first flow that has one, in the
hub's order; else the first approved sheet whose newest approval lacks images of its count, read-only; else a page
saying no sheet waits for review, with the way to the hub. The hub SHALL carry for each cell the number of images its
newest approval lacks, as the render stage counts it. Review's rail SHALL list every sheet of the flow that is
unapproved or lacks images, each marked untouched, edited, approved or re-opened, and its footer SHALL count the
approved among them; the Review tab SHALL count the unapproved. Approve SHALL leave the sheet open and read-only,
offering *Cancel approve* while the review stage can cancel it, else the reason beside it, and while no render runs
for the batch; a cancel SHALL leave the sheet open and editable. Opening a sheet that has no draft SHALL write one
through the review stage's own function, and opening it again SHALL write no second draft; a failure after approval
SHALL be shown in the approve bar, never dropped. ④ SHALL show one slot per image, a set seed or random, beside the
sheet rows. The photograph SHALL open in the viewer, stepping through the rail's sheets.

A sheet is done when its images are, not when it is approved, so the rail keeps it until then; the count is the
render stage's own. Approving is an act, not a navigation. A slot per image says what the next render draws before it
is approved.

```
the head:  first unapproved ─▶ else first approved and short ─▶ else "No sheet waits for review"
```

#### Scenario: a batch's Review opens its head
- **Key:** `ui:review:a-batch-opens-its-head`
- **Layers:** unit
- **WHEN** a batch holds an approved, short sheet and an unapproved one, then neither
- **THEN** its Review opens the unapproved sheet, then the approved one
- **AND** with no sheet left it opens none

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
- **WHEN** the photograph is opened, then `→` is pressed
- **THEN** the viewer shows it fitted, then the next sheet's photograph

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

