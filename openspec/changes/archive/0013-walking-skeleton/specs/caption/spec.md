## Purpose

Stage ① of the pipeline: reading a photograph into descriptive English prose, knowing nothing about
schemas, vocabularies, flows or what happens next, and licensed to say that something is absent.

## ADDED Requirements

### Requirement: The reader takes a photograph and returns prose

The system SHALL pass a reader exactly one input — the photograph — and SHALL accept exactly one output:
descriptive prose. It SHALL NOT pass a schema, a field list, a vocabulary or a flow identifier to the
reader, and SHALL NOT accept tags from it.

Pressing a reader into a schema is measured to make it invent. Instructed never to leave a field blank,
a reader manufactured nineteen identity marks across seven of ten subjects and its score fell from
0.518 to 0.307. A caption is also reused when a flow is added later, which it could not be if it had
been written against one flow's schema.

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
- **AND** no structured field or tag list is stored alongside it

#### Scenario: a caption is reusable across flows
- **Key:** `caption:output:caption-is-flow-neutral`
- **Layers:** unit
- **WHEN** a second flow is added to a run that already has a caption
- **THEN** the existing caption is used unchanged
- **AND** no new caption is produced for the added flow

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
- **AND** a caption produced by a different implementation is distinguishable from the record alone

### Requirement: A reader failure is classified and the stage refuses rather than guessing

The system SHALL classify a reader failure as transient or permanent, SHALL treat a declined request as
permanent, and SHALL NOT substitute a fallback implementation for the one that was asked for.

Falling back to a different reader when one declines would write an artifact whose provenance record is
untrue — the whole discipline of this pipeline is that a producer names what actually made the
artifact. A refusal is a result to be recorded and surfaced, not routed around.

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
- **AND** no other implementation is substituted to produce the caption

#### Scenario: an unusable response is permanent
- **Key:** `caption:failure:unusable-response-is-permanent`
- **Layers:** unit
- **WHEN** the reader returns something the stage cannot read as prose
- **THEN** the failure is recorded as permanent
- **AND** no caption artifact is written

### Requirement: An absent reader is a refusal that names its remedy

The system SHALL refuse with a message naming what to install or configure when the reader cannot be
reached at all, rather than failing with an unhandled error.

This is the posture the repository already takes for an optional dependency: the failure states the
command that would fix it. It matters more here, because the reader is the first thing a fresh clone
touches.

#### Scenario: a missing reader names the remedy
- **Key:** `caption:refusal:absent-reader-names-the-fix`
- **Layers:** unit
- **WHEN** the reader is not available on the machine
- **THEN** the command refuses with a message naming what to install or configure
- **AND** no run directory is left in a partially written state
