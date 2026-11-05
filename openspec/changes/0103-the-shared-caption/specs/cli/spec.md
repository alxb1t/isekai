## ADDED Requirements

### Requirement: A stage verb on a flow requires the flows it acts on, and the photograph's verbs take none

The system SHALL require a flow selection on every stage verb that acts on a flow — filling a sheet, reviewing,
approving and rendering — SHALL accept the selection more than once in a single invocation, and SHALL refuse an
invocation that names none, naming the flows that are tracked. It SHALL NOT fall back to every tracked flow. It SHALL
refuse a flow that is not tracked, at the point of selection, naming the flows that are. The tagging and reading verbs
act on the photograph: they SHALL take no flow, and SHALL refuse an invocation naming one before any artifact is
written, naming the command without it.

The flow supplies what a stage reads — its schema, its graph and its dials — so a stage on a flow cannot act without
one, and every tracked flow is an unbounded default that spends at the last verb. The selection repeats because flows
batch: every flow named in one rendering invocation shares one boot. A photograph's caption and tag lists are every
flow's, so a flow named to them selects nothing, and a stale command is refused rather than passed silently. The
serving verb is not a stage verb: it serves the flows its configuration offers, of every collection, and its page
selects one.

#### Scenario: a stage verb without a flow is refused
- **Key:** `cli:flow-selection:a-stage-verb-requires-a-flow`
- **Layers:** unit
- **WHEN** a stage verb that acts on a flow is invoked with no flow named
- **THEN** the invocation is refused
- **AND** the message lists the tracked flows

#### Scenario: the selection repeats
- **Key:** `cli:flow-selection:the-flag-is-repeatable`
- **Layers:** unit
- **WHEN** a stage verb is given more than one flow
- **THEN** every named flow is acted on in that one invocation
- **AND** no named flow is silently dropped

#### Scenario: every stage verb on a flow accepts it
- **Key:** `cli:flow-selection:every-stage-verb-accepts-it`
- **Layers:** unit
- **WHEN** each stage verb on a flow — `sheet`, `review`, `approve` and `generate` — is invoked with a flow named
- **THEN** none of them rejects the flag as unrecognised
- **AND** `tag`, `caption` and the inspection verb are the ones that refuse it

#### Scenario: the photograph's verbs refuse a flow
- **Key:** `cli:flow-selection:the-photographs-verbs-refuse-a-flow`
- **Layers:** unit
- **WHEN** `tag` or `caption` is given a flow
- **THEN** the invocation is refused, naming the command without it
- **AND** nothing is written

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

### Requirement: Every seam is resolved with no flow, on the configured model, and constructs nothing until it is asked

The system SHALL resolve every seam a stage reaches — the reader and each tagger — with no flow, SHALL run the reader
and the hosted tagger on the one model the caption config names, and SHALL construct nothing until a verb asks for a
seam. A front end that serves no hosted-model stage SHALL remain able to compose a wiring with none of them at all, and
SHALL refuse naming the seam if a verb that needs one is then invoked through it.

