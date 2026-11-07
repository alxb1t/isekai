## MODIFIED Requirements

### Requirement: Prepare runs what changed as one job, and refuses before it starts when Ollama does not answer

The system SHALL run Prepare as one job over every assigned cell with no sheet: one invocation of the pipeline's own
`prepare` verb over those cells, which takes each photograph in turn through tagging, only when it is assigned a flow
that declares the tagger, then reading, then the sheet stage of each of its cells, so a photograph's cells reach sheet
while later photographs wait. One job of each kind, a Prepare and a render, SHALL run at a time, the two side by side
in any collections; a job SHALL keep running when its page closes; Stop SHALL interrupt the current stage of the job it
names and start no other, leaving the other job running; stopping the surface SHALL interrupt every running job; each
line a job's verb writes to the collection's log SHALL name its job; and a job whose verb fails having reported nothing
SHALL end as failed, naming the collection's log. Before any stage starts, the surface SHALL check that the local model
server answers, and SHALL refuse with its message, starting nothing, when it does not. While Prepare runs, the job
strip and Prepare bar SHALL show each stage's completed photographs or cells out of its asked total — `tag 3 of 3 ·
caption 2 of 3 · sheet 0 of 6 · 00:35` — the bar as wide as the stages done over the stages asked; each total SHALL
stay fixed, a photograph or a cell SHALL count once per stage it completes and a refused one in none, a cell unticked
while the job runs among them, and elapsed time SHALL tick every second. Before it runs, the Prepare bar SHALL name how
many photographs it prepares in its collection, `2 photographs to prepare in <collection>`, its button the changes.

The pipeline's verb is the one path, so Prepare is exactly what the verbs do. A photograph's description is every
flow's, so it is tagged and read once, whatever flows it is assigned to, and one already described costs its verbs
nothing. Each photograph is taken end to end, so its sheet is ready for review while the rest prepare; no route waits
on Prepare. Prepare runs on the local models and a render on a rented GPU, and they write no file in common, so
neither waits for the other. A refusal before the start leaves every cell assigned, so pressing Prepare again is the
whole fix.

#### Scenario: Prepare runs each stage over the assigned cells
- **Key:** `ui:prepare:prepare-runs-the-assigned-cells`
- **Layers:** e2e
- **WHEN** Prepare is pressed with cells assigned
- **THEN** each cell reaches sheet
- **AND** no cell outside the assignment changes
- **AND** while it runs, the strip and bar show matching totals and ticking elapsed time across a reload, and Render
  is offered beside it

#### Scenario: a second job is refused while one runs
- **Key:** `ui:prepare:one-job-at-a-time`
- **Layers:** unit
- **WHEN** a job is asked for while another of its kind runs
- **THEN** it is refused naming the running job

#### Scenario: another batch's Prepare is disabled while one runs
- **Key:** `ui:prepare:another-batchs-prepare-is-disabled`
- **Layers:** unit
- **WHEN** a hub has changes waiting while a Prepare runs for another collection
- **THEN** its Prepare is disabled, naming the collection that runs

#### Scenario: Prepare refuses when Ollama does not answer
- **Key:** `ui:prepare:refused-when-ollama-does-not-answer`
- **Layers:** unit
- **WHEN** Prepare is asked for and the local model server does not answer
- **THEN** it is refused with the reader's message
- **AND** no stage starts

#### Scenario: Stop interrupts the job
- **Key:** `ui:prepare:stop-interrupts-the-job`
- **Layers:** unit
- **WHEN** Stop is asked for during a stage
- **THEN** that stage is interrupted and no later stage starts
- **AND** cells already at sheet stay at sheet

#### Scenario: a stage that fails before it reports ends the job
- **Key:** `ui:prepare:a-silent-failure-ends-the-job`
- **Layers:** unit
- **WHEN** the job's verb exits in failure having reported no item
- **THEN** the job ends as failed, naming the collection's log
- **AND** no later stage starts

#### Scenario: totals count cells rather than stage reports
- **Key:** `ui:prepare:totals-count-cells-not-stages`
- **Layers:** unit
- **WHEN** assigned photographs report tagging and reading, their cells sheet completion, and one a refusal
- **THEN** tagging and reading count once per photograph and the sheet once per cell, against fixed totals
- **AND** a refused cell counts in no stage, and a repeated completion never increments a count again

#### Scenario: a render runs beside a Prepare
- **Key:** `ui:prepare:a-render-runs-beside-a-prepare`
- **Layers:** unit
- **WHEN** a render is asked for while a Prepare runs
- **THEN** both run, and Stop of the render leaves the Prepare running

#### Scenario: stopping the surface interrupts both jobs
- **Key:** `ui:prepare:stopping-the-surface-interrupts-both`
- **Layers:** unit
- **WHEN** the surface stops while a Prepare and a render run
- **THEN** both are interrupted, and the render's window closes before the surface exits

#### Scenario: the log names each job
- **Key:** `ui:prepare:the-log-names-each-job`
- **Layers:** unit
- **WHEN** a Prepare and a render write to one collection's log
- **THEN** each line begins with its job's name

#### Scenario: the Prepare bar names its photographs
- **Key:** `ui:prepare:the-bar-names-its-photographs`
- **Layers:** unit
- **WHEN** two photographs are assigned to two flows each
- **THEN** the bar reads `2 photographs to prepare in <collection>`
- **AND** its button reads `4 changes · Prepare`

#### Scenario: a photograph is described once
- **Key:** `ui:prepare:a-photograph-is-described-once`
- **Layers:** unit
- **WHEN** Prepare is planned over a photograph assigned two flows
- **THEN** the job is one invocation of `prepare` naming each of its cells once
- **AND** tagging and reading are each asked once for it, and each flow's sheet stage once

#### Scenario: each photograph in turn
- **Key:** `ui:prepare:each-photograph-in-turn`
- **Layers:** unit
- **WHEN** Prepare is planned over two photographs, the second assigned a flow the first is not
- **THEN** its one invocation names every cell of the first photograph before any cell of the second
