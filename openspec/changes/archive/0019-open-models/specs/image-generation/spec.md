## ADDED Requirements

### Requirement: A flow may declare the hosted models its first two stages call

The system SHALL permit a flow manifest to declare, in one optional block, the implementation its reader
and sorter are reached through and the model name each of them runs. A manifest that declares no such
block SHALL use the build's default implementation, which is the behaviour of every flow written before
this key existed. A flow SHALL declare one implementation for both stages, not one per stage.

The block is separate from the models a flow's render is pinned to, and the separation is the point: one
names what a rented GPU loads and is pinned by digest, the other names what the two hosted-model stages
call over a network. Declaring the implementation once rather than per stage makes "this flow is wholly
one implementation" a property of the document rather than of two independent lookups that happen to
agree — a flow that mixed them would be a fifth configuration nobody asked for, and the flow is the unit
of freeze precisely so that a configuration is named rather than assembled.

Making the block optional is what keeps a version that introduces a second implementation from editing
the flows that predate it. A frozen flow's identifier means one configuration, and re-cutting two
manifests to add a key whose value was already implied would change two committed digests to record no
change in behaviour.

#### Scenario: a flow declaring hosted models is loaded with them
- **Key:** `image-generation:hosted:flow-declares-its-hosted-models`
- **Layers:** unit
- **WHEN** a flow manifest declares an implementation and a model name for each of the first two stages
- **THEN** the loaded flow carries that implementation and both model names
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
