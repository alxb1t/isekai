## REMOVED Requirements

### Requirement: Every stage verb requires the flows it acts on, and takes more than one

**Reason:** its last clause made the serving verb take exactly one flow; the serving verb now takes no flow at all,
and a requirement cannot drop a scenario in place.

**Migration:** the stage verbs' rule is unchanged, under *A stage verb requires the flows it acts on, and takes more
than one*, with the same scenario keys. The serving verb's arguments are the `ui` capability's *The surface serves
one library, from a verb that takes no arguments*.

## ADDED Requirements

### Requirement: A stage verb requires the flows it acts on, and takes more than one

The system SHALL require a flow selection on every stage verb — reading, tagging, filling a sheet, reviewing,
approving and rendering — SHALL accept the selection more than once in a single invocation, and SHALL refuse an
invocation that names none, naming the flows that are tracked. It SHALL NOT fall back to every tracked
flow. It SHALL refuse a flow that is not tracked, at the point of selection, naming the flows that are.

The flow supplies what a stage reads — its briefing, its schema, its graph and its dials — so a stage cannot act
without one, and every tracked flow is an unbounded default that spends at the last verb. The selection repeats
because flows batch: every flow named in one rendering invocation shares one boot. The serving verb is not a stage
verb: it serves every tracked flow of every batch, and its page selects one.

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

## MODIFIED Requirements

### Requirement: A comparison page shows every run's photograph beside its renders

The system SHALL offer a verb that, given a batch directory holding a `runs/` directory, writes one HTML page into
that batch directory showing, for each run, the run's photograph and every render of each flow's latest approval,
each render labelled by its flow and seed and carrying the positive prompt it came from, with each flow's caption
and a run without a render marked. The page SHALL link every image by a path relative to itself and SHALL embed
none. The verb SHALL print only the page's path, and SHALL refuse, naming the directory, a batch directory that
holds no `runs/`.

A batch ends in a question a person answers by eye: which flow kept whom. The page answers it without an agent
reading the run directories. Linking keeps the page small and every image where the run put it; printing only the
path lets an agent hand the page over unread.

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
