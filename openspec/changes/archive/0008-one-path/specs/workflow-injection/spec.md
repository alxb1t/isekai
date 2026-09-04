## ADDED Requirements

### Requirement: The positive prompt is graph configuration

The system SHALL commit the positive prompt to the workflow graph and SHALL expose no way to set it
from the command line — the prompt is the highest-leverage input to a Danbooru-trained base, and a
value a human retypes each run makes every render unattributable. It is configuration, in the same
category as `steps` and `cfg`.

#### Scenario: no command-line path sets the positive prompt
- **Key:** `workflow-injection:committed-prompt:not-settable-from-the-cli`
- **Layers:** unit
- **WHEN** the command line is parsed
- **THEN** no flag carries a prompt
- **AND** injection takes no prompt argument, so there is no path by which typed text reaches the
  encoder

#### Scenario: the committed positive string is pinned
- **Key:** `workflow-injection:committed-prompt:string-is-pinned`
- **Layers:** unit
- **WHEN** the shipped graph's positive encoder is inspected
- **THEN** its text equals a literal pinned by the suite
- **AND** changing the prompt therefore requires a deliberate test edit, which is what makes "not
  typeable" a property rather than a convention

#### Scenario: the committed string carries no typed subject text
- **Key:** `workflow-injection:committed-prompt:carries-no-pose-tag`
- **Layers:** unit
- **WHEN** the pinned positive string is read
- **THEN** it contains no pose tag
- **AND** pose is carried by the OpenPose ControlNet, so a pose tag in the prompt competes with the
  mechanism that owns that axis

#### Scenario: the negative encoder is left as the graph committed it
- **Key:** `workflow-injection:committed-prompt:negative-is-untouched`
- **Layers:** unit
- **WHEN** injection runs
- **THEN** the negative encoder's text is exactly what the graph shipped with

### Requirement: Node location on the one graph

The system SHALL locate a workflow node by class type, and SHALL refuse to guess when the query does
not identify exactly one node — an injection that edits the wrong node produces a silently wrong
render rather than an error.

This replaces the previous *Unambiguous node location* requirement. Title-based lookup is removed
with its last caller, and the two Qwen scenarios describe a graph this change deletes.

#### Scenario: a node is located by its class type
- **Key:** `workflow-injection:node-location:locates-by-class-type`
- **Layers:** unit
- **WHEN** a graph is queried for a node of a given class type that appears exactly once
- **THEN** that node's ID is returned

#### Scenario: a query matching nothing is refused
- **Key:** `workflow-injection:node-location:exits-when-no-node-matches`
- **Layers:** unit
- **WHEN** a graph is queried for a node that does not exist
- **THEN** the process exits rather than returning nothing for the caller to mishandle

#### Scenario: an ambiguous query is refused
- **Key:** `workflow-injection:node-location:exits-when-ambiguous`
- **Layers:** unit
- **WHEN** a query matches more than one node
- **THEN** the process exits rather than silently picking the first match

#### Scenario: the shipped graph has exactly one image loader
- **Key:** `workflow-injection:node-location:single-load-image-in-real-workflow`
- **Layers:** unit
- **WHEN** the shipped workflow is queried for its image-loading node
- **THEN** exactly one is found, which is what makes an unqualified lookup safe for the photo

#### Scenario: the two text encoders are genuinely ambiguous
- **Key:** `workflow-injection:node-location:text-encoders-are-ambiguous`
- **Layers:** unit
- **WHEN** the shipped workflow is queried for a text encoder by class type alone
- **THEN** the query is refused as ambiguous, because the graph carries a positive and a negative
  encoder
- **AND** this is why neither encoder is reached by class lookup, and why the positive string is
  committed to the graph rather than placed by injection

### Requirement: Photo wiring into the one graph

The system SHALL point the workflow's image loader at the uploaded file, so the graph reads the
photo the run actually uploaded.

This replaces the previous *Photo wiring* requirement, whose four scenarios wired four graphs. One
graph remains, and one loader feeds every consumer in it.

#### Scenario: one loader feeds the whole stack
- **Key:** `workflow-injection:photo-wiring:single-loader-fans-out`
- **Layers:** unit
- **WHEN** injection runs against the shipped workflow, where one loader feeds the latent encoder,
  the identity node and every ControlNet preprocessor
- **THEN** that single loader is wired to the uploaded filename
- **AND** the exactly-one-loader invariant holds across the entire stack, which is why injection
  needs no per-consumer branch

### Requirement: Latent initialisation from the photo

The system SHALL initialise the graph's latent from the photo rather than from noise, at a denoise
strength below one, so the photograph's composition survives into the render.

This replaces the previous *img2img latent initialisation* requirement. The behaviour is unchanged;
the name and its scenario key drop the `img2img` qualifier, which distinguished one of four graphs
that no longer exist.

#### Scenario: the graph inits its latent from the photo below full denoise
- **Key:** `workflow-injection:latent-init:inits-from-photo-below-one`
- **Layers:** unit
- **WHEN** the shipped workflow is inspected
- **THEN** its latent is encoded from the loaded photo rather than generated as empty noise
- **AND** the sampler's denoise is below one, which is the dial trading identity against style

## REMOVED Requirements

### Requirement: Unambiguous node location

**Reason**: Replaced by *Node location on the one graph*. Its title-lookup scenario described a
parameter with no caller, and two of its scenarios were about the Qwen graph, which this change
deletes.

**Migration**: None — node location behaves identically for the surviving graph; only the deleted
graphs' scenarios and the unused title argument are gone.

### Requirement: Photo wiring

**Reason**: Replaced by *Photo wiring into the one graph*. Three of its four scenarios named deleted
graphs.

**Migration**: None. The photo is wired exactly as before for the surviving path.

### Requirement: Prompt placement on the positive conditioning path

**Reason**: There is no prompt to place. The positive string is committed to the graph, so injection
wires the photo and nothing else, and the conditioning trace that walked `positive` links to find
the encoder has no caller. Its four scenarios described a behaviour the CLI can no longer trigger.

**Migration**: None for a caller — `--prompt` is removed. The trace's non-obvious insight is
preserved in this change's `design.md` and in the capability's own header: the sampler's positive
input may point at the identity node directly or through a stack of ControlNet apply nodes, so the
encoder is found by following that link, never by class lookup. A future tagger that generates a
prompt rebuilds this deliberately, as a purpose-built entry point.

### Requirement: img2img latent initialisation

**Reason**: Replaced by *Latent initialisation from the photo*. `img2img` named one graph among four;
with one graph left the qualifier distinguishes nothing, and phase 2 renames the scenario key to
match.

**Migration**: None — the latent is initialised exactly as before. Only the requirement name and the
scenario key change: `workflow-injection:latent-init:img2img-inits-from-photo-below-one` becomes
`workflow-injection:latent-init:inits-from-photo-below-one`.
