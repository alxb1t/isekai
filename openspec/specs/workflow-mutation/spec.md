# Capability: `workflow-mutation`

Determining the dial values a render actually runs with — the user's explicit choices, and the seeded jitter
applied around them.

**Source:** `isekai/overrides.py`, `isekai/mutate.py` ·
**Tests:** `tests/test_overrides.py`, `tests/test_mutation.py`, `tests/test_variations.py`

Two halves of one observable behaviour. `apply_overrides` sets the **base** values the user asked for; `mutate`
jitters **around that base**. The order is load → override → mutate, so a user-supplied base is what the jitter
centres on. Mutation is a seam distinct from injection: injection wires image and prompt, mutation varies dials.
The RNG is **injected**, which is what makes any of this deterministically testable.

## Requirements

### Requirement: Explicit dial overrides

The system SHALL let the user set base values for denoise, cfg and ip_weight, SHALL treat an unspecified dial as
a no-op rather than a reset to a default, and SHALL mutate the workflow in place.

#### Scenario: denoise is set on the sampler
- **Key:** `workflow-mutation:overrides:sets-denoise`
- **Layers:** unit
- **WHEN** a denoise override is applied to a workflow
- **THEN** the sampler's denoise input carries the requested value

#### Scenario: cfg is set on the sampler
- **Key:** `workflow-mutation:overrides:sets-cfg`
- **Layers:** unit
- **WHEN** a cfg override is applied
- **THEN** the sampler's cfg input carries the requested value

#### Scenario: ip_weight is set on the identity node
- **Key:** `workflow-mutation:overrides:sets-ip-weight`
- **Layers:** unit
- **WHEN** an ip_weight override is applied
- **THEN** the identity apply node's ip_weight input carries the requested value

#### Scenario: an unspecified dial is left exactly as it was
- **Key:** `workflow-mutation:overrides:unspecified-dial-untouched`
- **Layers:** unit
- **WHEN** an override is applied with a dial left unspecified
- **THEN** that dial keeps the value the workflow shipped with
- **AND** it is not reset to any default, so partial overrides are safe

#### Scenario: overriding nothing changes nothing
- **Key:** `workflow-mutation:overrides:all-unspecified-is-a-no-op`
- **Layers:** unit
- **WHEN** an override is applied with every dial unspecified
- **THEN** the workflow is unchanged

#### Scenario: ip_weight is silently ignored on graphs with no identity node
- **Key:** `workflow-mutation:overrides:ip-weight-ignored-without-identity-node`
- **Layers:** unit
- **WHEN** an ip_weight override is applied to a graph carrying no identity apply node, such as Qwen
- **THEN** the override is a silent no-op rather than an error
- **AND** the dial stays meaningful on the models that have it without breaking those that do not

#### Scenario: overrides mutate the workflow in place
- **Key:** `workflow-mutation:overrides:mutates-in-place`
- **Layers:** unit
- **WHEN** an override is applied
- **THEN** the caller's own workflow object is modified rather than a copy returned

### Requirement: Seeded dial jitter

The system SHALL vary the sampler seed and the denoise, cfg and ip_weight dials using an **injected** random
source, so a run's variation is reproducible from its seed.

#### Scenario: the sampler seed is drawn from the injected RNG
- **Key:** `workflow-mutation:jitter:seed-comes-from-the-rng`
- **Layers:** unit
- **WHEN** mutation runs with a given random source
- **THEN** the sampler's seed is the value that source produced

#### Scenario: the seed is drawn at full 64-bit width
- **Key:** `workflow-mutation:jitter:seed-is-64-bit`
- **Layers:** unit
- **WHEN** mutation draws a seed
- **THEN** it is drawn across the full 64-bit space rather than a narrower range

#### Scenario: denoise is jittered within its band
- **Key:** `workflow-mutation:jitter:denoise-within-band`
- **Layers:** unit
- **WHEN** mutation runs
- **THEN** the resulting denoise lies within the defined delta of its starting value, clamped to a valid range

#### Scenario: cfg is jittered within its band
- **Key:** `workflow-mutation:jitter:cfg-within-band`
- **Layers:** unit
- **WHEN** mutation runs
- **THEN** the resulting cfg lies within the defined delta of its starting value, clamped to a valid range

#### Scenario: ip_weight is jittered within its band
- **Key:** `workflow-mutation:jitter:ip-weight-within-band`
- **Layers:** unit
- **WHEN** mutation runs
- **THEN** the resulting ip_weight lies within the defined delta of its starting value, clamped to a valid range

### Requirement: Jitter is relative to the current base

The system SHALL centre every dial's jitter on that dial's **current** value rather than on a hardcoded constant,
so that a user-supplied override moves the band with it instead of being overwritten by it.

#### Scenario: denoise jitter centres on the current base
- **Key:** `workflow-mutation:base-relative:denoise-around-current-base`
- **Layers:** unit
- **WHEN** the workflow's denoise is changed before mutation runs
- **THEN** the jittered result falls around that new value, not around a fixed constant

