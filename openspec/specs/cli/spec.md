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
count of renders per photograph or an explicit list of seeds but not both, and SHALL default to the
count each photograph's newest approval states, one where it states none.

Rendering is where the money is, and a boot costs more than a render, so one photograph per invocation is mostly
overhead. Many identifiers let one boot serve a batch. With nothing asked for, the approval says how many, because
that is the number a person agreed to; one is the default where it says nothing, because the cheap option is what
happens then.

#### Scenario: several photographs render in one invocation
- **Key:** `cli:generate-signature:accepts-many-identifiers`
- **Layers:** unit
- **WHEN** several run identifiers are given
- **THEN** all of them are prepared and rendered in one invocation
- **AND** the endpoint is acquired once

#### Scenario: the count defaults to one
- **Key:** `cli:generate-signature:count-defaults-to-one`
- **Layers:** unit
- **WHEN** no count and no seed is given for a photograph whose approval states no count
- **THEN** one render is produced for it per approved flow
- **AND** its seed is drawn rather than fixed

#### Scenario: the count defaults to the approval's
- **Key:** `cli:generate-signature:count-defaults-to-the-approvals`
- **Layers:** unit
- **WHEN** no count and no seed is given for a photograph whose approval states a count of three
- **THEN** three renders are produced for it
- **AND** their seeds are drawn rather than fixed

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
stage, and what produced each one. It SHALL list every failure record under the stage or render group that
holds it, and SHALL name every file or directory below a flow's directory that it does not read.

A filename carries only what resume decides on, which leaves a directory that is precise and unreadable.
This command is what a person reads instead — and it is also the answer to "where is this run", which is
why no progress file is needed before something other than a human is watching. It reads a run in any
state, so a failure it hides, or a name it skips, is a run it describes as other than it is.

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

#### Scenario: failure records are listed under their stage
- **Key:** `cli:show:failure-records-are-listed`
- **Layers:** unit
- **WHEN** a stage or a render group holds failure records
- **THEN** each record is listed under it with its version, its attempt and its kind
- **AND** a stage whose only content is failure records is not reported as empty

#### Scenario: a name it does not read is named
- **Key:** `cli:show:an-unread-name-is-named`
- **Layers:** unit
- **WHEN** a flow's directory, a stage directory or the render outputs hold a file or directory the report does not read
- **THEN** the report names it as not read
- **AND** it lists the run's artifacts as it would otherwise

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

The system SHALL offer a verb that, given a collection directory holding a `runs/` directory, writes one HTML page into
that collection directory showing, for each run, the run's photograph and every render of each flow's latest approval,
each render labelled by its flow and seed and carrying the positive prompt it came from, with each flow's caption
and a run without a render marked. The page SHALL link every image by a path relative to itself and SHALL embed
none. The verb SHALL print only the page's path, and SHALL refuse, naming the directory, a collection directory that
holds no `runs/`.

A batch ends in a question a person answers by eye: which flow kept whom. The page answers it without an agent
reading the run directories. Linking keeps the page small and every image where the run put it; printing only the
path lets an agent hand the page over unread.

#### Scenario: the page links each photograph to its renders
- **Key:** `cli:compare:the-page-links-photographs-to-renders`
- **Layers:** unit
- **WHEN** the verb is run on a collection whose runs hold renders from more than one flow
- **THEN** the page holds one entry per run, with its photograph and each flow's renders labelled by flow and seed
- **AND** every image is linked by a relative path and none is embedded

#### Scenario: a run with no render is marked
- **Key:** `cli:compare:a-run-without-a-render-is-marked`
- **Layers:** unit
- **WHEN** a run in the collection has no render for a flow
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

### Requirement: A stage verb requires the flows it acts on, and takes more than one

