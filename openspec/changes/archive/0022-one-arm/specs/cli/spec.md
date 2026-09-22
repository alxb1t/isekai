## ADDED Requirements

### Requirement: Every per-flow seam is resolved per flow, on the model that flow names

The system SHALL resolve every seam a stage reaches — the reader and each tagger — once per flow being acted
on, rather than once for the whole invocation, so that a single command naming several flows runs each flow
on the model its own manifest declares. A seam a flow selects by manifest key SHALL construct nothing until a
flow asks for it, and a seam this build resolves without a manifest key SHALL resolve for every flow. A front
end that serves no hosted-model stage SHALL remain able to compose a wiring with none of them at all, and
SHALL refuse naming the seam if a verb that needs one is then invoked through it.

Every stage verb already takes more than one flow, and the flow is what supplies everything the stage reads
— its briefing, its schema, its dials. The model is now one more of those, so resolving it above the loop
over flows would hand one flow's model to another's, which is the single way a flow could run on a model it
did not declare while every artifact still looked well-formed. Keeping the uncomposed case expressible is
what stops a front end that only reviews sheets from having to fabricate doubles for seams it never calls.

Not every seam is selected the same way, and the requirement no longer pretends otherwise. A seam that
reaches a local runtime is named in a frozen manifest, because which model answers is a claim the flow makes
about itself and a wrong one falsifies a provenance record. A seam that reads a file this build pins makes no
such claim: there is no flow for which it would be the wrong answer, it reaches no network, and requiring a
key for it would mean re-pinning every existing flow to obtain a capability none of them has an opinion
about. What both cases share — and what this requirement is actually protecting — is that resolution happens
**inside** the loop, so nothing is constructed for a flow that did not ask and nothing is carried from one
flow to the next.

**What the per-flow rule protects has narrowed twice, and it is worth saying what is left.** v0.21 removed
the sheet's hosted seam: that stage now reads a pinned artifact and a committed table, so it is selected by
nothing. This change removes the second implementation, so there is no longer a way for one flow to run on
*another implementation's* models. What survives is the case that motivated the rule in the first place and
is unaffected by either narrowing: two flows in one command may name two different **models**, and each
artifact must record the one its own manifest asked for.

#### Scenario: a wiring composed without a hosted-model seam still refuses by name
- **Key:** `cli:resolution:uncomposed-seam-refuses-by-name`
- **Layers:** unit
- **WHEN** a verb that reaches a hosted model is invoked through a wiring composed without one
- **THEN** it refuses naming the seam and what that seam does
- **AND** no double is substituted for it

#### Scenario: a seam with no manifest key resolves for every flow
- **Key:** `cli:resolution:a-seam-without-a-manifest-key-resolves-for-every-flow`
- **Layers:** unit
- **WHEN** a stage verb runs against a flow whose manifest declares nothing about a seam this build pins
- **THEN** that seam is resolved and runs
- **AND** the flow's manifest and its committed digest are unchanged

#### Scenario: one command runs two flows on the models each declares
- **Key:** `cli:resolution:one-command-two-models`
- **Layers:** unit
- **WHEN** a stage verb is given two flows whose manifests name different models
- **THEN** each flow's artifact names the model its own manifest declared
- **AND** neither flow is run on the other's

## REMOVED Requirements

### Requirement: Every per-flow seam is resolved per flow, not once per invocation

**Reason:** Its scenario `cli:resolution:one-command-two-implementations` is premised on a build carrying
two reader implementations, and this change leaves one. The scenario cannot be narrowed in place, because
`openspec` treats a MODIFIED requirement as a whole-block replacement and refuses to drop a scenario from
one — so the requirement is removed and re-added with the surviving cases. v0.21 already modified this
requirement once, when the sheet's hosted seam was retired.

**Migration:** *Every per-flow seam is resolved per flow, on the model that flow names*, in this change's
ADDED block. `cli:resolution:uncomposed-seam-refuses-by-name` and
`cli:resolution:a-seam-without-a-manifest-key-resolves-for-every-flow` are carried unchanged and keep
their bindings. `cli:resolution:one-command-two-implementations` becomes
`cli:resolution:one-command-two-models` — the per-flow rule still has real work to do, because two flows
in one command may name two different **models** and each artifact must record its own.
