## MODIFIED Requirements

### Requirement: Import is staged, and a commit is one move

The system SHALL read chosen files into a staging folder under the library's `.staging/`, SHALL create the collection
and move every staged file into its `sources/` in one commit, SHALL delete the staging folder on cancel,
SHALL delete one staged file on request before the commit, refusing once it is sealed, and SHALL
delete, when the surface starts, each staging folder an import left in the library, keeping any written to within
the last hour and any folder import did not make. A file with the same bytes as a source already in the collection SHALL
be skipped; a different file whose name is taken SHALL be written as `<stem>-2`. A collection name SHALL be refused when
empty, holding `/`, starting with a dot, or taken. A collection whose folder sits inside the repository's working tree
and outside its ignored data root SHALL be refused before anything is staged.

Nothing half-read reaches a collection, and a collection never looks complete while files are still arriving. A staging
folder still being written belongs to an import open elsewhere, and a folder import did not make is not its to delete.
Bytes, not names, decide sameness. A collection holds copies of photographs, so it stays where git cannot reach it
([D18](../../../docs/decisions.md#d18--runs-stay-out-of-what-git-tracks)).

#### Scenario: a commit moves every staged file into the batch
- **Key:** `import:stage:a-commit-moves-every-file`
- **Layers:** unit
- **WHEN** a staging folder with read files is committed as a new collection
- **THEN** the collection holds them in `sources/`
- **AND** the staging folder is gone

#### Scenario: a cancel deletes the staging folder
- **Key:** `import:stage:a-cancel-deletes-staging`
- **Layers:** unit
- **WHEN** an import is cancelled
- **THEN** its staging folder is deleted
- **AND** the library is unchanged

#### Scenario: staging left behind is swept at start
- **Key:** `import:stage:leftover-staging-is-swept`
- **Layers:** unit
- **WHEN** the surface starts with a staging folder an import left under `.staging/`
- **THEN** that folder is deleted
- **AND** a folder import did not make, or one an import is still writing, is kept

#### Scenario: the same bytes are skipped and a taken name is renamed
- **Key:** `import:stage:same-bytes-skip-and-a-taken-name-is-renamed`
- **Layers:** unit
- **WHEN** a collection gains one file with a source's bytes and another with a source's name
- **THEN** the first writes nothing
- **AND** the second is written as `<stem>-2`

#### Scenario: an unusable batch name is refused
- **Key:** `import:stage:an-unusable-name-is-refused`
- **Layers:** unit
- **WHEN** a commit names a collection that is taken, empty, holds `/` or starts with a dot
- **THEN** it is refused
- **AND** the staging folder is kept

#### Scenario: a batch git can reach is refused
- **Key:** `import:stage:a-batch-git-can-reach-is-refused`
- **Layers:** unit
- **WHEN** `isekai import` names a collection inside the working tree and outside `.data/`
- **THEN** it is refused, naming where a collection may go
- **AND** nothing is written

#### Scenario: a staged file is removed alone
- **Key:** `import:stage:a-staged-file-is-removed-alone`
- **Layers:** unit
- **WHEN** one staged file is removed, and then the staging folder is committed
- **THEN** the collection holds every other staged file and not that one
- **AND** a removal asked once the commit has sealed the folder is refused, and no file changes
