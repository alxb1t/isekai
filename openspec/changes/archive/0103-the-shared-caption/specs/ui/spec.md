## ADDED Requirements

### Requirement: Both tag lists are the photograph's, shown beside the prose, read-only, and neither is editable there

The system SHALL show, beside the caption, the scored list the local tagger produced for the photograph and the
committable tags the hosted tagger offered for it, the same for every flow, and SHALL make neither list a way to change
a sheet.

**The two lists are narrowed differently, and the asymmetry is measured rather than chosen.** The local
tagger is scored against the vocabulary it emits, so every tag it returns is committable by
construction and all of them are shown, with the confidence beside each — a wrong tag sorted below a
right one refutes itself. The hosted tagger free-associates: on the acceptance collection roughly nine in
ten of its tags were outside the vocabulary, could not be committed to any field, and the operator's
verdict was that only the marked ones carried any value. So its list is **filtered to what the
vocabulary carries** before it is shown.

**Filtered on the way to the page, never on the way to disk.** The artifact keeps every tag the model
returned — that is `tagging`'s requirement and it is untouched — because narrowing what is *stored*
would make the record disagree with what the model said, and the reason the artifact exists is to be
able to look behind the sorter. What changes is only which of those tags the surface spends the
operator's attention on.

#### Scenario: the local list is shown whole and the hosted list is shown filtered
- **Key:** `ui:source:both-tag-lists-are-shown-raw-and-read-only`
- **Layers:** unit
- **WHEN** an input whose tag artifacts contain tags outside the flow's vocabulary is opened
- **THEN** every tag the local tagger scored is present in the response the surface renders
- **AND** only the hosted tags the vocabulary contains are present in it
- **AND** no interaction on either list writes to a draft

#### Scenario: filtering the panel does not filter the artifact
- **Key:** `ui:source:the-artifact-keeps-what-the-panel-drops`
- **Layers:** unit
- **WHEN** a hosted tag outside the vocabulary is withheld from the payload
- **THEN** that tag is still present in the stored artifact, unchanged

#### Scenario: every flow shows the photograph's lists
- **Key:** `ui:source:every-flow-shows-the-photographs-lists`
- **Layers:** unit
- **WHEN** two flows of one run are opened, one of them drafted from the other
- **THEN** both show the photograph's two lists

### Requirement: A photograph with no caption is shown with the command that writes it

The system SHALL show in the source pane the photograph's caption, the same for every flow, and, when the photograph
holds none, that there is none and the command that writes it, naming the run and the runs root and no flow. It SHALL
NOT refuse to open the surface for the absence.

**The prose is the one artifact a skipped verb leaves missing on a page under review.** The tag lists keep
their silence: a list is missing because a tagger failed, because the run predates it, or because the flow
declares no tagger. Skipping `tag` never reaches review, because the sheet refuses without a tag list the
flow declares.

The caption is now its own verb and nothing downstream needs it, so an input can reach review having never
been read. A blank pane cannot be told from a photograph with nothing to say, and the one-verb design kept
the caption bundled for exactly that reason; naming the command keeps the reason without the bundle.

The server builds the command, as it builds every other command a refusal prints, and it names the run and its
runs root so it works when pasted: a collection's runs root in the library is never the default.

#### Scenario: an input with no caption names the command that writes it
- **Key:** `ui:source:a-missing-caption-names-its-command`
- **Layers:** unit
- **WHEN** an input whose photograph holds no caption is opened
- **THEN** the payload carries no prose and the command that writes it, naming the run and the runs root and no flow
- **AND** the surface serves the input without a refusal

#### Scenario: every flow shows the photograph's caption
- **Key:** `ui:source:every-flow-shows-the-photographs-caption`
- **Layers:** unit
- **WHEN** two flows of one run are opened, one of them drafted from the other
- **THEN** both payloads carry the photograph's one caption
- **AND** neither names a flow it came from

## MODIFIED Requirements

### Requirement: The hub shows each source's stage in each offered flow, and a tick assigns it