#### Scenario: cfg jitter centres on the current base
- **Key:** `workflow-mutation:base-relative:cfg-around-current-base`
- **Layers:** unit
- **WHEN** the workflow's cfg is changed before mutation runs
- **THEN** the jittered result falls around that new value

#### Scenario: ip_weight jitter centres on the current base
- **Key:** `workflow-mutation:base-relative:ip-weight-around-current-base`
- **Layers:** unit
- **WHEN** the workflow's ip_weight is changed before mutation runs
- **THEN** the jittered result falls around that new value

#### Scenario: an override is applied before jitter, so jitter surrounds the new base
- **Key:** `workflow-mutation:base-relative:override-applied-before-jitter`
- **Layers:** unit
- **WHEN** a run supplies both an explicit dial override and a mutator
- **THEN** the override is applied first and the jitter is drawn around the overridden value
- **AND** the user's choice sets the centre of the variation rather than being discarded by it

### Requirement: ControlNet strength jitter

The system SHALL jitter each ControlNet strength around its own tuned baseline, and SHALL leave the output of
graphs that carry no ControlNet nodes byte-for-byte unchanged — so adding the ControlNet path is additive for
the models that predate it.

#### Scenario: each ControlNet strength is jittered
- **Key:** `workflow-mutation:controlnet:strengths-are-jittered`
- **Layers:** unit
- **WHEN** mutation runs against a graph carrying a ControlNet stack
- **THEN** each apply node's strength is varied from its starting value

#### Scenario: every ControlNet strength stays inside its band
- **Key:** `workflow-mutation:controlnet:strengths-stay-in-band`
- **Layers:** unit
- **WHEN** mutation runs against a ControlNet stack
- **THEN** every resulting strength lies within the defined delta of its own tuned baseline, clamped to a valid
  range
- **AND** each node keeps its own baseline, because tile, pose and lineart are tuned differently

#### Scenario: the ControlNet path is reproducible from its seed
- **Key:** `workflow-mutation:controlnet:reproducible-from-seed`
- **Layers:** unit
- **WHEN** mutation runs twice against a ControlNet graph from equal random states
- **THEN** both runs produce identical strengths

#### Scenario: graphs without ControlNet nodes are unaffected
- **Key:** `workflow-mutation:controlnet:no-draw-without-controlnet-nodes`
- **Layers:** unit
- **WHEN** mutation runs against a graph carrying no ControlNet apply nodes
- **THEN** the earlier img2img model's output is byte-for-byte what it was before the ControlNet path existed
- **AND** adding the ControlNet path is therefore proven additive for the models that predate it

### Requirement: Reproducibility contract

The system SHALL produce identical output for identical seeds and different output for different random states,
and SHALL report the seed it used so a run can be reproduced.

#### Scenario: the same seed reproduces the same mutation
- **Key:** `workflow-mutation:reproducibility:same-seed-same-result`
- **Layers:** unit
- **WHEN** mutation runs twice from equal random states
- **THEN** both workflows come out identical

#### Scenario: different random states diverge
- **Key:** `workflow-mutation:reproducibility:distinct-states-diverge`
- **Layers:** unit
- **WHEN** mutation runs from two different random states
- **THEN** the resulting dial values differ

#### Scenario: the seed used is printed
- **Key:** `workflow-mutation:reproducibility:seed-is-printed`
- **Layers:** unit
- **WHEN** a run completes
- **THEN** the seed it used is reported, so the run can be repeated exactly

#### Scenario: an override plus a seed reproduces exactly
- **Key:** `workflow-mutation:reproducibility:override-plus-seed-reproduces`
- **Layers:** unit
- **WHEN** a run supplies the same overrides and the same seed twice
- **THEN** both runs submit identical workflows

#### Scenario: the pre-override behaviour is preserved exactly
- **Key:** `workflow-mutation:reproducibility:no-override-matches-previous-release`
- **Layers:** unit
- **WHEN** a run supplies no overrides at all
- **THEN** the submitted workflow is byte-identical to what the previous release produced for that seed
- **AND** the override feature is proven additive rather than behaviour-changing

### Requirement: Variation runs

The system SHALL apply the mutator once per variation when a model carries one, and SHALL leave the workflow
untouched when it does not.

#### Scenario: a mutator varies the submitted workflow
- **Key:** `workflow-mutation:variations:mutator-varies-submission`
- **Layers:** unit
- **WHEN** a run executes with a model that carries a mutator
- **THEN** the workflow that is submitted differs from the one loaded from disk

#### Scenario: without a mutator the run stays deterministic
- **Key:** `workflow-mutation:variations:no-mutator-stays-deterministic`
- **Layers:** unit
- **WHEN** a run executes with a model carrying no mutator
- **THEN** the submitted workflow is exactly the one loaded from disk

#### Scenario: each variation produces its own output
- **Key:** `workflow-mutation:variations:one-output-per-variation`
- **Layers:** unit
- **WHEN** a run requests several variations
- **THEN** one output is written per variation
