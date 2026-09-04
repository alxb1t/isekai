## ADDED Requirements

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

## REMOVED Requirements

### Requirement: Model selection

**Reason**: `--model` is removed. Three of the four paths are deleted and the survivor is the only
thing the CLI can run, so there is no default to fall back to, no name to accept and no unregistered
name to refuse.

**Migration**: Drop the flag. `--model animagine-i2i-cn` becomes no flag at all; the other three
values name deleted paths and have no equivalent.

### Requirement: Model dispatch into a run

**Reason**: Dispatch existed to hand the run whichever workflow and injector the selected model
owned. With one graph and one injector, both are reached directly and there is nothing to select
between; `--workflow`, which overrode the dispatched graph, is removed with it.

**Migration**: None. A caller who used `--workflow` to substitute a graph must edit
`workflows/pipeline.json`, which is the committed graph the run loads.

### Requirement: Reproducibility flags

**Reason**: Replaced by *Seed and variation-count flags*. Two of its scenarios describe behaviour
this change deletes: the variation count no longer defaults to one, and the refusal of several
variations on a model carrying no mutation seam protected models that no longer exist. The
surviving path always varies.

**Migration**: `--seed` and `--variations` are unchanged in spelling. A caller relying on
`--variations` defaulting to one must now pass `--variations 1` explicitly.
