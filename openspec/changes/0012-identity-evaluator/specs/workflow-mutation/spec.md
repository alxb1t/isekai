## MODIFIED Requirements

### Requirement: Variation runs vary unless the run asks for the graph's own dials

The system SHALL apply the mutator once per variation by default, and SHALL write one output per variation —
so a run of N variations submits N distinct graphs. A run MAY instead ask for the graph's committed dials, in
which case no dial is jittered and every variation differs from the others in its sampler seed alone.

This replaces the previous *Variation runs always vary* requirement, whose text made mutation unconditional.
That made a baseline impossible to render: the mutator moves six dials at once, so no two renders this
repository has ever produced differ in one thing, and "same subject, one thing moved" was not a claim it
could make. The default is unchanged; what is added is the ability to hold the dials still.

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

#### Scenario: a fixed-dial run submits the graph's own dials
- **Key:** `workflow-mutation:variations:fixed-dials-are-the-graphs-own`
- **Layers:** unit
- **WHEN** a run asks for the graph's committed dials
- **THEN** every dial the mutator would have jittered carries the value the workflow shipped with
- **AND** any override the user supplied is still applied, because an override sets the base rather than
  jittering it

#### Scenario: a fixed-dial run still varies its seed
- **Key:** `workflow-mutation:variations:fixed-dials-still-vary-the-seed`
- **Layers:** unit
- **WHEN** a fixed-dial run asks for several variations
- **THEN** each variation carries its own distinct sampler seed
- **AND** the renders differ in exactly one thing, which is what makes them a baseline

#### Scenario: a fixed-dial run is reproducible from its seed
- **Key:** `workflow-mutation:variations:fixed-dials-reproduce-from-the-seed`
- **Layers:** unit
- **WHEN** a fixed-dial run is executed twice from the same run seed
- **THEN** both runs submit identical workflows

### Requirement: Run output layout

The system SHALL write every render of a run into a fresh timestamped directory beneath the
destination, one numbered image per variation, alongside a manifest recording what produced them —
so a run describes itself and reproducing a render does not depend on the operator still having the
terminal it was printed to.

The manifest is what a later comparison identifies a render by, so it records the inputs as well as the
draw: a manifest naming neither the photograph nor the graph nor the base cannot tell a scorer what it is
looking at, and a baseline nothing can identify is not a baseline.

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

#### Scenario: the manifest identifies the photograph it was rendered from
- **Key:** `workflow-mutation:output-layout:manifest-identifies-the-photo`
- **Layers:** unit
- **WHEN** a run completes
- **THEN** the manifest records a digest of the input photograph
- **AND** a later comparison can confirm it is scoring against the photograph that produced the render,
  without the photograph itself being committed anywhere

#### Scenario: the manifest identifies the graph and the base
- **Key:** `workflow-mutation:output-layout:manifest-identifies-the-graph-and-base`
- **Layers:** unit
- **WHEN** a run completes
- **THEN** the manifest records a digest of the graph as submitted and the base checkpoint named in it
- **AND** a comparison across two different bases is detectable rather than silent

#### Scenario: the manifest records the resolved dials per variation
- **Key:** `workflow-mutation:output-layout:manifest-records-resolved-dials`
- **Layers:** unit
- **WHEN** a run completes several variations
- **THEN** the manifest records, for each variation, the dial values actually submitted
- **AND** what a render was produced with is a property of the artifact rather than of re-deriving it

#### Scenario: the manifest records the working resolution
- **Key:** `workflow-mutation:output-layout:manifest-records-the-resolution`
- **Layers:** unit
- **WHEN** a run completes
- **THEN** the manifest records the render target derived from the photograph
- **AND** a scorer can check the canvas it derived against the one that was rendered

#### Scenario: the destination is resolved by the caller, not drawn inside the run
- **Key:** `workflow-mutation:output-layout:destination-is-resolved-by-the-caller`
- **Layers:** unit
- **WHEN** a run is started
- **THEN** it is handed an already-resolved destination directory
- **AND** it draws no clock of its own, which is what keeps the suite offline and deterministic

### Requirement: Dial overrides on the one graph

The system SHALL let the user set base values for denoise, cfg, ip_weight and cn_strength, SHALL treat an
unspecified dial as a no-op rather than a reset to a default, and SHALL mutate the workflow in place.

This replaces the previous *Dial overrides on the one graph* requirement, which covered three dials.
`cn_strength` is the identity node's second dial — the keypoint route, beside `ip_weight`'s embedding route —
and it was settable by nothing, jittered by nothing and pinned by nothing. It is added here so it can be
searched later; this change does not search it.

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

#### Scenario: cn_strength is set on the identity node
- **Key:** `workflow-mutation:overrides:sets-cn-strength`
- **Layers:** unit
- **WHEN** a cn_strength override is applied
- **THEN** the identity apply node's cn_strength input carries the requested value
- **AND** no ControlNet apply node's strength is touched, because this dial lives on the identity node

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

## ADDED Requirements

### Requirement: The committed dials are pinned

The system SHALL hold the graph's committed dial values under test, so that a re-tune is a deliberate edit
rather than a silent one. This covers `cn_strength` as well as the dials an earlier probe pinned: a baseline
is measured against the graph as committed, and a dial that can move unremarked moves the floor every later
measurement is read against.

#### Scenario: the identity node's keypoint dial is pinned
- **Key:** `workflow-mutation:pinned-dials:cn-strength-is-pinned`
- **Layers:** unit
- **WHEN** the shipped graph is loaded
- **THEN** the identity apply node's cn_strength carries the value the baseline was rendered at
- **AND** changing it requires editing the test that pins it
