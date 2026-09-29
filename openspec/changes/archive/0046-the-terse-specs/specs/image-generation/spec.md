## MODIFIED Requirements

### Requirement: A flow is pinned by equality; changing any file in it is an explicit act

The system SHALL hold each tracked flow against a committed digest computed over every file in its
directory, so that altering a dial, a prompt fragment, the graph, the schema or either briefing fails the
suite naming the flow. Re-pinning SHALL be possible only as a deliberate edit to the committed digest, in
a change that states what moved and why.

The freeze makes nothing change silently; it does not stop change. Where the old configuration is still wanted — a
variant, another base, a second generation — the answer is a new flow, because two flows are compared only while an
identifier means one configuration ([D15](../../../docs/decisions.md#d15--a-flow-is-named-for-what-it-is)). Where it
is abandoned, a re-pin records what moved in one place, and each sheet, prompt and render records the flow's digest,
so it shows which side of a re-pin it falls on.

#### Scenario: editing any file in a tracked flow fails the suite
- **Key:** `image-generation:immutability:flow-manifest-is-pinned-by-equality`
- **Layers:** unit
- **WHEN** any file in a tracked flow directory differs from its committed digest
- **THEN** the suite fails naming the flow

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
- **THEN** its provenance records the flow identifier, the flow's digest, the seed, the sheet it came from
  and the digest of the submitted graph
- **AND** two renders from the same flow identifier with different graphs are distinguishable

#### Scenario: a re-pin states what moved
- **Key:** `image-generation:immutability:a-re-pin-is-recorded`
- **Layers:** unit
- **WHEN** a tracked flow's committed digest is changed
- **THEN** every tracked flow still matches its committed digest
- **AND** the change that moved it records which flow moved and what changed in it

### Requirement: Only an approved sheet is rendered

The system SHALL render from an approved artifact only, and SHALL refuse a flow that has none, naming
the commands that would produce one.

A person's correction is what the render is for
([D33](../../../docs/decisions.md#d33--the-operator-decides-what-is-rendered)). Rendering an unapproved draft spends
money on the result the correction exists to improve, and leaves the two indistinguishable afterwards.

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

### Requirement: The endpoint is reached through the existing transport seam

The system SHALL reach the rendering endpoint through the repository's existing transport interface, so
the whole stage is exercised by the offline suite with no GPU and no network.

The transport is provider-neutral — HTTP to a host and a port — and backed by a test double. A second way to
reach the endpoint would give the network boundary two implementations to keep in step.

#### Scenario: the suite renders through the double
- **Key:** `image-generation:transport:offline-double-drives-the-stage`
- **Layers:** unit
- **WHEN** the stage runs with the transport double in place
- **THEN** outputs and provenance are written
- **AND** no GPU and no network are reached

### Requirement: The render target is derived from the photograph's own header

The system SHALL derive the render target from the photograph's own dimensions before any node reads it,
and SHALL scale the photograph to that target. The target SHALL preserve the photograph's aspect ratio, place its
short side at the base family's working scale, and keep both dimensions a multiple of the latent stride. The
dimensions SHALL be the ones the image loader will present, after any rotation the file records, read however deep
in the file the frame header sits. The system SHALL state every ceiling it enforces, SHALL refuse rather than
clamp, and SHALL refuse one photograph without terminating the process.

```
photograph ─▶ frame header ─▶ recorded rotation ─▶ target ─▶ scale node ─┬─▶ identity node
              (at any depth)   (as the loader)                           └─▶ each ControlNet preprocessor
```

Without a target, "the path runs" is a claim about the photographs tried, not about the path. A short side holds for
every aspect ratio; a fixed pixel count puts a wide photograph below the base's trained scale and reports nothing.
No node can derive a target from the image it is handed, and the scale node scales to the exact target, so a size
read before rotation squashes the photograph unreported. A clamp would distort the aspect ratio
([D11](../../../docs/decisions.md#d11--the-photograph-is-scaled-once)), and a refusal that ended the process would
cost every other photograph its rented session.

#### Scenario: the photograph is scaled before any consumer reads it
- **Key:** `image-generation:working-resolution:scale-precedes-every-consumer`
- **Layers:** unit
- **WHEN** a tracked flow's graph is inspected
- **THEN** a scaling node sits between the image loader and every node that reads the photograph — the
  identity node and each ControlNet preprocessor
- **AND** no consumer reads the loader directly, so every node is handed the same scaled image
- **AND** a preprocessor's own working resolution stays a separate dial on that node

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
- **AND** they are read from the photograph rather than declared alongside it

#### Scenario: a photograph below the working scale is scaled up
- **Key:** `image-generation:working-resolution:small-photos-are-scaled-up`
- **Layers:** unit
- **WHEN** the photograph's short side is below the working scale
- **THEN** the computed target is larger than the photograph

#### Scenario: a rotated photograph is measured as it will be loaded
- **Key:** `image-generation:working-resolution:orientation-is-honoured`
- **Layers:** unit
- **WHEN** the photograph records a rotation that transposes it, in either supported codec
- **THEN** the dimensions derived are the transposed ones the loader will present
- **AND** a photograph recording no rotation, or one that only flips it, is measured as its header states
- **AND** the rule holds wherever the codec puts the tag

#### Scenario: a photograph whose frame header sits behind large metadata is still read
- **Key:** `image-generation:working-resolution:a-deep-header-is-still-read`
- **Layers:** unit
- **WHEN** the photograph carries metadata larger than any fixed prefix ahead of its frame header
- **THEN** its dimensions are still read and the render proceeds
- **AND** only a file with no readable frame header is refused as unreadable

#### Scenario: a photograph whose dimensions cannot be read is refused
- **Key:** `image-generation:working-resolution:unreadable-dimensions-are-refused`
- **Layers:** unit
- **WHEN** the photograph is not a format whose dimensions can be read, or its header is truncated
- **THEN** that photograph is refused with a message naming the file
- **AND** no default size is substituted

#### Scenario: a photograph whose aspect ratio drives the target past the long-side bound is refused
- **Key:** `image-generation:working-resolution:an-extreme-aspect-ratio-is-refused`
- **Layers:** unit
- **WHEN** placing the photograph's short side at the working scale would put its long side past the
  stated bound
- **THEN** that photograph is refused with a message naming the file, both computed dimensions and the bound
- **AND** the target is not clamped instead

#### Scenario: a header declaring an impossible dimension is refused
- **Key:** `image-generation:working-resolution:an-out-of-range-header-dimension-is-refused`
- **Layers:** unit
- **WHEN** a header declares a dimension past the stated maximum
- **THEN** that photograph is refused with a message naming the file and the maximum, before any target
  is computed from it
- **AND** the maximum is the same for every format the system reads

#### Scenario: a file whose header walk exceeds the byte budget is refused
- **Key:** `image-generation:working-resolution:an-unbounded-header-walk-is-refused`
- **Layers:** unit
- **WHEN** reading a file's header consumes more than the stated byte budget without reaching a frame
  header
- **THEN** that photograph is refused with a message naming the file and the budget
- **AND** the budget holds any camera's metadata

#### Scenario: one unusable photograph does not end the batch
- **Key:** `image-generation:working-resolution:a-refusal-is-per-photograph`
- **Layers:** unit
- **WHEN** one photograph in a batch is refused for any of the reasons above
- **THEN** the remaining photographs are still rendered and the refusal is reported against its own
  photograph
- **AND** the process is not terminated

### Requirement: A render asks a flow which node roles it declares

The system SHALL require exactly four node roles of every flow — a positive conditioning node, a
negative conditioning node, a latent node and a sampler node — and SHALL refuse a flow declaring fewer
when the flow is loaded, before anything is executed. Every other node role SHALL be optional, and a
render SHALL patch only the roles the flow declares. The system SHALL NOT transfer an input a flow does
not declare. Where a role names both a transfer and a patch, the manifest's `inputs` and its `nodes`
SHALL agree about it, and a manifest declaring it under one and not the other SHALL be refused when the
flow is loaded, naming the flow and the key that is missing.

Refusing at load moves a broken flow's failure from a rented GPU to a test run. Every image flow has the required
roles; a sheet-only flow has no photograph, identity adapter or pose preprocessor, and a cheaper flow no hires
pass. The transfer is gated on `inputs` and the patch on `nodes`, so only the load check holds them together: a
photograph under `nodes` alone uploads nothing and renders the graph's own committed filename — somebody else, with
the suite green.

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

### Requirement: A flow is a flat directory of named files whose manifest declares and never computes

The system SHALL define a flow as a directory containing exactly the manifest and its named siblings — a
graph, a schema and a caption briefing — all of them directly in that directory, with no sub-directory
and no other file. The manifest SHALL declare its required inputs, the vocabulary and the models its
render is pinned to, the model its hosted stages run, whether it needs the tagger, its node roles, its
prompt fragments and its dials. The manifest SHALL NOT name any of its sibling files, SHALL declare the
version of its own format, and SHALL contain no computed or conditional value.

```
flows/<id>/
├── flow.json              the manifest
├── graph.json
├── schema.json
└── caption.briefing.md
```

A manifest that computes nothing is checkable without running anything, so a broken flow fails the suite, not a
boot. The briefing and the schema shape the image, so they sit inside the freeze, and the digest covers regular
files only, so a nested file would escape it ([D14](../../../docs/decisions.md#d14--a-flow-is-one-flat-directory)).
A key that can hold only one value is not a declaration, so the manifest names no filename.

#### Scenario: a flow holds the manifest and its named siblings, and nothing else
- **Key:** `image-generation:manifest:a-flow-is-flat-and-its-files-are-named`
- **Layers:** unit
- **WHEN** a tracked flow directory is read
- **THEN** it holds exactly a manifest, a graph, a schema and a caption briefing, each directly in the
  directory
- **AND** the manifest declares no filename for any of them
- **AND** the directory contains no sub-directory and no further file

#### Scenario: a flow declares its inputs, vocabulary, models and dials
- **Key:** `image-generation:manifest:flow-declares-its-inputs`
- **Layers:** unit
- **WHEN** a flow manifest is loaded
- **THEN** it names its required inputs, its vocabulary, its models, whether it needs the tagger, its node
  roles and every dial the render uses
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
- **AND** the schema, the caption briefing and the graph each one needs are present in its own directory

#### Scenario: an invalid manifest is refused naming the field
- **Key:** `image-generation:manifest:invalid-manifest-names-the-field`
- **Layers:** unit
- **WHEN** a flow manifest is missing or malformed in a declared field
- **THEN** loading it is refused naming that field
- **AND** the refusal does not require the flow to be executed

### Requirement: Every flow declares the model its hosted stages run

The system SHALL require every flow manifest to declare, in one top-level key, the model its hosted
stages run. It SHALL refuse a manifest that declares none, and SHALL refuse one whose value is not a
non-empty string, naming the key in both cases. It SHALL derive no part of that value at load time.

The key is a bare string, not a block: with one arm there is no choice to hold
([D5](../../../docs/decisions.md#d5--one-arm)), and the loader's allowlist of top-level keys catches a misspelling.
It is separate from the render's models, which a rented GPU loads by digest; this one the local runtime is asked for
by alias. One key, not one per stage, makes *this flow is wholly one model* a property of the document — the reader
and the hosted tagger share an alias, so two prompts reach one model framed alike.

#### Scenario: a flow declares the model it runs
- **Key:** `image-generation:model:flow-declares-the-model-it-runs`
- **Layers:** unit
- **WHEN** a flow manifest is loaded
- **THEN** the loaded flow carries the model name its manifest declares
- **AND** no part of that value is derived at load time

#### Scenario: a manifest declaring no model is refused
- **Key:** `image-generation:model:an-absent-model-is-refused`
- **Layers:** unit
- **WHEN** a flow manifest declares no model
- **THEN** loading it is refused naming the key
- **AND** the refusal does not require the flow to be executed

#### Scenario: a model that is not a non-empty string is refused
- **Key:** `image-generation:model:an-empty-model-is-refused`
- **Layers:** unit
- **WHEN** a flow manifest declares a model that is absent of characters or is not a string
- **THEN** loading it is refused naming the key
- **AND** the value is not coerced into a string

### Requirement: An unrecognised manifest key is refused, naming what it carries

The system SHALL refuse to load a flow whose manifest carries any top-level key the build does not
recognise, naming the key. The refusal SHALL NOT require the flow to be executed.

Every declared key is required, so a misspelt key is two failures: the key the build reads is absent, and a key it
does not read is present. A manifest carrying `modl` and no `model`, refused for the absence alone, sends the
operator to add a second key rather than fix the one they wrote.

#### Scenario: an unrecognised manifest key is refused naming it
- **Key:** `image-generation:manifest:unknown-key-is-refused`
- **Layers:** unit
- **WHEN** a flow manifest carries a top-level key the build does not recognise
- **THEN** loading it is refused naming that key
- **AND** the refusal does not require the flow to be executed

#### Scenario: a misspelled model key is refused naming what it carries
- **Key:** `image-generation:manifest:a-misspelled-model-key-is-refused`
- **Layers:** unit
- **WHEN** a flow manifest carries a near-miss spelling of the model key
- **THEN** loading it is refused naming the key it carries
- **AND** the refusal names the unrecognised key rather than only the absent one

### Requirement: A failure is recorded as the kind it was, and one flow's failure is its own

The system SHALL record a failure to reach an endpoint as transient rather than permanent, and SHALL
assemble each selected flow independently, so that one flow whose sheet cannot be assembled does not
prevent another from being assembled or rendered.

A transient record says trying again may succeed
([D21](../../../docs/decisions.md#d21--retries-follow-what-can-fail)). At the render the kind changes nothing: its
budget is one attempt, so a record of either kind refuses the next render until the operator deletes it. A flow is a
unit, as a photograph is: one flow's malformed sheet must not leave another unrenderable.

#### Scenario: an unreachable endpoint is recorded transient
- **Key:** `image-generation:failure:an-unreachable-endpoint-is-transient`
- **Layers:** unit
- **WHEN** a render fails because the endpoint cannot be reached
- **THEN** the failure record names the failure as transient
- **AND** a later invocation of that stage refuses on the record, naming it, until the record is deleted

#### Scenario: one flow's malformed sheet does not cost its siblings their assembly
- **Key:** `image-generation:assembly:a-bad-sheet-is-per-flow`
- **Layers:** unit
- **WHEN** an invocation selects more than one flow and one flow's approved sheet cannot be assembled
- **THEN** the other selected flows are still assembled
- **AND** the failure is reported naming the flow it belongs to

#### Scenario: a graph the endpoint rejects is recorded permanent
- **Key:** `image-generation:failure:a-rejected-graph-is-permanent`
- **Layers:** unit
- **WHEN** the endpoint answers a render's request with a client error
- **THEN** the failure record names the failure as permanent
- **AND** the refusal names the status and the endpoint's own error, and not the tunnel

#### Scenario: an endpoint's server error is recorded transient
- **Key:** `image-generation:failure:a-server-error-is-transient`
- **Layers:** unit
- **WHEN** the endpoint answers a render's request with a server error
- **THEN** the failure record names the failure as transient
- **AND** the refusal names the status and points at the endpoint's own log

#### Scenario: a failed upload is recorded
- **Key:** `image-generation:failure:a-failed-upload-is-recorded`
- **Layers:** unit
- **WHEN** the photograph's upload to the endpoint fails
- **THEN** a failure record is written for that render
- **AND** a later invocation of that stage refuses on the record, naming it, until the record is deleted

### Requirement: Every flow declares whether it needs the tagger

The system SHALL require every flow manifest to declare, in one top-level key, whether the flow needs the
tagger, as a boolean. It SHALL refuse a manifest that declares none, and SHALL refuse one whose value is
not a boolean, naming the key in both cases. It SHALL derive no part of that value at load time.

Flows differ in whether they are tagged, so the manifest declares it: the tag verb refuses a flow that declares no
tagger, and the sheet stage fills its sheet empty
([D31](../../../docs/decisions.md#d31--a-flow-declares-whether-it-is-tagged)). A boolean, not a list: the tag verb
runs both taggers together. A value that is not a boolean is refused, not coerced — a `"false"` read as true would
tag a flow that needs none.

#### Scenario: a flow declares whether it needs the tagger
- **Key:** `image-generation:tagger:flow-declares-whether-it-is-tagged`
- **Layers:** unit
- **WHEN** a flow manifest is loaded
- **THEN** the loaded flow carries the value its manifest declares
- **AND** no part of that value is derived at load time

#### Scenario: a manifest declaring nothing about the tagger is refused
- **Key:** `image-generation:tagger:an-absent-declaration-is-refused`
- **Layers:** unit
- **WHEN** a flow manifest does not declare whether it needs the tagger
- **THEN** loading it is refused naming the key
- **AND** the refusal does not require the flow to be executed

#### Scenario: a declaration that is not a boolean is refused
- **Key:** `image-generation:tagger:a-non-boolean-declaration-is-refused`
- **Layers:** unit
- **WHEN** a flow manifest declares the tagger with a string, a number or a null
- **THEN** loading it is refused naming the key
- **AND** the value is not coerced into a boolean

### Requirement: Seeds are explicit or drawn, and an output is named by its seed under its approval

The system SHALL accept either a count of renders or an explicit list of seeds, SHALL NOT accept both,
SHALL draw seeds from an injectable source when given a count, and SHALL name each output by its seed
under the number of the approval it was rendered from.

One image, one integer: the seed is the reproducibility contract
([D13](../../../docs/decisions.md#d13--the-seed-reproduces-the-graph-not-the-pixels)). A count explores and a seed list
reproduces, so combining them means nothing. An injectable source keeps the suite deterministic without making
output predictable. One sheet approved twice renders into two directories; the sheet's own number is recorded in
the render.

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

#### Scenario: outputs are grouped under the approval they came from
- **Key:** `image-generation:seeds:outputs-carry-the-approval`
- **Layers:** unit
- **WHEN** the same seed is rendered against two different approved versions
- **THEN** both renders exist
- **AND** neither overwrites the other

### Requirement: A prompt and a render record the flow's digest and the sheet they came from

The system SHALL record in every prompt and every render the digest of the flow's directory and the number
of the sheet the approval was made from. The number of the approval itself stays the producer's `from`.

A flow's identifier can mean two configurations across a re-pin, and only the digest tells them apart. The sheet's
number lets a render name the sheet the person corrected, not only its approval.

#### Scenario: a render records its flow's digest and its sheet
- **Key:** `image-generation:provenance:the-flow-digest-and-the-sheet-are-recorded`
- **Layers:** unit
- **WHEN** a prompt and a render are written from an approval of a sheet whose number differs from the
  approval's
- **THEN** each records the flow's digest and the sheet's number
- **AND** the producer's `from` still names the approval
