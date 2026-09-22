## ADDED Requirements

### Requirement: A flow is a flat directory of named files whose manifest declares and never computes

The system SHALL define a flow as a directory containing exactly the manifest and its named siblings — a
graph, a schema and a caption briefing — all of them directly in that directory, with no sub-directory
and no other file. The manifest SHALL declare its required inputs, the vocabulary and the models its
render is pinned to, the model its hosted stages run, its node roles, its prompt fragments and its dials.
The manifest SHALL NOT name any of its sibling files, SHALL declare the version of its own format, and
SHALL contain no computed or conditional value.

A manifest that computes nothing is fully checkable without executing anything, which is what lets a
broken flow be caught by the test suite rather than after a pod boot and several minutes. Holding the
schema and the briefing inside the directory is what makes a flow the complete specification of how an
input becomes an image: the briefing decides what enters the caption and the sheet decides the render, so
a changed briefing is a changed image and must be a new flow. The files sit directly in the directory
rather than in sub-directories because the digest that freezes a flow covers regular files only; a nested
layout would leave the schema and the briefing outside the freeze while the gate stayed green. A key that
can only ever hold one value is not a declaration, which is why the manifest names no filenames.

**The rule names its files rather than counting them, and the change of form is deliberate.** It was
written as *five flat files* when there were five, and the count has now changed once — the sheet
briefing had no reader after the sheet began to be filled from a tag list, and a file nothing reads is
not a member of a structural rule. A count in a requirement, in a scenario key, and in four test names
is five places to get it wrong the next time the set moves, and none of them was ever an assertion: the
check has always been that the directory's contents equal the manifest plus the named siblings, which is
true at any size. Naming the members makes the rule say what the check does.

**This is not the weakening v0.19 refused.** That refusal was to *add* a sixth file — a model recipe —
to the frozen set, and it was declined because a recipe that shapes no render makes no per-flow claim;
the file went to `scripts/` instead. Removing a member that stopped being read is the opposite act, and
the two are recorded together here so a later reader does not mistake one for a precedent for the other.

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

**The key is a bare string and not a block, and that is the shape the arm count decides.** A block was
right when a flow chose between an implementation reached over a network to a third party and one reached
over a socket to this machine: it held the choice, the model each stage ran, and the name of the
distinction. With one implementation the distinction is gone and a block holding a single key is what
this repository already calls not a declaration — the same rule that stops the manifest naming its own
siblings. Flattening also closes a hole rather than opening one: the loader's allowlist refuses an
unrecognised **top-level** key, so a misspelling is now caught by a check that already exists, where
inside a block it was caught by nothing.

The key is separate from the models a flow's render is pinned to, and the separation is the point: one
names what a rented GPU loads and is pinned by digest, the other names what the local runtime is asked
for by alias. One key rather than one per stage is what makes *this flow is wholly one model* a property
of the document rather than of two lookups that happen to agree — and it is true of the running system,
where the reader and the hosted tagger deliberately share an alias so that two prompts reach one model
framed alike.

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
- **AND** the value is not coerced into a string that would name a model no runtime holds

### Requirement: An unrecognised manifest key is refused, naming what it carries

The system SHALL refuse to load a flow whose manifest carries any top-level key the build does not
recognise, naming the key. The refusal SHALL NOT require the flow to be executed.

Every declared key is required, so a misspelled one is two failures at once: the key the build reads is
absent, and a key it does not read is present. The first is already caught. The second is what this
requirement closes, and it matters most for the model key — a manifest carrying `modl` alongside no
`model` would otherwise be refused for the absence alone, naming a key the operator did not misspell and
sending him to add a second one rather than to fix the one he wrote. The loader already refuses a missing
key, a manifest that calls itself something else, an absent sibling file and a missing node role; an
unknown key is that same shape.

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

## REMOVED Requirements

### Requirement: A flow is a directory of five files whose manifest declares and never computes

**Reason:** The sheet briefing has had no reader since the sheet began to be filled from a tag list, and
this change deletes it from every flow — so the set is four and the requirement's count is wrong in its
heading, its body and its scenario key. Replaced rather than renumbered: the count has now moved once,
and a rule expressed as a number is a rule that will be wrong again. The replacement names its members.

**Migration:** `image-generation:manifest:flow-is-five-flat-files` becomes
`image-generation:manifest:a-flow-is-flat-and-its-files-are-named`, and the binding moves with it. The
other five scenarios are carried into the replacement unchanged except
`tracked-flows-are-gate-checked`, whose *"both briefings"* becomes *"the caption briefing"*.

### Requirement: A flow may declare the hosted models it calls

**Reason:** The block was optional because a flow that declared none fell back to a default
implementation. With one implementation there is no default to fall back to, no choice to declare, and no
flow that may decline to name its model. Its four scenarios all die with it:
`flow-declares-its-hosted-models` is replaced by `image-generation:model:flow-declares-the-model-it-runs`;
`absent-block-means-the-default` becomes **false** rather than unreachable, since the state it describes
is now unrepresentable; `incumbent-flows-are-unchanged` loses its comparison target, which this change
deletes; and `an-unread-key-is-carried` described `hosted.sorter`, the key this change removes — it was
added at v0.21 and is removed at v0.22, having lived exactly one version, because the pass that gave it a
test is the one before the pass that deletes the key.

**Migration:** *Every flow declares the model its hosted stages run*, in this change's ADDED block.
`MANIFEST_VERSION` goes to 3, which is what makes the now-required key a format change rather than a
silent tightening — and the comment recording that the version stayed at 2 to avoid editing two frozen
directories is removed with the directories it was protecting.

### Requirement: A manifest key this build does not know is refused, naming it

**Reason:** Its scenario `image-generation:manifest:misspelled-hosted-block-is-refused` names the hosted
block and its fall-through to a default implementation, both of which this change deletes. The scenario
cannot be narrowed in place — `openspec` treats a MODIFIED requirement as a whole-block replacement and
refuses to drop a scenario from one — so the requirement is removed and re-added with its rationale
rewritten for a build in which every declared key is required.

**Migration:** *An unrecognised manifest key is refused, naming what it carries*, in this change's ADDED
block. `image-generation:manifest:unknown-key-is-refused` is carried unchanged and keeps its bindings.
`misspelled-hosted-block-is-refused` becomes
`image-generation:manifest:a-misspelled-model-key-is-refused`: the failure it guards is now sharper, not
softer, because with the key required a misspelling produces two faults at once and the refusal must name
the one the operator actually typed.
