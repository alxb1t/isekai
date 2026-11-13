# Capability: `tattoo`

## Purpose

A tattoo kept in the library and placed on a render: an upload is kept whole under the library's `.tattoos/`,
a cut under its photograph's `.tattoos/.cuts/<digest>/`, each until it is removed, with its outline and ink tone,
and its ink is warped onto a render by thin-plate splines and shown as a view the server makes and never stores.

## Requirements

### Requirement: A tattoo is cut from a photograph

The system SHALL keep a cut: a tattoo with no image of its own, whose record names the digest of the photograph
it is cut from, and whose outline is in that photograph's pixels.
It SHALL keep it under `.tattoos/.cuts/<digest>/<name>/`, so it is listed and named on that photograph's renders alone.
It SHALL start from the newest cut of the same photograph's tone, its neutral, depth and white point,
else from the photograph's defaults. A cut SHALL serve only the renders of its own photograph.

A cut carries that photograph's light and angle, so it is no input for another photograph;
another photograph takes an uploaded tattoo.

#### Scenario: a cut holds no image and names its photograph
- **Key:** `tattoo:cut:a-cut-holds-no-image`
- **Layers:** unit
- **WHEN** a tattoo is cut from a photograph's digest under a name
- **THEN** `.tattoos/.cuts/<digest>/<name>/` holds a record naming that digest and no image

#### Scenario: a first cut starts from the photograph's defaults
- **Key:** `tattoo:cut:a-first-cut-starts-from-the-defaults`
- **Layers:** unit
- **WHEN** a photograph's first cut is kept
- **THEN** its outline file holds neutral on, the photograph's depth and the automatic white point, and no points

#### Scenario: a second cut starts from the first cut's tone
- **Key:** `tattoo:cut:a-second-cut-starts-from-the-first-cuts-tone`
- **Layers:** unit
- **WHEN** a first cut of a photograph has neutral off, depth 1.2 and a white scale of 0.9,
  and a second is cut from the same photograph
- **THEN** the second holds neutral off, depth 1.2 and a white scale of 0.9, and no points

#### Scenario: a cut serves only its own photograph
- **Key:** `tattoo:cut:a-cut-serves-only-its-own-photograph`
- **Layers:** unit
- **WHEN** the ink view of a cut is asked on another photograph's digest
- **THEN** it is refused, naming the photograph the cut is from

### Requirement: An outline and its ink tone are kept with the tattoo

The system SHALL keep, per tattoo, one outline file: the points of a polygon in the pixels of the tattoo's image,
or of the photograph for a cut; whether it is closed; the white scale; neutral; and depth.
It SHALL save the file each time the page sends it, and SHALL refuse a point outside the image,
more points than the declared ceiling, a closed outline with fewer than the declared floor,
a depth outside the declared range and a white scale of zero or less, or past 255.
A tattoo SHALL read as outlined when its outline is closed.
A tattoo cut from a photograph SHALL default to neutral on and the photograph's depth,
an uploaded one to neutral off and the image's depth.

Saving happens as the operator goes, so a closed page loses nothing.

#### Scenario: an outline is saved as it is sent
- **Key:** `tattoo:outline:an-outline-is-saved-as-it-is-sent`
- **Layers:** unit
- **WHEN** an open outline of points is saved and then closed with one point more
- **THEN** each save replaces the file and reading it gives the last
- **AND** the tattoo reads as outlined only after the closed save

#### Scenario: the defaults follow the kind
- **Key:** `tattoo:outline:the-defaults-follow-the-kind`
- **Layers:** unit
- **WHEN** an uploaded tattoo and a cut are kept
- **THEN** the uploaded one holds neutral off and depth 1.0, and the cut neutral on and depth 1.6

#### Scenario: a point outside the image is refused
- **Key:** `tattoo:outline:a-point-outside-the-image-is-refused`
- **Layers:** unit
- **WHEN** a point lies outside the image's pixels
- **THEN** the save is refused naming the point, and the file is as it was

#### Scenario: the bounds are held
- **Key:** `tattoo:outline:the-bounds-are-held`
- **Layers:** unit
- **WHEN** a closed outline has fewer points than the floor, or an outline has more than the ceiling
- **THEN** the save is refused naming the bound

#### Scenario: a depth or a white scale out of range is refused
- **Key:** `tattoo:outline:a-tone-out-of-range-is-refused`
- **Layers:** unit
- **WHEN** the depth is below the declared minimum or above the declared maximum,
  or the white scale is zero or past 255
