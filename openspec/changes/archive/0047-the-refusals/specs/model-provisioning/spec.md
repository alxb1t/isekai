## MODIFIED Requirements

### Requirement: The tag vocabulary and the model it indexes are provisioned from one manifest

The system SHALL declare the tag list the pipeline fills sheets from as a pinned, digested artifact in
its own manifest, and SHALL provision and verify it exactly as every other model artifact is. Where a
build loads the model that tag list is the output layer of, the manifest SHALL pin that model beside
it, at the same revision, and a consumer SHALL verify both before its first use.

A pinned tag list lets a fresh clone fill a sheet, and swapping the vocabulary means pointing one manifest
elsewhere, not changing code. The list and the tagger are one artifact in two files: row N of the list names output
N of the model, so a pair from two revisions mislabels every tag, silently
([D7](../../../docs/decisions.md#d7--wd14-is-one-artifact-in-two-files)). The model is pinned only where a build
loads it, because a vocabulary no loaded model indexes outlives any particular tagger.

#### Scenario: the vocabulary has a pinned, digested entry
- **Key:** `model-provisioning:vocabulary:entry-is-pinned-and-digested`
- **Layers:** unit
- **WHEN** the vocabulary manifest is read
- **THEN** every entry carries a destination, a digest, a byte count and at least one source
- **AND** no source resolves a mutable reference

#### Scenario: the vocabulary manifest is separate from the graph's and the scorer's
- **Key:** `model-provisioning:vocabulary:manifest-is-its-own-file`
- **Layers:** unit
- **WHEN** every provisioning manifest is read
- **THEN** no destination the vocabulary manifest declares appears in any other
- **AND** each manifest continues to answer one question about one consumer

#### Scenario: the label index and the model it indexes are pinned to one revision
- **Key:** `model-provisioning:vocabulary:label-index-and-model-share-a-revision`
- **Layers:** unit
- **WHEN** the vocabulary manifest declares both the tag list and the model it is the output layer of
- **THEN** both entries resolve the same immutable revision of the same publisher's repository
- **AND** a pair naming two revisions fails the check rather than being provisioned

#### Scenario: the shipped driver fetches the vocabulary from its own manifest
- **Key:** `model-provisioning:vocabulary:driver-provisions-the-manifest`
- **Layers:** unit
- **WHEN** the provisioning driver is pointed at the vocabulary manifest
- **THEN** it plans and lands every entry that manifest declares
- **AND** it does so through the same command every other artifact is provisioned by

#### Scenario: an unprovisioned vocabulary refuses naming that command
- **Key:** `model-provisioning:vocabulary:absent-vocabulary-names-the-command`
- **Layers:** unit
- **WHEN** a stage reads the vocabulary and the artifact has not been provisioned
- **THEN** the read is refused rather than raising a file error
- **AND** the message names the command that would provision it

#### Scenario: an artifact the manifest does not declare is refused
- **Key:** `model-provisioning:vocabulary:an-undeclared-artifact-is-refused`
- **Layers:** unit
- **WHEN** a caller asks a manifest for an artifact it does not declare
- **THEN** the command refuses naming the artifact and the manifest it searched
