## MODIFIED Requirements

### Requirement: A transfer that fails advances to the next declared source

Provisioning SHALL try an entry's sources in the manifest's order and abort only when every one of them has
failed. It SHALL try a transfer that breaks off again from the same source, three attempts in all. A source has
failed when its third attempt breaks off, or at once when the bytes it served fail verification.

An alternate that is never reached buys no availability: a mirror that has gone away is the failure it exists for.
A dropped connection is transient, and an entry with one source has no alternate to fall to; bytes that do not
verify would fail the same way again ([D21](../../../docs/decisions.md#d21--retries-follow-what-can-fail)).

```
source ──▶ transfer ── breaks off, attempts left ──▶ wait ──▶ transfer again
              │
              ├── breaks off a third time ─┐
              ├── bytes do not verify ─────┴──▶ next source ── none left ──▶ abort
              └── bytes verify ──▶ land
```

#### Scenario: the plan carries every source that survives the pre-flight
- **Key:** `model-provisioning:source-fallback:the-plan-carries-every-surviving-source`
- **Layers:** unit
- **WHEN** an entry is absent and more than one of its sources survives the pre-flight
- **THEN** provisioning offers all of them, in the manifest's order
- **AND** a source the pre-flight rejected is not among them

#### Scenario: a failed transfer advances to the next source
- **Key:** `model-provisioning:source-fallback:a-failed-transfer-advances-to-the-next-source`
- **Layers:** unit
- **WHEN** a source has failed
- **THEN** provisioning moves on to the next source for that entry
- **AND** the run aborts only once every source for the entry has failed

#### Scenario: a broken transfer is tried again from the same source
- **Key:** `model-provisioning:source-fallback:a-broken-transfer-is-tried-again`
- **Layers:** unit
- **WHEN** a transfer breaks off before its source's third attempt
- **THEN** provisioning waits and transfers from the same source again
- **AND** the entry lands when a later attempt serves bytes that verify

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
- **WHEN** `fetch` is pointed at the vocabulary manifest
- **THEN** it lands every entry that manifest declares
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

### Requirement: The reader's files are provisioned from their own manifest, keyed by the model they build

The system SHALL declare the reader's model and projector files as pinned, digested entries in a manifest
of their own, derived like every other manifest, and SHALL name, for each model a flow may declare, which
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

#### Scenario: every model a tracked flow declares is pinned
- **Key:** `model-provisioning:reader:every-flow-model-is-pinned`
- **Layers:** unit
- **WHEN** the suite runs
- **THEN** the model every tracked flow declares has an entry in the reader's manifest

#### Scenario: the shipped driver provisions the reader's manifest
- **Key:** `model-provisioning:reader:driver-provisions-the-manifest`
- **Layers:** unit
- **WHEN** `fetch` is pointed at the reader's manifest
- **THEN** it lands every entry that manifest declares, verified by digest
