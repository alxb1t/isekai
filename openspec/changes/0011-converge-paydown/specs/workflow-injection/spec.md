## MODIFIED Requirements

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
