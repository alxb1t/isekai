## ADDED Requirements

### Requirement: A tattoo's stage-1 pairs are kept per photograph

The system SHALL keep, for each tattoo and each photograph, one stage-1 file under the tattoo's folder, named by the
photograph's digest: the pairs of points between the tattoo's image and the photograph, and whether the tattoo is
*not on this photo*. It SHALL save the file each time the page sends it, and SHALL refuse a point that is not a
finite, non-negative pair of numbers and a tattoo-side point outside the tattoo's image. It SHALL read a photograph
with no file as no pairs and the tattoo on the photograph. It SHALL tell the picker, for one photograph, each
tattoo's pair count and flag. A cut SHALL take no stage-1 file.

The pairs depend on the tattoo and the photograph, not on the render, so a second render of the same photograph
needs only its own stage. The photograph is named by its digest, as a run is
([D16](../../../docs/decisions.md#d16--a-run-is-keyed-by-the-photographs-bytes)).

#### Scenario: pairs are saved as they are sent
- **Key:** `tattoo:stage1:pairs-are-saved-as-they-are-sent`
- **Layers:** unit
- **WHEN** the pairs of a tattoo on a photograph are saved, and then saved again with one pair more
- **THEN** each save replaces the file, and reading it gives the last pairs

#### Scenario: a photograph with no file has no pairs
- **Key:** `tattoo:stage1:a-photograph-with-no-file-has-no-pairs`
- **Layers:** unit
- **WHEN** the stage-1 file of a tattoo on a photograph it was never placed on is read
- **THEN** it holds no pairs and the flag is off, and nothing is written

#### Scenario: a bad point is refused
- **Key:** `tattoo:stage1:a-bad-point-is-refused`
- **Layers:** unit
- **WHEN** a pair holds a negative coordinate, a non-number, or a tattoo-side point outside the tattoo's image
- **THEN** the save is refused naming the pair, and the file is as it was

#### Scenario: the flag keeps the pairs
- **Key:** `tattoo:stage1:the-flag-keeps-the-pairs`
- **Layers:** unit
- **WHEN** a tattoo with pairs is saved *not on this photo*, and then saved again with the flag off
- **THEN** each save holds the same pairs

#### Scenario: the picker is told each tattoo's state on a photograph
- **Key:** `tattoo:stage1:the-picker-is-told-each-tattoos-state`
- **Layers:** unit
- **WHEN** one tattoo has pairs on a photograph and another is flagged *not on this photo*
- **THEN** the states name the first's pair count and the second's flag
- **AND** a tattoo placed on no photograph is named by no state

#### Scenario: a cut takes no stage-1 file
- **Key:** `tattoo:stage1:a-cut-takes-no-stage-1-file`
- **Layers:** unit
- **WHEN** stage-1 pairs are saved for a cut
- **THEN** the save is refused, saying the ink is already in the photograph's pixels

### Requirement: The placement preview is made on the server

The system SHALL answer a `POST` naming a tattoo, a target and the pairs of a stage with the warped ink: the ink
view's layer carried through the stage's thin-plate splines onto the target's pixels, clipped to the limb outline and
removed under each exclusion, flattened on white as a JPEG, on a crop of the target. The crop SHALL be the box of the
stage's target-side points and the limb, grown by the declared margin, clipped to the target. The answer SHALL be
`no-store`, SHALL name the crop's box and the automatic white point in its headers, and SHALL be made now and kept
nowhere. The system SHALL read the mode from the tattoo: a cut, a tattoo not on this photo, or a tattoo placed in two
stages. It SHALL refuse fewer than the preview's floor of pairs, a lone point, a limb or an exclusion with fewer than
the declared floor of points, a second stage whose first holds fewer pairs than its floor, a cut asked on another
photograph, and an outline that is not closed.

A preview over a full grid takes seconds and over a crop about one
([D53](../../../docs/decisions.md#d53--a-placement-is-recorded-beside-its-edit)). The page multiplies the JPEG over
the target, which is the Multiply the bake makes.

#### Scenario: the preview is a JPEG on the crop of the target's points
- **Key:** `tattoo:placement-preview:a-jpeg-on-the-crop-of-the-targets-points`
- **Layers:** unit
- **WHEN** the preview of a stage-1 warp is asked on a photograph
- **THEN** the answer is a JPEG the size of the box its header names, inside the photograph
- **AND** the box holds the photograph-side points grown by the margin

#### Scenario: the ink is white where nothing lands
- **Key:** `tattoo:placement-preview:the-ink-is-white-where-nothing-lands`
- **Layers:** unit
- **WHEN** the preview of a render stage is asked
- **THEN** a pixel outside the tattoo's warped ink is white, and a pixel on its dark ink is darker

#### Scenario: the limb keeps the ink and an exclusion removes it
- **Key:** `tattoo:placement-preview:the-limb-keeps-the-ink-and-an-exclusion-removes-it`
- **Layers:** unit
- **WHEN** the preview of a render stage is asked with a limb polygon and an exclusion polygon inside it
- **THEN** the ink outside the limb is white, and the ink inside the exclusion is white

#### Scenario: a cut is carried by one stage
- **Key:** `tattoo:placement-preview:a-cut-is-carried-by-one-stage`
- **Layers:** unit
- **WHEN** the preview of a cut is asked with pairs between its photograph and the render
- **THEN** the ink lands on the render at the pairs' points, with no stage-1 file read

#### Scenario: a tattoo not on this photo is carried by the direct pairs
- **Key:** `tattoo:placement-preview:a-direct-tattoo-is-carried-by-the-direct-pairs`
- **Layers:** unit
- **WHEN** the preview is asked of a tattoo flagged *not on this photo*, with pairs between the tattoo and the render
- **THEN** the ink lands on the render at the pairs' points, with no stage-1 file read

#### Scenario: a second stage needs its first
- **Key:** `tattoo:placement-preview:a-second-stage-needs-its-first`
- **Layers:** unit
- **WHEN** the preview of a render stage is asked of a tattoo whose stage 1 holds fewer pairs than its floor
- **THEN** it is refused, naming the pairs held and the floor

#### Scenario: too few pairs, a lone point and a short region are refused
- **Key:** `tattoo:placement-preview:too-few-pairs-a-lone-point-and-a-short-region-are-refused`
- **Layers:** unit
- **WHEN** the preview is asked with two pairs, with a point that has no match, or with a limb of two points
- **THEN** each is refused, naming the floor, the point or the region

#### Scenario: a cut on another photograph is refused
- **Key:** `tattoo:placement-preview:a-cut-on-another-photograph-is-refused`
- **Layers:** unit
- **WHEN** the preview of a cut is asked on a photograph it is not cut from
- **THEN** it is refused, naming the photograph the cut is from

#### Scenario: the answer is kept nowhere
- **Key:** `tattoo:placement-preview:the-answer-is-kept-nowhere`
- **Layers:** unit
- **WHEN** the preview is asked
- **THEN** its cache header is `no-store`, and the library and the run hold no new file

### Requirement: A bake writes the edit request and its placement record

The system SHALL, on a bake, make the composite of the render from the tattoo's placement, the Multiply of the warped
ink over the whole render, and SHALL write it through the edit stage with the edit's record and a placement record
beside them, never the edit's image. The placement record SHALL hold the tattoo's name and kind, the mode, the image
it is placed on, the outline with its white scale, neutral and depth, the stage-1 pairs of the bake, the stage's
pairs, the limb and the exclusions. It SHALL refuse what the preview refuses, a stage short of its floor of pairs, and
a render that is not on disk. The photograph a tattoo was cut from SHALL never enter the run.

The edit stage owns a request's files and their order, so the screen asks it and writes nothing itself
([D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children)). The record is a copy, so a later
change of the tattoo's pairs leaves it as it was.

#### Scenario: a bake writes the composite, the placement and the record
- **Key:** `tattoo:bake:a-bake-writes-the-composite-the-placement-and-the-record`
- **Layers:** unit
- **WHEN** a two-stage tattoo is baked on a render
- **THEN** the render's group holds the edit's composite, its placement record and its record, and no image

#### Scenario: the composite is the render with the ink multiplied on
- **Key:** `tattoo:bake:the-composite-is-the-render-with-the-ink-multiplied-on`
- **Layers:** unit
- **WHEN** a bake's composite is read
- **THEN** it is the render's size, equal to the render away from the ink and darker on it

#### Scenario: the placement holds what was placed
- **Key:** `tattoo:bake:the-placement-holds-what-was-placed`
- **Layers:** unit
- **WHEN** a cut is baked with a limb and one exclusion
- **THEN** the placement names the tattoo and its kind, the mode, the outline and tone, the pairs, the limb and the
  exclusion
- **AND** it holds no stage-1 pairs

#### Scenario: the placement keeps the stage-1 pairs it used
- **Key:** `tattoo:bake:the-placement-keeps-the-stage-1-pairs-it-used`
- **Layers:** unit
- **WHEN** a tattoo is baked and its stage-1 pairs are then saved again with others
- **THEN** the placement still holds the pairs it was baked with

#### Scenario: a bake short of its floor is refused and writes nothing
- **Key:** `tattoo:bake:a-bake-short-of-its-floor-writes-nothing`
- **Layers:** unit
- **WHEN** a bake is asked with fewer pairs than its stage's floor
- **THEN** it is refused, naming the floor, and the group is as it was

#### Scenario: the photograph never enters the run
- **Key:** `tattoo:bake:the-photograph-never-enters-the-run`
- **Layers:** unit
- **WHEN** a cut is baked
- **THEN** the run's files hold no copy of the photograph beside the render's own

### Requirement: A bake is placed on an image, and a later bake changes no earlier one

The system SHALL place a bake on the render's image or on the image of a baked edit of it, and SHALL give each bake
the next free number of the render's seed, so a bake placed on an earlier image beside a later one is a new edit and
none is replaced. It SHALL record the number of the edit it is placed on, none for the render, and SHALL refuse to
place on an edit that has no image yet.

An edit's record is its own history, so placing again adds an edit and leaves the earlier ones, and every edit placed
on them, as they are.

#### Scenario: a bake on a baked edit chains
- **Key:** `tattoo:bake-chain:a-bake-on-a-baked-edit-chains`
- **Layers:** unit
- **WHEN** a render is baked, the bake's image exists, and a second tattoo is baked on that image
- **THEN** the second edit's record names the first edit's image as its source
- **AND** its placement names the first's number

#### Scenario: a second bake on the same image is a new edit
- **Key:** `tattoo:bake-chain:a-second-bake-on-the-same-image-is-a-new-edit`
- **Layers:** unit
- **WHEN** two tattoos are baked on the same render's image
- **THEN** the group holds two edits with their own numbers, each placed on the render, and the first is as it was

#### Scenario: a pending edit cannot be placed on
- **Key:** `tattoo:bake-chain:a-pending-edit-cannot-be-placed-on`
- **Layers:** unit
- **WHEN** a bake is asked on the number of an edit that has no image
- **THEN** it is refused, saying that edit waits for its render session, and nothing is written

### Requirement: A placement record goes with its edit

The system SHALL name an edit's placement record beside its record, SHALL leave it out of every listing of renders
and of unread files, and SHALL delete it with its edit when the edit is discarded and when the render the edit
belongs to is deleted.

A placement record is part of an edit, so an edit left with one would keep its group alive.

#### Scenario: the listings skip the placement
- **Key:** `tattoo:placement-file:the-listings-skip-the-placement`
- **Layers:** unit
- **WHEN** a group holds a render, an edit and its placement record
- **THEN** the seeds of the group's renders are the render's alone, and the unread list names no placement record

#### Scenario: a discarded edit takes its placement
- **Key:** `tattoo:placement-file:a-discarded-edit-takes-its-placement`
- **Layers:** unit
- **WHEN** an edit with a placement record is discarded
- **THEN** its composite, its record and its placement record are gone

#### Scenario: a deleted render takes the placement of its edits
- **Key:** `tattoo:placement-file:a-deleted-render-takes-the-placement-of-its-edits`
- **Layers:** unit
- **WHEN** a render with two edits and their placement records is deleted
- **THEN** no placement record of the seed is left in the group
