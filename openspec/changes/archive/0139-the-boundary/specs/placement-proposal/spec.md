## MODIFIED Requirements

### Requirement: A person's pose is read from one box and one crop

The system SHALL read a pose in two steps. The detector SHALL take the image scaled to fit its square input, the aspect
kept and the rest padded, and its highest-scoring person box SHALL be the one person. The estimator SHALL take a crop
of that box grown by a quarter, held to its input's aspect and scaled to its input size, and SHALL read each keypoint as
the position of the highest value on each axis, mapped back into the image's pixels. A keypoint's score SHALL be the
lower of its two highest values.

The estimator sees the person and little else, so a crowded image gives one person, the highest, and not an average.

#### Scenario: the detector sees the image fitted and padded
- **Key:** `placement-proposal:pose:the-detector-sees-the-image-fitted-and-padded`
- **Layers:** unit
- **WHEN** a wide image is given to the detector
- **THEN** its input holds the image at its aspect in the corner and the pad value elsewhere

#### Scenario: the highest-scoring person is the one
- **Key:** `placement-proposal:pose:the-highest-scoring-person-is-the-one`
- **Layers:** unit
- **WHEN** the detector answers two boxes with different scores
- **THEN** the pose is read from the higher one, in the image's pixels

#### Scenario: the estimator reads a crop grown by a quarter
- **Key:** `placement-proposal:pose:the-estimator-reads-a-crop-grown-by-a-quarter`
- **Layers:** unit
- **WHEN** a box is cropped for the estimator
- **THEN** the crop is the box grown by a quarter on each axis, held to the input's aspect and scaled to its size

#### Scenario: a keypoint is the highest value on each axis, mapped back
- **Key:** `placement-proposal:pose:a-keypoint-is-the-highest-value-on-each-axis-mapped-back`
- **Layers:** unit
- **WHEN** the estimator's two answers peak at known positions for a keypoint
- **THEN** the keypoint is at those positions in the image's pixels, and its score is the lower peak

#### Scenario: the estimator reads the crop's pixels, normalised
- **Key:** `placement-proposal:pose:the-estimator-reads-the-crops-pixels-normalised`
- **Layers:** unit
- **WHEN** an image is cropped for the estimator
- **THEN** its input holds the crop's own pixels, black where the crop leaves the image
- **AND** each channel is the pixel less the declared mean, over the declared deviation
