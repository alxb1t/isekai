# Capability: `evaluation`

## Purpose

Counting, over a cohort of known people, how often each render is nearest its own photograph and its own
person, beside the hits chance gives, with an encoder the generator does not use.

**Source:** `evaluation/__main__.py`, `evaluation/cohort.py`, `evaluation/face.py`,
`evaluation/eval_models.py`, `evaluation/eval_models.json`, `isekai/boundary/provision.py` ·
**Tests:** `tests/test_cohort.py`, `tests/test_face.py`, `tests/test_evaluation_cli.py`,
`tests/test_eval_manifest.py`

## Requirements

### Requirement: The cohort is the ground truth

The system SHALL read the cohort from a directory holding one sub-directory per person, each holding that
person's photographs, and SHALL match a run to its photograph by the digest the run's frame records against the
digests of the cohort's files. A run whose photograph is in no cohort file SHALL be reported as such and never
end the scoring. A cohort file that does not decode as an image, or in which no face is found, SHALL refuse
the scoring before any render is scored, naming the file, and two cohort files with one digest SHALL refuse it
naming both.

```
cohort/
├── <person>/
│   ├── 1.png        ← a run is this photograph's when the frame's digest is this file's
│   └── 2.png
└── <person>/…
```

Identification has a ground truth, which is who each photograph is of; the directory is the one place that says
so. A run is keyed by its photograph's bytes, so the digest is the match and no run file changes, and bytes two
people share would make a run both of theirs. The cohort is the instrument: a file with no face, or no image,
would leave a gallery with a hole and a count of photographs it does not hold, so it is refused up front while
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

#### Scenario: a cohort file that is not an image refuses the scoring
- **Key:** `evaluation:cohort:an-undecodable-file-is-refused`
- **Layers:** unit
- **WHEN** a file in a person's directory does not decode as an image
- **THEN** the scoring is refused naming the file and its removal
- **AND** no render is scored

#### Scenario: two cohort files with one digest refuse the scoring
- **Key:** `evaluation:cohort:two-files-with-one-digest-are-refused`
- **Layers:** unit
- **WHEN** two files in the cohort hash to one digest
- **THEN** the scoring is refused naming both files

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
encoder, both pinned in the evaluator's own manifest, and SHALL refuse to score when either destination, or
either digest, is one the render pipeline's manifest also carries. A render in which no face is found SHALL be
its own outcome, never a low score.

The identity adapter is trained to satisfy the generator's own recognizer, so a count on that recognizer is the
adapter grading itself; a different encoder has different blind spots. The bytes are what grade, so the
generator's file under another name is still the generator's. A face not found says nothing about whose it is.

#### Scenario: the evaluator shares no pin with the generator
- **Key:** `evaluation:encoder:shares-no-pin-with-the-generator`
- **Layers:** unit
- **WHEN** the evaluator's manifest and the render pipeline's manifest carry a destination in common
- **THEN** the scoring is refused naming the destination

#### Scenario: the generator's bytes under another destination refuse the scoring
- **Key:** `evaluation:encoder:shares-no-bytes-with-the-generator`
- **Layers:** unit
- **WHEN** an entry of the evaluator's manifest carries a digest the render pipeline's manifest also carries
- **THEN** the scoring is refused naming that entry's destination

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
seed, its nearest photograph and its outcome — a hit, a miss, no face found, unreadable, not rendered — and SHALL
print one table from that record alone, a row of counts per flow, each followed by its chance row. A run whose
frame, or one of whose flows, cannot be read SHALL be reported as unreadable, and its readable flows scored. The
record SHALL count the runs outside the cohort and the unreadable runs and name none of them, naming each on the
error stream alone, and SHALL be refused before anything is scored where git can reach it: inside the
repository's working tree and outside its ignored data root. No render's outcome, and no run's, SHALL end the
scoring of another.

```
                    photograph-level   person-level
summon-anime-wai         15 / 18           14 / 18
chance                  1.0 / 18          2.1 / 18
```