The system SHALL show a collection's hub as a grid of its sources by the flows the surface offers, each cell carrying
the stage read from that run's directory — no flow, assigned, tagged, sheet, draft, approved or rendered — and SHALL
ignore any other flow's directory. A cell whose run file cannot be read SHALL show that it is unreadable, with the
refusal the pipeline raised, and the rest of the grid SHALL still be shown. Reading the hub SHALL write nothing; a tick
SHALL write only through the assigning verb, and an untick only while the cell is assigned. A source imported as it is,
still carrying metadata, SHALL be marked on its row. Each source SHALL show its name and its thumbnail, and its row
SHALL carry the size read from its own file, with or without a run, which the viewer's title names. A source's thumbnail
and a cell's images SHALL sit at the foot of their cells, level across the row, whatever text stands above them; a
cell's refusal SHALL stand above its images, and `↵ view photo` SHALL take no line of the source's cell. A cell SHALL
name its newest image — the newest version holding images, then its last-written image — and a click or `↵` SHALL follow
the cell's stage: tick while unassigned or assigned, open Review on a sheet or a draft, open the sheet read-only on an
approval with no image, and open the viewer on the newest of the cell's images where it holds any, stepping through
them, `⇧↵` opening an image's large view; a tagged or unreadable cell SHALL do nothing. A cell holding images SHALL show
every one of them, oldest to newest, each marked with its version. A source's cell SHALL be the grid's first column,
reached by `h` and `←`, and `↵` there SHALL open its photograph in the viewer, stepping through the collection's
sources. The hub SHALL keep its focus across a large view, the Back button and a switch of tabs, a restored focus
scrolled to the window's centre. A key's move to the first row SHALL scroll the hub to its top, to the last row to its
foot, and to any other row only as far as the row needs. The header SHALL leave a 12 px gap between items.
An assigned cell SHALL read tagged from the photograph's tag list, so a photograph tagged once is tagged in
every flow it is assigned to.

A stage is a directory listing, the rule every stage already follows, so the grid cannot drift from the disk, and a tick
survives a reload. The mark and the size are read from the source itself, so no file records them. An approved cell can
hold an older version's images, so its newest image is named by the server rather than guessed by the page. A row's
pictures share a foot, so a long name, a mark or a refusal moves only the text above them. *Add sources…* and the flow
names sit above the first row, so a move there shows them.

#### Scenario: a cell's stage comes from its run's directory
- **Key:** `ui:hub:a-cells-stage-comes-from-its-run`
- **Layers:** unit
- **WHEN** a run holds a flow's approved sheet and no render
- **THEN** that cell's stage is approved

#### Scenario: a flow the surface does not offer is ignored
- **Key:** `ui:hub:an-untracked-flow-is-ignored`
- **Layers:** unit
- **WHEN** a run holds a directory for a flow the surface does not offer
- **THEN** the hub shows no column and no refusal for it

#### Scenario: an unreadable run file marks its cell alone
- **Key:** `ui:hub:an-unreadable-file-marks-its-cell`
- **Layers:** unit
- **WHEN** one cell's run file cannot be read
- **THEN** that cell is unreadable, with the pipeline's refusal
- **AND** every other cell shows its stage

#### Scenario: the hub writes nothing
- **Key:** `ui:hub:the-hub-writes-nothing`
- **Layers:** unit
- **WHEN** a collection's hub is read
- **THEN** no file in the collection is created, changed or removed

#### Scenario: a tick assigns the flow
- **Key:** `ui:hub:a-tick-assigns-the-flow`
- **Layers:** e2e
- **WHEN** an unassigned cell is ticked
- **THEN** the cell reads assigned
- **AND** it still reads assigned after a reload
- **AND** the header keeps a 12 px gap between its items

#### Scenario: a prepared cell's tick stays
- **Key:** `ui:hub:a-prepared-tick-stays`
- **Layers:** unit
- **WHEN** an untick is asked for a cell past assigned
- **THEN** it is refused and no file changes

#### Scenario: a source imported as it is is marked
- **Key:** `ui:hub:an-uncleaned-source-is-marked`
- **Layers:** unit
- **WHEN** a source still carries metadata
- **THEN** its row is marked not cleaned

#### Scenario: a source is sized from its file
- **Key:** `ui:hub:a-source-is-sized-from-its-file`
- **Layers:** unit
- **WHEN** the hub is read for a source that has no run
- **THEN** its row carries the width and height of its file

