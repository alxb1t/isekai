## ADDED Requirements

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

## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: The flow selects the reader implementation, and every way of getting that wrong is a refusal

**Reason:** There is one reader implementation. The requirement's own rationale describes the world that
justified it — *"one reaches a model over a network to a third party, the other over a socket to this
machine"* — and the first of those is deleted by this change. Its three scenarios go with it:
`caption:selection:the-flow-names-the-implementation` is replaced by
`caption:selection:the-flow-names-the-model`, which narrows the claim to the thing that still varies;
`caption:selection:unknown-implementation-is-refused` becomes
`caption:selection:an-unreachable-model-is-refused`, since a one-entry registry has no unknown-key case
left that is not simply an unreachable model; and
`caption:selection:no-path-reaches-another-implementation` is **unprovable**, because there is no other
implementation for a path to reach.

**Migration:** The replacements are in this change's ADDED block above.
`no-path-reaches-another-implementation` has no replacement and is named here rather than left to be
discovered at the fold: its only two bindings were `tests/test_isolation.py:91` and `:101`, and this
change deletes that file. This repository has no spec↔test binding checker, so nothing in the gate would
have reported the orphan.

### Requirement: An absent reader is a refusal that names its remedy

**Reason:** Its entire content is the absent-`claude`-binary message and its `npm install` remedy, and
both its tests drove the Claude reader directly. The surviving arm is HTTP to a local port — there is no
binary to be absent — and both of its real failure modes are already specified, with bindings, under *A
hosted model that is not running or not installed is refused before any attempt is spent*:
`caption:reachability:unreachable-host-refuses-without-an-attempt` for a refused connection and
`caption:reachability:absent-model-names-how-to-create-it` for a model that was never created.

**Migration:** None needed. Rewriting this requirement for the surviving arm would have produced a
second requirement saying what `caption:reachability:*` already says with three scenarios behind it.
