## ADDED Requirements

### Requirement: The tag vocabulary and the model it indexes are provisioned from one manifest

The system SHALL declare the tag list the pipeline fills sheets from as a pinned, digested artifact in
its own manifest, and SHALL provision and verify it exactly as every other model artifact is. Where a
build loads the model that tag list is the output layer of, the manifest SHALL pin that model beside
it, at the same revision, and a consumer SHALL verify both before its first use.

The file was untracked and produced only as a side effect of downloading a model this repository did
not run, so a fresh clone could not fill a sheet at all. Giving it its own manifest also makes swapping
the vocabulary a matter of pointing one manifest somewhere else, rather than a code change.

**The tag list and the tagger are one artifact split in two, and this version is what makes that
true.** Row N of the list names output neuron N of the graph, so a list and a graph from different
revisions mislabel every tag — silently, because the vector has the right length and every name in it
is a real tag. Nothing downstream can detect it. A manifest holding one half without the other is
therefore a manifest that cannot catch the one failure that matters, which is why the revision the two
entries name is itself a contract rather than a coincidence.

That claim is conditional on a build loading the model, and it was correct to refuse it while none
did: until the model is loaded, the vocabulary genuinely outlives any particular tagger and pinning
one would have made swapping the list a decision about a model nobody opened.

#### Scenario: the vocabulary has a pinned, digested entry
- **Key:** `model-provisioning:vocabulary:entry-is-pinned-and-digested`
- **Layers:** unit
- **WHEN** the vocabulary manifest is read
- **THEN** every entry carries a destination, a digest, a byte count and at least one source
- **AND** no source resolves a mutable reference

#### Scenario: the vocabulary manifest is separate from the graph's and the scorer's
- **Key:** `model-provisioning:vocabulary:manifest-is-its-own-file`
- **Layers:** unit
- **WHEN** the three manifests are read
- **THEN** no destination the vocabulary manifest declares appears in either of the other two
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

## MODIFIED Requirements

### Requirement: Manifest derivation is shared and each manifest stays byte-identical

The system SHALL derive every manifest through one shared module carrying the entry types and both
digest strategies — reading a published digest where the artifact is stored as a large file, and
hashing the bytes where it is small enough to fetch — and each deriver SHALL continue to produce output
that is byte-identical on a re-run. A deriver that hashes fetched bytes SHALL require the identity
content coding, so that what it hashes is the artifact rather than a transfer representation of it.

Two derivers already share these names by import, which makes that structure load-bearing the moment a
third arrives; the entry type is currently declared twice under one name with two different shapes, and
a third shape is how that becomes a defect rather than an oddity. The byte-identical rule is what makes
the extraction verifiable for nothing: re-run all three, and any difference is the refactor's fault.

**A request that states no acceptable coding accepts every coding**, and a host is free to answer one
fetch compressed and the next one not. A deriver that hashes whatever arrives therefore has a digest
that depends on the weather, which is the byte-identical rule failing in the one direction nothing
would notice: the wrong digest is well-formed, is written to a tracked file, and turns into a refusal
of the correct artifact at the consumer that verifies it.

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

#### Scenario: a fetched digest is of the artifact and not of a transfer encoding
- **Key:** `model-provisioning:derivation:fetched-digest-demands-identity-encoding`
- **Layers:** unit
- **WHEN** a deriver digests an artifact by fetching and hashing its bytes
- **THEN** the request declares that only the identity coding is acceptable
- **AND** a compressed response is therefore never hashed in place of the artifact

## REMOVED Requirements

### Requirement: The tag vocabulary is a provisioned artifact with its own manifest

**Reason:** One of its five scenarios —
`model-provisioning:vocabulary:tagger-model-is-not-included` — asserted that the vocabulary manifest
declares the tag list *and not the model published alongside it*, and that the two are *different
artifacts with different consumers*. This version loads that model, so the premise is gone: the list is
the model's output layer, the two have exactly one consumer between them, and a pair from different
revisions mislabels every tag with nothing downstream able to notice. Keeping the scenario would forbid
the only pin that can detect that. A scenario cannot be retired from a requirement in place, so the
requirement is replaced whole.

**Migration:** Replaced by **The tag vocabulary and the model it indexes are provisioned from one
manifest**, added above. Four of the five scenarios move across **under their existing keys and
unchanged in substance** — `entry-is-pinned-and-digested`, `manifest-is-its-own-file`,
`driver-provisions-the-manifest` and `absent-vocabulary-names-the-command` — with the first two worded
for a manifest that has more than one entry. The fifth is not dropped but inverted, as
`model-provisioning:vocabulary:label-index-and-model-share-a-revision`, which asserts the stronger
property the old one made unreachable: both entries resolve the same immutable revision of the same
publisher's repository. The two tests bound to the retired key — that the manifest declares no model
weights, and that no source fetches a model file — are rebound to the new scenario. No artifact is
unpinned by this removal and no manifest loses an entry.
