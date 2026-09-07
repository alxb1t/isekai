# Capability: `cli`

The command-line surface: parsing flags, validating their ranges before any GPU work starts, and dispatching the
chosen model into a run.

**Source:** `isekai/cli.py` · **Tests:** `tests/test_cli.py`

The CLI is where a bad value is cheapest to catch. Every dial is range-checked **at parse time**, so an
out-of-range flag fails before a pod is touched rather than after a paid render.

## Requirements

### Requirement: Dial flags default to unset

The system SHALL leave each dial override unset when its flag is absent, so that omitting a flag preserves the
workflow's own tuned value rather than imposing a CLI default.

This replaces the previous *Dial flags default to unset* requirement, which covered three dials. The identity
node's keypoint dial joins them under the same rule.

#### Scenario: denoise defaults to unset
- **Key:** `cli:dial-defaults:denoise-defaults-to-unset`
- **Layers:** unit
- **WHEN** no denoise flag is supplied
- **THEN** no denoise override is applied and the workflow keeps its own value

#### Scenario: cfg defaults to unset
- **Key:** `cli:dial-defaults:cfg-defaults-to-unset`
- **Layers:** unit
- **WHEN** no cfg flag is supplied
- **THEN** no cfg override is applied

#### Scenario: ip_weight defaults to unset
- **Key:** `cli:dial-defaults:ip-weight-defaults-to-unset`
- **Layers:** unit
- **WHEN** no ip_weight flag is supplied
- **THEN** no ip_weight override is applied

#### Scenario: cn_strength defaults to unset
- **Key:** `cli:dial-defaults:cn-strength-defaults-to-unset`
- **Layers:** unit
- **WHEN** no cn_strength flag is supplied
- **THEN** no cn_strength override is applied

### Requirement: Dial range validation at parse time

The system SHALL reject a dial value outside its valid range **before the run starts** — denoise, ip_weight and
cn_strength in zero-to-one, cfg in zero-to-thirty — because these runs cost real money and a rejected flag
should cost none.

This replaces the previous *Dial range validation at parse time* requirement, which covered three dials.

#### Scenario: an in-range denoise is accepted
- **Key:** `cli:dial-validation:accepts-denoise-in-range`
- **Layers:** unit
- **WHEN** a denoise within zero to one is supplied
- **THEN** it is accepted

#### Scenario: an in-range cfg is accepted
- **Key:** `cli:dial-validation:accepts-cfg-in-range`
- **Layers:** unit
- **WHEN** a cfg within zero to thirty is supplied
- **THEN** it is accepted

#### Scenario: an in-range ip_weight is accepted
- **Key:** `cli:dial-validation:accepts-ip-weight-in-range`
- **Layers:** unit
- **WHEN** an ip_weight within zero to one is supplied
- **THEN** it is accepted

#### Scenario: an in-range cn_strength is accepted
- **Key:** `cli:dial-validation:accepts-cn-strength-in-range`
- **Layers:** unit
- **WHEN** a cn_strength within zero to one is supplied
- **THEN** it is accepted

#### Scenario: a denoise above one is rejected
- **Key:** `cli:dial-validation:rejects-denoise-above-one`
- **Layers:** unit
- **WHEN** a denoise greater than one is supplied
- **THEN** parsing fails before any run begins

#### Scenario: a denoise below zero is rejected
- **Key:** `cli:dial-validation:rejects-denoise-below-zero`
- **Layers:** unit
- **WHEN** a denoise less than zero is supplied
- **THEN** parsing fails

#### Scenario: a cfg above thirty is rejected
- **Key:** `cli:dial-validation:rejects-cfg-above-thirty`
- **Layers:** unit
- **WHEN** a cfg greater than thirty is supplied
- **THEN** parsing fails

#### Scenario: a cfg below zero is rejected
- **Key:** `cli:dial-validation:rejects-cfg-below-zero`
- **Layers:** unit
- **WHEN** a cfg less than zero is supplied
- **THEN** parsing fails

#### Scenario: an ip_weight above one is rejected
- **Key:** `cli:dial-validation:rejects-ip-weight-above-one`
- **Layers:** unit
- **WHEN** an ip_weight greater than one is supplied
- **THEN** parsing fails

#### Scenario: an ip_weight below zero is rejected
- **Key:** `cli:dial-validation:rejects-ip-weight-below-zero`
- **Layers:** unit
- **WHEN** an ip_weight less than zero is supplied
- **THEN** parsing fails

#### Scenario: a cn_strength above one is rejected
- **Key:** `cli:dial-validation:rejects-cn-strength-above-one`
- **Layers:** unit
- **WHEN** a cn_strength greater than one is supplied
- **THEN** parsing fails

#### Scenario: a cn_strength below zero is rejected
- **Key:** `cli:dial-validation:rejects-cn-strength-below-zero`
- **Layers:** unit
- **WHEN** a cn_strength less than zero is supplied
- **THEN** parsing fails

### Requirement: Dial flags reach the run

