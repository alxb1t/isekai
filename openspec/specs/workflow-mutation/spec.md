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

### Requirement: Run output layout

The system SHALL write every render of a run into a fresh timestamped directory beneath the
destination, one numbered image per variation, alongside a manifest recording what produced them —
so a run describes itself and reproducing a render does not depend on the operator still having the
terminal it was printed to.

#### Scenario: each run writes into its own timestamped directory
- **Key:** `workflow-mutation:output-layout:run-gets-its-own-directory`
- **Layers:** unit
- **WHEN** a run executes against a destination directory
- **THEN** a new subdirectory named for the run's UTC start instant is created beneath it
- **AND** every image of that run is written inside it, so consecutive runs never overwrite one
  another

#### Scenario: images are numbered by variation
- **Key:** `workflow-mutation:output-layout:images-numbered-by-variation`
- **Layers:** unit
- **WHEN** a run completes several variations
- **THEN** each variation's image is named for its index within the run's directory

#### Scenario: the manifest records what produced the run
- **Key:** `workflow-mutation:output-layout:manifest-records-the-run`
- **Layers:** unit
- **WHEN** a run completes
- **THEN** a manifest is written into the run's directory recording the seed the run was given, the
  per-variation seed actually used, and the dial values in force
- **AND** the run is therefore reproducible from the directory alone

#### Scenario: the destination is resolved by the caller, not drawn inside the run
- **Key:** `workflow-mutation:output-layout:destination-is-resolved-by-the-caller`
- **Layers:** unit
- **WHEN** a run is started
- **THEN** it is handed an already-resolved destination directory
- **AND** it draws no clock of its own, which is what keeps the suite offline and deterministic

### Requirement: Dial overrides on the one graph

The system SHALL let the user set base values for denoise, cfg and ip_weight, SHALL treat an
unspecified dial as a no-op rather than a reset to a default, and SHALL mutate the workflow in
place.

