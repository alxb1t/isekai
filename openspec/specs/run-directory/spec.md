# Capability: `run-directory`

## Purpose

The directory every stage couples through, and the only thing stages share: a photograph becomes an identified run,
nested input above and flow below, whose artifacts are numbered, never overwritten, and read as done from their
filenames alone.

## Requirements

### Requirement: A run is identified by its input's content

The system SHALL identify a run by a twelve-character prefix of the input's SHA-256, an underscore, and
a readable slug derived from its filename stem, and SHALL treat a second offer of the same bytes as a
continuation of the same run rather than a new one. A prefix collision between different bytes SHALL be
refused naming the directory, never silently merged.

Two different inputs can share a filename, and a bare hash cannot be read in a directory listing.
Deriving the id from content is also what makes re-offering a resume rather than a duplicate: the same
bytes reach the same directory, and the artifacts already there decide what is left to do. The
separator is an underscore because the slug is hyphenated, so a hyphen would leave a reader no way to
see where the digest ends; a slug can never contain an underscore, which makes the boundary
unambiguous. Twelve characters rather than six because the remedy for a collision is a human renaming a
directory by hand, and the corpus this is meant to survive is larger than six characters comfortably
carries.

#### Scenario: the id combines a content hash and a readable slug
- **Key:** `run-directory:identity:id-is-hash-and-slug`
- **Layers:** unit
- **WHEN** a run is created for an input
- **THEN** its id is twelve hex characters of the input's SHA-256, an underscore, then a sanitised
  filename stem
- **AND** the full digest is recorded in the run's frame

#### Scenario: two inputs sharing a filename get different runs
- **Key:** `run-directory:identity:same-name-different-bytes-differ`
- **Layers:** unit
- **WHEN** two inputs with identical filenames and different bytes are each given a run
- **THEN** the two ids differ
- **AND** neither run's artifacts are visible to the other

#### Scenario: the same input twice is one run
- **Key:** `run-directory:identity:same-bytes-resume-the-same-run`
- **Layers:** unit
- **WHEN** an input is offered to a command and a run for those bytes already exists
- **THEN** the existing run is used
- **AND** no second directory is created

#### Scenario: a prefix collision is refused rather than merged
- **Key:** `run-directory:identity:a-prefix-collision-refuses`
- **Layers:** unit
- **WHEN** a run directory already carries the same digest prefix for different bytes
- **THEN** the offer is refused naming that directory
- **AND** the refusal states how to keep both

### Requirement: The photograph is copied into the run, and its type is preserved

The system SHALL copy the photograph into the run directory rather than record a path to it, SHALL
preserve the file's original extension, and SHALL record its digest, size and media type in the run's
frame.

A run that points at a file someone later moved is not reconstructable from disk, and the frame's whole
job is to be reconstructable. The extension is preserved because the header parser reads both JPEG and
PNG, and a PNG stored under a `.jpg` name is a filename that lies about its bytes.

#### Scenario: the photograph is copied, not referenced
- **Key:** `run-directory:frame:photograph-is-copied-in`
- **Layers:** unit
- **WHEN** a run is created
- **THEN** the photograph's bytes are present inside the run directory
- **AND** the run does not record the path the photograph was read from

#### Scenario: a PNG keeps its extension
- **Key:** `run-directory:frame:extension-is-preserved`
- **Layers:** unit
- **WHEN** the photograph is a PNG
- **THEN** the copy inside the run carries a `.png` extension
- **AND** the frame records `image/png` as its media type

#### Scenario: the frame records the digest of the copy's original
- **Key:** `run-directory:frame:digest-proves-the-copy`
- **Layers:** unit
- **WHEN** the frame is written
- **THEN** it carries the photograph's SHA-256, its byte count and its media type
- **AND** the digest matches the bytes of the copy inside the run

### Requirement: Every artifact declares its schema and what produced it

The system SHALL write every artifact with a schema name and version and a producer record, and SHALL
record in the producer which upstream artifact version the work was derived from.

A producer that names only a model cannot explain its result. The instruction text shapes what comes back, so its
digest is recorded beside the model that read it. Instructions fixed by this build rather than by a flow have
bytes to hash and no path, and a record that invented a path would assert a location that does not exist.

#### Scenario: an artifact carries its schema name and version
- **Key:** `run-directory:provenance:artifact-declares-its-schema`
- **Layers:** unit
- **WHEN** any artifact is written
- **THEN** it carries a schema name and an integer version
- **AND** a reader handed an unknown version refuses rather than parsing it

