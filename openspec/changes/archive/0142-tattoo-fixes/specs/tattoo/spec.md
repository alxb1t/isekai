## MODIFIED Requirements

### Requirement: Ink is placed by thin-plate splines

The system SHALL warp a tattoo's ink onto a target image by thin-plate splines fitted backwards from the target's
pixels through each stage's pairs, so each target pixel looks up the ink it shows and the warp leaves no hole.
A spline SHALL be exact at its pairs and SHALL refuse fewer than the declared floor of pairs, naming it,
and pairs that lie on one line. A lookup outside the tattoo SHALL be transparent white.
The ink SHALL be clipped to a polygon, softened by one pixel,
and SHALL be removed completely well inside each exclusion polygon.
A polygon's mask SHALL be antialiased: the polygon is filled at four times its size and reduced by a box filter, so a
pixel its edge crosses is partly covered. The ink's outline, the limb and each exclusion SHALL take that mask.
The composite SHALL be a Multiply of the ink over the target.
The module SHALL import numpy and Pillow only, inside its functions.

A thin-plate spline is an exact interpolator, so no per-pair error is shown.
The module is shared so the server and, later, a verb run one implementation.
A point within 1e-9 px of the tattoo's edge is on it: a solver's rounding puts a mapped point a hair past the edge on
one machine and on it on another, and no pixel row may flip between them.
A polygon's hard edge, enlarged onto a render, reads as a saw-tooth; a partly covered edge pixel keeps it smooth, and
the white point still reads the pixels whose opacity is over half.

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

#### Scenario: a polygon mask is antialiased
- **Key:** `tattoo:chain:a-polygon-mask-is-antialiased`
- **Layers:** unit
- **WHEN** a polygon with a slanted edge is filled into a mask, and the ink of an outline is cut
- **THEN** the pixels the edge crosses hold a coverage between empty and full, and a pixel well inside holds full
- **AND** the ink's opacity along the outline's edge holds values between none and full

#### Scenario: an exclusion's edge is partly removed
- **Key:** `tattoo:chain:an-exclusions-edge-is-partly-removed`
- **Layers:** unit
- **WHEN** ink is clipped with an exclusion polygon inside the limb
- **THEN** a pixel the exclusion's edge crosses keeps part of its opacity, and a pixel well inside it keeps none
