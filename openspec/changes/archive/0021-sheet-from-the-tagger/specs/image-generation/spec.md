## ADDED Requirements

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

## REMOVED Requirements

### Requirement: A flow may declare the hosted models its first two stages call

**Reason**: Replaced whole by *A flow may declare the hosted models it calls*. Stage ② reaches no hosted
model after this change, so *"its first two stages"*, *"a model name for each of the first two stages"* and
*"the loaded flow carries that implementation and both model names"* each become false as written.
`openspec` cannot restate a requirement's SHALL and add a scenario to it in place, and the replacement adds
one: a key no stage reads must load without claiming a stage exists.

**Migration**: None, and **no flow is re-cut**. All three scenarios move across **under their existing keys**
— `image-generation:hosted:flow-declares-its-hosted-models`,
`image-generation:hosted:absent-block-means-the-default`,
`image-generation:hosted:incumbent-flows-are-unchanged` — and a fourth is added for the carried key. The
`hosted` block's shape on disk is unchanged in every flow, `hosted.sorter` remains a required key of the
document, and all three committed manifest digests are bit-identical.
