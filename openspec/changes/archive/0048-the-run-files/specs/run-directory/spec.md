## ADDED Requirements

### Requirement: A run file is read only as the kind it declares

The system SHALL refuse to read a run file whose schema names a kind other than the one asked for, naming the kind
it declares and the kind this build reads, and SHALL check the kind before the version. A draft and its approval
are one kind.

A file copied or restored into the wrong place is otherwise read as whatever its place implies, and its fields mean
nothing. The kind is the first thing a file says about itself, so it is the first thing checked.

#### Scenario: a file of another kind is refused
- **Key:** `run-directory:kind:another-kind-is-refused`
- **Layers:** unit
- **WHEN** a run file whose schema names another kind is read
- **THEN** the read is refused naming the file, the kind it declares and the kind this build reads
- **AND** the remedy names an action this build can perform

#### Scenario: the kind is checked before the version
- **Key:** `run-directory:kind:the-kind-is-checked-first`
- **Layers:** unit
- **WHEN** a run file declares another kind and a version this build does not read
- **THEN** the refusal names the kind

## MODIFIED Requirements

### Requirement: Every "is this done?" test is a directory listing

The system SHALL make each stage's completion decidable from filenames alone, and SHALL carry in a
filename exactly the facts resume decides on: the version number, and whether an artifact is approved.
A file in a stage's directory that is not an artifact SHALL take a name no version listing reads.

A test that has to open and parse a file is a test that can be defeated by a truncated file, a
permission error or an unknown schema. Everything else a human wants to know — the model, the
instructions, the source version — lives inside the artifact and is read by a person, never by control
flow. A render's record is named for its seed, and a seed of three digits reads as a version
number unless its name says otherwise.

#### Scenario: approval is visible without opening the file
- **Key:** `run-directory:readdir:approval-is-in-the-filename`
- **Layers:** unit
- **WHEN** an approved artifact is present
- **THEN** its approval is determinable from its filename
- **AND** deciding it requires no read of the file's contents

#### Scenario: a filename carries nothing else
- **Key:** `run-directory:readdir:filename-carries-only-decidable-facts`
- **Layers:** unit
- **WHEN** an artifact is named
- **THEN** the name carries its version number and, where the concept applies, its approval
- **AND** the producing model, revision and instructions appear only inside the artifact

#### Scenario: a render's record is never read as a version
- **Key:** `run-directory:readdir:a-render-record-is-never-a-version`
- **Layers:** unit
- **WHEN** a render's record is written for a seed of three digits
- **THEN** its name is the seed followed by `.render.json`
- **AND** no version listing of its directory reads it

### Requirement: A failure is recorded as an attempt, never as a completion

The system SHALL record a stage's failure as a sibling of the artifact it failed to produce, SHALL
carry the attempt's ordinal and its kind in that file's name, and SHALL NOT consume the artifact's
version number with a failure.
The sheet stage SHALL record a damaged tag list and a tag outside the vocabulary as permanent failures, and
SHALL record nothing when the flow has no tag list.

Two stages take their version number from an upstream artifact rather than counting their own, so
"a retry writes the next number" has no next number to write there. Putting the kind and the ordinal in
the name is what keeps the retry decision a directory listing, which is the same rule the completion
tests are held to. The sheet stage is deterministic, so what fails once fails again
([D21](../../../docs/decisions.md#d21--retries-follow-what-can-fail)); an absent tag list is fixed by running
`tag`, and a record would bar the sheet that follows.

#### Scenario: an error file names the artifact it stands in for
- **Key:** `run-directory:failure:error-is-a-sibling-of-its-artifact`
- **Layers:** unit
- **WHEN** a stage fails
- **THEN** an error record is written beside where its artifact would have gone
- **AND** the artifact's version number is still available to a later successful attempt

#### Scenario: the attempt's kind and ordinal are in the filename
- **Key:** `run-directory:failure:kind-and-attempt-are-in-the-filename`
- **Layers:** unit
- **WHEN** an error record is written
- **THEN** its filename carries the attempt's ordinal and whether the failure was transient or permanent
- **AND** counting attempts requires no file to be opened

#### Scenario: a failed attempt is kept when a later one succeeds
- **Key:** `run-directory:failure:failed-attempts-survive-the-fix`
- **Layers:** unit
- **WHEN** a stage succeeds after an earlier failure
- **THEN** the earlier error record is still present
- **AND** the artifact is written under the number the failure did not take

#### Scenario: a sheet's failure is recorded as permanent
- **Key:** `run-directory:failure:a-sheet-failure-is-permanent`
- **Layers:** unit
- **WHEN** the sheet stage refuses a damaged tag list or a tag outside the vocabulary
- **THEN** a permanent error record is written beside the sheet it failed to produce
- **AND** the refusal names the record and its deletion

#### Scenario: an absent tag list leaves no record
- **Key:** `run-directory:failure:an-absent-tag-list-leaves-no-record`
- **Layers:** unit
- **WHEN** the sheet stage refuses a flow that declares the tagger and holds no tag list
- **THEN** no error record is written
