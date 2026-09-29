# Capability: `cli`

## Purpose

The command-line surface: one entry point whose stage verbs report every refusal a batch produced together, beside
the inspection verb `show`, the serving verb `ui` and the page verb `compare`. `--seed` and `--count` are
range-checked at parse time, so a bad one fails before a pod is touched; a flow's dials live in its manifest, and no
flag reaches them.

## Requirements

### Requirement: The pipeline surface is the only entry point, and its verbs are subcommands

The system SHALL expose the staged pipeline as subcommands of a module entry point, and that entry
point SHALL be the only command-line surface the system offers.

A pipeline that stops for a human needs verbs. Subcommands under one parser keep argument handling in one place,
and the entry point's import guard to one target
([D20](../../../docs/decisions.md#d20--the-entry-point-loads-no-third-party-package)).

#### Scenario: the pipeline verbs are reachable as subcommands
- **Key:** `cli:pipeline-surface:verbs-are-subcommands`
- **Layers:** unit
- **WHEN** the pipeline entry point is invoked with a subcommand
- **THEN** that stage runs

#### Scenario: the pipeline entry point needs no third-party import
- **Key:** `cli:pipeline-surface:entry-point-is-stdlib-only`
- **Layers:** unit
- **WHEN** the pipeline entry point is imported with third-party packages unavailable
- **THEN** the import succeeds
- **AND** the guard proving that condition is genuinely unavailable still holds

#### Scenario: an unknown subcommand is refused at parse time
- **Key:** `cli:pipeline-surface:unknown-verb-is-refused`
- **Layers:** unit
- **WHEN** an unrecognised subcommand is given
- **THEN** the invocation is refused before any work begins
- **AND** the available subcommands are listed

### Requirement: The rendering verb takes many photographs and either a count or explicit seeds

The system SHALL accept several run identifiers in one rendering invocation, SHALL accept either a
count of renders per photograph or an explicit list of seeds but not both, and SHALL default to one
render per photograph.

Rendering is where the money is, and a boot costs more than a render, so one photograph per invocation is mostly
overhead. Many identifiers let one boot serve a batch. The default is one because the cheap option is what happens
when nothing is asked for.

#### Scenario: several photographs render in one invocation
- **Key:** `cli:generate-signature:accepts-many-identifiers`
- **Layers:** unit
- **WHEN** several run identifiers are given
- **THEN** all of them are prepared and rendered in one invocation
- **AND** the endpoint is acquired once

#### Scenario: the count defaults to one
- **Key:** `cli:generate-signature:count-defaults-to-one`
- **Layers:** unit
- **WHEN** no count and no seed is given
- **THEN** one render is produced per photograph per approved flow
- **AND** its seed is drawn rather than fixed

#### Scenario: a count and explicit seeds cannot be combined
- **Key:** `cli:generate-signature:count-and-seed-are-exclusive`
- **Layers:** unit
- **WHEN** both a count and one or more seeds are given
- **THEN** the invocation is refused at parse time
- **AND** the message states that the two are alternatives

### Requirement: A new artifact version is requested explicitly

The system SHALL do nothing when a stage's artifact already exists, and SHALL require an explicit flag
to produce a new version. The flag SHALL produce the next version of every artifact its own verb writes,
and of no artifact another verb writes.

Deciding automatically would make an invocation that sometimes spends and sometimes does not, decided by a field
the operator did not look at; a flag puts the spend in the command line that caused it. Each verb writes only its
own artifacts, so its flag asks for exactly those
([D1](../../../docs/decisions.md#d1--stage--is-two-independent-verbs)).

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

### Requirement: Re-running every command is the whole of resume

The system SHALL make running the pipeline's commands a second time, with the same arguments, change
no byte of the run directory and make no external call.

There is no state machine, so there is nothing to corrupt and nothing to repair. A crashed process, a
closed laptop and a week-long pause are the same event, and the answer to all three is the same
invocation. This is also the only assertion that can prove the state model works, and it needs no GPU
and no network.

#### Scenario: a second full pass changes nothing and calls nothing
- **Key:** `cli:resume:second-pass-is-inert`
- **Layers:** unit
- **WHEN** every pipeline command is run against a complete run, and then run again
- **THEN** not one byte of the run directory differs
- **AND** not one external call is made

### Requirement: Inspection prints the run directory with its provenance

The system SHALL provide a command that prints a run's artifacts, which version is active for each
stage, and what produced each one.

A filename carries only what resume decides on, which leaves a directory that is precise and unreadable.
This command is what a person reads instead — and it is also the answer to "where is this run", which is
why no progress file is needed before something other than a human is watching.

#### Scenario: inspection names the active version for each stage
- **Key:** `cli:show:active-version-is-marked`
- **Layers:** unit
- **WHEN** a run is inspected
- **THEN** each stage's versions are listed and the active one is marked
- **AND** approval is shown where the concept applies

#### Scenario: inspection reports what produced each artifact
- **Key:** `cli:show:producers-are-reported`
- **Layers:** unit
- **WHEN** a run is inspected
- **THEN** each artifact's producer is shown
- **AND** artifacts produced by different implementations are distinguishable in the output

#### Scenario: a frame it cannot read is marked
- **Key:** `cli:show:an-unreadable-frame-is-marked`
- **Layers:** unit
- **WHEN** a run's frame is unreadable, declares an unknown version, or lacks its photograph
- **THEN** the report marks the frame with its refusal in place of the photograph line
- **AND** it lists the run's flows and artifacts as it would otherwise

### Requirement: Every refusal names the action that would resolve it

The system SHALL end every refusal with the action the operator can take, and SHALL NOT name an action
this build cannot perform.

This generalises the posture the evaluator already takes for a missing optional dependency: the failure
states the command that fixes it. A refusal that names a remedy the build does not have is worse than
one that names none, because it sends the operator looking for something that is not there.

#### Scenario: a refusal states a remedy
- **Key:** `cli:refusals:refusal-names-the-remedy`
- **Layers:** unit
- **WHEN** any pipeline command refuses
- **THEN** the message names the action that would resolve it
- **AND** that action is available in this build

#### Scenario: a refusal exits with a failure status
- **Key:** `cli:refusals:refusal-exits-non-zero`
- **Layers:** unit
- **WHEN** any pipeline command refuses
- **THEN** the process exits with a failure status
- **AND** the reason is written to the error stream

### Requirement: Every stage verb requires the flows it acts on, and takes more than one

The system SHALL require a flow selection on every stage verb — reading, tagging, filling a sheet, reviewing,
approving and rendering — SHALL accept the selection more than once in a single invocation, and SHALL refuse an
invocation that names none, naming the flows that are tracked. It SHALL NOT fall back to every tracked
flow. It SHALL refuse a flow that is not tracked, at the point of selection, naming the flows that are.
A verb that serves a surface rather than running a stage SHALL require the selection and SHALL accept
it exactly once.

The flow supplies what a stage reads — its briefing, its schema, its graph and its dials — so a stage cannot act
without one, and every tracked flow is an unbounded default that spends at the last verb. The selection repeats
because flows batch: every flow named in one rendering invocation shares one boot. A serving verb does not batch,
and its surface shows one schema's fields in one order, so two flows would be two layouts behind one set of
controls.

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

#### Scenario: one flow's refusal leaves the input's other flows
- **Key:** `cli:flow-selection:one-flows-refusal-leaves-the-others`
- **Layers:** unit
- **WHEN** a stage verb names more than one flow, and one of them refuses for an input
- **THEN** the input's other named flows are still acted on
- **AND** every refusal is reported together at the end

### Requirement: A flow manifest is refused at load when its declarations do not resolve

The system SHALL refuse a flow manifest that names a node role whose id is absent from that flow's own
graph, and SHALL refuse one that omits a dial the roles it declares require. Both refusals SHALL happen
at load, before any endpoint is contacted and before any input is transferred.

A manifest not checked at load is checked by a render, which spends a rented GPU and an uploaded photograph on a
typo and fails as a bare lookup error no refusal collects. The dial check follows the roles a flow declares, not a
fixed list: a flow with no identity leg declares none of that leg's dials.

#### Scenario: a role naming a node the graph does not carry is refused
- **Key:** `cli:manifest:a-dangling-node-id-is-refused-at-load`
- **Layers:** unit
- **WHEN** a flow manifest names a node role whose id is absent from that flow's graph
- **THEN** loading it is refused naming the role and the id
- **AND** no endpoint is contacted and no input is transferred

#### Scenario: every role a tracked flow names resolves in its own graph
- **Key:** `cli:manifest:every-tracked-role-resolves`
- **Layers:** unit
- **WHEN** each tracked flow is loaded
- **THEN** every node id its roles name is present in that flow's graph

#### Scenario: every dial a tracked flow declares is one its roles read
- **Key:** `cli:manifest:every-tracked-dial-is-read`
- **Layers:** unit
- **WHEN** each tracked flow is loaded
- **THEN** every dial the roles it declares require is present in its manifest

### Requirement: Every per-flow seam is resolved per flow, on the model that flow names, for a flow that declares its stage

The system SHALL resolve every seam a stage reaches — the reader and each tagger — once per flow being acted
on, rather than once for the whole invocation, so that a single command naming several flows runs each flow
on the model its own manifest declares. A seam a flow selects by manifest key SHALL construct nothing until a
flow asks for it, and a seam this build pins, whose model no manifest names, SHALL resolve for every flow
whose manifest declares the stage that seam serves. A front end that serves no hosted-model stage SHALL remain
able to compose a wiring with none of them at all, and SHALL refuse naming the seam if a verb that needs one is
then invoked through it.

A flow supplies everything a stage reads, its model included, so a seam resolved above the loop over flows would
hand one flow's model to another while every artifact looked well-formed. A seam reaching a local runtime is named
in the manifest, because which model answers is a claim the flow makes about itself; a seam reading a file this
build pins makes no such claim, and the manifest names none of its files. Whether a flow is tagged at all is its
manifest's own key ([D31](../../../docs/decisions.md#d31--a-flow-declares-whether-it-is-tagged)). A front end that
only reviews sheets composes no seam rather than fabricating doubles.

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

### Requirement: A comparison page shows every run's photograph beside its renders

The system SHALL offer a verb that, given a batch directory holding a `runs/` directory, writes one HTML page into
that batch directory showing, for each run, the run's photograph and every render of each flow's latest approval,
each render labelled by its flow and seed and carrying the positive prompt it came from, with each flow's caption
and a run without a render marked. The page SHALL link every image by a path relative to itself and SHALL embed
none. The verb SHALL print only the page's path, and SHALL refuse, naming the directory, a batch directory that
holds no `runs/`.

A batch ends in a question a person answers by eye: which flow kept whom. The page answers it without an agent
reading the run directories, the reading the flow skills exist to avoid. Linking keeps the page small and every
image where the run put it; printing only the path lets an agent hand the page over unread.

#### Scenario: the page links each photograph to its renders
- **Key:** `cli:compare:the-page-links-photographs-to-renders`
- **Layers:** unit
- **WHEN** the verb is run on a batch whose runs hold renders from more than one flow
- **THEN** the page holds one entry per run, with its photograph and each flow's renders labelled by flow and seed
- **AND** every image is linked by a relative path and none is embedded

#### Scenario: a run with no render is marked
- **Key:** `cli:compare:a-run-without-a-render-is-marked`
- **Layers:** unit
- **WHEN** a run in the batch has no render for a flow
- **THEN** its entry says so for that flow
- **AND** the page is still written

#### Scenario: the verb prints only the page's path
- **Key:** `cli:compare:only-the-path-is-printed`
- **Layers:** unit
- **WHEN** the verb writes the page
- **THEN** its standard output is the page's path and nothing else

#### Scenario: a batch with no runs is refused
- **Key:** `cli:compare:a-batch-without-runs-is-refused`
- **Layers:** unit
- **WHEN** the verb is given a directory that holds no `runs/`
- **THEN** it refuses naming the directory
- **AND** nothing is written
