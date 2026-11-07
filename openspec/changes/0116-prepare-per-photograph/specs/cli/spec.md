## ADDED Requirements

### Requirement: The prepare verb takes each photograph through tagging, reading and its cells' sheets in turn

The system SHALL offer a `prepare` verb over cells, each named `<run-id>/<flow>`, that takes each photograph, in the
order its first cell is named, through tagging — only when one of its cells' flows declares the tagger — then
reading, then the sheet of each of its cells in the order named, before it starts the next photograph. It SHALL tag
and read a photograph once however many of its cells are named, and SHALL open the local tagger at most once per
invocation. It SHALL refuse the whole invocation, before any run is opened, when a cell is not `<run-id>/<flow>`, names
a flow that is not tracked, naming the tracked flows, or names no run under the runs root. A cell whose flow directory
is absent when its sheet's turn comes SHALL refuse, naming the command that assigns it, and nothing SHALL be written
for that cell. Each refusal SHALL cost only its own step, and every refusal SHALL be reported together at the end.
With `--progress json` it SHALL print the lines `tag`, `caption` and `sheet` print, a photograph's naming no flow and a
sheet's naming its flow.

A photograph's sheet is ready as soon as that photograph is, so review can begin on the first while the rest prepare.
One local model reads every photograph, so they go one after another. The tagger's load hashes and reads a large
graph, so it is paid once. A cell is named whole because each photograph's assigned flows differ, and a cell unticked
since it was named is the operator's choice, never one to undo by making its directory again.

```
prepare r1/summon r2/summon r2/conjure
  r1  tag ─▶ caption ─▶ sheet summon
  r2  tag ─▶ caption ─▶ sheet summon ─▶ sheet conjure
```

#### Scenario: each photograph is prepared before the next is tagged
- **Key:** `cli:prepare:each-photograph-in-turn`
- **Layers:** unit
- **WHEN** `prepare` runs over cells of two photographs with `--progress json`
- **THEN** the first photograph's `tag`, `caption` and `sheet` lines all come before the second photograph's first
  line
- **AND** each photograph's lines come in the order tag, caption, sheet

#### Scenario: a photograph is tagged and read once for all its cells
- **Key:** `cli:prepare:a-photograph-is-described-once`
- **Layers:** unit
- **WHEN** two cells of one photograph are named
- **THEN** its `tag` and `caption` lines report once each, naming no flow
- **AND** each cell's `sheet` lines name its flow

#### Scenario: the local tagger opens once
- **Key:** `cli:prepare:the-tagger-opens-once`
- **Layers:** unit
- **WHEN** `prepare` tags two photographs
- **THEN** the local tagger is opened once

#### Scenario: a cell no longer assigned refuses its sheet
- **Key:** `cli:prepare:an-unassigned-cell-refuses`
- **Layers:** unit
- **WHEN** a named cell's flow directory is absent when its sheet's turn comes
- **THEN** its `sheet` line is `refused`, its message naming `assign`, and the flow's directory is still absent
- **AND** the photograph's other cells are still sheeted, and the invocation exits 1

#### Scenario: a bad cell is refused before any run is opened
- **Key:** `cli:prepare:a-bad-cell-is-refused`
- **Layers:** unit
- **WHEN** a cell names a flow that is not tracked, holds no `/`, or names no run under the runs root
- **THEN** the invocation is refused, naming the flows that are tracked for a flow that is not, and the cell otherwise
- **AND** no run is opened and nothing is written
