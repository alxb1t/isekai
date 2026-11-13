## MODIFIED Requirements

### Requirement: The model and its label index are verified together or not used

The system SHALL verify the local tagger's model file and its label index against the digests this
repository commits before the first inference, SHALL refuse naming the command that would fetch either
when it is absent or its bytes differ, and SHALL NOT use one without the other.

They are one artifact in two files: row N of the label index names output N of the model
([D7](../../../docs/decisions.md#d7--wd14-is-one-artifact-in-two-files)). A mismatched pair does not fail — it yields a
well-formed, confidently scored list in which every tag is wrong, and nothing downstream can tell. Checking at first
use lets a machine that never tags leave the model file unopened.

#### Scenario: a model and label index from different revisions are refused
- **Key:** `tagging:pin:the-label-index-and-the-model-are-verified-together`
- **Layers:** unit
- **WHEN** the model file or the label index does not match the digest this build commits for it
- **THEN** the command refuses naming what to fetch and where it belongs
- **AND** no inference is attempted and no attempt is recorded

#### Scenario: the check does not fire until a verb asks
- **Key:** `tagging:pin:the-check-fires-at-first-use`
- **Layers:** unit
- **WHEN** a wiring is composed and no tagging is performed
- **THEN** no model file is opened and no digest is computed

#### Scenario: a vector that disagrees with the index is refused
- **Key:** `tagging:pin:a-vector-that-disagrees-with-the-index-is-refused`
- **Layers:** unit
- **WHEN** the model answers a vector whose length differs from the label index's
- **THEN** the command refuses naming both lengths and what to fetch
- **AND** no tag list is built from the shorter of the two

#### Scenario: the graph is opened only after both digests verify
- **Key:** `tagging:pin:the-graph-is-opened-only-after-both-digests-verify`
- **Layers:** unit
- **WHEN** the label index matches its digest and the model's bytes do not
- **THEN** no session is opened on any model file
- **AND** the failure names the model file

### Requirement: The tagger is an injectable seam with an offline stand-in

The system SHALL reach every tagger through an interface a test double satisfies, so the suite exercises
this stage with no network call and without the model file present, and the double SHALL make it
provable that a complete stage made no call.

The model is not in the repository, and a suite that needed it would not run on a fresh clone, so the gate would
silently stop covering this stage. Proving that a complete stage made no call needs something that counts calls.
The seam sits at the boundary as well as at the stage, because the preparation rule and the label-index ordering
are logic the stage's own double does not reach.

#### Scenario: the suite produces both tag artifacts with no network and no model file
- **Key:** `tagging:seam:offline-double-satisfies-the-interface`
- **Layers:** unit
- **WHEN** the stage runs with the test doubles in place
- **THEN** both tag artifacts are written
- **AND** no network call is attempted and no model file is opened

#### Scenario: a photograph is prepared by the graph's rule
- **Key:** `tagging:seam:the-photograph-is-prepared-by-the-graphs-rule`
- **Layers:** unit
- **WHEN** a photograph that is not square and holds a transparent pixel is prepared for the graph's edge
- **THEN** the transparent pixel is white and the photograph sits centred on a white square
- **AND** each pixel's channels run blue, green, red
- **AND** the array is a batch of one, edge by edge by channels, in 32-bit floats

### Requirement: Each tagger's failure is its own, and the local tagger runs first

The system SHALL produce the local tag list, then the hosted tag list, under the tag verb, and a failure
in either SHALL NOT remove, prevent or invalidate the other's artifact — whether the failure is the
photograph's or the build's. The caption verb SHALL write no tag list.

Failures are collected per photograph, and the local list is the sheet's only input, so a refusal of the prose or of
the hosted list must not cost it ([D1](../../../docs/decisions.md#d1--stage--is-two-independent-verbs)). Inside the
tag verb each tagger's refusal is collected on its own. The local tagger runs first because it is the sheet's input
and reaches no network.

#### Scenario: a hosted tagger failure leaves the local tag list on disk
- **Key:** `tagging:order:a-late-failure-leaves-the-earlier-artifacts-complete`
- **Layers:** unit
- **WHEN** the hosted tagger fails for a photograph whose local tag list succeeded
- **THEN** that list is complete on disk
- **AND** the next invocation produces only the missing tag list

#### Scenario: a local tagger failure leaves the hosted list written
- **Key:** `tagging:order:a-local-failure-leaves-the-hosted-list-written`
- **Layers:** unit
- **WHEN** the local tagger fails for a photograph, or cannot be opened at all
- **THEN** the hosted tagger still runs for that photograph and its list is written
- **AND** the command refuses naming the local tagger's failure

#### Scenario: captioning writes no tag list
- **Key:** `tagging:order:captioning-writes-no-tag-list`
- **Layers:** unit
- **WHEN** a photograph is captioned
- **THEN** the prose is written
- **AND** no tag list is written and no tagger is called

#### Scenario: a photograph that will not decode is a local failure
- **Key:** `tagging:order:a-photograph-that-will-not-decode-is-a-local-failure`
- **Layers:** unit
- **WHEN** the local tagger is given a photograph too large to decode
- **THEN** the hosted tagger still runs for that photograph and its list is written
- **AND** the command refuses naming the photograph
- **AND** the failure is recorded as permanent beside the list it failed to produce
