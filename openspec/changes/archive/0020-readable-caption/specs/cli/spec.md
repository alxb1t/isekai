## RENAMED Requirements

- FROM: `### Requirement: The reader and sorter are resolved per flow, not once per invocation`
- TO: `### Requirement: Every per-flow seam is resolved per flow, not once per invocation`

## MODIFIED Requirements

### Requirement: Every per-flow seam is resolved per flow, not once per invocation

The system SHALL resolve every seam a stage reaches — the reader, the sorter and each tagger — once per
flow being acted on, rather than once for the whole invocation, so that a single command naming flows on
two different implementations runs each flow on the one its manifest declares. A seam a flow selects by
manifest key SHALL construct nothing until a flow asks for it, and a seam this build resolves without a
manifest key SHALL resolve for every flow. A front end that serves no hosted-model stage SHALL remain
able to compose a wiring with none of them at all, and SHALL refuse naming the seam if a verb that needs
one is then invoked through it.

Every stage verb already takes more than one flow, and the flow is what supplies everything the stage
reads — its briefing, its schema, its dials. The implementation is now one more of those, so resolving
it above the loop over flows would hand one flow's implementation to another's, which is the single way
a flow could run on models it did not declare while every artifact still looked well-formed. Keeping the
uncomposed case expressible is what stops a front end that only reviews sheets from having to fabricate
doubles for seams it never calls.

Not every seam is selected the same way, and the requirement no longer pretends otherwise. A seam that
reaches a third party or a local runtime is named in a frozen manifest, because which model answers is a
claim the flow makes about itself and a wrong one spends money or falsifies a provenance record. A seam
that reads a file this build pins makes no such claim: there is no flow for which it would be the wrong
answer, it reaches no network, and requiring a key for it would mean re-pinning every existing flow to
obtain a capability none of them has an opinion about. What both cases share — and what this requirement
is actually protecting — is that resolution happens **inside** the loop, so nothing is constructed for a
flow that did not ask and nothing is carried from one flow to the next.

#### Scenario: one command runs two flows on two implementations
- **Key:** `cli:resolution:one-command-two-implementations`
- **Layers:** unit
- **WHEN** a stage verb is given two flows whose manifests declare different implementations
- **THEN** each flow's artifact names the implementation its own manifest declared
- **AND** neither flow is run on the other's

#### Scenario: a wiring composed without a hosted-model seam still refuses by name
- **Key:** `cli:resolution:uncomposed-seam-refuses-by-name`
- **Layers:** unit
- **WHEN** a verb that reaches a hosted model is invoked through a wiring composed without one
- **THEN** it refuses naming the seam and what that seam does
- **AND** no double is substituted for it

#### Scenario: a seam with no manifest key resolves for every flow
- **Key:** `cli:resolution:a-seam-without-a-manifest-key-resolves-for-every-flow`
- **Layers:** unit
- **WHEN** a stage verb is given a flow whose manifest declares no hosted model
- **THEN** the seam this build resolves without a manifest key is constructed for it
- **AND** no seam that a manifest key would have selected is constructed, and no refusal is raised
