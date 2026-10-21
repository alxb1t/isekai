## ADDED Requirements

### Requirement: Revise starts from an image, and opens its drafts as a queue

The system SHALL offer Revise from an image's large view and over a selection in the Renders grid, SHALL show what it
will write before writing, and SHALL then open Review on the drafts it wrote, one after another, returning to the hub
after the last. On a revision, Review SHALL show the image being revised beside the photograph and mark each field
that differs from its approval.

The comparison that matters on a revision is the render against the photograph, read against the sheet.

#### Scenario: Revise opens Review on the revision
- **Key:** `ui:revise:revise-opens-review-on-the-revision`
- **Layers:** e2e
- **WHEN** Revise is confirmed on an image's large view
- **THEN** Review opens on its draft with the render beside the photograph and the seed prefilled

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
