## MODIFIED Requirements

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

## ADDED Requirements

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

#### Scenario: the photo is scaled before any consumer reads it
- **Key:** `workflow-injection:working-resolution:scale-precedes-every-consumer`
- **Layers:** unit
- **WHEN** the shipped workflow is inspected
- **THEN** a scaling node sits between the image loader and every node that reads the photo — the
  latent encoder, the identity node and each ControlNet preprocessor
- **AND** no consumer reads the loader directly, so one pixel grid feeds the whole graph and no
  control hint is registered against a different one

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
- **WHEN** the photo records a rotation that transposes it
- **THEN** the dimensions derived are the transposed ones the loader will present
- **AND** a photo recording no rotation, or one that only flips it, is measured as its header states,
  because the scale node scales to the exact target given rather than fitting to it — so a target
  computed against the untransposed size would squash the photo non-uniformly with nothing reporting it

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