The system SHALL pass the parsed dial overrides through to the run, so a flag the user typed actually changes
what is submitted.

#### Scenario: the override flags are handed to the run
- **Key:** `cli:dial-plumbing:overrides-reach-the-run`
- **Layers:** unit
- **WHEN** dial override flags are supplied on the command line
- **THEN** the run receives those values

### Requirement: The output destination is a directory

The system SHALL treat the output flag as a **directory** rather than a file, SHALL default it to a
conventional outputs directory, and SHALL reject a value naming an image file — because the flag
previously named a file, and silently accepting the old form would create a directory named
`out.png` full of images.

#### Scenario: the output flag defaults to a conventional directory
- **Key:** `cli:output-destination:defaults-to-an-outputs-directory`
- **Layers:** unit
- **WHEN** no output flag is supplied
- **THEN** the parsed destination is the project's conventional outputs directory
- **AND** the run is handed that destination, so the bare command needs no flag at all

#### Scenario: an explicit output directory is accepted
- **Key:** `cli:output-destination:accepts-a-directory`
- **Layers:** unit
- **WHEN** an output directory is supplied
- **THEN** it is carried into the run as the destination

#### Scenario: an output naming an image file is rejected at parse time
- **Key:** `cli:output-destination:rejects-an-image-filename`
- **Layers:** unit
- **WHEN** the output flag names a file with an image extension
- **THEN** parsing fails before the photo is uploaded
- **AND** the message says the flag now names a directory, so a caller carrying the previous
  release's command learns what changed rather than finding a directory where a file was expected

#### Scenario: the required surface is the photo alone
- **Key:** `cli:output-destination:photo-is-the-only-required-argument`
- **Layers:** unit
- **WHEN** the command line carries nothing but an input photo
- **THEN** parsing succeeds
- **AND** no other flag is required, because everything else is either defaulted or committed to the
  graph

### Requirement: Seed and variation-count flags

The system SHALL accept an explicit seed and a variation count, defaulting to an unset seed and
**five** variations, and SHALL reject a variation count below one or above a stated ceiling — five
renders is what the product produces, and an unbounded count bills a typo at GPU rates.

This replaces the previous *Reproducibility flags* requirement, whose default was one variation and
whose refusal of several variations on a model with no mutation seam described paths this change
deletes.

#### Scenario: the seed defaults to unset
- **Key:** `cli:reproducibility:seed-defaults-to-unset`
- **Layers:** unit
- **WHEN** no seed is supplied
- **THEN** the parsed seed is unset
- **AND** the run is handed no seed, leaving it to draw and report one of its own

#### Scenario: an explicit seed is accepted
- **Key:** `cli:reproducibility:accepts-a-seed`
- **Layers:** unit
- **WHEN** a seed is supplied
- **THEN** it is carried into the run, making that run repeatable

#### Scenario: the variation count defaults to five
- **Key:** `cli:reproducibility:variations-default-to-five`
- **Layers:** unit
- **WHEN** no variation count is supplied
- **THEN** the parsed variation count is five
- **AND** the run is handed that count, because five renders to choose between is the product rather
  than an option

#### Scenario: an explicit variation count is accepted
- **Key:** `cli:reproducibility:accepts-a-variation-count`
- **Layers:** unit
- **WHEN** a variation count is supplied
- **THEN** the run is handed that count

#### Scenario: a non-positive variation count is rejected
- **Key:** `cli:reproducibility:variations-must-be-positive`
- **Layers:** unit
- **WHEN** a variation count below one is supplied
- **THEN** parsing fails rather than the run uploading the photo and rendering nothing

#### Scenario: a variation count above the ceiling is rejected
- **Key:** `cli:reproducibility:variations-must-not-exceed-the-ceiling`
- **Layers:** unit
- **WHEN** a variation count above the stated ceiling is supplied
- **THEN** parsing fails before the photo is uploaded
- **AND** no render is billed, because a mistyped count would otherwise bill one GPU render per
  digit

### Requirement: A flag holds the graph's dials still

The system SHALL offer a flag that suppresses dial jitter for the whole run, SHALL default it to off so the
existing behaviour is unchanged, and SHALL record in the run's manifest which of the two the run was.

A baseline is the graph rendered as committed. Without a flag there is no way to ask for one, and without the
manifest recording which mode ran, two directories of renders are indistinguishable afterwards.

#### Scenario: jitter is on by default
- **Key:** `cli:fixed-dials:jitter-is-the-default`
- **Layers:** unit
- **WHEN** no fixed-dial flag is supplied
- **THEN** the run jitters dials exactly as it did before

#### Scenario: the flag reaches the run
- **Key:** `cli:fixed-dials:flag-reaches-the-run`
- **Layers:** unit
- **WHEN** the fixed-dial flag is supplied
- **THEN** the run receives it

#### Scenario: the mode is recorded in the manifest
- **Key:** `cli:fixed-dials:mode-is-recorded`
- **Layers:** unit
- **WHEN** a run completes
- **THEN** the manifest states whether dials were jittered or held
