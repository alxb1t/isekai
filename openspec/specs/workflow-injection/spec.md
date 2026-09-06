# Capability: `workflow-injection`

Wiring the uploaded photo and the text prompt into a ComfyUI workflow graph before it is queued — locating the
nodes that need editing, and setting the right inputs on exactly the right ones.

**Source:** `isekai/workflow.py` · **Tests:** `tests/test_workflow_injection.py`

Injection is **separate from mutation**: injection wires *image + prompt*, mutation varies *dials*. Each model
family owns an injection adapter, but the adapters share a node-locating primitive and the InstantID family
shares one generalised conditioning trace.

## Requirements

### Requirement: The positive prompt is graph configuration

The system SHALL commit the positive prompt to the workflow graph and SHALL expose no way to set it
from the command line — the prompt is the highest-leverage input to a Danbooru-trained base, and a
value a human retypes each run makes every render unattributable. It is configuration, in the same
category as `steps` and `cfg`.

The committed string SHALL assert no attribute of the person in the photo. Attributes the photo
already carries are the business of the mechanisms that read it: pose belongs to the OpenPose
ControlNet, and gender is a documented semantic of the face embedding the identity node computes. A
tag asserting one of them overrides the photo for every input that disagrees with it.

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

#### Scenario: the committed string asserts no gender
- **Key:** `workflow-injection:committed-prompt:asserts-no-gender`
- **Layers:** unit
- **WHEN** the pinned positive string is read
- **THEN** it contains no tag asserting the subject's gender
- **AND** the single-subject mode selector the base needs is carried by a tag that names no gender,
  so the register still selects the mode without deciding who the photo is of

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

### Requirement: The photo is scaled to a working resolution

The system SHALL scale the photo to a working resolution before any node reads it, and SHALL derive
that resolution from the photo's own dimensions. Without it the render happens at whatever size the
input happened to be, so "the path runs" is a claim about the photos that were tried rather than
about the path.

The dimensions it derives SHALL be the ones the image loader will present, which are not always the
ones the file's frame header states: a photo taken upright on a phone is stored rotated with a tag
recording the rotation, and the loader applies that tag before any node sees the pixels. It SHALL
also read those dimensions however deep in the file the header sits, because an ordinary camera
writes a thumbnail, a colour profile and rights metadata ahead of it.

The target SHALL preserve the photo's aspect ratio, place its short side at the base family's
working scale, and keep both dimensions a multiple of 64. A short side chosen this way holds for
every aspect ratio, which a target expressed as a total pixel count does not: at a fixed megapixel
budget a wide photo falls below the floor its line-art ControlNet requires, and nothing in the run
would say so.

Because a short-side rule places no bound on the other axis and a header field is an unverified
number, the system SHALL state every ceiling it enforces rather than leaving one implied. It SHALL
refuse a photo whose aspect ratio would drive the long side past a stated bound, refuse a header
declaring a dimension past a stated maximum, and stop reading a file's header past a stated byte
budget — each with a message naming the file and the limit. An unbounded target reaches a metered
GPU as an allocation failure partway through a render rather than as a refusal at the command line,
and a limit the operator cannot read is not a limit they can work around.

#### Scenario: the photo is scaled before any consumer reads it
- **Key:** `workflow-injection:working-resolution:scale-precedes-every-consumer`
- **Layers:** unit
- **WHEN** the shipped workflow is inspected
- **THEN** a scaling node sits between the image loader and every node that reads the photo — the
  latent encoder, the identity node and each ControlNet preprocessor
- **AND** no consumer reads the loader directly, so every node is handed the same scaled image
- **AND** this is a claim about which image each consumer receives and not about what a consumer
  then does with it internally: a preprocessor's own working resolution is a separate dial on that
  node, and one of them derives its hint below the graph's scale today

#### Scenario: the target preserves aspect and places the short side at the working scale
- **Key:** `workflow-injection:working-resolution:short-side-at-the-working-scale`
- **Layers:** unit
- **WHEN** dimensions are computed for a photo of a given size
- **THEN** the result preserves the photo's aspect ratio to within one rounding step, its short side
  is the working scale, and both dimensions are multiples of 64
- **AND** this holds for landscape, portrait and square inputs alike

#### Scenario: a photo below the working scale is scaled up
- **Key:** `workflow-injection:working-resolution:small-photos-are-scaled-up`
- **Layers:** unit
- **WHEN** the photo's short side is below the working scale
- **THEN** the computed target is larger than the photo
- **AND** scaling is therefore not a ceiling but a normalisation, because a photo below the base's
  trained scale renders as badly as one far above it

