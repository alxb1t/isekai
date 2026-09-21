# Capability: `image-generation`

## Purpose

Stage ④ of the pipeline: a flow declaring what it needs and the dials it runs at, prompt assembly from
an approved sheet performed locally before any GPU is rented, and rendering with enough provenance that
an output identifies the configuration that produced it.

**Source:** `isekai/foundation/flow.py`, `isekai/pipeline/generate.py`, `isekai/shared/image.py`,
`flows/summon-v1/` ·
**Tests:** `tests/test_flow.py`, `tests/test_generate.py`, `tests/test_image.py`,
`tests/test_resume.py`

## Requirements

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

### Requirement: Assembly is pure, local and happens before the session opens

The system SHALL assemble every prompt from its approved sheet and its flow's dials without a network
call or a rented machine, SHALL write each assembled prompt as an artifact, and SHALL complete assembly
for the whole batch before acquiring any endpoint.

Assembly is free and rendering is not, so a malformed sheet should cost nothing rather than a boot and
several minutes. Doing the whole batch first is what turns that from a per-item saving into a
guarantee, and it makes the entirety of prompt construction testable offline.

#### Scenario: assembly needs no endpoint
- **Key:** `image-generation:assembly:assembly-is-local-and-free`
- **Layers:** unit
- **WHEN** prompts are assembled
- **THEN** no endpoint is contacted and no machine is acquired
- **AND** each assembled prompt is written as an artifact

#### Scenario: a malformed sheet is caught before anything is rented
- **Key:** `image-generation:assembly:bad-sheet-fails-before-the-session`
- **Layers:** unit
- **WHEN** one photograph's approved sheet cannot be assembled
- **THEN** the failure is reported before any endpoint is acquired
- **AND** the remaining photographs' prompts are still assembled

#### Scenario: the prompt is built from the sheet and the flow's dials only
- **Key:** `image-generation:assembly:prompt-comes-from-sheet-and-dials`
- **Layers:** unit
- **WHEN** a prompt is assembled
- **THEN** its content is the flow's declared fragments and the sheet's fields in the schema's order
- **AND** no text is taken from the graph's own committed strings

### Requirement: Only an approved sheet is rendered

The system SHALL render from an approved artifact only, and SHALL refuse a flow that has none, naming
the commands that would produce one.

The correction is the single largest measured gain in the pipeline. Rendering an unapproved draft would
silently spend money producing the result the correction exists to improve on, and would make the two
indistinguishable afterwards.

#### Scenario: an unapproved flow is refused
- **Key:** `image-generation:inputs:unapproved-flow-is-refused`
- **Layers:** unit
- **WHEN** a run has no approved artifact for a flow
- **THEN** rendering is refused naming that flow
- **AND** the message names the commands that would produce one

#### Scenario: every flow with an approved artifact renders
- **Key:** `image-generation:inputs:every-approved-flow-renders`
- **Layers:** unit
- **WHEN** a run has approved artifacts for more than one flow
- **THEN** each of them is rendered
- **AND** selecting among them requires no flag

### Requirement: Seeds are explicit or drawn, and an output is named by its seed

The system SHALL accept either a count of renders or an explicit list of seeds, SHALL NOT accept both,
SHALL draw seeds from an injectable source when given a count, and SHALL name each output by its seed
under its sheet version.

Naming the output by its seed is the reproducibility contract at the finest grain the system has: one
image, one integer. The two ways of asking are separate verbs — one explores, one reproduces — and
combining them has no meaning. Drawing from an injectable source is what keeps the suite deterministic
without making production output predictable.

#### Scenario: a count draws that many distinct seeds
- **Key:** `image-generation:seeds:count-draws-distinct-seeds`
- **Layers:** unit
- **WHEN** a count of renders is requested
- **THEN** that many distinct seeds are drawn from the injected source
- **AND** each render is named by the seed that produced it

#### Scenario: explicit seeds render exactly those
- **Key:** `image-generation:seeds:explicit-seeds-render-exactly-those`
- **Layers:** unit
- **WHEN** seeds are named explicitly
- **THEN** exactly those seeds are rendered
- **AND** no additional seed is drawn

#### Scenario: asking for both is refused
- **Key:** `image-generation:seeds:count-and-seeds-are-exclusive`
- **Layers:** unit
- **WHEN** both a count and explicit seeds are given
- **THEN** the invocation is refused
- **AND** the message states that the two are alternatives

