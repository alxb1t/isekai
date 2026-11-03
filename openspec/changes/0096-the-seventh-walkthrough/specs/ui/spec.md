## MODIFIED Requirements

### Requirement: A missing caption is shown with the command that writes it

The system SHALL, when an input's flow holds no caption, show in the source pane the caption of the flow its sheet's
tags came from, followed from sheet to sheet to the flow that tagged, named as that flow's, and else that there is
none and the command that writes it, naming the flow, the run and the runs root. It SHALL NOT refuse to open the
surface for the absence.

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
- **WHEN** an input whose flow holds no caption is opened
- **THEN** the payload carries no prose and the command that writes it, naming the flow, the run and the runs root
- **AND** the surface serves the input without a refusal

#### Scenario: a sheet filled from another flow's tags shows that flow's caption
- **Key:** `ui:source:a-borrowed-sheet-shows-its-sources-caption`
- **Layers:** unit
- **WHEN** an input is opened whose flow holds no caption and whose sheet names another flow's tags
- **THEN** the payload carries that flow's caption prose and names that flow
- **AND** it carries no command

#### Scenario: a sheet two flows from its tags shows the tagger's caption
- **Key:** `ui:source:a-two-hop-sheet-shows-the-taggers-caption`
- **Layers:** unit
- **WHEN** a flow's sheet takes its tags from a flow whose own sheet takes them from a third, which holds the caption
- **THEN** the source pane shows the third flow's caption, named as its

### Requirement: Both tag lists are shown beside the prose, read-only, and neither is editable there

The system SHALL show, beside the caption, the scored list the local tagger produced and the
committable tags the hosted tagger offered — the input's flow's, else those of the flow its sheet's tags came from,
followed from sheet to sheet as the caption is — and SHALL make neither list a way to change a sheet.

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

#### Scenario: a sheet filled from another flow's tags shows that flow's lists
- **Key:** `ui:source:a-borrowed-sheet-shows-the-taggers-lists`
- **Layers:** unit
- **WHEN** a flow holding no tag lists has a sheet whose tags came, two flows back, from a flow that holds both
- **THEN** the source pane shows both of that flow's lists

## REMOVED Requirements

### Requirement: A folder in the library is a collection when it holds `sources/`

**Reason:** a collection's row counted approvals and renders for each offered flow; with five flows the counts wrapped
and crowded the row, and the hub shows each cell's stage.
**Migration:** the row lists its sources and the count with no flow; each flow's stage is the hub's.

## ADDED Requirements

### Requirement: A folder in the library is a collection when it holds `sources/`, listed by its sources

The system SHALL list as a collection every folder in the library that holds `sources/`, SHALL list any other folder as
not a collection and open none of it, and SHALL list no dot-folder. Each collection's row SHALL carry its name, its
source count, the names of its first fifteen sources, whose thumbnails it shows, the count of sources with no flow,
and the time and kind of the newest file written in it. Collections SHALL be ordered by that time, newest first, and
folders that are not collections after them. Home SHALL carry New collection at the right of the library's header row,
and on an empty library below the privacy line. Count labels on the surface SHALL use a singular noun at one and a
plural noun otherwise.

A folder is a collection by its layout alone, so no marker file can disagree with what is on disk, and the row is a
listing read on every request. A folder that is not a collection is shown rather than hidden so the screen matches the
folder, and nothing in the app writes into it. On first start the privacy line is read before the first import.

#### Scenario: a folder with `sources/` is a collection
- **Key:** `ui:batch-folder:a-folder-with-sources-is-a-batch`
- **Layers:** unit
- **WHEN** the library holds a folder with `sources/` and one without
- **THEN** the first is listed as a collection
- **AND** the second is listed as not a collection, and cannot be opened

#### Scenario: a dot-folder is not listed
- **Key:** `ui:batch-folder:a-dot-folder-is-not-listed`
- **Layers:** unit
- **WHEN** the library holds a folder whose name starts with a dot
- **THEN** it is not listed at all

#### Scenario: collections are ordered by their newest file
- **Key:** `ui:batch-folder:batches-are-ordered-by-their-newest-file`
- **Layers:** unit
- **WHEN** the library holds collections written at different times
- **THEN** they are listed newest first, by the newest file written in each

#### Scenario: no file records a collection
- **Key:** `ui:batch-folder:no-file-records-a-batch`
- **Layers:** unit
- **WHEN** the surface lists the library and opens a collection
- **THEN** no file describing a collection is created anywhere in the library

#### Scenario: count labels use singular at one
- **Key:** `ui:batch-folder:count-labels-use-singular-at-one`
- **Layers:** unit
- **WHEN** a count label is drawn for zero, one and several items
- **THEN** one uses the singular noun and the other counts use the plural noun

#### Scenario: a row names its first sources
- **Key:** `ui:batch-folder:a-row-names-its-first-sources`
- **Layers:** unit
- **WHEN** a collection holds seventeen sources
- **THEN** its row names the first fifteen in the hub's order
- **AND** its source count is seventeen

#### Scenario: first start shows New collection under the privacy line
- **Key:** `ui:batch-folder:first-start-shows-new-batch-under-the-privacy-line`
- **Layers:** e2e
- **WHEN** Home opens on an empty library
- **THEN** New collection sits below the privacy line