#### Scenario: a cell names its newest image
- **Key:** `ui:hub:a-cell-names-its-newest-image`
- **Layers:** unit
- **WHEN** an approved cell holds images only under an older version
- **THEN** it names that version and its last-written image

#### Scenario: a click follows the cell's stage
- **Key:** `ui:hub:a-click-follows-the-cells-stage`
- **Layers:** unit
- **WHEN** a cell is clicked at each stage
- **THEN** it ticks up to assigned, opens Review on a sheet, a draft or an unrendered approval, and opens an image
- **AND** a tagged or an unreadable cell does nothing

#### Scenario: a rendered cell opens its newest image
- **Key:** `ui:hub:a-rendered-cell-opens-its-newest-image`
- **Layers:** e2e
- **WHEN** a rendered cell is clicked, then `⇧↵` is pressed in the viewer
- **THEN** the viewer opens on its newest image, then that image's large view
- **AND** `Esc` returns to the hub, focused on that cell, and that cell in view

#### Scenario: a cell lists its images
- **Key:** `ui:hub:a-cell-lists-its-images`
- **Layers:** unit
- **WHEN** a cell holds images under two versions
- **THEN** the hub carries them oldest to newest, each with its version and seed

#### Scenario: the source cell opens its photograph
- **Key:** `ui:hub:the-source-cell-opens-its-photograph`
- **Layers:** e2e
- **WHEN** `h` is pressed on a row's first flow cell, then `↵`
- **THEN** the row's photograph opens in the viewer
- **AND** while the source cell holds the focus, its thumbnail's foot is level with the row's images' foot

#### Scenario: a key's move to an edge row shows the hub's head
- **Key:** `ui:hub:an-edge-row-shows-the-head`
- **Layers:** e2e
- **WHEN** in a window shorter than the grid, `j` moves the focus to the last row, then `k` back to the first
- **THEN** Add sources… is out of view on the last row
- **AND** it is in view again on the first

#### Scenario: a photograph tagged once is tagged in every flow
- **Key:** `ui:hub:a-tagged-photograph-is-tagged-in-every-flow`
- **Layers:** unit
- **WHEN** a photograph's tag list is written and two flows are assigned to it, neither with a sheet
- **THEN** both cells read tagged

### Requirement: Prepare runs what changed as one job, and refuses before it starts when Ollama does not answer

