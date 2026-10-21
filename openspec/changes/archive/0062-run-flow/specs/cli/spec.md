## MODIFIED Requirements

### Requirement: A stage verb requires the flows it acts on, and takes more than one

The system SHALL require a flow selection on every stage verb — reading, tagging, filling a sheet, reviewing,
approving and rendering — SHALL accept the selection more than once in a single invocation, and SHALL refuse an
invocation that names none, naming the flows that are tracked. It SHALL NOT fall back to every tracked
flow. It SHALL refuse a flow that is not tracked, at the point of selection, naming the flows that are.

The flow supplies what a stage reads — its briefing, its schema, its graph and its dials — so a stage cannot act
without one, and every tracked flow is an unbounded default that spends at the last verb. The selection repeats
because flows batch: every flow named in one rendering invocation shares one boot. The serving verb is not a stage
verb: it serves the flows its configuration offers, of every batch, and its page selects one.

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

## ADDED Requirements

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
