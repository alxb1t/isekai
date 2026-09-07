## MODIFIED Requirements

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

## ADDED Requirements

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