#### Scenario: outputs are grouped under the sheet version they came from
- **Key:** `image-generation:seeds:outputs-carry-the-sheet-version`
- **Layers:** unit
- **WHEN** the same seed is rendered against two different approved versions
- **THEN** both renders exist
- **AND** neither overwrites the other

### Requirement: Rendering is idempotent per image

The system SHALL treat a render whose output already exists as complete, and SHALL decide that from the
output directory's contents rather than by re-rendering.

Rendering is the only step in the pipeline that costs money on every pass, so it is the one where
idempotence is worth the most. Deciding it from the directory keeps the rule the same as every other
stage's: a listing, never a parse.

#### Scenario: a named seed already rendered is skipped
- **Key:** `image-generation:idempotence:existing-seed-is-not-rerendered`
- **Layers:** unit
- **WHEN** an explicitly named seed's output already exists
- **THEN** it is not rendered again
- **AND** no endpoint call is made for it

#### Scenario: raising the count renders only the shortfall
- **Key:** `image-generation:idempotence:raising-count-renders-the-shortfall`
- **Layers:** unit
- **WHEN** a count larger than the number of existing renders is requested
- **THEN** only the difference is rendered
- **AND** the existing renders are untouched

### Requirement: The endpoint is reached through the existing transport seam

The system SHALL reach the rendering endpoint through the repository's existing transport interface, so
the whole stage is exercised by the offline suite with no GPU and no network.

The transport is already provider-neutral — HTTP to a host and a port, knowing nothing about who rents
the machine — and is already backed by a test double the existing suite runs against. Introducing a
second way to reach it would give the network boundary two implementations to keep in step.

#### Scenario: the suite renders through the double
- **Key:** `image-generation:transport:offline-double-drives-the-stage`
- **Layers:** unit
- **WHEN** the stage runs with the transport double in place
- **THEN** outputs and provenance are written
- **AND** no GPU and no network are reached

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

### Requirement: A render asks a flow which node roles it declares

The system SHALL require exactly four node roles of every flow — a positive conditioning node, a
negative conditioning node, a latent node and a sampler node — and SHALL refuse a flow declaring fewer
when the flow is loaded, before anything is executed. Every other node role SHALL be optional, and a
render SHALL patch only the roles the flow declares. The system SHALL NOT transfer an input a flow does
not declare. Where a role names both a transfer and a patch, the manifest's `inputs` and its `nodes`
SHALL agree about it, and a manifest declaring it under one and not the other SHALL be refused when the
flow is loaded, naming the flow and the key that is missing.

A flow declaring fewer roles used to pass the whole suite and fail on a rented GPU, after the
photograph had already been uploaded — which is the half of "a broken flow costs a test run, not a
boot" that was not true. Four roles are required because every image flow has them; the seven that are
not required include a photograph, an identity adapter and a pose preprocessor, which a sheet-only flow
does not have, and a hires resize and a hires sampler, which an ordinary cheaper flow does not have
either. Refusing at load rather than at render is what moves the failure from money to a test run.

The two gates over the photograph sit in different places — the transfer is gated on `inputs` and the
patch on `nodes` — so nothing holds them in agreement unless the manifest is checked. A flow naming the
photograph under `nodes` alone would upload nothing and leave the graph file's own committed filename in
the load node: a paid render of the wrong person, with the whole suite green. The mirror case transfers a
photograph no node reads. Identity preservation is the product, so a disagreement that can render
somebody else is refused before anything runs rather than inspected afterwards.

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

#### Scenario: a manifest whose inputs and nodes disagree is refused at load
- **Key:** `image-generation:roles:transferred-input-and-node-must-agree`
- **Layers:** unit
- **WHEN** a flow manifest declares the photograph under `nodes` but not under `inputs`, or under
  `inputs` but not under `nodes`
- **THEN** loading it is refused naming the flow and the key the declaration is missing from
- **AND** no endpoint is contacted, no photograph is transferred, and no render is submitted

#### Scenario: an input a flow does not declare is not transferred
- **Key:** `image-generation:roles:undeclared-input-is-not-uploaded`
- **Layers:** unit
- **WHEN** a flow that does not declare a photograph input is rendered
- **THEN** no photograph is transferred to the endpoint
- **AND** the render proceeds from the flow's own declared inputs

