# Capability: `workflow-injection`

Wiring the uploaded photo and the text prompt into a ComfyUI workflow graph before it is queued — locating the
nodes that need editing, and setting the right inputs on exactly the right ones.

**Source:** `isekai/workflow.py` · **Tests:** `tests/test_workflow_injection.py`

Injection is **separate from mutation**: injection wires *image + prompt*, mutation varies *dials*. Each model
family owns an injection adapter, but the adapters share a node-locating primitive and the InstantID family
shares one generalised conditioning trace.

## Requirements

### Requirement: Unambiguous node location

The system SHALL locate a workflow node by class type and/or title, and SHALL refuse to guess when the query does
not identify exactly one node — an injection that edits the wrong node produces a silently wrong render rather
than an error.

#### Scenario: a node is located by its class type
- **Key:** `workflow-injection:node-location:locates-by-class-type`
- **Layers:** unit
- **WHEN** a graph is queried for a node of a given class type that appears exactly once
- **THEN** that node's ID is returned

#### Scenario: a node is located by its title
- **Key:** `workflow-injection:node-location:locates-by-title`
- **Layers:** unit
- **WHEN** a graph is queried by the title recorded in a node's metadata
- **THEN** the matching node's ID is returned

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

#### Scenario: the real Qwen workflow has exactly one image loader
- **Key:** `workflow-injection:node-location:single-load-image-in-real-workflow`
- **Layers:** unit
- **WHEN** the shipped Qwen workflow is queried for its image-loading node
- **THEN** exactly one is found, which is what makes an unqualified lookup safe for the photo

#### Scenario: the two Qwen text encoders are genuinely ambiguous
- **Key:** `workflow-injection:node-location:qwen-text-encoders-are-ambiguous`
- **Layers:** unit
- **WHEN** the shipped Qwen workflow is queried for a text encoder by class type alone
- **THEN** the query is refused as ambiguous, because the graph carries a positive and a negative encoder
- **AND** this is why the prompt is placed by following the sampler's positive link rather than by class lookup

### Requirement: Photo wiring

The system SHALL point the workflow's image loader at the uploaded file, for every model family, so the graph
reads the photo the run actually uploaded.

#### Scenario: the Qwen graph loads the uploaded file
- **Key:** `workflow-injection:photo-wiring:qwen-loads-the-uploaded-file`
- **Layers:** unit
- **WHEN** the Qwen injector runs against its workflow with an uploaded filename
- **THEN** the graph's image loader is pointed at that filename

#### Scenario: the Animagine graph loads the reference face
- **Key:** `workflow-injection:photo-wiring:animagine-loads-the-reference-face`
- **Layers:** unit
- **WHEN** the Animagine injector runs against the InstantID workflow
- **THEN** the graph's image loader is pointed at the uploaded filename, which is the face the identity signal is
  derived from

#### Scenario: one loader feeds both consumers in the img2img graph
- **Key:** `workflow-injection:photo-wiring:img2img-single-loader-fans-out`
- **Layers:** unit
- **WHEN** the Animagine injector runs against the img2img workflow, where one loader feeds both the latent
  encoder and the identity node
- **THEN** the single loader is wired to the uploaded file
- **AND** the exactly-one-loader invariant still holds, so the injector needs no img2img-specific branch

#### Scenario: one loader feeds the whole ControlNet stack
- **Key:** `workflow-injection:photo-wiring:controlnet-single-loader-across-stack`
- **Layers:** unit
- **WHEN** the Animagine injector runs against the ControlNet workflow
- **THEN** the single image loader is wired to the uploaded file across the entire stack

### Requirement: Prompt placement on the positive conditioning path

The system SHALL place the prompt on the **positive** conditioning encoder and no other, found by following the
sampler's positive link rather than by class lookup — the graphs carry a negative encoder of the same class, and
writing the prompt into it would invert the render's meaning.

#### Scenario: the Qwen prompt lands on the positive encoder only
- **Key:** `workflow-injection:prompt-placement:qwen-positive-encoder-only`
- **Layers:** unit
- **WHEN** the Qwen injector runs with a prompt
- **THEN** the encoder the sampler's positive input points at receives the prompt
- **AND** the negative encoder is left untouched

#### Scenario: the Animagine prompt lands on the positive encoder only
- **Key:** `workflow-injection:prompt-placement:animagine-positive-encoder-only`
- **Layers:** unit
- **WHEN** the Animagine injector runs with a prompt
- **THEN** only the positive encoder reached through the sampler's positive link receives it

#### Scenario: the img2img prompt lands on the positive encoder
- **Key:** `workflow-injection:prompt-placement:img2img-positive-encoder`
- **Layers:** unit
- **WHEN** the Animagine injector runs against the img2img workflow
- **THEN** the prompt reaches the positive encoder through the identity node in the conditioning path

#### Scenario: the trace walks through the ControlNet chain to the encoder
- **Key:** `workflow-injection:prompt-placement:traces-through-controlnet-chain`
- **Layers:** unit
- **WHEN** the Animagine injector runs against a graph whose positive path passes through a stack of ControlNet
  apply nodes before reaching the encoder
- **THEN** the trace follows the positive link through every intermediate node until it reaches the text encoder
- **AND** places the prompt there, so one generalised trace serves the whole InstantID family at any chain depth

### Requirement: img2img latent initialisation

The system SHALL initialise the img2img graph's latent from the photo rather than from noise, at a denoise
strength below one, so the photograph's composition survives into the render.

#### Scenario: the img2img graph inits its latent from the photo below full denoise
- **Key:** `workflow-injection:latent-init:img2img-inits-from-photo-below-one`
- **Layers:** unit
- **WHEN** the img2img workflow is inspected
- **THEN** its latent is encoded from the loaded photo rather than generated as empty noise
- **AND** the sampler's denoise is below one, which is the dial trading identity against style
