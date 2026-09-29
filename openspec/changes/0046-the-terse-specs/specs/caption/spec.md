## MODIFIED Requirements

### Requirement: The reader may state absence

The system SHALL permit the prose to state that an attribute is absent, and SHALL NOT treat such a
statement as an error or strip it at this stage.

Licensing absence keeps the reader from confabulating. A positive prompt has no negation — a sentence saying no
tattoos are visible renders tattoos — so turning a licensed absence into an empty field is the next stage's job,
and allowing it here names where that happens.

#### Scenario: an absence statement survives into the artifact
- **Key:** `caption:absence:absence-is-permitted-here`
- **Layers:** unit
- **WHEN** the prose states that an attribute is not visible
- **THEN** the caption artifact carries that statement unchanged
- **AND** the caption is not rejected for containing it

### Requirement: The reader is an injectable seam with an offline stand-in

The system SHALL reach the reader through an interface that a test double satisfies, so the suite
exercises the stage without a network call, and SHALL record which implementation produced each caption.

A parameter is a seam only when something passes through it: here the offline stand-in, which is also the only way
to prove a complete stage made no call. The producer names the implementation so a real run is told from the
stand-in's, and so the record still reads back once a second implementation exists.

#### Scenario: the suite produces a caption with no network
- **Key:** `caption:seam:offline-double-satisfies-the-interface`
- **Layers:** unit
- **WHEN** the stage runs with the test double in place
- **THEN** a caption artifact is written
- **AND** no network call is attempted

#### Scenario: the artifact records which reader produced it
- **Key:** `caption:seam:producer-names-the-implementation`
- **Layers:** unit
- **WHEN** a caption is written
- **THEN** its producer names the implementation and the model or models that ran

### Requirement: A reader failure is classified and the stage refuses rather than guessing

The system SHALL classify a reader failure as transient or permanent, SHALL treat a declined request as
permanent, and SHALL NOT produce a caption by any means other than the reader that was asked for.

A refusal is a result to record and surface, not to route around: a failed read yields a recorded failure, never an
artifact assembled from something else ([D21](../../../docs/decisions.md#d21--retries-follow-what-can-fail)).

#### Scenario: a rate limit or server error is transient
- **Key:** `caption:failure:rate-limit-is-transient`
- **Layers:** unit
- **WHEN** the reader fails with a rate limit, a server error or a timeout
- **THEN** the failure is recorded as transient
- **AND** it counts against the stage's retry budget

#### Scenario: a declined request is permanent and is not routed around
- **Key:** `caption:failure:decline-is-permanent`
- **Layers:** unit
- **WHEN** the reader declines to answer
- **THEN** the failure is recorded as permanent, naming the photograph
- **AND** no caption artifact is written for that attempt

#### Scenario: an unusable response is permanent
- **Key:** `caption:failure:unusable-response-is-permanent`
- **Layers:** unit
- **WHEN** the reader returns something the stage cannot read as prose
- **THEN** the failure is recorded as permanent
- **AND** no caption artifact is written

### Requirement: The reader takes a photograph and returns prose, for one flow

The system SHALL pass a reader exactly one input — the photograph — and SHALL accept exactly one output:
descriptive prose. It SHALL NOT pass a schema, a field list, a vocabulary or a flow identifier to the
reader, and SHALL NOT accept tags into the caption. A caption SHALL be written inside the flow that
asked for it, and SHALL NOT be read by any other flow.

Pressing a reader into a schema makes it invent: told never to leave a field blank, a reader manufactures identity
marks. A caption belongs to its flow because the flow's briefing is part of its frozen directory: a flow reusing
another's caption would inherit an answer to a different question, and a second reading costs little beside a
boot. The prohibition on tags is scoped to this artifact: the tag stage writes tag lists for the same photograph,
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

#### Scenario: the reader's standing instructions come from the flow
- **Key:** `caption:inputs:briefing-comes-from-the-flow`
- **Layers:** unit
- **WHEN** a caption is produced for a flow
- **THEN** the standing instructions are read from that flow's own directory
- **AND** the caption records the digest of the instructions it was produced under

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
- **WHEN** a flow names a model the reader's manifest has no entry for
- **THEN** the command refuses naming the model and the manifest
- **AND** no host is contacted

### Requirement: The flow names the model its reader runs

The system SHALL read the model a flow's reader runs from a required key in that flow's manifest, SHALL
construct no reader until a flow asks for one, and SHALL refuse — naming the model and the flow — when
the manifest names a model this build cannot reach.

The model differs between flows, and an alias never created is the failure that will happen, so the manifest names
it and a refusal can too. The reader is built per flow so one command naming two flows never hands one flow's
model to the other's artifact. The hosted tagger reads the same key: one alias answers both prompts, framed alike,
and no flow can take its prose and its tags from different models unrecorded
([D5](../../../docs/decisions.md#d5--one-arm)).

#### Scenario: the flow's manifest names the model that runs
- **Key:** `caption:selection:the-flow-names-the-model`
- **Layers:** unit
- **WHEN** a flow is captioned
- **THEN** the reader runs the model that flow's manifest names
- **AND** the caption's producer records that model

#### Scenario: a model this build cannot reach is refused, naming it
- **Key:** `caption:selection:an-unreachable-model-is-refused`
- **Layers:** unit
- **WHEN** a flow names a model the runtime does not hold
- **THEN** the stage refuses naming the model and the command that would create it
- **AND** no attempt is spent and no artifact is written

### Requirement: A caption records the files its model was built from and the options it was sampled at

The system SHALL record in each caption's producer the digests of the model and projector files the model
was verified to be built from, SHALL declare the caption pinned only when that verification ran, and SHALL
record the sampling options the reader was called with, as they were sent.

An alias records nothing a later reader can check: one name can be rebuilt from other files and every artifact would
still agree. Verifying the files before the call lets the record say which ones answered
([D6](../../../docs/decisions.md#d6--ollama-at-a-fixed-local-address-on-a-checked-model)). The sampling options
shape the prose as much as the model, and they are constants in code, not manifest keys; recording them as sent
tells two captions under different options apart.

#### Scenario: a verified model's caption declares its pin and names both files
- **Key:** `caption:provenance:a-verified-model-is-pinned`
- **Layers:** unit
- **WHEN** a caption is written by a reader whose model was verified against the manifest
- **THEN** its producer declares the caption pinned
- **AND** it names the digest of the model file and of the projector file

#### Scenario: the caption records the options it was sampled at
- **Key:** `caption:provenance:the-options-are-recorded`
- **Layers:** unit
- **WHEN** a caption is written
- **THEN** its producer records the sampling options the reader sent, key for key
