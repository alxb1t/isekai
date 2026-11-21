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

#### Scenario: a label index whose bytes differ is refused when the vocabulary loads
- **Key:** `tagging:pin:a-damaged-label-index-is-refused-when-the-vocabulary-loads`
- **Layers:** unit
- **WHEN** the vocabulary is loaded and the label index's bytes do not match the digest this build commits for it
- **THEN** the load refuses with a `Refusal` naming the file, the digest expected, the digest computed and the command that would fetch it
- **AND** no vocabulary is returned