- **THEN** the save is refused naming the value

### Requirement: The white point is a scale on the automatic point

The system SHALL accept on `extract_ink` a white scale, 1.0 by default, that multiplies the automatic per-channel
white point before the layer is divided by it; 1.0 SHALL give the layer the extraction gave without it.
It SHALL offer the automatic point as one 8-bit grey, the point's luminance, for the page to show.

The automatic point is a vector of three channels and the page shows one number,
so one scale carries the operator's choice without losing the tint the point removes.

#### Scenario: a scale of one changes nothing
- **Key:** `tattoo:white:a-scale-of-one-changes-nothing`
- **Layers:** unit
- **WHEN** a photograph is extracted with the white scale 1.0 and with none
- **THEN** the layers are equal

#### Scenario: a lower scale whitens paler ink
- **Key:** `tattoo:white:a-lower-scale-whitens-paler-ink`
- **Layers:** unit
- **WHEN** a photograph with a pale patch beside a dark fill is extracted with the white scale 0.8
- **THEN** the patch is whiter than at 1.0
- **AND** the fill stays darker than the patch

#### Scenario: the automatic point is one grey
- **Key:** `tattoo:white:the-automatic-point-is-one-grey`
- **Layers:** unit
- **WHEN** the automatic white point of a photograph inside an outline is asked
- **THEN** it is a whole number from 0 to 255, the point's luminance

### Requirement: Ink is placed by thin-plate splines

The system SHALL warp a tattoo's ink onto a target image by thin-plate splines fitted backwards from the target's
pixels through each stage's pairs, so each target pixel looks up the ink it shows and the warp leaves no hole.
A spline SHALL be exact at its pairs and SHALL refuse fewer than the declared floor of pairs, naming it,
and pairs that lie on one line. A lookup outside the tattoo SHALL be transparent white.
The ink SHALL be clipped to a polygon, softened by one pixel,
and SHALL be removed completely under each exclusion polygon.
The composite SHALL be a Multiply of the ink over the target.
The module SHALL import numpy and Pillow only, inside its functions.

A thin-plate spline is an exact interpolator, so no per-pair error is shown.
The module is shared so the server and, later, a verb run one implementation.
A point within 1e-9 px of the tattoo's edge is on it: a solver's rounding puts a mapped point a hair past the edge on
one machine and on it on another, and no pixel row may flip between them.

#### Scenario: a spline is exact at its pairs
- **Key:** `tattoo:chain:a-spline-is-exact-at-its-pairs`
- **Layers:** unit
- **WHEN** a spline is fitted to pairs that are not on a line
- **THEN** each source point of a pair maps to its target point

#### Scenario: a spline refuses too few pairs
- **Key:** `tattoo:chain:a-spline-refuses-too-few-pairs`
- **Layers:** unit
- **WHEN** a spline is fitted to fewer pairs than the floor
- **THEN** it is refused, naming the floor and the pairs given

#### Scenario: a spline refuses pairs on a line
- **Key:** `tattoo:chain:a-spline-refuses-pairs-on-a-line`
- **Layers:** unit
- **WHEN** a spline is fitted to the floor's number of pairs that lie on one line
- **THEN** it is refused as the too few are, saying the pairs lie on a line

#### Scenario: a translation is carried as a translation
- **Key:** `tattoo:chain:a-translation-is-carried`
- **Layers:** unit
- **WHEN** the pairs differ by one offset throughout
- **THEN** a point away from the pairs maps by the same offset

#### Scenario: the lookup is backwards and leaves no hole
- **Key:** `tattoo:chain:the-lookup-is-backwards-and-leaves-no-hole`
- **Layers:** unit
- **WHEN** a small ink is looked up over a larger target grid through two stages
- **THEN** every pixel of the grid holds a value, the ink inside the tattoo and transparent white outside

#### Scenario: a point a hair past the edge is on it
- **Key:** `tattoo:chain:a-point-a-hair-past-the-edge-is-on-it`
- **Layers:** unit
- **WHEN** a lookup maps a target pixel 1e-12 px past the ink's edge, and another 1e-6 px past it
- **THEN** the first shows the ink's edge pixel and the second is transparent white

#### Scenario: the outline clips and an exclusion removes
- **Key:** `tattoo:chain:the-outline-clips-and-an-exclusion-removes`
- **Layers:** unit
- **WHEN** ink is clipped to a limb polygon and an exclusion polygon lies inside it
- **THEN** the ink outside the limb is gone, and the ink inside the exclusion has no opacity left

