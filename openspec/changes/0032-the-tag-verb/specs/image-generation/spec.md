## MODIFIED Requirements

### Requirement: A flow is a flat directory of named files whose manifest declares and never computes

The system SHALL define a flow as a directory containing exactly the manifest and its named siblings — a
graph, a schema and a caption briefing — all of them directly in that directory, with no sub-directory
and no other file. The manifest SHALL declare its required inputs, the vocabulary and the models its
render is pinned to, the model its hosted stages run, whether it needs the tagger, its node roles, its
prompt fragments and its dials.
The manifest SHALL NOT name any of its sibling files, SHALL declare the version of its own format, and
SHALL contain no computed or conditional value.

A manifest that computes nothing is fully checkable without executing anything, which is what lets a
broken flow be caught by the test suite rather than after a pod boot and several minutes. Holding the
schema and the briefing inside the directory is what makes a flow the complete specification of how an
input becomes an image: the briefing decides what enters the caption and the sheet decides the render, so
a changed briefing is a changed image, which the freeze surfaces: a new flow when the old one is still
wanted, a recorded re-pin when it is abandoned. The files sit directly in the directory
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

## ADDED Requirements

### Requirement: Every flow declares whether it needs the tagger

The system SHALL require every flow manifest to declare, in one top-level key, whether the flow needs the
tagger, as a boolean. It SHALL refuse a manifest that declares none, and SHALL refuse one whose value is
not a boolean, naming the key in both cases. It SHALL derive no part of that value at load time.

**Flows that need no tag list are coming, and whether a flow is tagged is a thing flows now differ in** —
which is what the manifest declares. The tag verb reads it to refuse a flow that declares no tagger, and
the sheet stage is told it to fill such a flow's sheet empty rather than refuse.

**A boolean and not a list of taggers.** The tag verb runs both taggers together, so a list would declare a
choice no flow makes. **A value that is not a boolean is refused rather than coerced**: a manifest whose
`"false"` read as true would tag a flow that said it needs none.

**Adding the key moves the manifest's format version**, because every key is required and the loader
reads one version. Both tracked flows declare that they need the tagger and are re-pinned in place: their
configuration did not change, only the format that states it, and a new identifier would claim a variant
that does not exist.

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
