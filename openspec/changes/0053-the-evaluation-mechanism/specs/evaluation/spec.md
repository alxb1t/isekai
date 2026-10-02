## ADDED Requirements

### Requirement: The cohort is the ground truth

The system SHALL read the cohort from a directory holding one sub-directory per person, each holding that
person's photographs, and SHALL match a run to its photograph by the digest the run's frame records against the
digests of the cohort's files. A run whose photograph is in no cohort file SHALL be reported as such and never
end the scoring. A cohort photograph in which no face is found SHALL refuse the scoring before any render is
scored, naming the file.

```
cohort/
├── <person>/
│   ├── 1.png        ← a run is this photograph's when the frame's digest is this file's
│   └── 2.png
└── <person>/…
```

Identification has a ground truth, which is who each photograph is of; the directory is the one place that says
so. A run is keyed by its photograph's bytes, so the digest is the match and no run file changes. The cohort is
the instrument: a photograph with no face would leave a gallery with a hole, so it is refused up front while
nothing has been spent.

#### Scenario: a run is matched to its photograph by digest
- **Key:** `evaluation:cohort:a-run-is-matched-by-digest`
- **Layers:** unit
- **WHEN** a run's frame records a digest equal to a cohort file's
- **THEN** the run's renders are scored as that photograph's, under that photograph's person

#### Scenario: a run outside the cohort is reported and does not end the scoring
- **Key:** `evaluation:cohort:a-run-outside-the-cohort-is-reported`
- **Layers:** unit
- **WHEN** a run's frame records a digest no cohort file has
- **THEN** the run is reported as outside the cohort
- **AND** every other run is scored

#### Scenario: a cohort photograph with no face refuses the scoring
- **Key:** `evaluation:cohort:a-faceless-photograph-is-refused`
- **Layers:** unit
- **WHEN** no face is found in a cohort photograph
- **THEN** the scoring is refused naming the file
- **AND** no render is scored

### Requirement: Two counts over the cohort, never a score

For each render the system SHALL rank every cohort photograph by the cosine between the render's face embedding
and the photograph's, and SHALL count a photograph-level hit when the nearest is the render's own photograph and
a person-level hit when, with the render's own photograph removed, the nearest belongs to the same person. It
SHALL report each count with its denominator and the hits chance would give, and SHALL publish no cosine, no
average and no percentage.

```
render r of photograph p, person P
   rank the cohort's photographs by cosine to r
   photograph-level hit   nearest == p
   person-level hit       nearest among the others ∈ P
chance   photograph-level  Σ 1 / N            over renders
         person-level      Σ (K_P − 1) / (N − 1)   N photographs, K_P of person P
```

Identification needs no threshold and no human label, and a render that merely copied its photograph's pixels
scores on the first count and not the second. A count can be checked by a reader; a cosine has no scale across
a photograph and a drawing, and an average hides which render failed.

#### Scenario: a photograph-level hit
- **Key:** `evaluation:counts:photograph-level-hit`
- **Layers:** unit
- **WHEN** a render's nearest cohort photograph is the one it was rendered from
- **THEN** it counts one photograph-level hit

#### Scenario: a person-level hit excludes the source
- **Key:** `evaluation:counts:person-level-excludes-the-source`
- **Layers:** unit
- **WHEN** a render's own photograph is removed from the gallery and the nearest remaining belongs to the same
  person
- **THEN** it counts one person-level hit
- **AND** a render nearest only to its own photograph counts none

#### Scenario: chance is reported beside each count
- **Key:** `evaluation:counts:chance-is-reported`
- **Layers:** unit
- **WHEN** the counts are reported
- **THEN** each carries its denominator and the hits chance would give over the same renders

#### Scenario: no average, no percentage, no cosine
- **Key:** `evaluation:counts:no-average-no-percentage`
- **Layers:** unit
- **WHEN** the record and the table are written
- **THEN** neither carries a cosine, a mean or a percentage

### Requirement: The encoder shares no pin with the generator

The system SHALL find and align the face in every photograph and render with a detector, and embed it with an
encoder, both pinned in the evaluator's own manifest, and SHALL refuse to score when either destination is one
the render pipeline's manifest also carries. A render in which no face is found SHALL be its own outcome, never
a low score.

The identity adapter is trained to satisfy the generator's own recognizer, so a count on that recognizer is the
adapter grading itself; a different encoder has different blind spots. A face not found says nothing about
whose it is.

#### Scenario: the evaluator shares no pin with the generator
- **Key:** `evaluation:encoder:shares-no-pin-with-the-generator`
- **Layers:** unit
- **WHEN** the evaluator's manifest and the render pipeline's manifest carry a destination in common
- **THEN** the scoring is refused naming the destination

#### Scenario: the crop is aligned to the encoder's template
- **Key:** `evaluation:encoder:the-crop-is-aligned`
- **Layers:** unit
- **WHEN** a face's landmarks are found
- **THEN** the crop handed to the encoder is the similarity transform that lands them on the template
- **AND** landmarks already on the template leave the image unmoved

#### Scenario: no face in a render is its own outcome
- **Key:** `evaluation:encoder:no-face-is-its-own-outcome`
- **Layers:** unit
- **WHEN** no face is found in a render
- **THEN** its row says so
- **AND** it counts no hit and no cosine is computed for it

### Requirement: Every render is a row

The system SHALL write one record per batch holding, for every cohort photograph and every flow, the render's
seed, its nearest photograph and its outcome — a hit, a miss, no face found, not rendered — and SHALL print one
table with a column per flow from that record alone. No render's outcome SHALL end the scoring of another.

```
                    photograph-level   person-level
summon-anime-wai         15 / 18           14 / 18
chance                  1.0 / 18          2.1 / 18
```

A table that shows only its wins is not evidence; a failure reported mid-batch scrolls away. A column per flow
is what lets a second flow be read beside the first without a second tool.

#### Scenario: one column per flow
- **Key:** `evaluation:table:one-column-per-flow`
- **Layers:** unit
- **WHEN** the runs hold renders of more than one flow
- **THEN** the table carries one column per flow, each with both counts

#### Scenario: a failure is a row, never an exit
- **Key:** `evaluation:table:a-failure-is-a-row`
- **Layers:** unit
- **WHEN** one render has no face found and another photograph was never rendered
- **THEN** each is a row naming its outcome
- **AND** every other render is scored and written

#### Scenario: the table re-derives from the record
- **Key:** `evaluation:table:the-table-re-derives-from-the-record`
- **Layers:** unit
- **WHEN** the table is printed from a committed record
- **THEN** it equals the table committed beside that record
