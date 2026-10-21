## ADDED Requirements

### Requirement: Revise starts from an image, and opens its drafts as a queue

The system SHALL offer Revise from an image's large view and over a selection in the Renders grid, SHALL show what it
will write before writing, and SHALL then open Review on the drafts it wrote, one after another, returning to the hub
after the last. It SHALL write a selection's drafts all or none, refusing by name an image of a flow this build does
not track, and refusing a selection that names a version or a seed no run can hold. On a revision, Review SHALL show
the image being revised beside the photograph, mark each field that differs from its approval, and offer to discard
the draft, deleting it only once the operator confirms.

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

### Requirement: A version says what it was, and Compare shows a seed's two versions

The system SHALL head each approval version in the Renders view with the version it came from, read from its producer,
naming it a revision when its fields differ from that version's and a re-roll when only its count or seeds do. A large
view whose seed is rendered under an older version of the same source and flow SHALL offer Compare with the newest
such version, showing both images at equal size, the fields that changed, what changed in the count and seeds, and the
tokens before and after.

The origin is already on disk, so nothing new records it. Same seed, same composition: the difference left is the edit.

#### Scenario: a version is named a revision or a re-roll
- **Key:** `ui:compare:a-version-is-named-by-what-changed`
- **Layers:** unit
- **WHEN** one version changes a field of the version it came from and another changes only its seeds
- **THEN** the first is headed a revision and the second a re-roll

#### Scenario: Compare pairs a seed with its newest older version
- **Key:** `ui:compare:a-seed-pairs-with-its-newest-older-version`
- **Layers:** unit
- **WHEN** a seed is rendered under versions one, two and three
- **THEN** version three's large view compares with version two

#### Scenario: Compare shows the pair and the changed fields
- **Key:** `ui:compare:compare-shows-the-pair-and-the-change`
- **Layers:** e2e
- **WHEN** Compare is opened on a revised image
- **THEN** both images and the changed fields are shown

## MODIFIED Requirements

### Requirement: A draft update states the version of the draft it replaces

The system SHALL refuse a draft update, an approval or a discard whose stated precondition does not match the draft
on disk, and SHALL accept an update that states no precondition.

The surface autosaves on a debounce, so two updates can be in flight at once, and the server runs them
in a threadpool — which leaves the order they commit in decided by whichever finishes first rather than
by which keystroke came last. A precondition makes that order observable instead of silent: the loser is
told, rather than the winner's text being replaced by older text and the receipt describing a save that
is not on disk. A discard deletes, so a page deletes only the draft it last read.

An update stating no precondition is accepted because the artifact carries no revision of its own to
state, and a client that cannot read one must still be able to write.

#### Scenario: an update against a stale draft is refused
- **Key:** `ui:draft-update:a-stale-precondition-is-refused`
- **Layers:** unit
- **WHEN** a draft update states a precondition that does not match the draft on disk
- **THEN** it is refused
- **AND** the draft on disk is unchanged

#### Scenario: an update stating no precondition is accepted
- **Key:** `ui:draft-update:no-precondition-is-accepted`
- **Layers:** unit
- **WHEN** a draft update states no precondition
- **THEN** it is accepted

#### Scenario: overlapping updates cannot both commit
- **Key:** `ui:draft-update:overlapping-updates-cannot-both-commit`
- **Layers:** unit
- **WHEN** two draft updates stating the same precondition are in flight at once
- **THEN** one is accepted and the other is refused
- **AND** the draft on disk is the accepted update's

#### Scenario: an approval against a stale draft is refused
- **Key:** `ui:draft-update:a-stale-approval-is-refused`
- **Layers:** unit
- **WHEN** an approval states a precondition that does not match the draft on disk
- **THEN** it is refused
- **AND** nothing is approved

#### Scenario: a discard against a stale draft is refused
- **Key:** `ui:draft-update:a-stale-discard-is-refused`
- **Layers:** unit
- **WHEN** a discard states a precondition that does not match the draft on disk
- **THEN** it is refused
- **AND** the draft on disk is not deleted
