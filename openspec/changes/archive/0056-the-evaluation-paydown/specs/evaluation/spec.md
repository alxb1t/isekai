## MODIFIED Requirements

### Requirement: Every render is a row

The system SHALL write one record per batch holding, for every cohort photograph and every flow, the render's
seed, its nearest photograph and its outcome — a hit, a miss, no face found, unreadable, not rendered — and SHALL
print one table from that record alone, a row of counts per flow, each followed by its chance row. The render
ranked SHALL be the first seed of the flow's latest render group; where that group holds no render the row SHALL
say not rendered, and no earlier group SHALL be ranked in its place. The record and the table SHALL name a run
they score by its digest prefix alone. A run whose
frame, or one of whose flows, cannot be read SHALL be reported as unreadable, and its readable flows scored. The
record SHALL count the runs outside the cohort and the unreadable runs and name none of them, naming each on the
error stream alone, and SHALL be refused before anything is scored where git can reach it: inside the
repository's working tree and outside its ignored data root. No render's outcome, and no run's, SHALL end the
scoring of another.

```
                    photograph-level   person-level
summon-anime-wai         15 / 18           14 / 18
chance                  1.0 / 18          2.1 / 18
```

A table that shows only its wins is not evidence; a failure reported mid-batch scrolls away, and one damaged
file is no reason to lose the rest. A row per flow, with its own chance beneath it, is what lets a second flow be
read beside the first without a second tool. The latest group is the render the operator last made, and the one
a control flow's seeds are taken from; an empty one is a render that failed, not one to look past. A run's id
carries its photograph's digest and filename, and a run
outside the cohort is by construction not one of its synthetic people, so the record — the file a batch
publishes — names none, and is never written where one `git add` publishes it
([D18](../../../docs/decisions.md#d18--runs-stay-out-of-what-git-tracks)).
A run it does score is named by the digest half of its id, which still finds the run and carries no filename.

#### Scenario: one row per flow
- **Key:** `evaluation:table:one-row-per-flow`
- **Layers:** unit
- **WHEN** the runs hold renders of more than one flow
- **THEN** the table carries one row per flow, each with both counts
- **AND** each followed by the chance row over that flow's renders

#### Scenario: a failure is a row, never an exit
- **Key:** `evaluation:table:a-failure-is-a-row`
- **Layers:** unit
- **WHEN** one render has no face found and another photograph was never rendered
- **THEN** each is a row naming its outcome
- **AND** every other render is scored and written

#### Scenario: a render that does not decode is a row
- **Key:** `evaluation:table:an-unreadable-render-is-a-row`
- **Layers:** unit
- **WHEN** a render file does not decode as an image
- **THEN** its photograph's row says it is unreadable
- **AND** every other render is scored

#### Scenario: a run that cannot be read is reported and does not end the scoring
- **Key:** `evaluation:table:an-unreadable-run-is-reported`
- **Layers:** unit
- **WHEN** a run's frame or one of its flows cannot be read
- **THEN** the run is reported as unreadable
- **AND** every other run is scored

#### Scenario: a flow that cannot be read costs only its own renders
- **Key:** `evaluation:table:an-unreadable-flow-costs-only-its-own`
- **Layers:** unit
- **WHEN** one flow of a run cannot be read and another can
- **THEN** the readable flow's render is scored
- **AND** the unreadable flow is reported with what to move out of the run

#### Scenario: the record counts the runs it does not score and names none
- **Key:** `evaluation:table:the-record-names-no-unscored-run`
- **Layers:** unit
- **WHEN** a batch holds a run outside the cohort and a run that cannot be read
- **THEN** the record and the table count each and carry neither run's id
- **AND** each run's id is printed on the error stream

#### Scenario: a record git can reach is refused
- **Key:** `evaluation:table:a-record-git-can-reach-is-refused`
- **Layers:** unit
- **WHEN** the record would be written inside the working tree and outside the ignored data root
- **THEN** the scoring is refused naming the path, before any photograph is embedded
- **AND** no record is written

#### Scenario: the table re-derives from the record
- **Key:** `evaluation:table:the-table-re-derives-from-the-record`
- **Layers:** unit
- **WHEN** the table is printed from a committed record
- **THEN** it equals the table committed beside that record

#### Scenario: the latest render group is the one ranked
- **Key:** `evaluation:table:the-latest-group-is-ranked`
- **Layers:** unit
- **WHEN** a flow holds renders under two approvals
- **THEN** the row ranks the first seed of the later approval's group
- **AND** every other seed is listed as also rendered

#### Scenario: a latest group holding no render is not rendered
- **Key:** `evaluation:table:an-empty-latest-group-is-not-rendered`
- **Layers:** unit
- **WHEN** a flow's latest render group holds no render and an earlier group does
- **THEN** the row says not rendered
- **AND** no render of the earlier group is ranked

#### Scenario: a scored run is named by its digest prefix
- **Key:** `evaluation:table:a-run-is-named-by-its-digest-prefix`
- **Layers:** unit
- **WHEN** a render is ranked
- **THEN** its row and its table line name the run by the digest prefix of its id
- **AND** neither carries the photograph's filename

### Requirement: Attribute recall counts the approved sheet's scored tags read back from each render

For each render under the runs it is given, the system SHALL read the render with the tagger that fills the
sheet, at that tagger's own floor, and SHALL count, per scored field of the render's flow, the tags of the
approval the render was made from that it reads back, naming each tag it does not. It SHALL read each render
alone, with no cohort, SHALL write one record per batch holding a row per render and a total per flow, and SHALL
print its table from that record alone. A render that does not decode, and a render whose approval cannot be
read, SHALL each be a row saying so and SHALL NOT end the reading of another. Named runs SHALL narrow the
reading, and a name the runs do not hold SHALL refuse before any render is read. The record SHALL name the
tagger's files by digest and its floor, and SHALL be refused where git can reach it. A row SHALL name its run by
its digest prefix alone.

```
review/<NNN>.approved.json ── the scored fields' tags ──▶ tags asked ─┐
outputs/<NNN>/<seed>.png ──── the tagger, at its floor ──▶ tags seen ──┴─▶ read back / asked, each miss named
```

Hair, eyes and clothes reach a render as the approved sheet's tags, so whether they survived is whether the
tagger can read them back; the sheet's vocabulary is that tagger's label set, so it answers in the sheet's own
words
([D39](../../../docs/decisions.md#d39--attribute-recall-uses-the-sheets-tagger)).
Tags are counted, not renders: a field showing three of its four tags is not a failed render, and the missing
one is the finding. Whether the sheet is true of the photograph is the review's to say. A run's id carries its
photograph's filename, which may be a person's name; the digest half still finds the run.

#### Scenario: a tag read back is counted
- **Key:** `evaluation:recall:a-tag-read-back-is-counted`
- **Layers:** unit
- **WHEN** the tagger reads a scored field's tag from the render at or above its floor
- **THEN** the tag counts as read back
- **AND** the field's count is the tags read back over the tags asked

#### Scenario: a missed tag is named
- **Key:** `evaluation:recall:a-missed-tag-is-named`
- **Layers:** unit
- **WHEN** a scored field's tag is not read from the render
- **THEN** the row names the tag under its field

#### Scenario: only the flow's scored fields are counted
- **Key:** `evaluation:recall:only-scored-fields-are-counted`
- **Layers:** unit
- **WHEN** the approval holds tags in a field the flow's schema does not score
- **THEN** no count is taken over them
- **AND** a scored field holding no tag counts nothing

#### Scenario: every render is a row, and every flow has a total
- **Key:** `evaluation:recall:every-render-is-a-row`
- **Layers:** unit
- **WHEN** the runs hold renders across flows, approvals and seeds
- **THEN** each render is a row counted against the approval its group names
- **AND** each flow has a total over its rows

#### Scenario: a render that does not decode is a row
- **Key:** `evaluation:recall:an-unreadable-render-is-a-row`
- **Layers:** unit
- **WHEN** a render file does not decode as an image
- **THEN** its row says it is unreadable
- **AND** every other render is read

#### Scenario: a render without its approval is a row
- **Key:** `evaluation:recall:a-render-without-its-approval-is-a-row`
- **Layers:** unit
- **WHEN** the approval a render's group names is absent or cannot be read
- **THEN** its row says so
- **AND** every other render is read

#### Scenario: named runs narrow the reading
- **Key:** `evaluation:recall:named-runs-narrow-the-reading`
- **Layers:** unit
- **WHEN** runs are named after the runs directory
- **THEN** only their renders are read
- **AND** a name the runs directory does not hold refuses naming it, before any render is read

#### Scenario: the record names the tagger and its floor
- **Key:** `evaluation:recall:the-record-names-the-tagger-and-its-floor`
- **Layers:** unit
- **WHEN** the record is written
- **THEN** it names the tagger's model and label files by digest
- **AND** it names the floor a tag was read at

#### Scenario: a record git can reach is refused
- **Key:** `evaluation:recall:a-record-git-can-reach-is-refused`
- **Layers:** unit
- **WHEN** the record would be written inside the working tree and outside the ignored data root
- **THEN** the reading is refused naming the path and the move that fixes it, before any render is read
- **AND** no record is written

#### Scenario: the table re-derives from the record
- **Key:** `evaluation:recall:the-table-re-derives-from-the-record`
- **Layers:** unit
- **WHEN** the table is printed from a committed record
- **THEN** it equals the table committed beside that record

#### Scenario: a row names its run by its digest prefix
- **Key:** `evaluation:recall:a-run-is-named-by-its-digest-prefix`
- **Layers:** unit
- **WHEN** a render is read
- **THEN** its row names the run by the digest prefix of its id
- **AND** the record carries no photograph's filename
