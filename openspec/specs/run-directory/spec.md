# Capability: `run-directory`

## Purpose

The directory every pipeline stage couples through, and the only thing they share: how a photograph
becomes an identified run, how the run is nested input above and flow below, how artifacts are numbered
and never overwritten, how a filename carries everything resume decides on, and how a failure is
recorded without becoming a completion.

**Source:** `isekai/foundation/run.py`, `isekai/foundation/refusal.py`,
`isekai/shared/atomic_write.py` ·
**Tests:** `tests/test_run_directory.py`, `tests/test_resume.py`, `tests/test_caption.py`,
`tests/test_sheet_stage.py`, `tests/test_review.py`, `tests/test_generate.py`

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

A producer that names only a model cannot explain its own result. The instruction text given to a
reader is the variable with the largest measured effect on what comes back — one briefing change moved
a reader's score from 0.518 to 0.307 and manufactured nineteen identity marks that were not in the
photographs — so the digest of that text is recorded beside the model that read it.

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
- **THEN** the producer records that text's path and digest
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

A test that has to open and parse a file is a test that can be defeated by a truncated file, a
permission error or an unknown schema. Everything else a human wants to know — the model, the
instructions, the source version — lives inside the artifact and is read by a person, never by control
flow.

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

### Requirement: A failure is recorded as an attempt, never as a completion

The system SHALL record a stage's failure as a sibling of the artifact it failed to produce, SHALL
carry the attempt's ordinal and its kind in that file's name, and SHALL NOT consume the artifact's
version number with a failure.

Two stages take their version number from an upstream artifact rather than counting their own, so
"a retry writes the next number" has no next number to write there. Putting the kind and the ordinal in
the name is what keeps the retry decision a directory listing, which is the same rule the completion
tests are held to.

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

A best-effort parse of a format you do not know produces numbers that look fine and mean nothing. This
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

### Requirement: A run root is under the ignored root or outside the repository

The system SHALL refuse a run root that lies inside the repository working tree and is not under the
repository's single ignored data root. A run root outside the repository entirely SHALL be accepted.

A run holds a copy of the photograph by construction — that is what makes a run reconstructable from
disk — so a run directory is a directory of personal photographs. Inside the working tree and outside
the ignored root, those photographs are trackable by version control and are one `git add` from being
published; outside the repository they are not, whatever path they sit at. The rule therefore bounds
the working tree rather than bounding the filesystem, which is also what keeps the flag useful: a
version's acceptance run, or a run on another disk, remains expressible.

Stating it as a requirement is the point. The claim has been made in a source comment since the flag
was introduced and has been false for that whole time, because no scenario held it.

#### Scenario: a run root inside the working tree and outside the ignored root is refused
- **Key:** `run-directory:containment:in-tree-run-root-is-refused`
- **Layers:** unit
- **WHEN** a run root resolves to a path inside the repository working tree that is not under the
  ignored data root
- **THEN** the invocation is refused before any run is created
- **AND** the message names the path given and what would be accepted

#### Scenario: a run root outside the repository is accepted
- **Key:** `run-directory:containment:external-run-root-is-accepted`
- **Layers:** unit
- **WHEN** a run root resolves to a path outside the repository working tree
- **THEN** it is accepted and runs are created under it
- **AND** no containment check applies to it, because version control cannot reach it

#### Scenario: the default run root is under the ignored root
- **Key:** `run-directory:containment:default-is-the-ignored-root`
- **Layers:** unit
- **WHEN** no run root is given
- **THEN** runs are created under the repository's ignored data root

### Requirement: The run directory is input above, flow below, and every artifact is a flow's own

The system SHALL place the input and its frame at the root of a run, and SHALL place every artifact any
stage produces under a directory named for the flow that produced it. It SHALL NOT place any stage's
artifacts above the flow level, and SHALL NOT let one flow read another flow's artifacts.

The layout is a picture of the coupling rather than a filing convention: above the flow split sits what
every flow shares, and after this change the only thing every flow shares is the input itself, copied
once however many flows run. Nesting stage-first meant adding a flow scattered four entries across four
stage directories; nesting flow-first means adding a flow adds one subtree, and retiring one flow's work
for one input is removing one directory. Keeping captions below the split is what makes a flow's
briefing binding: a caption written under one flow's instructions can never be picked up by a flow whose
instructions differ, because the two never name the same directory.

#### Scenario: every stage writes under the flow
- **Key:** `run-directory:layout:stage-artifacts-live-under-the-flow`
- **Layers:** unit
- **WHEN** a run has been carried through every stage for a flow
- **THEN** that flow's captions, sheets, reviews, prompts and outputs are all under one directory named
  for the flow
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

Every "is this done?" test is a directory listing, and the rendering test was the one that had an
extension written into it — so a flow whose output is not a still image would have had its finished work
reported as missing and re-rendered, on the one stage that costs money on every pass. The path already
generalised; the predicate did not.

#### Scenario: the completed-output check is not tied to one format
- **Key:** `run-directory:listings:resume-does-not-assume-an-image-format`
- **Layers:** unit
- **WHEN** the set of already-produced outputs is computed for a flow
- **THEN** it is derived from the output form that flow declares
- **AND** no image format is named in the predicate
