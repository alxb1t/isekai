## Purpose

Scoring one render against the photograph that produced it: the shared canvas the two agree on pixel for
pixel, the guard that refuses rather than scores the wrong region, four axes and the claim each is allowed
to make, and the blind human labelling that is what any of those numbers are checked against.

## ADDED Requirements

### Requirement: The comparison canvas is the render's own

The system SHALL compare a photograph to a render on the render's canvas, deriving that canvas by asking the
injector for the working resolution of the photo rather than re-deriving the rule, and SHALL apply the
loader's orientation correction to the photograph's pixels before any region is parsed from them.

The graph scales the photo once and every consumer reads that scaled image, so the scaled photo and the
render are the same canvas exactly rather than approximately. A second implementation of the resolution rule
would be a second thing to keep in step, and a photograph parsed upright while the render was produced from
transposed pixels would place every region in the wrong place.

#### Scenario: the working resolution comes from the injector
- **Key:** `evaluation:canvas:resolution-comes-from-the-injector`
- **Layers:** unit
- **WHEN** a photograph is prepared for comparison
- **THEN** its target dimensions are the ones the injector computes for that photograph
- **AND** the evaluator states no resolution rule of its own

#### Scenario: an orientation tag is honoured before regions are parsed
- **Key:** `evaluation:canvas:orientation-is-applied-before-parsing`
- **Layers:** unit
- **WHEN** the photograph declares a transposing orientation
- **THEN** the pixels are transposed before any region is derived from them
- **AND** the regions therefore land where the render's own pixels are

#### Scenario: a render whose dimensions disagree with the canvas is refused
- **Key:** `evaluation:canvas:mismatched-render-is-refused`
- **Layers:** unit
- **WHEN** a render's dimensions are not the ones derived from the photograph
- **THEN** the comparison is refused naming both sizes
- **AND** no axis is scored against a canvas the two images do not share

### Requirement: Regions are parsed from the photograph only

The system SHALL derive every region — the face, the hair — from the photograph, and SHALL apply those same
pixel regions to the render. It SHALL NOT parse a render for regions.

A human parser is trained on photographs, and its behaviour on a drawing is unknown. Parsing both sides
would make every axis a comparison of two different parsers as much as of two images.

#### Scenario: no region is derived from a render
- **Key:** `evaluation:regions:render-is-never-parsed`
- **Layers:** unit
- **WHEN** a render is scored
- **THEN** every region applied to it was derived from the photograph

#### Scenario: a region too small to measure is refused rather than scored
- **Key:** `evaluation:regions:tiny-region-is-refused`
- **Layers:** unit
- **WHEN** a parsed region covers less than the stated fraction of the canvas
- **THEN** the axes over that region report a refusal naming the region and its measured area
- **AND** they do not report a number derived from too few pixels

### Requirement: The face-location guard refuses rather than scores the wrong pixels

The system SHALL confirm, on the render itself, that a face is where the photograph's face region is, and
SHALL refuse every region axis when it cannot. A render that recomposed the subject would otherwise be
scored on whatever happens to occupy those coordinates.

#### Scenario: the guard reports which method located the face
- **Key:** `evaluation:guard:method-is-reported`
- **Layers:** unit
- **WHEN** the guard runs
- **THEN** the report names the method it used and the agreement it measured

#### Scenario: a failed guard refuses the region axes
- **Key:** `evaluation:guard:failure-refuses-region-axes`
- **Layers:** unit
- **WHEN** the guard cannot locate a face at the photograph's face region
- **THEN** every region axis reports a refusal rather than a value
- **AND** the refusal names the guard as its cause

#### Scenario: an axis that needs no region survives a failed guard
- **Key:** `evaluation:guard:whole-image-axes-survive-a-refusal`
- **Layers:** unit
- **WHEN** the guard fails
- **THEN** an axis measured over the whole image is still reported
- **AND** the operator is not deprived of the measurements the failure does not invalidate

### Requirement: An absent face is its own outcome, never a low score