#### Scenario: the computed dimensions are written into the graph
- **Key:** `workflow-injection:working-resolution:dimensions-are-written-by-injection`
- **Layers:** unit
- **WHEN** injection runs against a photo
- **THEN** the scaling node's width and height carry the computed values
- **AND** they are computed by injection rather than by the graph, because no node available to this
  pipeline can derive a target from the image it is given

#### Scenario: a rotated photo is measured as it will be loaded
- **Key:** `workflow-injection:working-resolution:orientation-is-honoured`
- **Layers:** unit
- **WHEN** the photo records a rotation that transposes it, **in either supported codec**
- **THEN** the dimensions derived are the transposed ones the loader will present
- **AND** a photo recording no rotation, or one that only flips it, is measured as its header states,
  because the scale node scales to the exact target given rather than fitting to it — so a target
  computed against the untransposed size would squash the photo non-uniformly with nothing reporting it
- **AND** the rule holds wherever the codec puts the tag, because the loader reads it from both and
  the mismatch this prevents is a property of the loader rather than of the container: a rule applied
  to one codec and not the other leaves the defect open in whichever codec the project actually feeds
  it, while looking closed

#### Scenario: a photo whose frame header sits behind large metadata is still read
- **Key:** `workflow-injection:working-resolution:a-deep-header-is-still-read`
- **Layers:** unit
- **WHEN** the photo carries metadata larger than any fixed prefix ahead of its frame header
- **THEN** its dimensions are still read and the run proceeds
- **AND** the refusal is reserved for a file that genuinely has no readable frame header, because a
  valid camera photo refused as unreadable is a false report of a defect in the input

#### Scenario: a photo whose dimensions cannot be read is refused
- **Key:** `workflow-injection:working-resolution:unreadable-dimensions-are-refused`
- **Layers:** unit
- **WHEN** the photo is not a format whose dimensions can be read, or its header is truncated
- **THEN** the run stops with a message naming the file
- **AND** it does not fall back to a default size, because a silently wrong resolution is a wrong
  render rather than an error

#### Scenario: a photo whose aspect ratio drives the target past the long-side bound is refused
- **Key:** `workflow-injection:working-resolution:an-extreme-aspect-ratio-is-refused`
- **Layers:** unit
- **WHEN** placing the photo's short side at the working scale would put its long side past the
  stated bound
- **THEN** the run stops with a message naming the file, both computed dimensions and the bound
- **AND** it does not clamp the target instead, because a clamped target no longer preserves the
  aspect ratio and would squash the photo in the way the orientation rule exists to prevent

#### Scenario: a header declaring an impossible dimension is refused
- **Key:** `workflow-injection:working-resolution:an-out-of-range-header-dimension-is-refused`
- **Layers:** unit
- **WHEN** a header declares a dimension past the stated maximum
- **THEN** the run stops with a message naming the file and the maximum, before any target is
  computed from it
- **AND** the maximum is the same for every format the system reads, so a file is not accepted in one
  codec and refused in another for a dimension neither can render

#### Scenario: a file whose header walk exceeds the byte budget is refused
- **Key:** `workflow-injection:working-resolution:an-unbounded-header-walk-is-refused`
- **Layers:** unit
- **WHEN** reading a file's header consumes more than the stated byte budget without reaching a frame
  header
- **THEN** the run stops with a message naming the file and the budget
- **AND** the budget is generous enough for any camera's metadata, so this bounds the work a
  malformed or hostile file can demand without refusing a valid one
</content>

### Requirement: The base's CLIP layer is committed to the graph

The system SHALL commit the CLIP layer at which conditioning is taken, rather than inheriting the
loader's default. It is configuration of the same kind as the prompt: the base family's publisher
generates at a specific layer, and a graph that does not set it ships a configuration the publisher
never tested while looking identical to one that does.

#### Scenario: conditioning is taken from the layer the base family expects
- **Key:** `workflow-injection:clip-layer:conditioning-stops-at-the-expected-layer`
- **Layers:** unit
- **WHEN** the shipped workflow is inspected
- **THEN** a node sets the CLIP layer, and both text encoders take their CLIP through it rather than
  from the checkpoint loader directly
- **AND** the value it sets is pinned by the suite, so changing it is a deliberate test edit
