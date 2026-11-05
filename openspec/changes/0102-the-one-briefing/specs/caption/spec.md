## ADDED Requirements

### Requirement: The caption config names the reader's model and its briefing

The system SHALL read the model the reader and the hosted tagger run, and the briefing the reader is given, from
one caption config, `config/caption.json`, holding exactly a `model` and a `briefing` naming a file beside it. It
SHALL refuse, naming the key, a config that declares no model or one that is not a non-empty string, SHALL refuse a
key it does not read, naming it, and SHALL refuse a briefing that is not a file beside the config, naming the file.
It SHALL construct no reader until a flow asks for one, and SHALL refuse, naming the model, a model this build
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
- **WHEN** any flow is captioned
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

### Requirement: The reader takes a photograph and its briefing, and returns prose for one flow

The system SHALL pass a reader exactly the photograph and the briefing the caption config names, and SHALL
accept exactly one output: descriptive prose. It SHALL NOT pass a schema, a field list, a vocabulary or a flow
identifier to the reader, and SHALL NOT accept tags into the caption. A caption SHALL be written inside the flow
that asked for it, and SHALL NOT be read by any other flow.

Pressing a reader into a schema makes it invent: told never to leave a field blank, a reader manufactures identity
marks. A caption is written under its flow, as every stage's artifact is
([D17](../../../docs/decisions.md#d17--input-above-flow-below)), and a second reading costs little beside a boot.
Every flow is read under one briefing, the caption config's, so a caption records the same instructions whichever
flow asked. The prohibition on tags is scoped to this artifact: the tag stage writes tag lists for the same photograph,
into its own directories, from models given the photograph alone
([D1](../../../docs/decisions.md#d1--stage--is-two-independent-verbs)).

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

#### Scenario: a caption belongs to the flow that asked for it
- **Key:** `caption:output:caption-belongs-to-one-flow`
- **Layers:** unit
- **WHEN** a second flow is added to a run that already has a caption
- **THEN** the added flow produces its own caption
- **AND** the existing flow's caption is neither read nor changed

#### Scenario: the reader's standing instructions come from the caption config
- **Key:** `caption:inputs:briefing-comes-from-the-config`
- **Layers:** unit
- **WHEN** a caption is produced for any flow
- **THEN** the standing instructions are read from the briefing the caption config names
- **AND** the caption records the digest of the instructions it was produced under

## MODIFIED Requirements

### Requirement: A hosted model that is not running or not installed is refused before any attempt is spent

The system SHALL refuse, naming the command that would fix it, when the host serving a declared model
cannot be reached or reports that the model does not exist, when the model is built from files other than
the ones the reader's manifest pins for it, and when no entry in that manifest pins the model at all. It
SHALL record no attempt against the stage's retry budget for any of these conditions, and SHALL make that check
at the first call rather than when the implementation is constructed.

A retry budget counts models tried and failed. A server not running, a model never created and a model built from
other files are none of these: each is the operator's one-command fix, and a spent attempt would leave error records
to delete by hand before the run resumes. The alias is a name the runtime resolves and the files behind it shape the
prose, so the runtime's record of them is compared with the manifest's digests
([D6](../../../docs/decisions.md#d6--ollama-at-a-fixed-local-address-on-a-checked-model)). Checking at the first
call lets a machine that never captions leave the reader untouched.

#### Scenario: an unreachable host is refused and costs no attempt
- **Key:** `caption:reachability:unreachable-host-refuses-without-an-attempt`
- **Layers:** unit
- **WHEN** the host serving the declared reader is not answering
- **THEN** the command refuses naming what to start
- **AND** no attempt is recorded against the stage's budget

#### Scenario: a model the host does not have is refused naming how to create it
- **Key:** `caption:reachability:absent-model-names-how-to-create-it`
- **Layers:** unit
- **WHEN** the host reports that the declared model does not exist
- **THEN** the command refuses naming the command that would create or fetch it
- **AND** no attempt is recorded against the stage's budget

#### Scenario: the reachability check is not made until a flow asks
- **Key:** `caption:reachability:the-check-fires-at-first-call`
- **Layers:** unit
- **WHEN** a wiring is composed and no captioning is performed
- **THEN** no host is contacted, no binary is looked up and no model record is read

#### Scenario: a model built from other files is refused naming how to rebuild it
- **Key:** `caption:reachability:an-unpinned-build-is-refused`
- **Layers:** unit
- **WHEN** the runtime's record of the declared model names a model or projector file whose digest is not
  the one the reader's manifest pins
- **THEN** the command refuses naming both digests and the commands that provision the pinned files and
  rebuild the model
- **AND** no attempt is recorded against the stage's budget

#### Scenario: a model no manifest entry pins is refused
- **Key:** `caption:reachability:an-unpinned-model-is-refused`
- **Layers:** unit
- **WHEN** the caption config names a model the reader's manifest has no entry for
- **THEN** the command refuses naming the model and the manifest
- **AND** no host is contacted

#### Scenario: a model with no readable record names the files first
- **Key:** `caption:reachability:no-record-names-the-files-first`
- **Layers:** unit
- **WHEN** the runtime holds no readable record of the declared model
- **THEN** the command refuses naming the command that fetches the pinned files, then the one that builds the model

## REMOVED Requirements

### Requirement: The flow names the model its reader runs

**Reason**: no flow names a model; the caption config names the one model the reader and the hosted tagger run.

**Migration**: *The caption config names the reader's model and its briefing* holds the selection;
`caption:selection:the-flow-names-the-model` is `caption:selection:the-config-names-the-model`, and
`caption:selection:an-unreachable-model-is-refused` keeps its key.

### Requirement: The reader takes a photograph and returns prose, for one flow

**Reason**: its briefing scenario names the flow's own directory, which holds no briefing; a MODIFIED block may not
drop a scenario title, so the requirement is removed and added under a new title.

**Migration**: *The reader takes a photograph and its briefing, and returns prose for one flow* carries every scenario;
`caption:inputs:briefing-comes-from-the-flow` is `caption:inputs:briefing-comes-from-the-config`.