The system SHALL report the absence of a detectable face as a distinct field, and SHALL NOT emit a number in
its place. A zero indistinguishable from a genuine zero would rank a render with no face at all against
renders that have one.

#### Scenario: no face in the photograph is reported as absence
- **Key:** `evaluation:absence:no-face-in-the-photo-is-reported`
- **Layers:** unit
- **WHEN** no face can be found in the photograph
- **THEN** the report states that, and the face axis carries no value

#### Scenario: no face in the render is reported as absence
- **Key:** `evaluation:absence:no-face-in-the-render-is-reported`
- **Layers:** unit
- **WHEN** no face can be found in the render
- **THEN** the report states that, and the face axis carries no value

### Requirement: Every axis declares what it may claim

The system SHALL tag each axis as absolute or relative, and SHALL state on every report that no axis
isolates a single dial. Colour distance, region area and keypoint agreement mean the same thing in a
photograph and in a drawing; an embedding cosine across that gap does not, and is readable only as a
ranking within one batch on one base.

#### Scenario: each axis carries its interpretation
- **Key:** `evaluation:claims:axes-are-tagged-absolute-or-relative`
- **Layers:** unit
- **WHEN** a report is produced
- **THEN** every axis in it is tagged absolute or relative

#### Scenario: the report states that no axis isolates one dial
- **Key:** `evaluation:claims:no-axis-isolates-one-dial`
- **Layers:** unit
- **WHEN** a report is produced
- **THEN** it states that the photograph reaches the render by several paths at once
- **AND** a change in any axis is therefore attributable to the pipeline rather than to one component

#### Scenario: the recognizer shared with the generator is marked as a sanity channel
- **Key:** `evaluation:claims:shared-recognizer-is-a-sanity-channel`
- **Layers:** unit
- **WHEN** the face axis reports the encoder the generator itself injects identity with
- **THEN** that value is marked as falsifying only
- **AND** the report states that a high value from it asserts nothing

### Requirement: A cross-base comparison refuses only the axes it invalidates

The system SHALL compare the base each run recorded, and where two runs do not share one SHALL report the
embedding axes as refused with the reason stated, while still reporting the axes whose meaning does not
depend on the base.

A global refusal would punish an operator for a comparison that is partly valid; a warning above a table of
numbers is read as decoration.

#### Scenario: differing bases refuse the embedding axes
- **Key:** `evaluation:cross-base:embedding-axes-are-refused`
- **Layers:** unit
- **WHEN** two runs being compared recorded different bases
- **THEN** each embedding axis reports a refusal naming the cross-base comparison as its reason

#### Scenario: the absolute axes still report across bases
- **Key:** `evaluation:cross-base:absolute-axes-still-report`
- **Layers:** unit
- **WHEN** two runs being compared recorded different bases
- **THEN** the colour, area and keypoint axes still report values

#### Scenario: a run recording no base cannot be compared silently
- **Key:** `evaluation:cross-base:missing-base-is-not-assumed-equal`
- **Layers:** unit
- **WHEN** a run under comparison records no base
- **THEN** it is treated as unknown rather than as matching
- **AND** the embedding axes refuse

### Requirement: The report is one record per render and one table per run

The system SHALL write a machine-readable record for each render and a single human-readable table for the
run, and the table SHALL state the direction of every column and the run it belongs to. It SHALL NOT emit a
combined score, a verdict or a percentage.

Averaging the axes would hide the identity-versus-style trade-off the axes exist to expose, and a threshold
cannot honestly be stated before any human label exists.

#### Scenario: each render gets its own record
- **Key:** `evaluation:report:one-record-per-render`
- **Layers:** unit
- **WHEN** a run is scored
- **THEN** one machine-readable record is written per render, naming that render

#### Scenario: the table states each column's direction
- **Key:** `evaluation:report:table-states-column-directions`
- **Layers:** unit
- **WHEN** the run's table is produced
- **THEN** it states for every column whether a higher or a lower value is the better one