The system SHALL run Prepare as one job over every assigned cell with no sheet: the tagging and reading stages once
each, one invocation of the pipeline's own verb over those cells' photographs, tagging only the photographs assigned a
flow that declares the tagger, then, for each flow, the sheet stage, one invocation over that flow's cells. One job of
each kind, a Prepare and a render, SHALL run at a time, the two side by side in any collections; a job SHALL keep
running when its page closes; Stop SHALL interrupt the current stage of the job it names and start no other, leaving
the other job running; stopping the surface SHALL interrupt every running job; each line a job's verbs write to the
collection's log SHALL name its job; and a stage that fails having reported nothing SHALL end the job as failed, naming
the collection's log, and start no other. Before any stage starts, the surface SHALL check that the local model server
answers, and SHALL refuse with its message, starting nothing, when it does not. While Prepare runs, the job strip and
Prepare bar SHALL show each stage's completed photographs or cells out of its asked total — `tag 3 of 3 · caption 2 of
3 · sheet 0 of 6 · 00:35` — the bar as wide as the stages done over the stages asked; each total SHALL stay fixed, a
photograph or a cell SHALL count once per stage it completes and a refused one in none, and elapsed time SHALL tick
every second. Before it runs, the Prepare bar SHALL name how many photographs it prepares in its collection, `2
photographs to prepare in <collection>`, its button the changes.

The pipeline's verb is the one path, so Prepare is exactly what the verbs do. A photograph's description is every
flow's, so it is tagged and read once, whatever flows it is assigned to, and one already described costs its verbs
nothing. Prepare runs on the local models and a
render on a rented GPU, and they write no file in common, so neither waits for the other. A refusal before the start
leaves every cell assigned, so pressing Prepare again is the whole fix.

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
- **WHEN** a stage exits in failure having reported no item
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
- **THEN** tagging and reading are each one invocation that names it once and names no flow
- **AND** each flow's sheet stage is an invocation of its own

### Requirement: Draft from this starts from an image, for any flow the app offers, and opens Review on the draft

The system SHALL offer *Draft from this* on `⇧D` from an image's large view and over a selection in the Renders grid,
opening a dialog that lists every flow the app offers, the image's own first, named *revise*, focused, and the others
after it, assigned or not; `↵` SHALL draft the chosen flow from each image's approval, as the draft verb does — a
revision for the image's own flow, a draft from that approval for another, assigning a target and filling its sheet from
the photograph's tags where it holds none, the image's seed prefilled and the image recorded — then open Review on the
first draft, the others of its flow in the rail. A target holding a waiting draft with edits of its own SHALL write
nothing for that image and open Review on that draft; one equal to its sheet SHALL be replaced. A selection SHALL be
drafted all or none, refusing by name an image of a flow this build does not track, and refusing a selection that names
a version or a seed no run can hold. On such a draft, draft or approved, Review SHALL show the photograph and the image
the draft records — whatever its seeds became, else, for a revision, the first of its seeds rendered under its approval
— on one line, at equal height under one header row, headed by its flow, version and seed, and offer *Side by side*,
also on `⌃P`, both in one dialog, `⌃P` in it showing the photograph alone and back; it SHALL mark each field that
differs from the approval a revision came from, or from the target's sheet for another flow, naming the source flow and
approval in the sheet's kicker; on a draft it SHALL offer to discard it from the approve bar, deleting it only once the
operator confirms.

```
large view · summon-anime-wai v2 · seed 9423…   ⇧D
  Draft from this
  ▸ summon-anime-wai           revise
    summon-semireal-anime-wai
    summon-flat-anime-wai
    summon-vivid-anime-wai
    conjure-anime-wai
  ↵ ─▶ Review on the draft: the photograph │ the image it came from