A table that shows only its wins is not evidence; a failure reported mid-batch scrolls away, and one damaged
file is no reason to lose the rest. A row per flow, with its own chance beneath it, is what lets a second flow be
read beside the first without a second tool. A run's id carries its photograph's digest and filename, and a run
outside the cohort is by construction not one of its synthetic people, so the record — the file a later change
commits — names none, and is never written where one `git add` publishes it
([D18](../../../docs/decisions.md#d18--runs-stay-out-of-what-git-tracks)).

#### Scenario: one row per flow
- **Key:** `evaluation:table:one-row-per-flow`
- **Layers:** unit
- **WHEN** the runs hold renders of more than one flow
- **THEN** the table carries one row per flow, each with both counts
- **AND** each followed by the chance row over that flow's renders

#### Scenario: a failure is a row, never an exit
- **Key:** `evaluation:table:a-failure-is-a-row`
- **Layers:** unit
- **WHEN** one render has no face found and another photograph was never rendered
- **THEN** each is a row naming its outcome
- **AND** every other render is scored and written

#### Scenario: a render that does not decode is a row
- **Key:** `evaluation:table:an-unreadable-render-is-a-row`
- **Layers:** unit
- **WHEN** a render file does not decode as an image
- **THEN** its photograph's row says it is unreadable
- **AND** every other render is scored

#### Scenario: a run that cannot be read is reported and does not end the scoring
- **Key:** `evaluation:table:an-unreadable-run-is-reported`
- **Layers:** unit
- **WHEN** a run's frame or one of its flows cannot be read
- **THEN** the run is reported as unreadable
- **AND** every other run is scored

#### Scenario: a flow that cannot be read costs only its own renders
- **Key:** `evaluation:table:an-unreadable-flow-costs-only-its-own`
- **Layers:** unit
- **WHEN** one flow of a run cannot be read and another can
- **THEN** the readable flow's render is scored
- **AND** the unreadable flow is reported with what to move out of the run

#### Scenario: the record counts the runs it does not score and names none
- **Key:** `evaluation:table:the-record-names-no-unscored-run`
- **Layers:** unit
- **WHEN** a batch holds a run outside the cohort and a run that cannot be read
- **THEN** the record and the table count each and carry neither run's id
- **AND** each run's id is printed on the error stream

#### Scenario: a record git can reach is refused
- **Key:** `evaluation:table:a-record-git-can-reach-is-refused`
- **Layers:** unit
- **WHEN** the record would be written inside the working tree and outside the ignored data root
- **THEN** the scoring is refused naming the path, before any photograph is embedded
- **AND** no record is written

#### Scenario: the table re-derives from the record
- **Key:** `evaluation:table:the-table-re-derives-from-the-record`
- **Layers:** unit
- **WHEN** the table is printed from a committed record
- **THEN** it equals the table committed beside that record

### Requirement: Every model the evaluator loads is pinned and verified

The system SHALL resolve each model it loads from a pinned manifest carrying a revision and a digest,
SHALL verify that digest before use, and SHALL refuse rather than score when it does not match. It
SHALL join the manifest's destination onto the models root through the same containment check the
provisioner uses, and SHALL refuse a destination that does not land under that root. The record SHALL name
each model by its destination and digest, and each cohort photograph by its digest.

A score produced by an unverified model is a number from an unknown thing, and a record that does not name the
bytes it was counted with cannot be walked back to them.

#### Scenario: a digest mismatch refuses the run
- **Key:** `evaluation:pinned-artifacts:digest-mismatch-is-refused`
- **Layers:** unit
- **WHEN** a model artifact on disk does not match the digest the manifest pins
- **THEN** the run is refused naming the artifact and both digests
- **AND** no render is ranked with it

#### Scenario: an unpinned entry is refused
- **Key:** `evaluation:pinned-artifacts:unpinned-source-is-refused`
- **Layers:** unit
- **WHEN** a manifest entry names a source that is not a pinned revision
- **THEN** it is refused rather than fetched

#### Scenario: the record names the bytes it was counted with
- **Key:** `evaluation:pinned-artifacts:the-record-names-the-bytes`
- **Layers:** unit
- **WHEN** a batch's record is written
- **THEN** it names the detector and the encoder each by its destination and its pinned digest
- **AND** it names each cohort photograph's digest

#### Scenario: a destination that escapes the models root is refused
- **Key:** `evaluation:pinned-artifacts:escaping-destination-is-refused`
- **Layers:** unit
- **WHEN** the evaluator resolves an entry whose destination climbs out of, or is absolute against, the
  models root
- **THEN** it is refused naming the destination, before any bytes are read
- **AND** the check is the provisioner's own, so the containment rule has one enforcement site rather
  than two
