## ADDED Requirements

### Requirement: The reader takes a photograph and its briefing, and returns the photograph's prose

The system SHALL pass a reader exactly the photograph and the briefing the caption config names, and SHALL
accept exactly one output: descriptive prose. It SHALL NOT pass a schema, a field list, a vocabulary or a flow
identifier to the reader, and SHALL NOT accept tags into the caption. A caption SHALL be written once per photograph,
under `photo/`, and every flow SHALL read that one caption.

Pressing a reader into a schema makes it invent: told never to leave a field blank, a reader manufactures identity
marks. Every flow is read under one briefing, the caption config's, on one model, so the prose is the photograph's and a
second reading would say the same ([D17](../../../docs/decisions.md#d17--input-above-flow-below)). The prohibition on
tags is scoped to this artifact: the tag stage writes tag lists for the same photograph, into its own directories, from
models given the photograph alone ([D1](../../../docs/decisions.md#d1--stage--is-two-independent-verbs)).

#### Scenario: the reader is given the photograph and nothing else
- **Key:** `caption:inputs:only-the-photograph-is-passed`
- **Layers:** unit
- **WHEN** a caption is produced
- **THEN** the reader receives the photograph and its standing instructions
- **AND** it receives no schema, no field list, no vocabulary and no flow identifier

#### Scenario: the artifact holds prose, not tags
- **Key:** `caption:output:artifact-is-prose`
- **Layers:** unit
- **WHEN** the caption artifact is written
- **THEN** its content is a single block of descriptive prose
- **AND** no structured field or tag list is stored inside the caption artifact

#### Scenario: every flow reads the one caption
- **Key:** `caption:output:every-flow-reads-one-caption`
- **Layers:** unit
- **WHEN** a photograph already captioned is captioned again, as a second flow's Prepare does
- **THEN** no second caption is written
- **AND** the run holds its one caption under `photo/`

#### Scenario: the reader's standing instructions come from the caption config
- **Key:** `caption:inputs:briefing-comes-from-the-config`
- **Layers:** unit
- **WHEN** a caption is produced
- **THEN** the standing instructions are read from the briefing the caption config names
- **AND** the caption records the digest of the instructions it was produced under

## MODIFIED Requirements

### Requirement: The caption config names the reader's model and its briefing

The system SHALL read the model the reader and the hosted tagger run, and the briefing the reader is given, from
one caption config, `config/caption.json`, holding exactly a `model` and a `briefing` naming a file beside it. It
SHALL refuse, naming the key, a config that declares no model or one that is not a non-empty string, SHALL refuse a
key it does not read, naming it, and SHALL refuse a briefing that is not a file beside the config, naming the file.
It SHALL construct no reader until a verb asks for one, and SHALL refuse, naming the model, a model this build
cannot reach.

```
config/
├── caption.json          {"briefing": "caption.briefing.md", "model": "<alias>"}
└── caption.briefing.md   the standing instructions every photograph is read under
```

Every flow reads a photograph the same way, so the briefing and the model are the library's, not a flow's: one file
names them once, and no flow can take its prose and its tags from different models
([D6](../../../docs/decisions.md#d6--ollama-at-a-fixed-local-address-on-a-checked-model)). An alias never created is
the failure that will happen, so a refusal names it.

#### Scenario: the caption config names the model that runs
- **Key:** `caption:selection:the-config-names-the-model`
- **Layers:** unit
- **WHEN** a photograph is captioned
- **THEN** the reader runs the model the caption config names
- **AND** the caption's producer records that model

#### Scenario: a model this build cannot reach is refused, naming it
- **Key:** `caption:selection:an-unreachable-model-is-refused`
- **Layers:** unit
- **WHEN** the caption config names a model the runtime does not hold
- **THEN** the stage refuses naming the model and the command that would create it
- **AND** no attempt is spent and no artifact is written

#### Scenario: a config with no model, or an empty one, is refused
- **Key:** `caption:selection:an-absent-or-empty-model-is-refused`
- **Layers:** unit
- **WHEN** the caption config declares no model, or one that is not a non-empty string
- **THEN** loading it is refused naming the key
- **AND** the value is not coerced into a string

#### Scenario: a key the config does not read is refused
- **Key:** `caption:selection:an-unknown-key-is-refused`
- **Layers:** unit
- **WHEN** the caption config carries a key this build does not read
- **THEN** loading it is refused naming that key

#### Scenario: a briefing that is not beside the config is refused
- **Key:** `caption:selection:an-absent-briefing-is-refused`
- **Layers:** unit
- **WHEN** the caption config names a briefing that is not a file beside it
- **THEN** loading it is refused naming the file

## REMOVED Requirements

### Requirement: The reader takes a photograph and its briefing, and returns prose for one flow

**Reason**: a caption is the photograph's, written once under `photo/` and read by every flow.

**Migration**: *The reader takes a photograph and its briefing, and returns the photograph's prose* replaces it; its
other keys stay, and `caption:output:caption-belongs-to-one-flow` gives way to
`caption:output:every-flow-reads-one-caption`.
