## ADDED Requirements

### Requirement: The render target is derived from the photograph's own header

The system SHALL derive the render target from the photograph's own dimensions before any node reads
it, and SHALL scale the photograph to that target. Without it the render happens at whatever size the
input happened to be, so "the path runs" is a claim about the photographs that were tried rather than
about the path.

What the target buys is the photograph's **aspect ratio**; its magnitude is discarded. The target SHALL
preserve that aspect ratio, place the short side at the base family's working scale, and keep both
dimensions a multiple of the latent stride. A short side chosen this way holds for every aspect ratio,
which a target expressed as a total pixel count does not: at a fixed megapixel budget the short side
moves with the aspect ratio, so a wide photograph lands below the base's trained scale while a squarer
one clears it — a failure that varies by input and reports nothing.

The dimensions it derives SHALL be the ones the image loader will present, which are not always the
ones the file's frame header states: a photograph taken upright on a phone is stored rotated with a tag
recording the rotation, and the loader applies that tag before any node sees the pixels. It SHALL also
read those dimensions however deep in the file the header sits, because an ordinary camera writes a
thumbnail, a colour profile and rights metadata ahead of it.

Because a short-side rule places no bound on the other axis and a header field is an unverified number,
the system SHALL state every ceiling it enforces rather than leaving one implied, and SHALL refuse
rather than clamp. A refusal SHALL be recoverable per photograph rather than terminating the process,
because a batch holds many photographs and one unreadable header must not cost the others their
session.

#### Scenario: the photograph is scaled before any consumer reads it
- **Key:** `image-generation:working-resolution:scale-precedes-every-consumer`
- **Layers:** unit
- **WHEN** a tracked flow's graph is inspected
- **THEN** a scaling node sits between the image loader and every node that reads the photograph — the
  identity node and each ControlNet preprocessor
- **AND** no consumer reads the loader directly, so every node is handed the same scaled image
- **AND** this is a claim about which image each consumer receives and not about what a consumer then
  does with it internally: a preprocessor's own working resolution is a separate dial on that node

#### Scenario: the target preserves aspect and places the short side at the working scale
- **Key:** `image-generation:working-resolution:short-side-at-the-working-scale`
- **Layers:** unit
- **WHEN** a target is computed for a photograph of a given size
- **THEN** the result preserves the photograph's aspect ratio to within one rounding step, its short
  side is the working scale, and both dimensions are multiples of the latent stride
- **AND** this holds for landscape, portrait and square inputs alike

#### Scenario: the dimensions come from the photograph's own frame header
- **Key:** `image-generation:working-resolution:dimensions-come-from-the-header`
- **Layers:** unit
- **WHEN** a photograph in either supported codec is measured
- **THEN** the dimensions derived are the ones its own frame header states, for a landscape, a portrait
  and a square photograph alike
- **AND** they are read from the photograph rather than declared alongside it, because no node
  available to this pipeline can derive a target from the image it is handed — so a dimension the
  system does not read is a dimension nothing supplies

#### Scenario: a photograph below the working scale is scaled up
- **Key:** `image-generation:working-resolution:small-photos-are-scaled-up`
- **Layers:** unit
- **WHEN** the photograph's short side is below the working scale
- **THEN** the computed target is larger than the photograph
- **AND** scaling is therefore not a ceiling but a normalisation, because a photograph below the base's
  trained scale renders as badly as one far above it

#### Scenario: a rotated photograph is measured as it will be loaded
- **Key:** `image-generation:working-resolution:orientation-is-honoured`
- **Layers:** unit
- **WHEN** the photograph records a rotation that transposes it, **in either supported codec**
- **THEN** the dimensions derived are the transposed ones the loader will present
- **AND** a photograph recording no rotation, or one that only flips it, is measured as its header
  states, because the scale node scales to the exact target given rather than fitting to it — so a
  target computed against the untransposed size would squash the photograph non-uniformly with nothing
  reporting it
- **AND** the rule holds wherever the codec puts the tag, because the loader reads it from both and the
  mismatch this prevents is a property of the loader rather than of the container

#### Scenario: a photograph whose frame header sits behind large metadata is still read
- **Key:** `image-generation:working-resolution:a-deep-header-is-still-read`
- **Layers:** unit
- **WHEN** the photograph carries metadata larger than any fixed prefix ahead of its frame header
- **THEN** its dimensions are still read and the render proceeds
- **AND** the refusal is reserved for a file that genuinely has no readable frame header, because a
  valid camera photograph refused as unreadable is a false report of a defect in the input

#### Scenario: a photograph whose dimensions cannot be read is refused
- **Key:** `image-generation:working-resolution:unreadable-dimensions-are-refused`
- **Layers:** unit
- **WHEN** the photograph is not a format whose dimensions can be read, or its header is truncated
- **THEN** that photograph is refused with a message naming the file
- **AND** no default size is substituted, because a silently wrong resolution is a wrong render rather
  than an error

#### Scenario: a photograph whose aspect ratio drives the target past the long-side bound is refused
- **Key:** `image-generation:working-resolution:an-extreme-aspect-ratio-is-refused`
- **Layers:** unit
- **WHEN** placing the photograph's short side at the working scale would put its long side past the
  stated bound
- **THEN** that photograph is refused with a message naming the file, both computed dimensions and the
  bound
- **AND** the target is not clamped instead, because a clamped target no longer preserves the aspect
  ratio and would squash the photograph in the way the orientation rule exists to prevent

#### Scenario: a header declaring an impossible dimension is refused
- **Key:** `image-generation:working-resolution:an-out-of-range-header-dimension-is-refused`
- **Layers:** unit
- **WHEN** a header declares a dimension past the stated maximum
- **THEN** that photograph is refused with a message naming the file and the maximum, before any target
  is computed from it
- **AND** the maximum is the same for every format the system reads, so a file is not accepted in one
  codec and refused in another for a dimension neither can render

#### Scenario: a file whose header walk exceeds the byte budget is refused
- **Key:** `image-generation:working-resolution:an-unbounded-header-walk-is-refused`
- **Layers:** unit
- **WHEN** reading a file's header consumes more than the stated byte budget without reaching a frame
  header
- **THEN** that photograph is refused with a message naming the file and the budget
- **AND** the budget is generous enough for any camera's metadata, so this bounds the work a malformed
  or hostile file can demand without refusing a valid one

#### Scenario: one unusable photograph does not end the batch
- **Key:** `image-generation:working-resolution:a-refusal-is-per-photograph`
- **Layers:** unit
- **WHEN** one photograph in a batch is refused for any of the reasons above
- **THEN** the remaining photographs are still rendered and the refusal is reported against its own
  photograph
- **AND** the process is not terminated, because the endpoint is already rented by the time the batch
  runs and a terminating refusal takes every other photograph with it

### Requirement: A seed is drawn at full width

The system SHALL draw a seed across the full width the sampler accepts rather than a narrower range.

An output is named by the seed that produced it, so the seed space is the reproducibility contract at
its finest grain. Narrowing it raises the rate at which a drawn seed collides with one already on disk,
which is the condition the drawing rule already guards against.

#### Scenario: a drawn seed spans the full width
- **Key:** `image-generation:seeds:seeds-are-drawn-at-full-64-bit-width`
- **Layers:** unit
- **WHEN** a seed is drawn from the injected source
- **THEN** it is drawn across the full 64-bit space
- **AND** the width is stated in one place rather than repeated as a literal at each draw
