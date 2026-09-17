## MODIFIED Requirements

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

## ADDED Requirements

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
