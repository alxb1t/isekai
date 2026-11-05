## ADDED Requirements

### Requirement: The reader's files are provisioned from their own manifest, keyed by the model the caption config names

The system SHALL declare the reader's model and projector files as pinned, digested entries in a manifest
of their own, derived like every other manifest, and SHALL name, for each model the caption config may name, which
entry is its model file and which its projector. Provisioning SHALL fetch and verify that manifest's entries
exactly as it does every other's.

A manifest makes the reader's files fetchable by the same command as every other artifact, and gives the pre-call
check one place to read the pins from
([D6](../../../docs/decisions.md#d6--ollama-at-a-fixed-local-address-on-a-checked-model)).

#### Scenario: the reader's manifest pins both files of each model
- **Key:** `model-provisioning:reader:each-model-names-its-model-and-projector`
- **Layers:** unit
- **WHEN** the reader's manifest is read
- **THEN** every entry carries a destination, a digest, a byte count and a source at an immutable revision
- **AND** every model it names points at exactly one model file and one projector file among its entries

#### Scenario: the model the caption config names is pinned
- **Key:** `model-provisioning:reader:the-caption-model-is-pinned`
- **Layers:** unit
- **WHEN** the suite runs
- **THEN** the model the caption config names has an entry in the reader's manifest

#### Scenario: the shipped driver provisions the reader's manifest
- **Key:** `model-provisioning:reader:driver-provisions-the-manifest`
- **Layers:** unit
- **WHEN** `fetch` is pointed at the reader's manifest
- **THEN** it lands every entry that manifest declares, verified by digest

## REMOVED Requirements

### Requirement: The reader's files are provisioned from their own manifest, keyed by the model they build

**Reason**: its pinning scenario names the model each tracked flow declares, and no flow declares one; a MODIFIED
block may not drop a scenario title, so the requirement is removed and added under a new title.

**Migration**: *The reader's files are provisioned from their own manifest, keyed by the model the caption config names*
carries every scenario;
`model-provisioning:reader:every-flow-model-is-pinned` is
`model-provisioning:reader:the-caption-model-is-pinned`.
