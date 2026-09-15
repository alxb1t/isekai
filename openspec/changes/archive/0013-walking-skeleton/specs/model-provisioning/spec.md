## ADDED Requirements

### Requirement: The tag vocabulary is a provisioned artifact with its own manifest

The system SHALL declare the tag list the pipeline fills sheets from as a pinned, digested artifact in
its own manifest, and SHALL provision and verify it exactly as every other model artifact is.

The file is currently untracked and produced only as a side effect of downloading an unrelated model,
so a fresh clone cannot fill a sheet at all. Giving it its own manifest also makes swapping the
vocabulary a matter of pointing one manifest somewhere else, rather than a code change.

#### Scenario: the vocabulary has a pinned, digested entry
- **Key:** `model-provisioning:vocabulary:entry-is-pinned-and-digested`
- **Layers:** unit
- **WHEN** the vocabulary manifest is read
- **THEN** its entry carries a destination, a digest, a byte count and at least one source
- **AND** no source resolves a mutable reference

#### Scenario: the vocabulary manifest is separate from the graph's and the scorer's
- **Key:** `model-provisioning:vocabulary:manifest-is-its-own-file`
- **Layers:** unit
- **WHEN** the three manifests are read
- **THEN** the vocabulary's entry appears only in its own manifest
- **AND** each manifest continues to answer one question about one consumer

#### Scenario: the tagger model is not in the vocabulary manifest
- **Key:** `model-provisioning:vocabulary:tagger-model-is-not-included`
- **Layers:** unit
- **WHEN** the vocabulary manifest is read
- **THEN** it declares the tag list and not the model published alongside it
- **AND** the two are treated as different artifacts with different consumers

#### Scenario: the shipped driver fetches the vocabulary from its own manifest
- **Key:** `model-provisioning:vocabulary:driver-provisions-the-manifest`
- **Layers:** unit
- **WHEN** the provisioning driver is pointed at the vocabulary manifest
- **THEN** it plans and lands that manifest's entries
- **AND** it does so through the same command every other artifact is provisioned by

#### Scenario: an unprovisioned vocabulary refuses naming that command
- **Key:** `model-provisioning:vocabulary:absent-vocabulary-names-the-command`
- **Layers:** unit
- **WHEN** a stage reads the vocabulary and the artifact has not been provisioned
- **THEN** the read is refused rather than raising a file error
- **AND** the message names the command that would provision it

### Requirement: Manifest derivation is shared and each manifest stays byte-identical

The system SHALL derive every manifest through one shared module carrying the entry types and both
digest strategies — reading a published digest where the artifact is stored as a large file, and
hashing the bytes where it is small enough to fetch — and each deriver SHALL continue to produce output
that is byte-identical on a re-run.

Two derivers already share these names by import, which makes that structure load-bearing the moment a
third arrives; the entry type is currently declared twice under one name with two different shapes, and
a third shape is how that becomes a defect rather than an oddity. The byte-identical rule is what makes
the extraction verifiable for nothing: re-run all three, and any difference is the refactor's fault.

#### Scenario: the entry type is declared once
- **Key:** `model-provisioning:derivation:entry-type-has-one-definition`
- **Layers:** unit
- **WHEN** the derivers are loaded
- **THEN** each takes its manifest entry type from the shared module
- **AND** no deriver declares a competing type under the same name

#### Scenario: both digest strategies are available to every deriver
- **Key:** `model-provisioning:derivation:both-digest-strategies-are-shared`
- **Layers:** unit
- **WHEN** an artifact is not stored as a large file and so publishes no digest to read
- **THEN** its digest is obtained by fetching and hashing the bytes
- **AND** that strategy is the same one every deriver reaches for

#### Scenario: re-deriving leaves every manifest unchanged
- **Key:** `model-provisioning:derivation:rerun-is-byte-identical`
- **Layers:** unit
- **WHEN** a deriver is re-run against unchanged upstream state
- **THEN** its manifest file is byte-identical to the committed one
- **AND** any difference is surfaced as a change to be reviewed rather than applied silently

### Requirement: Every provisioned artifact's licence is recorded before it is relied on

The system SHALL record, for each artifact it provisions, the terms that artifact carries, the source
those terms were read from, and the date they were read.

The repository already keeps this record for the artifacts the scorer loads, and the reason is that a
public repository which distributes no weights still points at them. Recording the terms at the version
that first provisions an artifact is what keeps the record from being a list of the ones somebody
happened to check.

#### Scenario: the vocabulary's terms are recorded
- **Key:** `model-provisioning:licences:vocabulary-terms-are-recorded`
- **Layers:** unit
- **WHEN** the licence record is read
- **THEN** it carries an entry for the vocabulary artifact
- **AND** that entry names the terms, the source and the date they were read
