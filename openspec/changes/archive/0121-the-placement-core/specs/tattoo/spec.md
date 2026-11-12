## ADDED Requirements

### Requirement: A tattoo is kept in the library, whole and never deleted

The system SHALL keep each tattoo under the library's `.tattoos/<name>/`, one folder a tattoo,
outside every collection.
An uploaded tattoo SHALL be taken from the import's staging, where it was cleaned to pixels and orientation,
and kept upright, with its metadata gone, at most the declared long side,
its size and the size it came with recorded.
A name SHALL be kept once, and SHALL be refused when it is empty, starts with a dot, holds a separator or a NUL,
or is taken; a file still carrying metadata SHALL be refused.
The system SHALL offer no way to delete or rename a kept tattoo.

A tattoo is one input to many renders, in any collection, so it lives beside the collections
and is never listed as one
([D40](../../../docs/decisions.md#d40--a-collection-is-a-library-folder-holding-sources)).
The photograph of a tattoo never leaves the machine.

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
- **WHEN** a tattoo is kept under a name a kept tattoo has
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

#### Scenario: the list names each tattoo
- **Key:** `tattoo:library:the-list-names-each-tattoo`
- **Layers:** unit
- **WHEN** the library holds a tattoo uploaded and a tattoo cut
- **THEN** the list holds each, with its name, kind, size and whether it is outlined, in the order kept

#### Scenario: the library lists no collection from the tattoos
- **Key:** `tattoo:library:the-library-lists-no-collection-from-it`
- **Layers:** unit
- **WHEN** the library holds `.tattoos/`
- **THEN** no collection is listed from it

#### Scenario: no route deletes or renames a tattoo
- **Key:** `tattoo:library:no-route-deletes-or-renames`
- **Layers:** unit
- **WHEN** the application's routes are read
- **THEN** none under `/api/tattoos` deletes or renames a tattoo

### Requirement: A tattoo is cut from a photograph

The system SHALL keep a cut: a tattoo with no image of its own, whose record names the digest of the photograph
it is cut from, and whose outline is in that photograph's pixels.
It SHALL start from the newest cut of the same photograph's tone, its neutral, depth and white point,
else from the photograph's defaults. A cut SHALL serve only the renders of its own photograph.

A cut carries that photograph's light and angle, so it is no input for another photograph;
another photograph takes an uploaded tattoo.

#### Scenario: a cut holds no image and names its photograph
- **Key:** `tattoo:cut:a-cut-holds-no-image`
- **Layers:** unit
- **WHEN** a tattoo is cut from a photograph's digest under a name
- **THEN** the folder holds a record naming that digest and no image

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
