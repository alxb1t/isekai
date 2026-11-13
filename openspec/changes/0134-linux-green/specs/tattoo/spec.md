## MODIFIED Requirements

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