The system SHALL require a flow selection on every stage verb — reading, tagging, filling a sheet, reviewing,
approving and rendering — SHALL accept the selection more than once in a single invocation, and SHALL refuse an
invocation that names none, naming the flows that are tracked. It SHALL NOT fall back to every tracked
flow. It SHALL refuse a flow that is not tracked, at the point of selection, naming the flows that are.

The flow supplies what a stage reads — its briefing, its schema, its graph and its dials — so a stage cannot act
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

### Requirement: Assigning a flow writes its run and the flow's empty directory, and nothing else

The system SHALL offer a verb that, for each named flow and source, creates the source's run when absent and that
flow's empty directory in it, calls no model and writes no other file, and does nothing for a flow already
assigned. With `--remove` it SHALL delete a flow's directory only while it is empty, and SHALL refuse, naming the
run and the flow, when it is not.

A tick is the operator's choice, written as the layout's own fact: a run holding a flow's directory is assigned to
it. Unticking may not delete work, so only an empty directory goes.

#### Scenario: assigning creates the run and the flow's directory
- **Key:** `cli:assign:assigning-creates-the-run-and-the-flow`
- **Layers:** unit
- **WHEN** a flow is assigned to a source with no run
- **THEN** the run exists with the flow's directory, empty
- **AND** no other file is written and no model is called

#### Scenario: assigning an assigned flow writes nothing
- **Key:** `cli:assign:assigning-again-writes-nothing`
- **Layers:** unit
- **WHEN** a flow already assigned is assigned again
- **THEN** no file changes

#### Scenario: removing an empty assignment deletes its directory
- **Key:** `cli:assign:removing-an-empty-flow-deletes-it`
- **Layers:** unit
- **WHEN** an assigned flow whose directory is empty is removed
- **THEN** that directory is gone

#### Scenario: removing a prepared flow is refused
- **Key:** `cli:assign:removing-a-prepared-flow-is-refused`
- **Layers:** unit
- **WHEN** a flow whose directory holds a file is removed
- **THEN** the invocation is refused naming the run and the flow
- **AND** no file changes

### Requirement: A stage verb reports its progress as JSON lines when asked

The system SHALL, when `tag`, `caption` or `sheet` is given `--progress json`, print one JSON object per line on
standard output for each item's start, completion and refusal, naming the run, the flow, the stage, the state and,
for a refusal, its message; it SHALL print its human lines on standard error instead. Without the flag, its output
SHALL be unchanged.

A program reading a stage's progress reads a format meant for it, never sentences meant for a person.

```
{"run": "0d4b7e6fb2a8_portrait", "flow": "summon-anime-wai", "stage": "caption", "state": "start"}
{"run": "0d4b7e6fb2a8_portrait", "flow": "summon-anime-wai", "stage": "caption", "state": "done"}
```

#### Scenario: each item reports its start and its end
- **Key:** `cli:progress:each-item-reports-start-and-end`
- **Layers:** unit
- **WHEN** a stage verb runs over a run with `--progress json`
- **THEN** standard output holds a `start` line and a `done` line for that run, each one JSON object
- **AND** the human lines are on standard error

#### Scenario: a refusal is a line with its message
- **Key:** `cli:progress:a-refusal-is-a-line`
- **Layers:** unit
- **WHEN** an item refuses under `--progress json`
- **THEN** a `refused` line carries its message
- **AND** the other items still report

#### Scenario: without the flag the output is unchanged
- **Key:** `cli:progress:without-the-flag-nothing-changes`
- **Layers:** unit
- **WHEN** a stage verb runs without `--progress`
- **THEN** standard output holds its human lines

### Requirement: A render with no request renders every approval short of its count

The system SHALL, when the rendering verb names one or more collections' runs roots and no request, render in one
session, collection after collection in the order named, for every run of each and every flow its directory holds whose
newest approval holds fewer images than its count; SHALL skip a run that has no directory for a flow; and SHALL leave
out a flow a run holds without an approval, naming the run and the flow on standard error. A request
`<flow>=<count|source>` SHALL keep its meaning beside one runs root, and SHALL be refused beside a second.