#### Scenario: the composite is a Multiply
- **Key:** `tattoo:chain:the-composite-is-a-multiply`
- **Layers:** unit
- **WHEN** a layer that is white but for one dark pixel is multiplied over a render
- **THEN** the composite equals the render away from that pixel and is darker at it

#### Scenario: the crop box is the points' box and its margin
- **Key:** `tattoo:chain:the-crop-box-is-the-points-box`
- **Layers:** unit
- **WHEN** a crop box is asked for points inside an image and a margin
- **THEN** it is the points' box grown by the margin and clipped to the image

### Requirement: The ink view is made on the server

The system SHALL answer a `POST` naming a tattoo, the outline and the tone with the ink view:
the tattoo's ink on white, as a JPEG, on the crop of the outline's box grown by the extraction's reach,
clipped to the image.
The answer SHALL be `no-store`, SHALL name the crop's box and the automatic white point as an 8-bit grey
in its headers, and SHALL be made now and kept nowhere.
It SHALL refuse an outline that is not closed, an unknown tattoo and a cut asked on another photograph,
and SHALL be answered only to a request addressed to this server.

The page holds no extraction: one implementation is tested, and the photograph of a tattoo never leaves the machine.

#### Scenario: the ink view is a JPEG on the outline's crop
- **Key:** `tattoo:ink-view:a-jpeg-on-the-outlines-crop`
- **Layers:** unit
- **WHEN** the ink view of an outlined tattoo is asked
- **THEN** the answer is a JPEG the size of the crop its box header names
- **AND** the box is the outline's box grown by the reach, inside the image

#### Scenario: the answer carries the automatic white point
- **Key:** `tattoo:ink-view:the-answer-carries-the-automatic-white-point`
- **Layers:** unit
- **WHEN** the ink view is asked
- **THEN** its white header holds a whole number from 0 to 255

#### Scenario: the answer is kept nowhere
- **Key:** `tattoo:ink-view:the-answer-is-kept-nowhere`
- **Layers:** unit
- **WHEN** the ink view is asked
- **THEN** its cache header is `no-store`
- **AND** the library holds no new file

#### Scenario: an open outline is refused
- **Key:** `tattoo:ink-view:an-open-outline-is-refused`
- **Layers:** unit
- **WHEN** the ink view is asked of an outline that is not closed
- **THEN** it is refused, saying the outline is open

#### Scenario: an unknown tattoo is refused
- **Key:** `tattoo:ink-view:an-unknown-tattoo-is-refused`
- **Layers:** unit
- **WHEN** the ink view is asked of a name no tattoo has
- **THEN** it is refused, naming the name

#### Scenario: a request from another site is refused
- **Key:** `tattoo:ink-view:a-request-from-another-site-is-refused`
- **Layers:** unit
- **WHEN** the ink view is asked with an `Origin` the application does not serve
- **THEN** it is refused, as every route is

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

The page multiplies the JPEG over the target, which is the Multiply the bake makes.

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

### Requirement: A tattoo is kept in the library, whole until it is removed

The system SHALL keep an uploaded tattoo under the library's `.tattoos/<name>/` and a cut under
`.tattoos/.cuts/<digest>/<name>/`, `<digest>` the photograph's twelve characters, one folder a tattoo,
outside every collection.
An uploaded tattoo SHALL be taken from the import's staging, where it was cleaned to pixels and orientation,
and kept upright, with its metadata gone, at most the declared long side,
its size and the size it came with recorded.
A name SHALL be refused when it is empty, starts with a dot, holds a separator or a NUL,
or is taken: an upload's by an upload or by a cut of any photograph,
a cut's by an upload or by a cut of the same photograph.
A file still carrying metadata SHALL be refused.
The system SHALL list for a photograph's digest the uploads and that photograph's cuts, and no other cut,
and SHALL take that digest with every name it reads a tattoo by, so one name resolves to one tattoo.
The system SHALL remove a tattoo on the operator's word: its folder and what the folder holds, and nothing else.
The system SHALL offer no way to rename a kept tattoo.
A cut kept at `.tattoos/<name>/` SHALL move to `.tattoos/.cuts/<cut_from>/<name>/` the first time the library is read.

