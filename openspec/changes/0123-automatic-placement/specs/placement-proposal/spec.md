## ADDED Requirements

### Requirement: Pairs are proposed from the pose and the silhouettes of the arm

The system SHALL answer a `POST` naming a render and the tattoo's points on the photograph with proposed stage-2 pairs,
the photograph's point first. It SHALL find one person in each image, the highest-scoring box, and take the arm whose
bones lie nearest those points in the photograph. For each bone of that arm it SHALL segment the limb in both images,
prompted by points along the bone and, as negatives, by the other bone's middle and the torso, and at each fixed
fraction along the bone propose the silhouette's two edges and its middle. It SHALL add the arm's three joints after
the bones. An edge SHALL lie no further from the bone than the declared fraction of its length, and in the render SHALL
stop at the first dark line past the declared distance from the bone. A keypoint scoring under the declared cut SHALL
propose nothing for its bone or joint.
The answer SHALL be `no-store`, SHALL be made now and kept nowhere, and SHALL refuse a missing model by naming the
fetch, and a point that is not a finite, non-negative pair of numbers.

A pair is the same fraction along the bone and the same side of it in both images, so the splines of the chain carry the
limb's own coordinates. The pose holds where the silhouette does not, which is why an edge is bounded: on flat skin the
mask cannot part the arm from the chest.

#### Scenario: a bone gives two edges and a middle at each fraction
- **Key:** `placement-proposal:pairs:a-bone-gives-two-edges-and-a-middle-at-each-fraction`
- **Layers:** unit
- **WHEN** a straight limb of two bones is proposed from masks that fill it in both images
- **THEN** each bone holds, at each fraction, the two edges and the middle as three pairs, in that order

#### Scenario: a pair is the same fraction and side in both images
- **Key:** `placement-proposal:pairs:a-pair-is-the-same-fraction-and-side-in-both-images`
- **Layers:** unit
- **WHEN** the render's limb is a scaled and moved copy of the photograph's
- **THEN** each pair's render point is the scaled and moved image of its photograph point

#### Scenario: an edge stops at the band round the bone
- **Key:** `placement-proposal:pairs:an-edge-stops-at-the-band-round-the-bone`
- **Layers:** unit
- **WHEN** a mask spills far past the bone on one side
- **THEN** that edge lies at the declared fraction of the bone's length from it, and no further

#### Scenario: a render edge stops at the first dark line
- **Key:** `placement-proposal:pairs:a-render-edge-stops-at-the-first-dark-line`
- **Layers:** unit
- **WHEN** the render holds a dark line across a mask that goes on past it, beyond the declared distance from the bone
- **THEN** the render's edge is the last light pixel before the line, and the photograph's edge is not stopped by it

#### Scenario: a dark line at the bone stops nothing
- **Key:** `placement-proposal:pairs:a-dark-line-at-the-bone-stops-nothing`
- **Layers:** unit
- **WHEN** the render's bone is drawn as a dark line, and the mask goes on past the declared distance
- **THEN** the render's edge is not at the bone's own line

#### Scenario: the joints are pairs after the bones
- **Key:** `placement-proposal:pairs:the-joints-are-pairs-after-the-bones`
- **Layers:** unit
- **WHEN** an arm is proposed
- **THEN** the last three pairs are the shoulder, the elbow and the wrist
- **AND** each is its keypoint in the photograph and in the render

#### Scenario: a keypoint under the cut proposes nothing for its bone
- **Key:** `placement-proposal:pairs:a-keypoint-under-the-cut-proposes-nothing-for-its-bone`
- **Layers:** unit
- **WHEN** the wrist scores 0.23 in the photograph and the rest score above the cut
- **THEN** the forearm and the wrist joint give no pair, and the upper arm and the other joints give theirs

#### Scenario: the arm nearest the tattoo is proposed
- **Key:** `placement-proposal:pairs:the-arm-nearest-the-tattoo-is-proposed`
- **Layers:** unit
- **WHEN** both arms have usable bones, and the tattoo's points lie along the left arm in the photograph
- **THEN** every pair belongs to the left arm, and none to the right

#### Scenario: no person or no usable bone proposes nothing
- **Key:** `placement-proposal:pairs:no-person-or-no-usable-bone-proposes-nothing`
- **Layers:** unit
- **WHEN** the pose finds no person in the render, and then every bone of the chosen arm is under the cut
- **THEN** each answer holds no pair, and the request is not refused

#### Scenario: the answer is kept nowhere
- **Key:** `placement-proposal:pairs:the-answer-is-kept-nowhere`
- **Layers:** unit
- **WHEN** a proposal is asked
- **THEN** its cache header is `no-store`, and the library and the run hold no new file