The operator approves what to render, so the verb renders what is approved and not yet made. A source may hold only some
flows, and a draft still being corrected waits for its approval rather than holding up the rest. One boot serves every
collection named, so a second collection costs its images and no second pod.

#### Scenario: what is short is rendered
- **Key:** `cli:render-short:what-is-short-is-rendered`
- **Layers:** unit
- **WHEN** a runs root holds an approval of count two with one image and another with its two
- **THEN** one image is rendered, for the first
- **AND** nothing is rendered for the second

#### Scenario: a run without the flow is skipped
- **Key:** `cli:render-short:a-run-without-the-flow-is-skipped`
- **Layers:** unit
- **WHEN** a run holds no directory for a flow another run is approved in
- **THEN** that run is not rendered for the flow and is not refused

#### Scenario: an unapproved flow is left out
- **Key:** `cli:render-short:an-unapproved-flow-is-left-out`
- **Layers:** unit
- **WHEN** a run holds a flow's directory and no approval for it, and another run's approval is short
- **THEN** the other run is rendered and the first is not
- **AND** standard error names the run and the flow left out

#### Scenario: many collections render in one session
- **Key:** `cli:render-short:many-collections-render-in-one-session`
- **Layers:** unit
- **WHEN** the verb names two collections' runs roots, each short of an image
- **THEN** one session renders both, the first collection's lines before the second's
- **AND** a request beside the two runs roots is refused before anything is rented

### Requirement: A render session's limit is estimated from its work, at most the configured ceiling

The system SHALL bound a render session by a limit: the one `--limit` names, or else one boot plus the images it will
render, of every collection it names, times the median duration of that flow's last recorded renders in that
collection, plus teardown, times the configured factor,
with configured figures where nothing is recorded, and never below the pod's provisioning hold plus five minutes. It
SHALL refuse a limit above the ceiling `gpunit.toml` names, and SHALL give the same estimate the surface quotes.

A fixed limit caps a batch at what fits in it; a limit from the work fits the work, and the ceiling still bounds the
spend. A pod held for diagnosis must stop after its hold ends, not before.

#### Scenario: the estimate comes from recorded durations
- **Key:** `cli:render-limit:the-estimate-comes-from-durations`
- **Layers:** unit
- **WHEN** a flow's last renders took a median of ninety seconds and four images will render
- **THEN** the limit is boot plus four times ninety seconds plus teardown, times the factor

#### Scenario: with nothing recorded the configured figure is used
- **Key:** `cli:render-limit:the-configured-figure-without-records`
- **Layers:** unit
- **WHEN** no render of a flow carries a duration
- **THEN** the estimate uses the configured time per image

#### Scenario: a short session's limit is the floor
- **Key:** `cli:render-limit:a-short-session-takes-the-floor`
- **Layers:** unit
- **WHEN** the estimate for one image is shorter than the hold plus five minutes
- **THEN** the limit is the hold plus five minutes

#### Scenario: a limit above the ceiling is refused
- **Key:** `cli:render-limit:above-the-ceiling-is-refused`
- **Layers:** unit
- **WHEN** a limit above `gpunit.toml`'s ceiling is given
- **THEN** the invocation is refused naming the ceiling
- **AND** no session is opened

#### Scenario: one boot for many collections
- **Key:** `cli:render-limit:one-boot-for-many-collections`
- **Layers:** unit
- **WHEN** the limit is estimated for two collections
- **THEN** it holds one boot and one teardown, and both collections' images

### Requirement: A render session reports its steps as JSON lines when asked

The system SHALL, when the rendering verb is given `--progress json`, print one JSON object per line on standard
output as the session opens its pod, renders each image and tears its pod down, each naming its step, its state and,
for an image, its number of the total, and SHALL report the teardown of a session that ends in a refusal; it SHALL
print its human lines on standard error instead.

