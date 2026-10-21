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
