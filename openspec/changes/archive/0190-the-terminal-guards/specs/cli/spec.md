## MODIFIED Requirements

### Requirement: The approve verb cancels an approval with `--cancel`

The system SHALL take `--cancel` on `isekai approve`, cancelling each named run's approval in each named flow through
the review stage, SHALL answer each run on its own so one refusal stops no other, SHALL refuse a run whose runs root a
render session holds, cancelling nothing in it, as the app's cancel does, and SHALL refuse `--cancel` beside `--from`.

A cancel is the review stage's act and decides nothing about a render, so the verb asks for one before it calls the
stage; a collection is many runs, and one refused run must not cost the rest.

#### Scenario: each run is cancelled on its own
- **Key:** `cli:approve-cancel:each-run-on-its-own`
- **Layers:** unit
- **WHEN** `approve --cancel` names a cancellable run and a run with a prompt
- **THEN** the first is a draft again and the second is refused naming its prompt

#### Scenario: cancel beside from is refused
- **Key:** `cli:approve-cancel:not-beside-from`
- **Layers:** unit
- **WHEN** `approve` is given `--cancel` and `--from`
- **THEN** it is refused before any run is read

#### Scenario: a running render refuses the cancel of its runs root
- **Key:** `cli:approve-cancel:a-running-render-refuses-it`
- **Layers:** unit
- **WHEN** `approve --cancel` names a cancellable run under a runs root a render session holds,
  and one under another root
- **THEN** the first is refused, saying a render session is running, and its approval stays
- **AND** the second is a draft again

### Requirement: The discard verb deletes a render named by its image path

The system SHALL offer `isekai discard <image>`, which reads the run, flow, approval and seed from the image's path,
deletes the image's own thumbnail from the cache of the library whose collection holds the run, discards the render
through the render stage, then, where that removed an approval's group, deletes that approval and what goes with it,
as the render stage's discard says — older approvals with no render, the newest's waiting draft and, once no approval
is left, the flow's sheets — writing no draft; it prints each path it deleted, a run's file from its runs root and a
thumbnail from its library. A render's edits go with it, and a path that is an edit's image SHALL discard that edit and
every edit made from it, as the edit stage's discard says, and nothing else. A path that names neither a render nor an
edit SHALL be refused, naming the forms a render's path and an edit's path take, the verb exiting 1 and deleting
nothing; so SHALL a discard while a render session holds the image's runs root, a collection's or not, as the app's
delete is for a collection.

The hand path stays ([D3](../../../docs/decisions.md#d3--the-hand-path-stays)): the page's Delete is this verb's act,
run in the server's process. An image's path names everything a discard needs, so the verb takes nothing else.

#### Scenario: the render and its thumbnail are deleted
- **Key:** `cli:discard:the-render-and-its-thumbnail-are-deleted`
- **Layers:** unit
- **WHEN** the verb is given the path of a render in a collection's run whose thumbnail is cached
- **THEN** the image, its record and the thumbnail are deleted
- **AND** each deleted path is printed, and the verb exits 0

#### Scenario: the last render takes its approval with it
- **Key:** `cli:discard:the-last-render-takes-its-approval`
- **Layers:** unit
- **WHEN** the verb is given the path of the only render of the flow's only approval, its prompt assembled
- **THEN** the group, the prompt, the approval, the sheet and the emptied directories are deleted, each printed
- **AND** no draft is written, and the flow's directory is left empty
- **AND** another collection's thumbnail of the same photograph and seed stays

#### Scenario: a running render refuses it
- **Key:** `cli:discard:a-running-render-refuses-it`
- **Layers:** unit
- **WHEN** the verb is given the path of a render in a collection whose render session holds its record's lock
- **THEN** it exits 1, saying a render session is running
- **AND** the image, its record and its thumbnail are not deleted

#### Scenario: a running render beside a plain runs root refuses it
- **Key:** `cli:discard:a-session-beside-a-plain-runs-root-refuses-it`
- **Layers:** unit
- **WHEN** the verb is given the path of a render under a runs root no collection holds, a render session holding the
  lock of its record beside that root
- **THEN** it exits 1, saying a render session is running
- **AND** the image and its record are not deleted

#### Scenario: a path naming no render is refused
- **Key:** `cli:discard:a-path-naming-no-render-is-refused`
- **Layers:** unit
- **WHEN** the verb is given a path that is neither a render nor an edit
- **THEN** it exits 1, naming the path and the forms a render's path and an edit's path take
- **AND** no file is deleted

#### Scenario: an edit's path discards the edit
- **Key:** `cli:discard:an-edits-path-discards-the-edit`
- **Layers:** unit
- **WHEN** the verb is given the path of an edit's image beside its render
- **THEN** the edit's image, record and composite are deleted, each printed, and the verb exits 0
- **AND** the render and its approval stay

#### Scenario: a render takes its edits with it
- **Key:** `cli:discard:a-render-takes-its-edits-with-it`
- **Layers:** unit
- **WHEN** the verb is given the path of a render that has an edit
- **THEN** the edit's image, record and composite are deleted with the render, each printed

#### Scenario: a render takes its edits' thumbnails with it
- **Key:** `cli:discard:a-render-takes-its-edits-thumbnails-with-it`
- **Layers:** unit
- **WHEN** the verb is given the path of a render with two edits, the thumbnails of the render and each edit cached
- **THEN** each of those thumbnails is deleted and printed after the run's files, the render's first
- **AND** another collection's thumbnails of the same images stay

#### Scenario: an edit takes its own thumbnail and its chain's
- **Key:** `cli:discard:an-edit-takes-its-own-thumbnail-and-its-chains`
- **Layers:** unit
- **WHEN** the verb is given the path of an edit that another edit was made from, the thumbnails of both cached
- **THEN** both thumbnails are deleted and printed after the run's files, in the edits' order
- **AND** the render's thumbnail stays