The surface shows a session as the verb reports it, so a session that never reported its teardown would read as one
still billing.

#### Scenario: a session reports each image of the total
- **Key:** `cli:render-progress:each-image-of-the-total`
- **Layers:** unit
- **WHEN** a session renders two images with `--progress json`
- **THEN** standard output holds a line for image one of two and image two of two
- **AND** a line for the teardown's end

#### Scenario: a refused session reports its teardown
- **Key:** `cli:render-progress:a-refused-session-reports-its-teardown`
- **Layers:** unit
- **WHEN** a session's endpoint never answers, with `--progress json`
- **THEN** its last line on standard output is the teardown's end

### Requirement: The revise verb takes image paths, and writes every draft or none

The system SHALL offer a verb that takes the paths of rendered images, reads from each its run, flow, approval and
seed, checks every image before writing anything — the image exists, its approval can be read, its flow holds no
unapproved draft, and no two images share a run and flow — and then writes a revision for each, or, when any check
fails, writes nothing and names every image that failed, with its reason. It SHALL tell two images' runs apart by
the identity of their directories, never by the text of their paths.

An image's path names everything a revision needs, so the verb takes nothing else. A selection is revised whole or
not at all, so a retry after a fix does not meet the drafts the first try wrote. Two spellings of one run are one
run, and only its identity says so.

#### Scenario: every image is revised
- **Key:** `cli:revise:every-image-is-revised`
- **Layers:** unit
- **WHEN** the verb is given two images from different runs
- **THEN** each run's flow gains a revision of its image

#### Scenario: one refusal writes nothing
- **Key:** `cli:revise:one-refusal-writes-nothing`
- **Layers:** unit
- **WHEN** one image given has its flow's draft waiting, an unreadable approval, or another image's run and flow
- **THEN** no draft is written for any image
- **AND** the refusal names that image and its reason

### Requirement: The approve verb cancels an approval with `--cancel`

The system SHALL take `--cancel` on `isekai approve`, cancelling each named run's approval in each named flow through
the review stage, SHALL answer each run on its own so one refusal stops no other, and SHALL refuse `--cancel` beside
`--from`.

A cancel is the review stage's act, so the verb composes it and decides nothing; a collection is many runs, and one
refused run must not cost the rest.

#### Scenario: each run is cancelled on its own
- **Key:** `cli:approve-cancel:each-run-on-its-own`
- **Layers:** unit
- **WHEN** `approve --cancel` names a cancellable run and a run with a prompt
- **THEN** the first is a draft again and the second is refused naming its prompt

#### Scenario: cancel beside from is refused
- **Key:** `cli:approve-cancel:not-beside-from`
- **Layers:** unit
- **WHEN** `approve` is given `--cancel` and `--from`
- **THEN** it is refused before any run is read

### Requirement: The review verb drafts from another flow's approval with `--from`

The system SHALL take `--from FLOW` on `isekai review`, drafting each named flow of each named run from that flow's
approval through the review stage, first assigning a named flow that holds no sheet and filling its sheet from the
source's tag list, of the version `--version N` names, else the source's newest approval. It SHALL
answer each run on its own, and SHALL refuse, before any run is read, `--from` beside `--discard` or
`--new-version`, `--version` without `--from`, and a source that is a named flow or no tracked flow.

The draft is the review stage's act, so the verb composes it and decides nothing. The newest approval is the one the
operator just finished, so it needs no number. A target with no sheet needs no Prepare: the source's tags are
the target's.

#### Scenario: each flow is drafted from the source's newest approval
- **Key:** `cli:review-from:each-flow-is-drafted-from-the-newest-approval`
- **Layers:** unit
- **WHEN** `review --from` names a source holding two approvals and no `--version`
- **THEN** each named flow's draft is drafted from the source's newest approval
- **AND** with `--version 1` it is drafted from approval one

