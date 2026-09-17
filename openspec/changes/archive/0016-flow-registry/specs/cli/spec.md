## ADDED Requirements

### Requirement: Every stage verb requires the flows it acts on, and takes more than one

The system SHALL require a flow selection on every stage verb — reading, sorting, reviewing, approving
and rendering — SHALL accept the selection more than once in a single invocation, and SHALL refuse an
invocation that names none, naming the flows that are tracked. It SHALL NOT fall back to every tracked
flow. It SHALL refuse a flow that is not tracked, at the point of selection, naming the flows that are.

A stage cannot act without knowing which flow asked, because the flow is what supplies the thing the
stage reads: its briefing, its schema, its graph and its dials. Falling back to every tracked flow is an
unbounded default that spends money at the last verb and burns a paid model call at the first — at
catalogue scale "everything tracked" is not a selection, it is the absence of one. The selection repeats
because flows batch: every flow named in one rendering invocation renders on one endpoint, and a second
boot costs what eight more renders would, so a flow left off the line is a flow that pays for its own
boot.

#### Scenario: a stage verb without a flow is refused
- **Key:** `cli:flow-selection:a-stage-verb-requires-a-flow`
- **Layers:** unit
- **WHEN** a stage verb is invoked with no flow named
- **THEN** the invocation is refused
- **AND** the message lists the tracked flows

#### Scenario: the selection repeats
- **Key:** `cli:flow-selection:the-flag-is-repeatable`
- **Layers:** unit
- **WHEN** a stage verb is given more than one flow
- **THEN** every named flow is acted on in that one invocation
- **AND** no named flow is silently dropped

#### Scenario: every stage verb accepts it
- **Key:** `cli:flow-selection:every-stage-verb-accepts-it`
- **Layers:** unit
- **WHEN** each of the five stage verbs is invoked with a flow named
- **THEN** none of them rejects the flag as unrecognised
- **AND** the inspection verb is the only one that does not take it

#### Scenario: an untracked flow is refused at selection
- **Key:** `cli:flow-selection:an-untracked-flow-is-refused`
- **Layers:** unit
- **WHEN** a stage verb names a flow that is not tracked
- **THEN** the invocation is refused naming that flow
- **AND** the message lists the flows that are tracked
