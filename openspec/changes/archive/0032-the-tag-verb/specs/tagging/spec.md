## REMOVED Requirements

### Requirement: A failing tagger leaves every artifact produced before it complete

**Reason**: It ordered the caption and both taggers inside one verb, where the first refusal ended a
photograph's work and the order was the isolation. The caption is now its own verb, and the two taggers are
isolated from each other both ways; the title said less than that and named the caption.

**Migration**: None. A hosted failure still leaves the local list written; a local failure now also leaves
the hosted list written.

### Requirement: The local tagger runs for every flow, and the hosted one runs on the model the flow names

**Reason**: A flow now declares whether it needs the tagger, because flows that need no tag list are
coming; the title said every flow is tagged. The requirement that replaces it keeps the hosted tagger on
the flow's model and the local tagger on no model key.

**Migration**: Both tracked flows declare the tagger, so both are tagged as before — by `tag` rather than
`caption`. A flow that declares none is refused by `tag`.

## ADDED Requirements

### Requirement: Each tagger's failure is its own, and the local tagger runs first

The system SHALL produce the local tag list, then the hosted tag list, under the tag verb, and a failure
in either SHALL NOT remove, prevent or invalidate the other's artifact — whether the failure is the
photograph's or the build's. The caption verb SHALL write no tag list.

The two taggers used to share a verb with the caption, and failures are collected per photograph rather
than per stage, so the first refusal ended that photograph's work and the order was the isolation. That
made a prose refusal cost the local tag list, which is the sheet's only input.

The caption is now its own verb, and inside the tag verb each tagger's refusal is collected on its own: a
local tagger that fails for one photograph, or cannot be opened for any, still lets the hosted tagger run,
and a hosted tagger that fails never costs the local list. The local tagger still runs first, because it is
the sheet's input and it reaches no network.

#### Scenario: a hosted tagger failure leaves the local tag list on disk
- **Key:** `tagging:order:a-late-failure-leaves-the-earlier-artifacts-complete`
- **Layers:** unit
- **WHEN** the hosted tagger fails for a photograph whose local tag list succeeded
- **THEN** that list is complete on disk
- **AND** the next invocation produces only the missing tag list

#### Scenario: a local tagger failure leaves the hosted list written
- **Key:** `tagging:order:a-local-failure-leaves-the-hosted-list-written`
- **Layers:** unit
- **WHEN** the local tagger fails for a photograph, or cannot be opened at all
- **THEN** the hosted tagger still runs for that photograph and its list is written
- **AND** the command refuses naming the local tagger's failure

#### Scenario: captioning writes no tag list
- **Key:** `tagging:order:captioning-writes-no-tag-list`
- **Layers:** unit
- **WHEN** a flow is captioned
- **THEN** the prose is written
- **AND** no tag list is written and no tagger is called

### Requirement: Both taggers run for a flow that declares the tagger, and the hosted one runs on the model the flow names

The system SHALL run both taggers for a flow whose manifest declares the tagger, SHALL resolve the local
tagger through no key that names its model, and SHALL resolve the hosted tagger on the model that flow's
manifest names. The tag verb SHALL refuse, before any artifact is written, an invocation naming a flow
whose manifest declares no tagger, naming the flow and the key. A hosted tagger that cannot reach its
model SHALL refuse without spending an attempt, and that refusal SHALL NOT prevent the local tag list from
being written.

The two are not implementations of one thing and must not be made to look like one. The hosted tagger is
selected by a string in a frozen manifest, because which model answers is a claim the flow makes about
itself. The local tagger makes no such claim: it is a file this build pins, it costs nothing, it reaches
no network, and there is no flow for which it would be the wrong model. **Whether a flow is tagged at all
is a claim the flow does make**, now that flows needing no tag list are coming — so the manifest declares
it, and still names nothing about which model tags.

**The hosted tagger reads the same key the reader does, and that is a decision rather than an economy.**
One alias answers both prompts, which is why the tag prompt is not chat-framed — two calls to one model
must not arrive framed differently. A key of its own would let a flow be written in which the prose and
the hosted tags came from different models with nothing in the record saying which was which, and it
would say twice what the manifest already says once.

**A flow that declares no tagger is refused rather than skipped.** An operator who names it asked for work
the flow does not do; a skip would report success for a flow that wrote nothing, and the refusal says which
flow to drop from the command.

#### Scenario: the local tagger needs no model key
- **Key:** `tagging:independence:the-local-tagger-needs-no-model-key`
- **Layers:** unit
- **WHEN** any tracked flow is tagged
- **THEN** the local tagger's artifact is written
- **AND** the flow's manifest names none of the local tagger's files

#### Scenario: the hosted tagger runs the model the flow names
- **Key:** `tagging:independence:the-hosted-tagger-runs-the-flows-model`
- **Layers:** unit
- **WHEN** a flow is tagged
- **THEN** the hosted tag artifact's producer names the model that flow's manifest declares
- **AND** it is the same model the caption's producer names

#### Scenario: a flow that declares no tagger is refused by the tag verb
- **Key:** `tagging:declaration:a-flow-without-a-tagger-is-refused`
- **Layers:** unit
- **WHEN** the tag verb names a flow whose manifest declares no tagger
- **THEN** the invocation is refused before any artifact is written, naming the flow and the key
- **AND** no other flow named with it is tagged