#### Scenario: a target with no sheet is assigned and filled first
- **Key:** `cli:review-from:a-target-with-no-sheet-is-filled-first`
- **Layers:** unit
- **WHEN** `review --from` names a target the run is not assigned to
- **THEN** the target is assigned, its sheet filled from the source's tag list, and its draft written
- **AND** no caption or tag list is written for the target

#### Scenario: a conflicting option is refused before any run is read
- **Key:** `cli:review-from:a-conflicting-option-is-refused`
- **Layers:** unit
- **WHEN** `review --from` is given beside `--discard`, or `--version` without `--from`
- **THEN** it is refused naming the options
- **AND** no run is read

### Requirement: A render session writes its record into the collection, from its start to its end

The system SHALL, once a render session asks for a pod, write a record to each collection's `sessions/` folder it
renders, beside its log, every record holding the session's id and naming the other collections in `collections`, named
by the session's id — the id `--session` gives, else the start in UTC as `20261024T091200Z` — and SHALL replace a record
whole as each of its collection's images lands and as the session ends, the pod's and the teardown's steps in every
record; the session's log lines SHALL go to every collection's log, and every record SHALL name the complete
traversal in `collection_order`, including its own collection. The record SHALL hold the id, the start, the end,
the limit, what each flow was asked to render and what it plans for each photograph, the pod's and the teardown's steps,
each image as its run digest, flow, version and seed in order, and the outcome — running, done, stopped or failed, with
its message — and no price. A session refused before anything is rented SHALL write no record. An existing id SHALL be
refused without replacing its record or asking for a pod, including when concurrent starts choose the same id.

The state of a session lives on disk, so a page, a second tab, a restarted surface and a render started in the
terminal all read the same truth; no price follows the quote.

```
free checks ─▶ claim id + lifetime lock ─▶ running record ─▶ images ─▶ ended record ─▶ release lock
                    └ occupied ─▶ refuse without asking for a pod
```

#### Scenario: a session writes its record
- **Key:** `cli:render-session:a-session-writes-its-record`
- **Layers:** unit
- **WHEN** a session renders two images
- **THEN** its record names both images in order and the outcome done
- **AND** it holds no price

#### Scenario: the record follows each image
- **Key:** `cli:render-session:the-record-follows-each-image`
- **Layers:** unit
- **WHEN** a session has rendered its first of two images
- **THEN** its record reads running, with that one image

#### Scenario: the given id names the record
- **Key:** `cli:render-session:the-given-id-names-the-record`
- **Layers:** unit
- **WHEN** a session is run with `--session 20261024T091200Z`
- **THEN** its record is `sessions/20261024T091200Z.json`

#### Scenario: a refusal before renting writes no record
- **Key:** `cli:render-session:a-refusal-before-renting-writes-none`
- **Layers:** unit
- **WHEN** a session is refused before it asks for a pod
- **THEN** no record is written

#### Scenario: an owned id is refused
- **Key:** `cli:render-session:an-owned-id-is-refused`
- **Layers:** unit
- **WHEN** another session chooses an id whose record already exists, explicitly or automatically
- **THEN** it refuses before asking for a pod and leaves the existing record unchanged

#### Scenario: concurrent starts reserve one record
- **Key:** `cli:render-session:concurrent-starts-reserve-one-record`
- **Layers:** unit
- **WHEN** concurrent starts choose the same unused id
- **THEN** exactly one owns the complete record and the other refuses

#### Scenario: the record plans each photograph
- **Key:** `cli:render-session:the-record-plans-each-photograph`
- **Layers:** unit
- **WHEN** a session is asked for two images of one run and one of another
- **THEN** its record plans each run and flow with its number of images

#### Scenario: each collection holds its record
- **Key:** `cli:render-session:each-collection-holds-its-record`
- **Layers:** unit
- **WHEN** a session renders two collections
- **THEN** each collection's record holds the shared id, its own images and plan, and the complete collection order
- **AND** both records hold the pod's and the teardown's steps, and both logs the session's lines