The reader and the taggers read the photograph, never a flow, so nothing a flow holds could select one. Which model
answers is a claim the library makes once, in its caption config
([D6](../../../docs/decisions.md#d6--ollama-at-a-fixed-local-address-on-a-checked-model)); a seam reading a file this
build pins makes no such claim, and no manifest names its files. A front end that only reviews sheets composes no seam
rather than fabricating doubles.

#### Scenario: a wiring composed without a hosted-model seam still refuses by name
- **Key:** `cli:resolution:uncomposed-seam-refuses-by-name`
- **Layers:** unit
- **WHEN** a verb that reaches a hosted model is invoked through a wiring composed without one
- **THEN** it refuses naming the seam and what that seam does
- **AND** no double is substituted for it

#### Scenario: the pinned tagger resolves with no flow
- **Key:** `cli:resolution:the-pinned-tagger-needs-no-flow`
- **Layers:** unit
- **WHEN** the tag verb runs
- **THEN** the local tagger is resolved and runs
- **AND** no flow's manifest names any of the local tagger's files

#### Scenario: the reader and the hosted tagger run the configured model
- **Key:** `cli:resolution:one-command-one-model`
- **Layers:** unit
- **WHEN** the reader and the hosted tagger are resolved
- **THEN** each runs the model the caption config names

### Requirement: The migrate verb copies each run's description into photo/ once, and leaves the old files

The system SHALL offer `isekai migrate`, which walks the default runs root and every collection's runs root in the
library, or the one runs root `--runs` names, and for each run copies into `photo/`, byte for byte, each kind of
description its flows hold that `photo/` lacks — the caption, the WD14 list and the hosted tags — printing one line per
run. A tag list's kind SHALL be copied only where every flow holding it holds the same numbered lists with the same
tags, under the same numbers; the caption SHALL be the newest any flow holds. A run whose flows' lists differ SHALL be
refused by name, naming the kind and the flows, and nothing of it copied. It SHALL leave every file it copies from in
place, SHALL copy each kind whole or not at all, and run a second time SHALL change nothing.

```
runs/<id>/summon-anime-wai/wd14/001.json ─┐ equal lists ──▶ runs/<id>/photo/wd14/001.json
runs/<id>/control-anime-wai/wd14/001.json ┘ else the run is refused, nothing copied
runs/<id>/<flow>/captions/<newest>       ──────────────▶ runs/<id>/photo/captions/001.json
```

The tag lists come from one pinned model, one floor and one prompt at temperature 0, so lists that differ mean
something changed between two tagging passes, and the operator decides which holds. Each flow was captioned on its own,
so two captions may differ in wording; the newest is the latest reading. A list keeps its number, so a sheet's record
of the list it was filled from names the same list under `photo/`. The old files stay, so nothing is lost until the
operator deletes them.

#### Scenario: a second run changes nothing
- **Key:** `cli:migrate:a-second-run-changes-nothing`
- **Layers:** unit
- **WHEN** `isekai migrate` runs twice over a library
- **THEN** the second run changes no byte
- **AND** it reports each run already migrated

#### Scenario: the old files stay
- **Key:** `cli:migrate:the-old-files-stay`
- **Layers:** unit
- **WHEN** a run is migrated
- **THEN** every caption and tag list under its flows is unchanged
- **AND** `photo/` holds a copy of each kind they hold

#### Scenario: lists that differ refuse the run
- **Key:** `cli:migrate:differing-lists-refuse-the-run`
- **Layers:** unit
- **WHEN** two flows of a run hold different WD14 lists
- **THEN** the run is refused, naming the kind and the flows
- **AND** nothing is copied for it

#### Scenario: the newest caption is kept
- **Key:** `cli:migrate:the-newest-caption-is-kept`
- **Layers:** unit
- **WHEN** two flows of a run hold captions written at different times
- **THEN** `photo/captions/` holds the newer, byte for byte

#### Scenario: a list keeps its number
- **Key:** `cli:migrate:a-list-keeps-its-number`
- **Layers:** unit
- **WHEN** a run's flows hold WD14 lists numbered 001 and 002
- **THEN** `photo/wd14/` holds both, under the same numbers

#### Scenario: every collection is walked
- **Key:** `cli:migrate:every-collection-is-walked`
- **Layers:** unit
- **WHEN** the library holds two collections with runs to migrate
- **THEN** one line is printed for each run of each
- **AND** `--runs` walks the one runs root it names instead

#### Scenario: a kind is copied whole or not at all
- **Key:** `cli:migrate:a-kind-is-copied-whole`
- **Layers:** unit
- **WHEN** a run holds a partial copy a stopped migration left
- **THEN** the next run replaces it with the whole kind

## MODIFIED Requirements

### Requirement: Inspection prints the run directory with its provenance

The system SHALL provide a command that prints a run's artifacts, which version is active for each
stage, and what produced each one, listing the photograph's description under `photo/` once, before the flows. It
SHALL list every failure record under the stage or render group that holds it, and SHALL name every file or directory
below `photo/` or a flow's directory that it does not read, a caption or tag list left under a flow among them. It
SHALL read a run whose description sits under its flows as it reads any other.

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

#### Scenario: the description is listed once, before the flows
- **Key:** `cli:show:the-description-is-listed-once`
- **Layers:** unit
- **WHEN** a run holding a description and two flows is inspected
- **THEN** `photo/`'s caption and tag lists are listed once, before either flow's stages
- **AND** a caption left under a flow is named as not read

### Requirement: A stage verb reports its progress as JSON lines when asked

The system SHALL, when `tag`, `caption` or `sheet` is given `--progress json`, print one JSON object per line on
standard output for each item's start, completion and refusal, naming the run, the stage, the state, the flow for
`sheet`, and, for a refusal, its message; it SHALL print its human lines on standard error instead. Without the flag,
its output SHALL be unchanged.

A program reading a stage's progress reads a format meant for it, never sentences meant for a person. A caption and
a tag list are the photograph's, so their lines name no flow.

```
{"run": "0d4b7e6fb2a8_portrait", "stage": "caption", "state": "start"}
{"run": "0d4b7e6fb2a8_portrait", "stage": "caption", "state": "done"}
{"run": "0d4b7e6fb2a8_portrait", "flow": "summon-anime-wai", "stage": "sheet", "state": "done"}
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

#### Scenario: a photograph's line names no flow
- **Key:** `cli:progress:a-photographs-line-names-no-flow`
- **Layers:** unit
- **WHEN** `tag` or `caption` runs over a run with `--progress json`
- **THEN** its lines carry no flow
- **AND** a `sheet` line names its flow

### Requirement: The draft verb drafts a flow from image paths, and writes every draft or none

The system SHALL offer `isekai draft --flow FLOW <image>…`, which reads from each image path its run, flow, approval and
seed, checks every image before writing anything — the image exists, its approval can be read, the target holds no
waiting draft with edits of its own, and no two images share a run and target — and then writes, through the review
stage, a revision where `FLOW` is the image's own flow and a draft from its approval where it is another, assigning a
target with no sheet and filling its sheet from the photograph's tags; when any check fails it SHALL write nothing and
name every image that failed, with its reason. It SHALL tell two images' runs apart by the identity of their
directories, never by the text of their paths.

An image's path names everything a draft needs but its target, so the verb takes nothing else. A selection is drafted
whole or not at all, so a retry after a fix does not meet the drafts the first try wrote. A target with no sheet needs
no Prepare: the photograph's tags are every flow's.

#### Scenario: every image is revised
- **Key:** `cli:revise:every-image-is-revised`
- **Layers:** unit
- **WHEN** the verb is given two images from different runs and their own flow
- **THEN** each run's flow gains a revision of its image

#### Scenario: one refusal writes nothing
- **Key:** `cli:revise:one-refusal-writes-nothing`
- **Layers:** unit
- **WHEN** one image given has its target's edited draft waiting, an unreadable approval, or another's run and target
- **THEN** no draft is written for any image
- **AND** the refusal names that image and its reason

#### Scenario: a target with no sheet is assigned and filled first
- **Key:** `cli:review-from:a-target-with-no-sheet-is-filled-first`
- **Layers:** unit
- **WHEN** `draft --flow` names a target an image's run is not assigned to
- **THEN** the target is assigned, its sheet filled from the photograph's tag list, and its draft written
- **AND** no caption or tag list is written for the target

#### Scenario: another flow is drafted from the image
- **Key:** `cli:draft:another-flow-is-drafted-from-the-image`
- **Layers:** unit
- **WHEN** the verb is given a summon image and another flow
- **THEN** the target's draft holds the image's approval's shared fields, its seed and its image

## REMOVED Requirements

### Requirement: A stage verb requires the flows it acts on, and takes more than one

**Reason**: tagging and reading act on the photograph, so they take no flow.

**Migration**: *A stage verb on a flow requires the flows it acts on, and the photograph's verbs take none* replaces
it with the same keys and `cli:flow-selection:the-photographs-verbs-refuse-a-flow` added.

### Requirement: Every per-flow seam is resolved per flow, for a flow that declares its stage

**Reason**: no verb that reaches a seam names a flow.

**Migration**: *Every seam is resolved with no flow, on the configured model, and constructs nothing until it is
asked* replaces it; `cli:resolution:a-pinned-seam-resolves-for-every-flow-that-declares-it` gives way to
`cli:resolution:the-pinned-tagger-needs-no-flow`, and the other keys stay.