#### Scenario: a producer records the instruction text it was given
- **Key:** `run-directory:provenance:producer-records-the-briefing`
- **Layers:** unit
- **WHEN** a stage that is given instruction text writes its artifact
- **THEN** the producer records that text's digest, and its path where the text has one
- **AND** two artifacts written under different instructions are distinguishable from the record alone

#### Scenario: a producer records which upstream version it came from
- **Key:** `run-directory:provenance:producer-records-its-source`
- **Layers:** unit
- **WHEN** an artifact is derived from an earlier stage's artifact
- **THEN** its producer names that artifact's version number
- **AND** the chain from the render back to the photograph is traceable without a second numbering scheme

#### Scenario: an unpinnable producer says so rather than claiming a pin
- **Key:** `run-directory:provenance:unpinned-producer-is-declared`
- **Layers:** unit
- **WHEN** the producer is a hosted service that exposes no immutable revision
- **THEN** the record declares that it is not pinned
- **AND** it does not carry a revision or digest field that would be untrue

### Requirement: Artifacts are append-only and numbered, and re-running a command is a no-op

The system SHALL number each stage's artifacts within that stage's own directory, SHALL never overwrite
a written artifact, and SHALL make a command whose artifact already exists do nothing — write nothing,
call nothing — unless a new version is explicitly requested.

Idempotence is what makes resume ordinary: there is no special mode and no state machine, because
running every command again is the whole of it. It is also the only defence against a shell loop
retrying after a network blip and silently burning a call.

#### Scenario: re-running a completed command changes nothing
- **Key:** `run-directory:idempotence:rerun-is-a-no-op`
- **Layers:** unit
- **WHEN** a command runs against a run whose artifact for that stage already exists
- **THEN** no file in the run directory changes
- **AND** no call is made to any external service

#### Scenario: a new version is an explicit act
- **Key:** `run-directory:idempotence:new-version-must-be-asked-for`
- **Layers:** unit
- **WHEN** a command is asked explicitly for a new version
- **THEN** the next number is written
- **AND** the previous version is left exactly as it was

#### Scenario: numbering is per directory and linked by provenance
- **Key:** `run-directory:numbering:each-directory-counts-its-own`
- **Layers:** unit
- **WHEN** two stages each write artifacts for the same run
- **THEN** each stage's numbers are assigned within its own directory
- **AND** the link between them is the producer record, not a shared counter

#### Scenario: approving an approved flow writes nothing
- **Key:** `run-directory:idempotence:approving-an-approved-flow-writes-nothing`
- **Layers:** unit
- **WHEN** approval is asked for a flow that is already approved and still holds a draft numbered below its approval
- **THEN** no file in the run directory changes
- **AND** the command reports the stage as already complete

### Requirement: An artifact is written atomically or not at all

The system SHALL write every artifact to a temporary file on the same filesystem and move it onto its
final path, so that a partially written artifact never exists under its final name.

Resume treats the presence of an artifact as proof the stage finished. A crash during a plain write
leaves a truncated file that exists, and resume would skip a stage that never completed — which makes
atomicity a precondition of the state model rather than a nicety.

#### Scenario: a failed write leaves no artifact behind
- **Key:** `run-directory:atomicity:interrupted-write-leaves-nothing`
- **Layers:** unit
- **WHEN** writing an artifact fails part-way
- **THEN** no file exists at the artifact's final path
- **AND** any temporary file is not mistaken for the artifact

#### Scenario: the replacement is atomic
- **Key:** `run-directory:atomicity:final-move-is-atomic`
- **Layers:** unit
- **WHEN** an artifact is written
- **THEN** it appears at its final path in one step
- **AND** the temporary file shares the artifact's filesystem

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

### Requirement: A stage has a retry budget, and a permanent failure is never retried

The system SHALL classify each failure as transient or permanent, SHALL never retry a permanent
failure, and SHALL refuse a stage whose transient attempts have reached its budget, naming the
photograph and the error record rather than spending again.

Without a budget every resume retries every failure forever, and at the rendering stage that costs
money on every pass. A render that has failed once should cost a person's attention rather than another
attempt, which is why that stage's budget is one.

#### Scenario: a permanent failure is not retried
- **Key:** `run-directory:budget:permanent-is-never-retried`
- **Layers:** unit
- **WHEN** a stage's most recent failure was permanent
- **THEN** the command refuses without attempting the work
- **AND** the refusal names the photograph and the error record