A tattoo is one input to many renders, in any collection, so it lives beside the collections
and is never listed as one
([D40](../../../docs/decisions.md#d40--a-collection-is-a-library-folder-holding-sources)).
A cut serves its photograph's renders alone, so it is kept by that photograph and named there.
The photograph of a tattoo never leaves the machine. A baked edit keeps its own copy of what it was placed with,
so a removal changes no edit.

#### Scenario: an upload is kept upright and bounded
- **Key:** `tattoo:library:an-upload-is-kept-upright-and-bounded`
- **Layers:** unit
- **WHEN** a staged JPEG with an orientation tag is kept as `bow`
- **THEN** `.tattoos/bow/` holds its pixels turned upright, with no metadata
- **AND** its record holds the kept size

#### Scenario: an oversized upload is downscaled and says so
- **Key:** `tattoo:library:an-oversized-upload-is-downscaled`
- **Layers:** unit
- **WHEN** a staged image longer than the declared long side is kept
- **THEN** the kept image's long side is the declared one and its aspect is held
- **AND** the record holds the size it came with

#### Scenario: a taken name is refused
- **Key:** `tattoo:library:a-taken-name-is-refused`
- **Layers:** unit
- **WHEN** a tattoo is kept under a name a kept upload has
- **THEN** it is refused, naming the name and asking for another
- **AND** the kept tattoo is as it was

#### Scenario: a name that is no folder name is refused
- **Key:** `tattoo:library:a-bad-name-is-refused`
- **Layers:** unit
- **WHEN** a tattoo is kept as an empty name, `.hidden`, `a/b` or a name holding a NUL
- **THEN** each is refused and nothing is written

#### Scenario: a file that still carries metadata is refused
- **Key:** `tattoo:library:an-unclean-file-is-refused`
- **Layers:** unit
- **WHEN** a staged file that the import's walk reports as not cleaned is kept
- **THEN** it is refused, naming what it carries
- **AND** nothing is written

#### Scenario: a name is one tattoo on a render
- **Key:** `tattoo:library:a-name-is-one-tattoo-on-a-render`
- **Layers:** unit
- **WHEN** an upload is kept under a name a cut of any photograph holds, and a cut is kept under a name an upload
  or a cut of the same photograph holds
- **THEN** each is refused, naming the name and asking for another
- **AND** a cut of another photograph under a name a cut holds is kept

#### Scenario: the list names each tattoo of a photograph
- **Key:** `tattoo:library:the-list-names-each-tattoo`
- **Layers:** unit
- **WHEN** the library holds an upload, a cut of one photograph and a cut of another,
  and the list is read for the first photograph's digest
- **THEN** it holds the upload and the first photograph's cut,
  each with its name, kind, size and whether it is outlined, in the order kept
- **AND** the other photograph's cut is not in it

#### Scenario: a name resolves by the render's digest
- **Key:** `tattoo:library:a-name-resolves-by-the-renders-digest`
- **Layers:** unit
- **WHEN** two photographs each hold a cut of one name, and the name is read with each digest
- **THEN** each read gives its own photograph's cut
- **AND** a name read with a digest that holds none of that name is refused,
  naming the photograph a cut of it is from when one is

#### Scenario: a removed tattoo is gone
- **Key:** `tattoo:library:a-removed-tattoo-is-gone`
- **Layers:** unit
- **WHEN** an upload and a cut are removed
- **THEN** their folders are gone, and the other tattoos and the library's other folders are as they were
- **AND** the removed names can be kept again

#### Scenario: a removal reaches only the named tattoo
- **Key:** `tattoo:library:a-removal-reaches-only-the-named-tattoo`
- **Layers:** unit
- **WHEN** a removal is asked of an unknown name, of `.cuts`, of `..`, of a name holding a separator,
  and of a name with a digest that is no photograph's
- **THEN** each is refused and nothing is removed

#### Scenario: a cut kept the old way moves
- **Key:** `tattoo:library:a-cut-kept-the-old-way-moves`
- **Layers:** unit
- **WHEN** a cut sits at `.tattoos/<name>/` and the library is read
- **THEN** it sits at `.tattoos/.cuts/<cut_from>/<name>/` with its record and outline as they were
- **AND** an upload at `.tattoos/<name>/` stays

#### Scenario: the library lists no collection from the tattoos
- **Key:** `tattoo:library:the-library-lists-no-collection-from-it`
- **Layers:** unit
- **WHEN** the library holds `.tattoos/`
- **THEN** no collection is listed from it

#### Scenario: no route renames a tattoo
- **Key:** `tattoo:library:no-route-renames`
- **Layers:** unit
- **WHEN** the application's routes are read
- **THEN** none under `/api/tattoos` renames a tattoo, and `DELETE /api/tattoos/{name}` is the one that removes
