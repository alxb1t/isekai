# Capability: `caption`

## Purpose

Stage ① of the pipeline: reading a photograph into descriptive English prose under the standing
instructions of the flow that asked, knowing nothing about schemas, vocabularies or what happens next,
and licensed to say that something is absent.

**Source:** `isekai/pipeline/caption.py`, `isekai/boundary/ollama.py`,
`flows/summon-anime-wai/caption.briefing.md` ·
**Tests:** `tests/test_caption.py`

## Requirements

### Requirement: The reader may state absence

The system SHALL permit the prose to state that an attribute is absent, and SHALL NOT treat such a
statement as an error or strip it at this stage.

Licensing absence is what stopped the confabulation. It is also why the next stage is a seam rather
than plumbing: a positive prompt has no negation, so a sentence saying no tattoos are visible rendered
tattoos. The component that turns a licensed absence into an empty field is the next stage's job, and
naming where that happens is the point of allowing it here.

#### Scenario: an absence statement survives into the artifact
- **Key:** `caption:absence:absence-is-permitted-here`
- **Layers:** unit
- **WHEN** the prose states that an attribute is not visible
- **THEN** the caption artifact carries that statement unchanged
- **AND** the caption is not rejected for containing it

### Requirement: The reader is an injectable seam with an offline stand-in

The system SHALL reach the reader through an interface that a test double satisfies, so the suite
exercises the stage without a network call, and SHALL record which implementation produced each caption.

The repository's standing rule is that a parameter is a seam only when something is actually passed
through it. A stand-in for the offline suite is what passes through this one, and it is also the only
way the idempotence guarantee can be asserted — proving no call was made requires something that counts
calls.

**The producer still names the implementation, and the reason has changed.** It used to be what
distinguished two arms in the record. With one arm it is what distinguishes a real run from a run
produced by the offline stand-in, and what will distinguish this arm from whatever a later version adds
beside it — a record that stops naming the implementation because there is only one is a record that
cannot be read back once there are two.

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

A refusal is a result to be recorded and surfaced, not routed around. The rule was first written against
a second implementation that a failure could silently fall through to; with one arm there is nothing to
fall through to, and the rule now protects the weaker but still live case — that a failed read produces a
recorded failure rather than an artifact assembled from something else.

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

Pressing a reader into a schema is measured to make it invent. Instructed never to leave a field blank,
a reader manufactured nineteen identity marks across seven of ten subjects and its score fell from
0.518 to 0.307. That is a rule about what reaches the reader, and it is unchanged: the reader still
receives the photograph and its standing instructions and nothing else. What changes is who the answer
belongs to. A caption used to be written once per run and reused by any flow added later, which meant a
second flow silently inherited a reading written to answer a different question — its briefing is part
of its frozen directory, so two flows asking different questions were sharing one answer. Reuse was
worth that risk only while a reading was expensive: it costs $0.0159 per photograph at worst and $0.0013
cached and batched, against a boot that costs $0.036. Two flows over one input now read it twice, and
the class of error disappears rather than being checked for.

**The prohibition on tags is scoped to this artifact rather than to the run.** A separate stage produces
tag lists for the same photograph, into its own directories, from models given the photograph and
nothing else — and that stage exists precisely because asking one call for prose and tags at once would
rewrite the instruction the prose was measured under. What this requirement forbids is unchanged in
substance: a caption is prose, a reader is not asked for structure, and nothing about the tag stage
sends a schema or a field list to any model.

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
cannot be reached or reports that the model does not exist. It SHALL record no attempt against the
stage's retry budget for either condition, and SHALL make that check at the first call rather than when
the implementation is constructed.

A retry budget counts models tried and failed. A server that is not running and a model that was never
created are neither: both are the operator's single-command fix, and spending a budgeted attempt on them
leaves a run whose error records have to be deleted by hand before it can be resumed. This is the posture
the build already takes toward a missing binary, applied to a port and to a model name instead of a path
entry. Checking at first call rather than at construction is what lets a machine that will never use an
implementation avoid touching it at all.

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
- **THEN** no host is contacted and no binary is looked up

### Requirement: The flow names the model its reader runs

The system SHALL read the model a flow's reader runs from a required key in that flow's manifest, SHALL
construct no reader until a flow asks for one, and SHALL refuse — naming the model and the flow — when
the manifest names a model this build cannot reach.

The implementation no longer varies, so the manifest no longer declares one: a key that can only ever
hold one value is not a declaration. The model still varies, still differs between flows, and is still
the thing that costs the operator time when it is wrong — an alias that was never created is the failure
that will actually happen, and it is the one this key makes nameable. The reader is constructed per flow
rather than once per invocation for the same reason it always was: one command naming two flows must not
hand one flow's model to the other's artifact.

The same key names the model the hosted tagger runs, and that is deliberate rather than an economy. One
alias answers both prompts, which is why the tag prompt is not chat-framed — two calls to one model must
not arrive framed differently. A second key would say twice what the manifest says once, and would make
a flow expressible in which the prose and the tags came from different models with nothing recording
which.

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
