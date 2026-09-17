## MODIFIED Requirements

### Requirement: A flow is a directory of five files whose manifest declares and never computes

The system SHALL define a flow as a directory containing exactly five files — a manifest, a graph, a
schema, a caption briefing and a sheet briefing — all of them directly in that directory. The manifest
SHALL declare its required inputs, the vocabulary and the models its render is pinned to, its node
roles, its prompt fragments and its dials. The manifest SHALL NOT name any of its sibling files, SHALL
declare the version of its own format, and SHALL contain no computed or conditional value.

A manifest that computes nothing is fully checkable without executing anything, which is what lets a
broken flow be caught by the test suite rather than after a pod boot and several minutes. Holding the
schema and both briefings inside the directory is what makes a flow the complete specification of how an
input becomes an image: a briefing decides what enters the caption, the caption decides the sheet, and
the sheet decides the render, so a changed briefing is a changed image and must be a new flow. The files
sit directly in the directory rather than in sub-directories because the digest that freezes a flow
covers regular files only; a nested layout would leave the schema and the briefings outside the freeze
while the gate stayed green. A key that can only ever hold one value is not a declaration, which is why
the manifest names no filenames.

#### Scenario: a flow is five files and the manifest names none of them
- **Key:** `image-generation:manifest:flow-is-five-flat-files`
- **Layers:** unit
- **WHEN** a tracked flow directory is read
- **THEN** it holds a manifest, a graph, a schema, a caption briefing and a sheet briefing, each directly
  in the directory
- **AND** the manifest declares no filename for any of them
- **AND** the directory contains no sub-directory

#### Scenario: a flow declares its inputs, vocabulary, models and dials
- **Key:** `image-generation:manifest:flow-declares-its-inputs`
- **Layers:** unit
- **WHEN** a flow manifest is loaded
- **THEN** it names its required inputs, its vocabulary, its models, its node roles and every dial the
  render uses
- **AND** no value in it is derived at load time

#### Scenario: the manifest declares the version of its own format
- **Key:** `image-generation:manifest:manifest-declares-its-format-version`
- **Layers:** unit
- **WHEN** a manifest declares a format version this build does not read
- **THEN** loading it is refused naming both versions
- **AND** the refusal states that the build is what needs upgrading

#### Scenario: a flow pins every model it uses by digest
- **Key:** `image-generation:manifest:flow-pins-its-models-by-digest`
- **Layers:** unit
- **WHEN** the suite runs
- **THEN** every model a tracked flow declares carries a digest as well as a destination
- **AND** that digest equals the one the provisioning manifest declares for the same destination
- **AND** a flow whose digest disagrees with the provisioning manifest fails the suite naming the flow

#### Scenario: every tracked flow parses and resolves
- **Key:** `image-generation:manifest:tracked-flows-are-gate-checked`
- **Layers:** unit
- **WHEN** the suite runs
- **THEN** every tracked flow manifest parses
- **AND** the schema, both briefings and the graph each one needs are present in its own directory

#### Scenario: an invalid manifest is refused naming the field
- **Key:** `image-generation:manifest:invalid-manifest-names-the-field`
- **Layers:** unit
- **WHEN** a flow manifest is missing or malformed in a declared field
- **THEN** loading it is refused naming that field
- **AND** the refusal does not require the flow to be executed

### Requirement: A flow is immutable; changing any file in it creates a new flow

The system SHALL hold each tracked flow against a committed digest computed over every file in its
directory, so that altering a dial, a prompt fragment, the graph, the schema or either briefing fails
the suite rather than changing an existing flow's behaviour.

An output's path identifies a configuration only if a flow identifier never silently means something
else. Every render already carries a graph digest to prove that held; pinning the whole directory by
equality is what makes the claim checkable rather than assumed. Extending it from the manifest to every
file is what lets two flows be rendered over one cohort and compared: if a briefing could be edited in
place, the comparison would not exist to run.

#### Scenario: editing any file in a tracked flow fails the suite
- **Key:** `image-generation:immutability:flow-manifest-is-pinned-by-equality`
- **Layers:** unit
- **WHEN** any file in a tracked flow directory differs from its committed digest
- **THEN** the suite fails naming the flow
- **AND** the failure states that a changed value means a new flow identifier

#### Scenario: adding a file to a flow moves its digest
- **Key:** `image-generation:immutability:a-new-file-moves-the-digest`
- **Layers:** unit
- **WHEN** a file is added to a tracked flow's directory
- **THEN** that flow's digest differs from the committed one
- **AND** the suite fails naming the flow

#### Scenario: an output's provenance carries the graph digest
- **Key:** `image-generation:immutability:output-records-the-graph-digest`
- **Layers:** unit
- **WHEN** a render is written
- **THEN** its provenance records the flow identifier, the seed, the sheet version and the digest of the
  submitted graph
- **AND** two renders from the same flow identifier with different graphs are distinguishable

## ADDED Requirements

### Requirement: A render asks a flow which node roles it declares

The system SHALL require exactly four node roles of every flow — a positive conditioning node, a
negative conditioning node, a latent node and a sampler node — and SHALL refuse a flow declaring fewer
when the flow is loaded, before anything is executed. Every other node role SHALL be optional, and a
render SHALL patch only the roles the flow declares. The system SHALL NOT transfer an input a flow does
not declare.

A flow declaring fewer roles used to pass the whole suite and fail on a rented GPU, after the
photograph had already been uploaded — which is the half of "a broken flow costs a test run, not a
boot" that was not true. Four roles are required because every image flow has them; the seven that are
not required include a photograph, an identity adapter and a pose preprocessor, which a sheet-only flow
does not have, and a hires resize and a hires sampler, which an ordinary cheaper flow does not have
either. Refusing at load rather than at render is what moves the failure from money to a test run.

#### Scenario: a flow missing a required role is refused at load
- **Key:** `image-generation:roles:a-missing-required-role-is-refused-offline`
- **Layers:** unit
- **WHEN** a flow manifest declares fewer than the four required node roles
- **THEN** loading it is refused naming the missing role
- **AND** no endpoint is contacted and no input is transferred

#### Scenario: a flow declaring fewer optional roles renders
- **Key:** `image-generation:roles:optional-roles-are-not-assumed`
- **Layers:** unit
- **WHEN** a flow declares the four required roles and none of the optional ones
- **THEN** its graph is built without error
- **AND** only the roles it declares are patched

#### Scenario: an input a flow does not declare is not transferred
- **Key:** `image-generation:roles:undeclared-input-is-not-uploaded`
- **Layers:** unit
- **WHEN** a flow that does not declare a photograph input is rendered
- **THEN** no photograph is transferred to the endpoint
- **AND** the render proceeds from the flow's own declared inputs