#### Scenario: the report emits no combined score
- **Key:** `evaluation:report:no-combined-score`
- **Layers:** unit
- **WHEN** a report is produced
- **THEN** it contains no average of the axes, no verdict and no percentage of fidelity

#### Scenario: the report names the run it describes
- **Key:** `evaluation:report:names-its-run`
- **Layers:** unit
- **WHEN** a report is produced
- **THEN** it names the subject, the base and the image the run was produced on
- **AND** a table read months later can be attributed to what produced it

### Requirement: Human labels are collected blind and pairwise

The system SHALL emit a comparison sheet of within-subject render pairs carrying no scores, and SHALL refuse
to correlate labels against scores unless the labels were recorded before the scores existed.

A rating invented while looking drifts across a sitting where a forced pairwise choice does not, and a label
collected after the scores were seen cannot check them.

#### Scenario: the sheet carries no scores
- **Key:** `evaluation:labels:sheet-carries-no-scores`
- **Layers:** unit
- **WHEN** a comparison sheet is emitted
- **THEN** it contains no metric value for any render on it

#### Scenario: pairs are within a subject
- **Key:** `evaluation:labels:pairs-are-within-one-subject`
- **Layers:** unit
- **WHEN** a comparison sheet is emitted for several subjects
- **THEN** every pair on it draws both renders from the same subject
- **AND** no pair asks the operator to compare two different people

#### Scenario: correlation refuses labels that are not demonstrably prior
- **Key:** `evaluation:labels:correlation-requires-prior-labels`
- **Layers:** unit
- **WHEN** a correlation is asked for against labels not recorded before the scores
- **THEN** it is refused, naming the ordering as the reason

#### Scenario: the correlation is reported per axis and never rolled up
- **Key:** `evaluation:labels:correlation-is-per-axis`
- **Layers:** unit
- **WHEN** labels are correlated against scores
- **THEN** the agreement is reported separately for every axis
- **AND** the count of judgements behind it is reported with it

### Requirement: Every model the scorer loads is pinned and verified

The system SHALL resolve each model it loads from a pinned manifest carrying a revision and a digest,
SHALL verify that digest before use, and SHALL refuse rather than score when it does not match. It
SHALL join the manifest's destination onto the models root through the same containment check the
provisioner uses, and SHALL refuse a destination that does not land under that root. The
recognizer the scorer reports as a sanity channel SHALL be the same pinned artifact the generator
injects identity with.

A score produced by an unverified model is a number from an unknown thing. And a sanity channel drawn
from a *different* build of the generator's recognizer would make the claim about self-grading a claim
about two different models.

#### Scenario: a digest mismatch refuses the run
- **Key:** `evaluation:pinned-artifacts:digest-mismatch-is-refused`
- **Layers:** unit
- **WHEN** a model artifact on disk does not match the digest the manifest pins
- **THEN** the run is refused naming the artifact and both digests
- **AND** no axis is scored from it

#### Scenario: the sanity recognizer is the generator's own pinned artifact
- **Key:** `evaluation:pinned-artifacts:recognizer-matches-the-generators-pin`
- **Layers:** unit
- **WHEN** the scorer resolves the recognizer it reports as a sanity channel
- **THEN** the pin it resolves is the one the render pipeline's own manifest carries
- **AND** the two manifests cannot drift apart unnoticed

#### Scenario: an unpinned entry is refused
- **Key:** `evaluation:pinned-artifacts:unpinned-source-is-refused`
- **Layers:** unit
- **WHEN** a manifest entry names a source that is not a pinned revision
- **THEN** it is refused rather than fetched

#### Scenario: a destination that escapes the models root is refused
- **Key:** `evaluation:pinned-artifacts:escaping-destination-is-refused`
- **Layers:** unit
- **WHEN** the scorer resolves an entry whose destination climbs out of, or is absolute against, the
  models root
- **THEN** it is refused naming the destination, before any bytes are read
- **AND** the check is the provisioner's own, so the containment rule has one enforcement site rather
  than two