#### Scenario: a stage at its budget refuses
- **Key:** `run-directory:budget:at-budget-the-stage-refuses`
- **Layers:** unit
- **WHEN** a stage's transient attempts have reached its declared budget
- **THEN** the command refuses rather than attempting again
- **AND** the refusal names the photograph and the error record

#### Scenario: a batch does not halt on one item's failure
- **Key:** `run-directory:budget:one-failure-does-not-halt-the-batch`
- **Layers:** unit
- **WHEN** one photograph in a batch fails
- **THEN** the remaining photographs are still processed
- **AND** every failure is reported together at the end

### Requirement: An unknown schema version is refused, naming the fix

The system SHALL refuse to read an artifact whose schema version it does not know, and SHALL name what
the operator can do about it rather than parsing the artifact as best it can.

A best-effort parse of a format this build does not know produces numbers that look fine and mean nothing. This
is the same posture the evaluator already takes when an optional dependency is absent: refuse, and say
what would fix it.

#### Scenario: an artifact from a newer version is refused
- **Key:** `run-directory:schema:unknown-version-is-refused`
- **Layers:** unit
- **WHEN** an artifact declares a schema version this build does not know
- **THEN** the read is refused naming the file, the version it declares and the version this build reads
- **AND** no field of the artifact is interpreted

#### Scenario: the refusal states the remedy
- **Key:** `run-directory:schema:refusal-names-the-fix`
- **Layers:** unit
- **WHEN** an unknown schema version is refused
- **THEN** the message tells the operator what action would resolve it
- **AND** it does not suggest an action this build cannot perform

#### Scenario: an unreadable artifact is refused by name
- **Key:** `run-directory:schema:an-unreadable-artifact-is-refused-by-name`
- **Layers:** unit
- **WHEN** an artifact is not valid JSON, is not a JSON object, or carries a schema block that is not an object
- **THEN** the read is refused naming the file
- **AND** no field of the artifact is interpreted
- **AND** the remedy names an action this build can perform

### Requirement: A run root is under the ignored root or outside the repository

The system SHALL refuse a run root inside the repository's working tree unless it is under the ignored
data root, and SHALL accept one outside the repository. It SHALL decide containment by the identity of
the directories, never by comparing the text of their paths.