### Requirement: A manifest key this build does not know is refused, naming it

The system SHALL refuse to load a flow whose manifest carries any top-level key the build does not
recognise, naming the key. The refusal SHALL NOT require the flow to be executed.

The hosted-model block is optional and its absence means the default implementation, so a misspelled key
is indistinguishable from a deliberate omission: a flow meant to run one implementation would silently
run the other, producing a complete and correct-looking run on the wrong models. Every other way of
getting that block wrong is already caught — an unknown implementation has no entry to resolve, and an
unreachable one refuses at first call — which leaves the typo as the only silent path, and an allowlist
is the only thing that closes it. The loader already refuses a missing key, a manifest that calls itself
something else, an absent sibling file and a missing node role; an unknown key is that same shape.

#### Scenario: an unrecognised manifest key is refused naming it
- **Key:** `image-generation:manifest:unknown-key-is-refused`
- **Layers:** unit
- **WHEN** a flow manifest carries a top-level key the build does not recognise
- **THEN** loading it is refused naming that key
- **AND** the refusal does not require the flow to be executed

#### Scenario: a misspelled hosted-model block does not fall through to the default
- **Key:** `image-generation:manifest:misspelled-hosted-block-is-refused`
- **Layers:** unit
- **WHEN** a flow manifest carries a near-miss spelling of the hosted-model key
- **THEN** loading it is refused naming the key it carries
- **AND** the flow is not loaded as though it had declared no block at all

### Requirement: A flow may declare the hosted models it calls

The system SHALL permit a flow manifest to declare, in one optional block, the implementation its
hosted-model stages are reached through and the model name each of them runs. A manifest that declares no
such block SHALL use the build's default implementation, which is the behaviour of every flow written before
this key existed. A flow SHALL declare one implementation for every hosted-model stage it has, not one per
stage. A key in the block that no stage reads SHALL be loaded and SHALL NOT be required to name a stage that
exists.

The block is separate from the models a flow's render is pinned to, and the separation is the point: one
names what a rented GPU loads and is pinned by digest, the other names what the hosted-model stages call
over a network. Declaring the implementation once rather than per stage makes "this flow is wholly one
implementation" a property of the document rather than of two independent lookups that happen to agree — a
flow that mixed them would be a configuration nobody asked for, and the flow is the unit of freeze precisely
so that a configuration is named rather than assembled.

Making the block optional is what keeps a version that introduces a second implementation from editing the
flows that predate it. A frozen flow's identifier means one configuration, and re-cutting two manifests to
add a key whose value was already implied would change two committed digests to record no change in
behaviour.

**The same argument is why a key outlives the stage that read it.** The stage that fills a sheet no longer
calls a hosted model, so the `sorter` key names nothing — and deleting it would move a committed digest,
which this repository's rules make a new flow rather than an edit. The block therefore carries it unread.
That is not a wart: it is the immutability rule holding under a deletion, and it is what lets the arm be
removed without the flow set being replaced in the same version.

#### Scenario: a flow declaring hosted models is loaded with them
- **Key:** `image-generation:hosted:flow-declares-its-hosted-models`
- **Layers:** unit
- **WHEN** a flow manifest declares an implementation and a model name for each key in the block
- **THEN** the loaded flow carries that implementation and every model name
- **AND** no value in the block is derived at load time

#### Scenario: a flow declaring no hosted models keeps the default implementation
- **Key:** `image-generation:hosted:absent-block-means-the-default`
- **Layers:** unit
- **WHEN** a flow manifest declares no hosted-model block
- **THEN** the loaded flow reports none
- **AND** loading it is not refused for the omission

#### Scenario: the flows written before this key are byte-identical
- **Key:** `image-generation:hosted:incumbent-flows-are-unchanged`
- **Layers:** unit
- **WHEN** the suite runs
- **THEN** every flow that predates this key has the digest it had before
- **AND** the manifest format version is unchanged

#### Scenario: a key no stage reads is loaded and does not move a digest
- **Key:** `image-generation:hosted:an-unread-key-is-carried`
- **Layers:** unit
- **WHEN** a flow's hosted block declares a model for a stage that reaches no hosted model
- **THEN** the flow loads and the key is carried
- **AND** the flow's manifest digest is the digest it had before the stage stopped reading it
