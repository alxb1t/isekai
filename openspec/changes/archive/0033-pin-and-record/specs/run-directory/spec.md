## ADDED Requirements

### Requirement: A record key added under a kind's version is optional to every reader

The system SHALL read a file of a kind's current version whether or not it carries a record key that was
added under that version, and SHALL move a kind's version only when a file written before the change could
be misread by a reader after it.

A version is what lets a reader refuse a file it would misunderstand, and moving one makes every existing
file of that kind unreadable, so a run in progress could not resume. A key that only records — one no reader
acts on — cannot be misread by its absence, so adding it moves nothing. A key whose meaning changes is the
case the version exists for, and is a new key instead.

#### Scenario: a file written before a record key existed still reads
- **Key:** `run-directory:schema:an-added-record-key-is-optional`
- **Layers:** unit
- **WHEN** a stage reads a file of its kind's current version that lacks a record key added under that
  version
- **THEN** the file is read and the stage proceeds
- **AND** nothing refuses it for the missing key
