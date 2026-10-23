## MODIFIED Requirements

### Requirement: An approved input is read-only on the surface until it is re-opened

The system SHALL present an input whose flow has an approved artifact and no later draft as not editable,
SHALL refuse a draft update against such an input, and SHALL state on the page that the input is approved
and when, naming no file. Where a draft numbered above the approved artifact's `approved_from`
exists, the system SHALL present the input as **re-opened**: editable, its approval still
stated.

`review --flow F --new-version` writes a new numbered draft from the approved copy, and the surface shows that
state as its own rather than as something it is not: re-opened is a third status, and the approved artifact is
never edited in place in either case. The library counts every approval the run directories hold; Review's rail
holds the sheets not yet rendered and the one open, and its footer counts the approved among them.

#### Scenario: a draft update against an approved input is refused
- **Key:** `ui:approval:approved-input-refuses-a-draft-update`
- **Layers:** unit
- **WHEN** a draft update is submitted for an input whose flow is approved and holds no later draft
- **THEN** it is refused
- **AND** no file in the run directory is created, changed or removed

#### Scenario: an input approved in an earlier sitting opens read-only
- **Key:** `ui:approval:approved-input-opens-read-only`
- **Layers:** unit
- **WHEN** the surface serves an input whose flow has an approved artifact and no draft
- **THEN** the sheet it shows is the approved artifact's
- **AND** the input is presented as not editable

#### Scenario: an input re-opened with a new version is editable again
- **Key:** `ui:approval:a-re-opened-input-is-editable`
- **Layers:** unit
- **WHEN** the surface serves an input whose flow has an approved artifact and a draft numbered above the
  version that artifact records as its origin
- **THEN** the sheet it shows is the draft's
- **AND** the input is presented as editable
- **AND** a draft update against it is accepted

#### Scenario: a re-opened input is not counted as approved
- **Key:** `ui:approval:a-re-opened-input-is-not-counted-approved`
- **Layers:** unit
- **WHEN** the batch is read while one of its inputs is re-opened
- **THEN** that input's reported status is neither approved nor a plain draft
- **AND** the batch's approved count agrees with what the run directories hold
- **AND** Review's footer counts the approved among the rail's sheets, the re-opened one included

#### Scenario: a stale lower draft does not re-open an approved input
- **Key:** `ui:approval:a-stale-lower-draft-does-not-reopen`
- **Layers:** unit
- **WHEN** the surface serves an input whose flow has an approved artifact and a draft numbered below it
- **THEN** the sheet it shows is the approved artifact's
- **AND** the input is presented as not editable, naming no draft

#### Scenario: an update that overlaps an approval is refused
- **Key:** `ui:approval:an-update-overlapping-an-approval-is-refused`
- **Layers:** unit
- **WHEN** a draft update is in flight while the same input is approved
- **THEN** the update is refused once the approval has written
- **AND** the approved artifact is the one the approval wrote


### Requirement: The page's save state is true to the requests in flight, and a pending edit is sent on leaving

The system SHALL report a draft as saving exactly while a save it started is unanswered, whatever order saves and
input switches answer in, and SHALL send a pending edit when the page leaves the sheet — to another sheet, another
screen, or by closing — by a request the browser keeps alive past the page. A save SHALL wait for the sheet's save in
flight and state the draft it wrote, and a page closing while an edit waits behind a save in flight SHALL ask before
it goes. An approval SHALL wait for a save in flight, and state the draft that save wrote.

The saved receipt is the only thing on the page that speaks about saving, so a counter one stale answer can drive
below zero silences it for the rest of the input. An edit typed inside the debounce is the operator's work, and
closing the tab is an ordinary way to leave. An edit or an approval pressed inside a save's round trip is the
operator's own, not another tab's, and a closing page never reads the receipt it would have to state.

#### Scenario: a stale save cannot clear the saving state
- **Key:** `ui:save:a-stale-save-cannot-clear-saving`
- **Layers:** unit
- **WHEN** an input switch answers before the save it interrupted
- **THEN** the saving state clears only when that save answers
- **AND** the saved receipt returns

#### Scenario: a pending edit is sent on leaving
- **Key:** `ui:save:a-pending-edit-is-sent-on-leaving`
- **Layers:** unit
- **WHEN** the page leaves a sheet inside the debounce
- **THEN** the pending edit is sent with a request kept alive past the page
- **AND** a page closing while an edit waits behind an unanswered save asks before it goes

#### Scenario: an approval waits for a save in flight
- **Key:** `ui:save:an-approval-waits-for-a-save-in-flight`
- **Layers:** unit
- **WHEN** Approve is pressed while a save is unanswered
- **THEN** the approval is sent once that save answers, stating the draft it wrote


### Requirement: Revise starts from an image, and opens Review on its first draft

The system SHALL offer Revise from an image's large view and over a selection in the Renders grid, SHALL show what it
will write before writing, and SHALL then open Review on the first draft it wrote, the others of its flow
in the rail. It SHALL
write a selection's drafts all or none, refusing by name an image of a flow this build does not track, and refusing a
selection that names a version or a seed no run can hold. On a revision, Review SHALL show the photograph and the
image being revised on one line, at equal height under one header row, mark each field that differs from its
approval, offer *Side by side* to see both in one dialog, and offer to discard the draft from the approve bar,
deleting it only once the operator confirms.

The comparison that matters on a revision is the render against the photograph, read against the sheet. A discard
deletes the operator's edits, so one click never does.

#### Scenario: Revise opens Review on the revision
- **Key:** `ui:revise:revise-opens-review-on-the-revision`
- **Layers:** e2e
- **WHEN** Revise is confirmed on an image's large view
- **THEN** Review opens on its draft with the render beside the photograph and the seed prefilled

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
- **WHEN** *Side by side* is opened on a revision
- **THEN** one dialog shows the photograph and the render at equal height
- **AND** `Esc` closes it


### Requirement: Every screen has a URL naming its batch and its run

The system SHALL give Home, a batch's hub, a batch's Review and a review of a source in a flow each its own URL,
SHALL name the batch in every URL inside one, and SHALL name a run by the twelve-character digest its identifier
begins with. A batch's Review SHALL open the sheet Review starts from and put that sheet's URL in its place. It SHALL
answer any of them on a fresh load, and SHALL refuse one naming a batch or a run the library does not hold, naming
the way back.

A reload, a second tab or a bookmark then lands where it was, never on whatever the server last held open. A run's
short name is a sanitised filename and can repeat; its digest cannot.

```
/                                  Home
/b/<batch>/hub                     the hub
/b/<batch>/review                  the head of Review, replaced by its sheet's URL
/b/<batch>/review/<digest>/<flow>  Review
```

#### Scenario: a reload lands on the same screen
- **Key:** `ui:routes:a-reload-lands-on-the-same-screen`
- **Layers:** e2e
- **WHEN** a hub, a review or a batch's Review address is loaded again
- **THEN** the same batch, source and flow are shown
- **AND** a batch's Review address is replaced by its head's sheet URL
- **AND** a batch with no sheet waiting says none waits

#### Scenario: a run is named by its digest
- **Key:** `ui:routes:a-run-is-named-by-its-digest`
- **Layers:** unit
- **WHEN** a review URL names a run
- **THEN** the run is the one whose identifier begins with that digest

#### Scenario: an unknown batch is refused with the way back
- **Key:** `ui:routes:an-unknown-batch-is-refused`
- **Layers:** e2e
- **WHEN** a URL names a batch the library does not hold
- **THEN** the page refuses, naming the batch
- **AND** it offers the way back to Home

