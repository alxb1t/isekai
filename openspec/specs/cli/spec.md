# Capability: `cli`

The command-line surface: parsing flags, validating their ranges before any GPU work starts, and dispatching the
chosen model into a run.

**Source:** `isekai/cli.py` · **Tests:** `tests/test_cli.py`

The CLI is where a bad value is cheapest to catch. Every dial is range-checked **at parse time**, so an
out-of-range flag fails before a pod is touched rather than after a paid render.

## Requirements

### Requirement: Model selection

The system SHALL default to a model when none is named, accept every registered model by name, and reject an
unregistered one at parse time.

#### Scenario: the img2img model is the default
- **Key:** `cli:model-selection:defaults-to-animagine-i2i`
- **Layers:** unit
- **WHEN** no model flag is supplied
- **THEN** the img2img Animagine model is selected

#### Scenario: the Animagine model is accepted by name
- **Key:** `cli:model-selection:accepts-animagine`
- **Layers:** unit
- **WHEN** the Animagine model is named on the command line
- **THEN** it is selected

#### Scenario: the img2img model is accepted by name
- **Key:** `cli:model-selection:accepts-animagine-i2i`
- **Layers:** unit
- **WHEN** the img2img model is named
- **THEN** it is selected

#### Scenario: the ControlNet model is accepted by name
- **Key:** `cli:model-selection:accepts-animagine-i2i-cn`
- **Layers:** unit
- **WHEN** the ControlNet model is named
- **THEN** it is selected
- **AND** every previously shipped model remains selectable alongside it

#### Scenario: an unregistered model name is rejected at parse time
- **Key:** `cli:model-selection:rejects-unknown-model`
- **Layers:** unit
- **WHEN** a name that is not a registered model is supplied
- **THEN** parsing fails rather than the run proceeding with a default

### Requirement: Model dispatch into a run

The system SHALL hand the run the workflow and injector belonging to the selected model, so that adding a model
does not require changing the run.

#### Scenario: selecting Animagine dispatches its workflow and injector
- **Key:** `cli:dispatch:animagine-workflow-and-injector`
- **Layers:** unit
- **WHEN** a run is started with the Animagine model selected
- **THEN** the run receives that model's workflow and its injection adapter

#### Scenario: selecting img2img dispatches its workflow and reuses the injector
- **Key:** `cli:dispatch:img2img-workflow-reuses-injector`
- **Layers:** unit
- **WHEN** a run is started with the img2img model selected
- **THEN** the run receives the img2img workflow
- **AND** the same Animagine injection adapter, unchanged

### Requirement: Reproducibility flags

The system SHALL accept an explicit seed and a variation count, defaulting to an unset seed and a single
variation.

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

#### Scenario: the variation count defaults to one
- **Key:** `cli:reproducibility:variations-default-to-one`
- **Layers:** unit
- **WHEN** no variation count is supplied
- **THEN** the parsed variation count is one
- **AND** the run is handed that count

#### Scenario: an explicit variation count is accepted
- **Key:** `cli:reproducibility:accepts-a-variation-count`
- **Layers:** unit
- **WHEN** a variation count is supplied
- **THEN** the run is handed that count

### Requirement: Dial flags default to unset

The system SHALL leave each dial override unset when its flag is absent, so that omitting a flag preserves the
workflow's own tuned value rather than imposing a CLI default.

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

### Requirement: Dial range validation at parse time

The system SHALL reject a dial value outside its valid range **before the run starts** — denoise and ip_weight in
zero-to-one, cfg in zero-to-thirty — because these runs cost real money and a rejected flag should cost none.

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

### Requirement: Dial flags reach the run

The system SHALL pass the parsed dial overrides through to the run, so a flag the user typed actually changes
what is submitted.

#### Scenario: the override flags are handed to the run
- **Key:** `cli:dial-plumbing:overrides-reach-the-run`
- **Layers:** unit
- **WHEN** dial override flags are supplied on the command line
- **THEN** the run receives those values