#### Scenario: a missing model refuses naming the fetch
- **Key:** `placement-proposal:pairs:a-missing-model-refuses-naming-the-fetch`
- **Layers:** unit
- **WHEN** a proposal is asked and the models are not provisioned
- **THEN** it is refused, and the refusal names `uv run python -m isekai.boundary.unpack fetch config/placement.json`

#### Scenario: a bad point is refused
- **Key:** `placement-proposal:pairs:a-bad-point-is-refused`
- **Layers:** unit
- **WHEN** the points hold a negative coordinate, a non-number, or no point at all
- **THEN** the request is refused, naming the point, and no model is opened

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

### Requirement: A silhouette is segmented once an image and prompted once a bone

The system SHALL embed each image once, scaled to the segmenter's square input and normalised, and SHALL prompt the
embedding once for each bone with positive and negative points in the input's pixels, answering as the mask the
candidate the decoder scores highest, its logits resized to the image's size and taken above 0. It SHALL give the
decoder every input it declares, and refuse, naming it, an input it has no value for.

The encoder costs seconds and the decoder milliseconds, so a bone's prompt is cheap and an image's embedding is not
repeated.

#### Scenario: an image is embedded once for all its bones
- **Key:** `placement-proposal:segment:an-image-is-embedded-once-for-all-its-bones`
- **Layers:** unit
- **WHEN** two bones are prompted on one image
- **THEN** the encoder ran once and the decoder twice

#### Scenario: a mask is prompted by positive and negative points
- **Key:** `placement-proposal:segment:a-mask-is-prompted-by-positive-and-negative-points`
- **Layers:** unit
- **WHEN** a bone is prompted with three positive points and two negative points
- **THEN** the decoder's coordinates are the five points scaled to the input
- **AND** the first three are labelled 1 and the others 0

#### Scenario: the mask is the candidate scored highest, at the image's size
- **Key:** `placement-proposal:segment:the-mask-is-the-candidate-scored-highest`
- **Layers:** unit
- **WHEN** the decoder answers three candidate masks at its low resolution and scores the second highest
- **THEN** the mask is the second candidate's logits above 0
- **AND** it has the image's size

#### Scenario: the image is scaled and normalised for the encoder
- **Key:** `placement-proposal:segment:the-image-is-scaled-and-normalised-for-the-encoder`
- **Layers:** unit
- **WHEN** an image is prepared
- **THEN** the array is the input's square, three channels first, each normalised by the declared mean and deviation

#### Scenario: a declared input with no value is refused
- **Key:** `placement-proposal:segment:a-declared-input-with-no-value-is-refused`
- **Layers:** unit
- **WHEN** the decoder declares an input the segmenter has no value for
- **THEN** the prompt is refused, naming that input

### Requirement: The models open on the CPU after their digests verify

The system SHALL open the pose detector, the pose estimator and the segmenter's encoder and decoder through the
declared runtime on the CPU provider alone, SHALL verify each file against its manifest digest before a session over it
opens, and SHALL open them once and keep them for the process. An absent file SHALL refuse, naming the fetch, and a file
with other bytes SHALL be refused by the digest check, naming the file and both digests. No package beyond the runtime's
list SHALL be added, and none SHALL be imported at module scope.

A stale pin must cost a refusal and not a loaded model, and a machine without the models must still run every free verb
([D20](../../../docs/decisions.md#d20--the-entry-point-loads-no-third-party-package)).

#### Scenario: the sessions use the CPU provider alone
- **Key:** `placement-proposal:models:the-sessions-use-the-cpu-provider-alone`
- **Layers:** unit
- **WHEN** the models are opened over a recording runtime
- **THEN** each session is made with the CPU provider and no other

#### Scenario: a stale pin refuses before a session opens
- **Key:** `placement-proposal:models:a-stale-pin-refuses-before-a-session-opens`
- **Layers:** unit
- **WHEN** a model file's bytes differ from its manifest digest
- **THEN** opening is refused naming the file and both digests, and no session was made

#### Scenario: an absent file refuses naming the fetch
- **Key:** `placement-proposal:models:an-absent-file-refuses-naming-the-fetch`
- **Layers:** unit
- **WHEN** a file the manifest declares is absent from the models directory
- **THEN** opening is refused
- **AND** the refusal names `uv run python -m isekai.boundary.unpack fetch config/placement.json`

#### Scenario: the sessions are opened once
- **Key:** `placement-proposal:models:the-sessions-are-opened-once`
- **Layers:** unit
- **WHEN** two proposals are made through one wiring
- **THEN** the models were opened once