This replaces the previous *Explicit dial overrides* requirement. Its two dropped scenarios both
described graphs this change deletes: a graph with no identity node (Qwen), and a dial wired to
another node rather than set to a value (Qwen's `cfg`). The surviving graph has neither.

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

#### Scenario: overrides mutate the workflow in place
- **Key:** `workflow-mutation:overrides:mutates-in-place`
- **Layers:** unit
- **WHEN** an override is applied
- **THEN** the caller's own workflow object is modified rather than a copy returned

### Requirement: Seeded dial jitter from an injected source

The system SHALL vary the sampler seed and the denoise, cfg and ip_weight dials using an
**injected** random source, so a run's variation is reproducible from its seed.

This replaces the previous *Seeded dial jitter* requirement. Its dropped scenario — a dial wired to
another node, refused legibly — guarded against Qwen's linked `cfg`, and no surviving graph can
reach it.

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
- **THEN** the resulting denoise lies within the defined delta of its starting value, clamped to a
  valid range

#### Scenario: cfg is jittered within its band
- **Key:** `workflow-mutation:jitter:cfg-within-band`
- **Layers:** unit
- **WHEN** mutation runs
- **THEN** the resulting cfg lies within the defined delta of its starting value, clamped to a valid
  range

#### Scenario: ip_weight is jittered within its band
- **Key:** `workflow-mutation:jitter:ip-weight-within-band`
- **Layers:** unit
- **WHEN** mutation runs
- **THEN** the resulting ip_weight lies within the defined delta of its starting value, clamped to a
  valid range

### Requirement: ControlNet strength jitter around per-node baselines

The system SHALL jitter each ControlNet strength around its **own** tuned baseline, because tile,
pose and lineart are tuned differently and a shared constant would erase that tuning.

This replaces the previous *ControlNet strength jitter* requirement. Its dropped scenario asserted
that graphs carrying no ControlNet nodes were left byte-for-byte unchanged — an additivity guarantee
for the img2img model, which this change deletes. Every surviving graph carries the stack.

#### Scenario: each ControlNet strength is jittered
- **Key:** `workflow-mutation:controlnet:strengths-are-jittered`
- **Layers:** unit
- **WHEN** mutation runs against the shipped graph's ControlNet stack
- **THEN** each apply node's strength is varied from its starting value

#### Scenario: every ControlNet strength stays inside its band
- **Key:** `workflow-mutation:controlnet:strengths-stay-in-band`
- **Layers:** unit
- **WHEN** mutation runs against the ControlNet stack
- **THEN** every resulting strength lies within the defined delta of its own tuned baseline, clamped
  to a valid range
- **AND** each node keeps its own baseline, because tile, pose and lineart are tuned differently

#### Scenario: the ControlNet path is reproducible from its seed
- **Key:** `workflow-mutation:controlnet:reproducible-from-seed`
- **Layers:** unit
- **WHEN** mutation runs twice against the ControlNet graph from equal random states
- **THEN** both runs produce identical strengths

### Requirement: Reproducibility contract for a varied run

The system SHALL produce identical output for identical seeds and different output for different
random states, SHALL derive **every** variation's seed uniformly from the run's seed, and SHALL
report the seed each variation used so a single render can be reproduced.

This replaces the previous *Reproducibility contract* requirement. Its dropped scenario pinned the
submitted workflow byte-for-byte against a previous release's output for a path this change deletes.

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
- **WHEN** a run completes a variation
- **THEN** the seed that variation used is reported, so it can be repeated exactly

#### Scenario: the seed covers every variation, not only the first
- **Key:** `workflow-mutation:reproducibility:seed-covers-every-variation`
- **Layers:** unit
- **WHEN** a run supplies a seed and asks for several variations
- **THEN** every variation's dials derive from that seed
- **AND** re-running the same command reproduces all of them, not only the first

#### Scenario: every variation's seed is derived, including the first
- **Key:** `workflow-mutation:reproducibility:every-variation-seed-is-derived`
- **Layers:** unit
- **WHEN** a run supplies a seed
- **THEN** no variation uses that seed verbatim as its sampler seed
- **AND** the run seed has exactly one meaning — the source every variation derives from — rather
  than doubling as the first render's sampler seed

#### Scenario: an override plus a seed reproduces exactly
- **Key:** `workflow-mutation:reproducibility:override-plus-seed-reproduces`
- **Layers:** unit
- **WHEN** a run supplies the same overrides and the same seed twice
- **THEN** both runs submit identical workflows

#### Scenario: every submitted graph of a seeded run is reproducible and distinct
- **Key:** `workflow-mutation:reproducibility:seeded-run-is-reproducible-and-distinct`
- **Layers:** unit
- **WHEN** a seeded run of several variations is executed twice
- **THEN** the submitted workflows match pairwise between the two runs
- **AND** within a run they differ from one another, because a run that reproduces one graph N times
  would bill N renders for one image

### Requirement: Variation runs always vary

The system SHALL apply the mutator once per variation, and SHALL write one output per variation —
the pipeline always varies, so a run of N variations submits N distinct graphs.

This replaces the previous *Variation runs* requirement. Its dropped scenario described a run with
no mutator staying deterministic; every path that lacked a mutation seam is deleted, so the branch
is unreachable.

#### Scenario: a mutator varies the submitted workflow
- **Key:** `workflow-mutation:variations:mutator-varies-submission`
- **Layers:** unit
- **WHEN** a run executes
- **THEN** the workflow that is submitted differs from the one loaded from disk

#### Scenario: variations differ from one another
- **Key:** `workflow-mutation:variations:variations-differ-from-each-other`
- **Layers:** unit
- **WHEN** a run asks for several variations
- **THEN** each is drawn from its own distinct seed
- **AND** the run cannot collapse into the same render repeated, which would bill once per copy

#### Scenario: each variation produces its own output
- **Key:** `workflow-mutation:variations:one-output-per-variation`
- **Layers:** unit
- **WHEN** a run requests several variations
- **THEN** one output is written per variation, into the run's own directory