```

An image the operator approved is where the next draft starts, in its own flow or another: one act, whatever the flows
become. The comparison that matters is the render against the photograph, read against the sheet. A waiting edit is the
work in hand; a draft the operator never touched holds no work. A discard deletes the operator's edits, so one click
never does.

#### Scenario: Revise opens Review on the revision
- **Key:** `ui:revise:revise-opens-review-on-the-revision`
- **Layers:** e2e
- **WHEN** *Draft from this* is drafted into the image's own flow on its large view
- **THEN** Review opens on its draft with the render beside the photograph and the seed prefilled
- **AND** once approved, the render still stands beside the photograph

#### Scenario: a revision keeps its image after its seed changes
- **Key:** `ui:revise:a-revision-keeps-its-image-after-its-seed-changes`
- **Layers:** unit
- **WHEN** Review reads a revision whose seed was changed, draft and then approved
- **THEN** its payload names the image the revision was written from

#### Scenario: an approved revision keeps its image
- **Key:** `ui:revise:an-approved-revision-keeps-its-image`
- **Layers:** unit
- **WHEN** Review reads a revision's approval
- **THEN** its payload names the approval it came from, its image and that approval's fields

#### Scenario: a waiting draft is opened, not refused
- **Key:** `ui:revise:a-waiting-draft-is-opened`
- **Layers:** unit
- **WHEN** a revision is asked for an image whose flow holds a waiting draft with edits of its own
- **THEN** it answers with that draft and writes nothing

#### Scenario: an untracked flow refuses its image
- **Key:** `ui:revise:an-untracked-flow-refuses-its-image`
- **Layers:** unit
- **WHEN** a draft is asked for a selection holding an image of a flow this build does not track
- **THEN** that image is refused naming its flow
- **AND** no draft is written for any image

#### Scenario: an image no run can hold is refused
- **Key:** `ui:revise:an-image-no-run-can-hold-is-refused`
- **Layers:** unit
- **WHEN** a draft is asked for an image whose version or seed no run can hold
- **THEN** the selection is refused
- **AND** no draft is written

#### Scenario: a discard deletes the draft the page read
- **Key:** `ui:revise:a-discard-deletes-the-draft-the-page-read`
- **Layers:** unit
- **WHEN** a discard states the draft on disk
- **THEN** that draft is deleted
- **AND** every approval is unchanged

#### Scenario: Discard asks before it deletes
- **Key:** `ui:revise:discard-asks-before-it-deletes`
- **Layers:** e2e
- **WHEN** Discard is pressed on a revision, then Keep
- **THEN** the draft is still on disk and the sheet still open

#### Scenario: Side by side shows the pair
- **Key:** `ui:revise:side-by-side-shows-the-pair`
- **Layers:** e2e
- **WHEN** `⌃P` is pressed on a revision with focus in a tag field, then `⌃P` again
- **THEN** one dialog shows the photograph and the render at equal height, then the photograph alone
- **AND** `Esc` closes it

#### Scenario: the large view names its targets
- **Key:** `ui:conjure-from:the-large-view-names-its-targets`
- **Layers:** unit
- **WHEN** a summon image's large view is read in a collection where no source is assigned another flow
- **THEN** its targets are every flow the app offers, summon first

#### Scenario: a refused draft writes nothing
- **Key:** `ui:conjure-from:a-refused-draft-writes-nothing`
- **Layers:** unit
- **WHEN** a draft is asked from an approval version the source does not hold
- **THEN** it is refused naming that version
- **AND** no file is written

#### Scenario: a waiting edit is opened
- **Key:** `ui:conjure-from:a-waiting-edit-is-opened`
- **Layers:** unit
- **WHEN** a draft is asked for a target whose waiting draft has edits of its own
- **THEN** it answers with that draft and writes nothing

#### Scenario: an approved draft keeps its marks
- **Key:** `ui:conjure-from:an-approved-draft-keeps-its-marks`
- **Layers:** unit
- **WHEN** Review reads the approval of a draft written from another flow's approval
- **THEN** it names the source flow and approval, and carries the target sheet's fields

#### Scenario: Review reads the draft against the target's sheet
- **Key:** `ui:conjure-from:review-reads-the-draft-against-the-sheet`
- **Layers:** unit
- **WHEN** Review reads a draft written from another flow's approval
- **THEN** it names the source flow and approval, and carries the target sheet's fields

#### Scenario: Conjure from this opens Review on the draft
- **Key:** `ui:conjure-from:conjure-from-this-opens-review`
- **Layers:** e2e
- **WHEN** `⇧D` is pressed on a summon image whose source is not assigned conjure, conjure chosen and `↵` pressed
- **THEN** Review opens on conjure's draft, its kicker naming the summon approval
- **AND** a field summon changed is marked against conjure's sheet
- **AND** its caption pane shows the photograph's caption, naming no flow, and the summon image stands beside the
  photograph

#### Scenario: an unedited waiting draft is replaced
- **Key:** `ui:draft-from:an-unedited-waiting-draft-is-replaced`
- **Layers:** unit
- **WHEN** a draft is asked for a target whose waiting draft equals its sheet
- **THEN** the draft from the image is written at that draft's number

#### Scenario: a selection drafts into the flow chosen
- **Key:** `ui:draft-from:a-selection-drafts-into-the-flow-chosen`
- **Layers:** unit
- **WHEN** a selection of two images from different runs is drafted into another flow
- **THEN** each run's target gains a draft from its image's approval, its seed prefilled

## REMOVED Requirements

### Requirement: Both tag lists are shown beside the prose, read-only, and neither is editable there

**Reason**: the lists are the photograph's, so every flow shows the same two, and none is followed from sheet to sheet.

**Migration**: *Both tag lists are the photograph's, shown beside the prose, read-only, and neither is editable there*
replaces it with its other keys; `ui:source:a-borrowed-sheet-shows-the-taggers-lists` gives way to
`ui:source:every-flow-shows-the-photographs-lists`.

### Requirement: A missing caption is shown with the command that writes it

**Reason**: the caption is the photograph's, so no flow borrows one, and the command that writes it names no flow.

**Migration**: *A photograph with no caption is shown with the command that writes it* replaces it, keeping
`ui:source:a-missing-caption-names-its-command`; `ui:source:a-borrowed-sheet-shows-its-sources-caption` and
`ui:source:a-two-hop-sheet-shows-the-taggers-caption` give way to `ui:source:every-flow-shows-the-photographs-caption`.
