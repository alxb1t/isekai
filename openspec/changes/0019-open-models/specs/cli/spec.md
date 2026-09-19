## ADDED Requirements

### Requirement: The reader and sorter are resolved per flow, not once per invocation

The system SHALL resolve which reader and sorter implementation to use once per flow being acted on,
rather than once for the whole invocation, so that a single command naming flows on two different
implementations runs each flow on the one its manifest declares. A front end that serves no hosted-model
stage SHALL remain able to compose a wiring with no reader and no sorter at all, and SHALL refuse naming
the seam if a verb that needs one is then invoked through it.

Every stage verb already takes more than one flow, and the flow is what supplies everything the stage
reads — its briefing, its schema, its dials. The implementation is now one more of those, so resolving it
above the loop over flows would hand one flow's implementation to another's, which is the single way a
flow could run on models it did not declare while every artifact still looked well-formed. Keeping the
uncomposed case expressible is what stops a front end that only reviews sheets from having to fabricate
doubles for seams it never calls.

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
