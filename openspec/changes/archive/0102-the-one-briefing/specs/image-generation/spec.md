## ADDED Requirements

### Requirement: An unrecognised or misspelled manifest key is refused, naming what it carries

The system SHALL refuse to load a flow whose manifest carries any top-level key the build does not
recognise, naming the key. The refusal SHALL NOT require the flow to be executed.

Every declared key is required, so a misspelt key is two failures: the key the build reads is absent, and a key it
does not read is present. A manifest carrying `taggr` and no `tagger`, refused for the absence alone, sends the
operator to add a second key rather than fix the one they wrote.

#### Scenario: an unrecognised manifest key is refused naming it
- **Key:** `image-generation:manifest:unknown-key-is-refused`
- **Layers:** unit
- **WHEN** a flow manifest carries a top-level key the build does not recognise
- **THEN** loading it is refused naming that key
- **AND** the refusal does not require the flow to be executed

#### Scenario: a misspelled key is refused naming what it carries
- **Key:** `image-generation:manifest:a-misspelled-key-is-refused`
- **Layers:** unit
- **WHEN** a flow manifest carries a near-miss spelling of a key the build reads
- **THEN** loading it is refused naming the key it carries
- **AND** the refusal names the unrecognised key rather than only the absent one

## MODIFIED Requirements

### Requirement: A flow is pinned by equality; changing any file in it is an explicit act

The system SHALL hold each tracked flow against a committed digest computed over every file in its
directory, so that altering a dial, a prompt fragment, the graph or the schema fails the suite naming
the flow. Re-pinning SHALL be possible only as a deliberate edit to the committed digest, in
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

### Requirement: A flow is a flat directory of named files whose manifest declares and never computes

The system SHALL define a flow as a directory containing exactly the manifest and its named siblings — a
graph and a schema — all of them directly in that directory, with no sub-directory
and no other file. The manifest SHALL declare its required inputs, the vocabulary and the models its
render is pinned to, whether it needs the tagger, its node roles, its
prompt fragments and its dials. The manifest SHALL NOT name any of its sibling files, SHALL declare the
version of its own format, and SHALL contain no computed or conditional value.

```
flows/<id>/
├── flow.json              the manifest
├── graph.json
└── schema.json
```