A run holds a copy of the photograph, so a run root git can reach is one `git add` from publishing a
likeness ([D18](../../../docs/decisions.md#d18--runs-stay-out-of-what-git-tracks)). Two spellings of
one directory are one directory, and only its identity says so.

#### Scenario: a run root inside the working tree and outside the ignored root is refused
- **Key:** `run-directory:containment:in-tree-run-root-is-refused`
- **Layers:** unit
- **WHEN** a run root resolves to a path inside the repository working tree that is not under the
  ignored data root
- **THEN** the invocation is refused before any run is created
- **AND** the message names the path given and what would be accepted

#### Scenario: a differently-spelled name for a directory inside the tree is still inside it
- **Key:** `run-directory:containment:containment-is-decided-by-identity`
- **Layers:** unit
- **WHEN** a run root names a directory inside the working tree by a spelling the filesystem treats as
  the same directory but a textual comparison does not
- **THEN** the invocation is refused exactly as the plainly-spelled path would be

#### Scenario: a run root outside the repository is accepted
- **Key:** `run-directory:containment:external-run-root-is-accepted`
- **Layers:** unit
- **WHEN** a run root resolves to a path outside the repository working tree
- **THEN** it is accepted and runs are created under it
- **AND** no containment check applies to it

#### Scenario: the default run root is under the ignored root
- **Key:** `run-directory:containment:default-is-the-ignored-root`
- **Layers:** unit
- **WHEN** no run root is given
- **THEN** runs are created under the repository's ignored data root

### Requirement: The run directory is input above, flow below, and every artifact is a flow's own

The system SHALL place the input and its frame at the root of a run, and SHALL place every artifact any
stage produces under a directory named for the flow that produced it. It SHALL NOT place any stage's
artifacts above the flow level, and SHALL NOT let one flow read another flow's artifacts.

```
runs/<input-id>/
├── run.json, the photograph      shared by every flow, copied once
└── <flow-id>/                    one subtree per flow
    └── captions/ wd14/ tags/ sheets/ review/ prompts/ outputs/
```

Above the split sits the one thing every flow shares, the input. A flow adds one subtree, and retiring one flow's
work for one input removes one directory ([D17](../../../docs/decisions.md#d17--input-above-flow-below)). A caption
written under one flow's briefing can never be picked up by another flow, because the two never name the same
directory, and a stage directory that is absent records that the flow did not declare what would fill it.

#### Scenario: every stage writes under the flow
- **Key:** `run-directory:layout:stage-artifacts-live-under-the-flow`
- **Layers:** unit
- **WHEN** a run has been carried through every stage for a flow
- **THEN** that flow's captions, tag lists, sheets, reviews, prompts and outputs are all under one
  directory named for the flow
- **AND** the only entries above it are the input and its frame

#### Scenario: a second flow adds one subtree
- **Key:** `run-directory:layout:a-second-flow-adds-one-subtree`
- **Layers:** unit
- **WHEN** a second flow is carried through a run that already holds one
- **THEN** exactly one new directory appears, named for that flow
- **AND** the first flow's artifacts are unchanged

#### Scenario: the input is copied once however many flows run
- **Key:** `run-directory:layout:the-input-is-copied-once`
- **Layers:** unit
- **WHEN** several flows are run over one input
- **THEN** the run holds exactly one copy of the input
- **AND** its frame is written once

#### Scenario: removing one flow's work leaves the others intact
- **Key:** `run-directory:layout:one-flow-s-work-is-one-directory`
- **Layers:** unit
- **WHEN** one flow's directory is removed from a run
- **THEN** every other flow's artifacts remain readable
- **AND** the input and its frame remain

### Requirement: A resume check asks the flow what it produces rather than assuming an image

The system SHALL determine which of a flow's outputs are already produced from filenames alone, using
the output form that flow declares, and SHALL NOT assume any particular image format.

A listing with an image extension written into it would report a non-image flow's finished work as missing and
render it again, on the one stage that costs money on every pass.

#### Scenario: the completed-output check is not tied to one format
- **Key:** `run-directory:listings:resume-does-not-assume-an-image-format`
- **Layers:** unit
- **WHEN** the set of already-produced outputs is computed for a flow
- **THEN** it is derived from the output form that flow declares
- **AND** no image format is named in the predicate

### Requirement: Inspection reads the flows root it was given, and refuses before it prints

The system SHALL resolve a run's flows through the flows root the invocation supplies rather than a
default, and SHALL refuse a run holding a directory no flow answers for before any line of the report is
printed.

A verb that takes an injected root and reads another is a seam that is not one: a run captured under another root
cannot be inspected, and inspection's whole job is reading a run in any state. The report streams, so a refusal
after output begins leaves a partial account with no way to tell which lines were complete.

#### Scenario: inspection reads the flows root it is given
- **Key:** `run-directory:inspection:the-injected-flows-root-is-used`
- **Layers:** unit
- **WHEN** a run is inspected with a flows root supplied by the invocation
- **THEN** the flows it reports are resolved through that root

#### Scenario: a directory no flow answers for refuses before any line is printed
- **Key:** `run-directory:inspection:an-unanswerable-directory-refuses-first`
- **Layers:** unit
- **WHEN** a run holds a directory no tracked flow answers for
- **THEN** the invocation is refused
- **AND** no line of the report has been printed

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

### Requirement: A run's photograph is named inside the run

The system SHALL refuse a run whose frame names its photograph with anything but one plain filename, or lacks the
photograph's name or digest, naming the frame and its remedy. It SHALL NOT read, serve or send a file outside the
run on the frame's word.

The frame is a file on disk. A name holding a separator or `..` would point the run at any image on the machine,
which the review surface serves and the render uploads.

#### Scenario: a name that leaves the run is refused
- **Key:** `run-directory:frame:a-name-that-leaves-the-run-is-refused`
- **Layers:** unit
- **WHEN** a frame's photograph name holds a path separator, is `..`, or is absolute
- **THEN** reading the run's photograph is refused naming the frame
- **AND** no file outside the run is opened

#### Scenario: a photograph that is a link is refused
- **Key:** `run-directory:frame:a-photograph-that-is-a-link-is-refused`
- **Layers:** unit
- **WHEN** the file a frame names as its photograph is a symbolic link
- **THEN** reading the run's photograph is refused naming the frame and its remedy
- **AND** the file the link points at is not opened

#### Scenario: a frame without its photograph is refused
- **Key:** `run-directory:frame:a-frame-without-its-photograph-is-refused`
- **Layers:** unit
- **WHEN** a frame lacks the photograph block, its name or its digest
- **THEN** the run is refused naming the frame and the missing key
- **AND** the batch's other photographs go on

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
