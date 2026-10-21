## MODIFIED Requirements

### Requirement: Sources are chosen in the file dialog, and each shows its own upload

The system SHALL take sources through the browser's file dialog, sending each file in its own request, and SHALL show
for each its upload's progress, then its reading, then whether it is ready, converted, refused or not cleaned, with
the reason, and a preview of each file read. Import SHALL stay disabled, with its reason, until every chosen file is
read, and SHALL commit only the ready files and those the operator chose to import as they are.

Each file's bar answers which one is slow; each reason sits on the file it concerns.

#### Scenario: each file shows its own progress, then its result
- **Key:** `ui:sheet:each-file-shows-its-progress`
- **Layers:** e2e
- **WHEN** files are chosen in the dialog
- **THEN** each tile shows its upload, then its result
- **AND** a refused file names its reason

#### Scenario: import waits for every file to be read
- **Key:** `ui:sheet:import-waits-for-reading`
- **Layers:** e2e
- **WHEN** a chosen file is still being read
- **THEN** Import is disabled, naming how many are read

#### Scenario: an imported batch opens its hub
- **Key:** `ui:sheet:an-import-opens-the-hub`
- **Layers:** e2e
- **WHEN** Import is pressed on a new batch
- **THEN** the batch's hub opens with every source unassigned

#### Scenario: a staged file serves its preview
- **Key:** `ui:sheet:a-staged-file-serves-its-preview`
- **Layers:** unit
- **WHEN** a staged file's preview is asked for
- **THEN** a downscaled JPEG of it is served
- **AND** nothing of it is kept

#### Scenario: the stream reports each file's reading
- **Key:** `ui:sheet:the-stream-reports-each-files-reading`
- **Layers:** unit
- **WHEN** an uploaded file is read
- **THEN** the import's stream reports it waiting, then converting, then its result

#### Scenario: an upload is answered before it is read
- **Key:** `ui:sheet:an-upload-is-answered-before-reading`
- **Layers:** unit
- **WHEN** a file's bytes have all arrived
- **THEN** its request is answered before the file is read
- **AND** the files are read one at a time, in the order their uploads ended

### Requirement: A draft update states the version of the draft it replaces

The system SHALL refuse a draft update, or an approval, whose stated precondition does not match the draft on
disk, and SHALL accept an update that states no precondition.

The surface autosaves on a debounce, so two updates can be in flight at once, and the server runs them
in a threadpool — which leaves the order they commit in decided by whichever finishes first rather than
by which keystroke came last. A precondition makes that order observable instead of silent: the loser is
told, rather than the winner's text being replaced by older text and the receipt describing a save that
is not on disk.

An update stating no precondition is accepted because the artifact carries no revision of its own to
state, and a client that cannot read one must still be able to write.

#### Scenario: an update against a stale draft is refused
- **Key:** `ui:draft-update:a-stale-precondition-is-refused`
- **Layers:** unit
- **WHEN** a draft update states a precondition that does not match the draft on disk
- **THEN** it is refused
- **AND** the draft on disk is unchanged

#### Scenario: an update stating no precondition is accepted
- **Key:** `ui:draft-update:no-precondition-is-accepted`
- **Layers:** unit
- **WHEN** a draft update states no precondition
- **THEN** it is accepted

#### Scenario: overlapping updates cannot both commit
- **Key:** `ui:draft-update:overlapping-updates-cannot-both-commit`
- **Layers:** unit
- **WHEN** two draft updates stating the same precondition are in flight at once
- **THEN** one is accepted and the other is refused
- **AND** the draft on disk is the accepted update's

#### Scenario: an approval against a stale draft is refused
- **Key:** `ui:draft-update:a-stale-approval-is-refused`
- **Layers:** unit
- **WHEN** an approval states a precondition that does not match the draft on disk
- **THEN** it is refused
- **AND** nothing is approved