A manifest that computes nothing is checkable without running anything, so a broken flow fails the suite, not a
boot. The schema shapes the image, so it sits inside the freeze, and the digest covers regular
files only, so a nested file would escape it ([D14](../../../docs/decisions.md#d14--a-flow-is-one-flat-directory)).
A key that can hold only one value is not a declaration, so the manifest names no filename.

#### Scenario: a flow holds the manifest and its named siblings, and nothing else
- **Key:** `image-generation:manifest:a-flow-is-flat-and-its-files-are-named`
- **Layers:** unit
- **WHEN** a tracked flow directory is read
- **THEN** it holds exactly a manifest, a graph and a schema, each directly in the directory
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
- **AND** the schema and the graph each one needs are present in its own directory

#### Scenario: an invalid manifest is refused naming the field
- **Key:** `image-generation:manifest:invalid-manifest-names-the-field`
- **Layers:** unit
- **WHEN** a flow manifest is missing or malformed in a declared field
- **THEN** loading it is refused naming that field
- **AND** the refusal does not require the flow to be executed

### Requirement: A control flow equals its subject flow but for the dials it zeroes

The system SHALL hold a control flow equal to its subject flow: the graph and the schema byte for byte,
and the manifest equal once the identifier and the face dials are set aside, with those
dials at zero. A difference anywhere else SHALL fail the suite naming the file.

```
flows/summon-anime-wai/                    flows/control-anime-wai/
  flow.json   ip_weight 0.9, cn 0.8   ──▶    flow.json   the identifier; ip_weight 0, cn 0
  graph.json                          ══▶    graph.json           byte-identical
  schema.json                         ══▶    schema.json          byte-identical
```

A control is a floor only while it differs from its subject in exactly the thing under test. Each flow is
pinned by its own digest, so a drift in the subject is caught by its pin and by the control's equality,
and the two move together or not at all
([D38](../../../docs/decisions.md#d38--a-control-flow-is-its-subject-with-the-face-chain-at-zero)).

#### Scenario: the control's files equal the subject's
- **Key:** `image-generation:control:files-equal-the-subject`
- **Layers:** unit
- **WHEN** the control flow's graph and schema are compared with the subject's
- **THEN** each is byte-identical

#### Scenario: the manifests differ only in the identifier and the face dials
- **Key:** `image-generation:control:manifest-differs-only-in-the-face-dials`
- **Layers:** unit
- **WHEN** the two manifests are compared with the identifier and the face dials set aside
- **THEN** they are equal
- **AND** the control's face dials are zero

### Requirement: A flat flow is its subject with the face chain ending early and a flat style

The system SHALL hold a flat flow equal to its subject flow but for its style: the schema byte for
byte; the graph equal but for the identity node's `end_at`, below one; and the manifest equal once the identifier,
`ip_weight` and the prompt's trailer and negative are set aside, the trailer gaining `flat color, cel shading, anime
coloring, colorful` and the negative `realistic, photorealistic, 3d, semi-realistic`. A difference anywhere else SHALL
fail the suite naming the file.

```
flows/summon-anime-wai/            flows/summon-flat-anime-wai/
  schema.json              ══▶       byte-identical
  graph.json  end_at 1     ──▶       end_at below 1
  flow.json   ip_weight    ──▶       a lower ip_weight; the flat trailer and negative
```

The face is set in the early steps, and the rendering style in the late ones, so ending the face chain early keeps
the likeness and frees the style. A flat flow is a variant, compared with summon on the same sheet and seed, never a
migration of it ([D15](../../../docs/decisions.md#d15--a-flow-is-named-for-what-it-is)).

#### Scenario: the flat flow's files equal the subject's
- **Key:** `image-generation:flat:files-equal-the-subject`
- **Layers:** unit
- **WHEN** a flat flow's schema is compared with its subject's
- **THEN** it is byte-identical

#### Scenario: the graph differs only in the face chain's end
- **Key:** `image-generation:flat:the-graph-differs-in-the-face-chains-end`
- **Layers:** unit
- **WHEN** a flat flow's graph is compared with its subject's
- **THEN** the identity node's `end_at` is below one, and nothing else differs

#### Scenario: the manifest differs only in the style
- **Key:** `image-generation:flat:the-manifest-differs-in-the-style`
- **Layers:** unit
- **WHEN** a flat flow's manifest is compared with its subject's, the identifier, `ip_weight` and the prompt's trailer
  and negative set aside
- **THEN** they are equal
- **AND** the trailer and the negative hold the flat terms

### Requirement: A semireal and a vivid flow are their subject's face chain ending early, in a style of their own

The system SHALL hold `summon-semireal-anime-wai` and `summon-vivid-anime-wai` each equal to `summon-anime-wai` but
for its style, as a flat flow is held: the schema byte for byte; the graph equal but for the identity
node's `end_at`, below one; and the manifest equal once the identifier, `ip_weight` and the prompt's trailer and
negative are set aside. The semireal flow's trailer and negative SHALL be its subject's; the vivid flow's trailer SHALL
be its subject's, and its negative SHALL gain `realistic, photorealistic, 3d, semi-realistic, monochrome, greyscale,
muted color`. A difference anywhere else SHALL fail the suite naming the file.

```
summon-anime-wai ─▶ face chain ending early, lower ip_weight ─┬─▶ summon-semireal-anime-wai  summon's prompt
                                                              ├─▶ summon-flat-anime-wai      the flat terms
                                                              └─▶ summon-vivid-anime-wai     no muted colour
```

Ending the face chain early keeps the likeness and frees the look; the prompt then sets how far the look moves. Each
was chosen by eye on the operator's photographs, as the cohort count cannot read a drawn face
([D46](../../../docs/decisions.md#d46--a-semireal-and-a-vivid-flow-are-flats-face-chain-in-other-looks)).

#### Scenario: their files equal the subject's
- **Key:** `image-generation:styled:files-equal-the-subject`
- **Layers:** unit
- **WHEN** the semireal or the vivid flow's schema is compared with its subject's
- **THEN** it is byte-identical

#### Scenario: their graph differs only in the face chain's end
- **Key:** `image-generation:styled:the-graph-differs-in-the-face-chains-end`
- **Layers:** unit
- **WHEN** the semireal or the vivid flow's graph is compared with its subject's
- **THEN** the identity node's `end_at` is below one, and nothing else differs

#### Scenario: their manifest differs only in its style
- **Key:** `image-generation:styled:the-manifest-differs-in-the-style`
- **Layers:** unit
- **WHEN** the semireal or the vivid flow's manifest is compared with its subject's, the identifier, `ip_weight` and the
  prompt's trailer and negative set aside
- **THEN** they are equal
- **AND** the trailer and the negative hold that flow's terms

## REMOVED Requirements

### Requirement: Every flow declares the model its hosted stages run

**Reason**: no flow names a model; the caption config names the one model the reader and the hosted tagger run.

**Migration**: *The caption config names the reader's model and its briefing*, in `caption`, holds the model and its
refusals; the `image-generation:model:*` keys go, each carried as the design's test table says.

### Requirement: An unrecognised manifest key is refused, naming what it carries

**Reason**: its misspelling scenario names the model key, which no manifest carries; a MODIFIED block may not drop a
scenario title, so the requirement is removed and added under a new title.

**Migration**: *An unrecognised or misspelled manifest key is refused, naming what it carries* carries every scenario;
`image-generation:manifest:a-misspelled-model-key-is-refused` is
`image-generation:manifest:a-misspelled-key-is-refused`.
