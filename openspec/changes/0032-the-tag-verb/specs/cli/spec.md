## MODIFIED Requirements

### Requirement: A new artifact version is requested explicitly

The system SHALL do nothing when a stage's artifact already exists, and SHALL require an explicit flag
to produce a new version. The flag SHALL produce the next version of every artifact its own verb writes,
and of no artifact another verb writes.

Deciding automatically — writing a new version when some recorded field differs — would make an
invocation that sometimes costs money and sometimes does not, decided by a field the operator did not
look at. An explicit flag makes the spend visible in the command line that caused it.

**One meaning per verb.** When one verb wrote the prose and both tag lists, its flag re-read the
photograph to recover a tag list, and the fix for a damaged tag list re-read prose nothing needed. Each
verb now writes only its own artifacts, so the flag asks for exactly those: `caption`'s writes the next
prose and no tag list, and `tag`'s writes the next version of both tag lists and no prose.

#### Scenario: a repeat invocation does nothing
- **Key:** `cli:explicit-versions:repeat-invocation-is-a-no-op`
- **Layers:** unit
- **WHEN** a stage's command is invoked and its artifact exists
- **THEN** nothing is written and nothing is called
- **AND** the command reports that the stage is already complete

#### Scenario: the flag produces the next version
- **Key:** `cli:explicit-versions:flag-writes-the-next-version`
- **Layers:** unit
- **WHEN** the explicit flag is given
- **THEN** the next numbered artifact is written
- **AND** the previous one is unchanged

#### Scenario: the caption verb's flag writes the next prose and no tag list
- **Key:** `cli:explicit-versions:the-caption-flag-writes-prose-only`
- **Layers:** unit
- **WHEN** `caption` is given the flag for a run that holds prose and both tag lists
- **THEN** the next prose is written
- **AND** neither tag list gains a version

#### Scenario: the tag verb's flag writes both tag lists and no prose
- **Key:** `cli:explicit-versions:the-tag-flag-writes-both-lists`
- **Layers:** unit
- **WHEN** `tag` is given the flag for a run that holds prose and both tag lists
- **THEN** the next version of each tag list is written
- **AND** the prose gains no version

### Requirement: Every stage verb requires the flows it acts on, and takes more than one

The system SHALL require a flow selection on every stage verb — reading, tagging, filling a sheet, reviewing,
approving and rendering — SHALL accept the selection more than once in a single invocation, and SHALL refuse an
invocation that names none, naming the flows that are tracked. It SHALL NOT fall back to every tracked
flow. It SHALL refuse a flow that is not tracked, at the point of selection, naming the flows that are.
A verb that serves a surface rather than running a stage SHALL require the selection and SHALL accept
it **exactly once**.

A stage cannot act without knowing which flow asked, because the flow is what supplies the thing the
stage reads: its briefing, its schema, its graph and its dials. Falling back to every tracked flow is an
unbounded default that spends money at the last verb and burns a paid model call at the first — at
catalogue scale "everything tracked" is not a selection, it is the absence of one. The selection repeats
because flows batch: every flow named in one rendering invocation renders on one endpoint, and a second
boot costs what eight more renders would, so a flow left off the line is a flow that pays for its own
boot.

A serving verb does not batch, so the reason the flag repeats does not reach it. What it opens is a
surface showing one schema's fields in one fixed order, and two flows on that surface would be two
layouts, two field orders and two token budgets sharing one set of controls — a second page rather than
a wider one. Requiring exactly one keeps the limit where an operator meets it, at the command they
typed, rather than at a screen that half-works.

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

#### Scenario: a serving verb takes exactly one flow
- **Key:** `cli:flow-selection:a-serving-verb-takes-one-flow`
- **Layers:** unit
- **WHEN** a verb that serves a surface is given more than one flow
- **THEN** the invocation is refused
- **AND** the message states that the surface serves one flow at a time

## REMOVED Requirements

### Requirement: Every per-flow seam is resolved per flow, on the model that flow names

**Reason**: Its scenario said a seam this build pins resolves for every flow; a flow now declares whether
it needs the tagger, and the local tagger resolves only for a flow that does. The requirement that replaces
it keeps the per-flow resolution, the uncomposed wiring's refusal and the two-models rule unchanged.

**Migration**: None for either tracked flow — both declare the tagger.

## ADDED Requirements

### Requirement: Every per-flow seam is resolved per flow, on the model that flow names, for a flow that declares its stage

The system SHALL resolve every seam a stage reaches — the reader and each tagger — once per flow being acted
on, rather than once for the whole invocation, so that a single command naming several flows runs each flow
on the model its own manifest declares. A seam a flow selects by manifest key SHALL construct nothing until a
flow asks for it, and a seam this build pins, whose model no manifest names, SHALL resolve for every flow
whose manifest declares the stage that seam serves. A front
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
such claim: there is no flow for which it would be the wrong model, it reaches no network, and the manifest
names none of its files. **Whether a flow is tagged at all is a different question, and the manifest now
answers it**: flows that need no tag list are coming, so a flow declares whether it needs the tagger, and
still nothing about which model tags. What both cases share — and what this requirement is actually protecting — is that resolution happens
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

#### Scenario: a pinned seam resolves for every flow that declares its stage
- **Key:** `cli:resolution:a-pinned-seam-resolves-for-every-flow-that-declares-it`
- **Layers:** unit
- **WHEN** the tag verb runs against a flow that declares the tagger and names no model for the local tagger
- **THEN** the local tagger is resolved and runs
- **AND** the flow's manifest names none of the local tagger's files

#### Scenario: one command runs two flows on the models each declares
- **Key:** `cli:resolution:one-command-two-models`
- **Layers:** unit
- **WHEN** a stage verb is given two flows whose manifests name different models
- **THEN** each flow's artifact names the model its own manifest declared
- **AND** neither flow is run on the other's
