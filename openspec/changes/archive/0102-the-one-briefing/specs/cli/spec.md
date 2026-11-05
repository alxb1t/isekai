## ADDED Requirements

### Requirement: Every per-flow seam is resolved per flow, for a flow that declares its stage

The system SHALL resolve every seam a stage reaches — the reader and each tagger — once per flow being acted
on, rather than once for the whole invocation, and SHALL run the reader and the hosted tagger, for every flow, on
the one model the caption config names. A seam SHALL construct nothing until a flow asks for it, and a seam this
build pins SHALL resolve for every flow whose manifest declares the stage that seam serves. A front end that serves
no hosted-model stage SHALL remain able to compose a wiring with none of them at all, and SHALL refuse naming the
seam if a verb that needs one is then invoked through it.

A seam resolved per flow refuses for that flow alone, so the other flows named with it still run. Which model
answers is a claim the library makes once, in its caption config, so no flow is read by one model and tagged by
another ([D6](../../../docs/decisions.md#d6--ollama-at-a-fixed-local-address-on-a-checked-model)); a seam reading a
file this build pins makes no such claim, and the manifest names none of its files. Whether a flow is tagged at
all is its manifest's own key ([D31](../../../docs/decisions.md#d31--a-flow-declares-whether-it-is-tagged)). A
front end that only reviews sheets composes no seam rather than fabricating doubles.

#### Scenario: a wiring composed without a hosted-model seam still refuses by name
- **Key:** `cli:resolution:uncomposed-seam-refuses-by-name`
- **Layers:** unit
- **WHEN** a verb that reaches a hosted model is invoked through a wiring composed without one
- **THEN** it refuses naming the seam and what that seam does
- **AND** no double is substituted for it

#### Scenario: a pinned seam resolves for every flow that declares its stage
- **Key:** `cli:resolution:a-pinned-seam-resolves-for-every-flow-that-declares-it`
- **Layers:** unit
- **WHEN** the tag verb runs against a flow that declares the tagger and names no model for the local tagger
- **THEN** the local tagger is resolved and runs
- **AND** the flow's manifest names none of the local tagger's files

#### Scenario: one command runs every flow on the configured model
- **Key:** `cli:resolution:one-command-one-model`
- **Layers:** unit
- **WHEN** the reader is resolved for each of two flows named in one command
- **THEN** each runs the model the caption config names

## MODIFIED Requirements

### Requirement: A stage verb requires the flows it acts on, and takes more than one

The system SHALL require a flow selection on every stage verb — reading, tagging, filling a sheet, reviewing,
approving and rendering — SHALL accept the selection more than once in a single invocation, and SHALL refuse an
invocation that names none, naming the flows that are tracked. It SHALL NOT fall back to every tracked
flow. It SHALL refuse a flow that is not tracked, at the point of selection, naming the flows that are.

The flow supplies what a stage reads — its schema, its graph and its dials — so a stage cannot act
without one, and every tracked flow is an unbounded default that spends at the last verb. The selection repeats
because flows batch: every flow named in one rendering invocation shares one boot. The serving verb is not a stage
verb: it serves the flows its configuration offers, of every collection, and its page selects one.

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
- **WHEN** each stage verb — `caption`, `tag`, `sheet`, `review`, `approve` and `generate` — is invoked
  with a flow named
- **THEN** none of them rejects the flag as unrecognised
- **AND** the inspection verb is the only one that does not take it

#### Scenario: an untracked flow is refused at selection
- **Key:** `cli:flow-selection:an-untracked-flow-is-refused`
- **Layers:** unit
- **WHEN** a stage verb names a flow that is not tracked
- **THEN** the invocation is refused naming that flow
- **AND** the message lists the flows that are tracked

#### Scenario: one flow's refusal leaves the input's other flows
- **Key:** `cli:flow-selection:one-flows-refusal-leaves-the-others`
- **Layers:** unit
- **WHEN** a stage verb names more than one flow, and one of them refuses for an input
- **THEN** the input's other named flows are still acted on
- **AND** every refusal is reported together at the end

## REMOVED Requirements

### Requirement: Every per-flow seam is resolved per flow, on the model that flow names, for a flow that declares its stage

**Reason**: no flow names a model; the caption config names the one model every flow runs.

**Migration**: *Every per-flow seam is resolved per flow, for a flow that declares its stage* holds the seams;
`cli:resolution:one-command-two-models` is `cli:resolution:one-command-one-model`.
