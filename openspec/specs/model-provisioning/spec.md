# Capability: `model-provisioning`

## Purpose

Which model artifacts the shipped graph requires, where each comes from, and how its bytes are proven to be the
intended ones before anything loads them. The manifest is the source of truth: every source pinned to an immutable
revision, every artifact carrying a digest, nothing trusted by name.

## Requirements

### Requirement: The manifest declares every artifact the shipped graph requires

The manifest SHALL declare an entry for every model file a render of a tracked flow's graph loads,
including files that no field of the graph names — the annotator checkpoints a preprocessor node
fetches for itself. A graph that requires a file the manifest does not declare MUST fail the suite
offline.

Otherwise the missing file is found on a metered pod. The rule is stated over every tracked flow's
`flows/<id>/graph.json`, because a check against one hand-named graph still passes once that graph is no longer
rendered.

#### Scenario: a model filename named in the graph has a manifest entry
- **Key:** `model-provisioning:manifest-completeness:graph-filename-has-an-entry`
- **Layers:** unit
- **WHEN** the shipped graph names a model file in a node's inputs — a checkpoint, a ControlNet, an
  InstantID file, a detector or a pose estimator
- **THEN** the manifest declares an entry whose destination filename is that file
- **AND** a graph edited to name a file the manifest does not carry fails the check

#### Scenario: a preprocessor's own models are declared even though the graph never names them
- **Key:** `model-provisioning:manifest-completeness:preprocessor-models-are-declared`
- **Layers:** unit
- **WHEN** the graph contains a preprocessor node that downloads model files it exposes no field for
- **THEN** the manifest declares those files, resolved through a tracked mapping from node class to
  required filenames
- **AND** adding such a node without extending the mapping fails the check

### Requirement: Every source is pinned to an immutable revision and a digest

Every entry SHALL name its bytes by a revision that cannot move and by a SHA-256 digest. Where every host
serving an artifact is a mirror, its digest SHALL be the one the artifact's publisher states, not one computed from
a fetched copy. These rules SHALL be enforced where the manifest is read on the pod: the system SHALL refuse,
before any transfer begins and with a message naming the entry, a destination that does not resolve inside the
models root, a source that is not a pinned URL free of whitespace, and an entry declaring no sources at all. The
system SHALL carry the resolved destination through to whatever performs the transfer, rather than have that
component join paths of its own.

A branch is not a pin: one URL returns different bytes on different days, and no record here would show it. Where
no first-party source exists the digest is the whole trust root, and a digest taken from a mirror attests only that
the mirrors agree. A check at commit time constrains the tracked manifest, not one the module is handed, and the
module is what joins a destination onto the filesystem and hands a URL to a transfer; carrying the resolved path
keeps containment in one place.

#### Scenario: no source resolves a mutable ref
- **Key:** `model-provisioning:immutable-pins:no-source-resolves-a-mutable-ref`
- **Layers:** unit
- **WHEN** the manifest's sources are examined
- **THEN** every one addresses an immutable revision
- **AND** a source naming a branch rather than a revision fails the check

#### Scenario: every entry carries a digest
- **Key:** `model-provisioning:immutable-pins:every-entry-carries-a-digest`
- **Layers:** unit
- **WHEN** the manifest's entries are examined
- **THEN** each declares a SHA-256 digest of the file's full contents
- **AND** an entry with a missing or malformed digest fails the check

#### Scenario: an artifact with no first-party source carries an alternate
- **Key:** `model-provisioning:immutable-pins:third-party-artifact-carries-an-alternate`
- **Layers:** unit
- **WHEN** an entry's primary source is a third-party mirror rather than the publisher
- **THEN** the entry declares at least one additional source for the same digest
- **AND** every source is accepted only by that digest

#### Scenario: an artifact its publisher does not host is pinned to the publisher's stated digest
- **Key:** `model-provisioning:immutable-pins:mirrored-artifact-pins-the-published-digest`
- **Layers:** unit
- **WHEN** an entry is served only by mirrors, none of them the publisher
- **THEN** its declared digest equals the one the publisher states for that artifact, checked offline in the suite
- **AND** that digest is read from the publisher's own machine-readable record when the manifest is derived, not
  transcribed by hand

#### Scenario: a destination that escapes the models root is refused
- **Key:** `model-provisioning:immutable-pins:an-escaping-destination-is-refused`
- **Layers:** unit
- **WHEN** an entry names a destination that is absolute, or that resolves outside the models root
- **THEN** provisioning refuses before any transfer, naming the entry and the destination
- **AND** the destination handed to the transfer is the already-resolved path

#### Scenario: a source that is not a pinned URL is refused at the point of use
- **Key:** `model-provisioning:immutable-pins:a-malformed-source-is-refused-at-runtime`
- **Layers:** unit
- **WHEN** an entry declares a source that is not a pinned URL, or that contains whitespace
- **THEN** provisioning refuses before any transfer, naming the entry and the source
- **AND** the transfer receives the sources as a list rather than as a string it must split

#### Scenario: an entry declaring no sources is refused
- **Key:** `model-provisioning:immutable-pins:an-entry-with-no-sources-is-refused`
- **Layers:** unit
- **WHEN** an entry declares an empty list of sources
- **THEN** provisioning refuses with a message saying that no source was declared for that destination
- **AND** it does not report that every source was rejected

### Requirement: Bytes are verified before they are trusted

Provisioning SHALL compute each file's digest and compare it to the manifest before that file is
usable, whether it was just downloaded or was already on the volume.

Verification only on the download path leaves a warm volume unchecked for good, and that is the case the digest
exists for.

#### Scenario: contents that do not match the declared digest are rejected
- **Key:** `model-provisioning:byte-verification:mismatched-bytes-are-rejected`
- **Layers:** unit
- **WHEN** a file's computed digest differs from the digest declared for it
- **THEN** verification fails and provisioning stops with a non-zero exit
- **AND** the failure names the file, the expected digest and the computed one

#### Scenario: a file already present is verified rather than skipped
- **Key:** `model-provisioning:byte-verification:a-present-file-is-verified-not-skipped`
- **Layers:** unit
- **WHEN** provisioning encounters a file that already exists at its destination
- **THEN** its digest is computed and compared before it is treated as present
- **AND** a file whose bytes were replaced out of band is caught rather than accepted by name

#### Scenario: a failed download never lands under its final name
- **Key:** `model-provisioning:byte-verification:a-failed-download-never-lands`
- **Layers:** unit
- **WHEN** a download is interrupted or its bytes fail verification
- **THEN** nothing appears at the destination filename
- **AND** a later run sees the file as absent

#### Scenario: an existing file that fails verification is left on disk
- **Key:** `model-provisioning:byte-verification:a-present-file-that-fails-is-not-deleted`
- **Layers:** unit
- **WHEN** a file that was already present fails verification
- **THEN** provisioning stops without removing it
- **AND** the file survives for inspection

### Requirement: A source is checked before a large transfer begins

Where a source publishes the digest of what it will serve, provisioning SHALL compare that published
digest against the manifest before transferring the file.

A multi-gigabyte download that ends in a mismatch costs the same as one that ends in success.

#### Scenario: a published digest that disagrees with the manifest aborts before transfer
- **Key:** `model-provisioning:preflight:published-digest-mismatch-aborts-before-transfer`
- **Layers:** unit
- **WHEN** a source advertises a digest for the file it would serve, and that digest differs from
  the manifest's
- **THEN** provisioning rejects the source without transferring the file
- **AND** the next declared source for that entry is tried

### Requirement: A transfer that fails advances to the next declared source

Where an entry declares more than one source, provisioning SHALL try them in the manifest's order
and abort only when every one of them has failed.

An alternate that is never reached buys no availability: a mirror that has gone away is the failure it exists for.

#### Scenario: the plan carries every source that survives the pre-flight
- **Key:** `model-provisioning:source-fallback:the-plan-carries-every-surviving-source`
- **Layers:** unit
- **WHEN** an entry is absent and more than one of its sources survives the pre-flight
- **THEN** the plan carries all of them, in the manifest's order
- **AND** a source the pre-flight rejected is absent from that list

#### Scenario: a failed transfer advances to the next source
- **Key:** `model-provisioning:source-fallback:a-failed-transfer-advances-to-the-next-source`
- **Layers:** unit
- **WHEN** a transfer from one source fails, or the bytes it served fail verification
- **THEN** the driver moves on to the next source the plan carries for that entry
- **AND** the run aborts only once every source for the entry has been exhausted

### Requirement: A provisioning failure leaves the pod reachable

When provisioning aborts — preparing the models namespace or fetching into it — the pod SHALL stay up with its
SSH daemon running rather than terminating. The hold SHALL be bounded, shorter than the session's spending ceiling
allows, SHALL end in the pod stopping itself, and the failure SHALL be legible from outside the container's log.

```
provisioning fails ──▶ hold: SSH up, inference server not started, marker written off the volume
                          │
                          └── window ends ──▶ the pod stops itself
```

The abort policy leaves a mismatched file on disk for a person to inspect, which holds only if they can get in: an
entrypoint that exits takes its daemon with it and dies again on every boot. A pod holding open reports as running
and healthy while it bills, so an unbounded hold outlasts the spending ceiling; a hold that ended in its process
exiting would restart with the container and hold again.

#### Scenario: a provisioning abort holds the pod open instead of stopping it
- **Key:** `model-provisioning:reachability:a-provisioning-abort-holds-the-pod-open`
- **Layers:** unit
- **WHEN** the pod entrypoint's provisioning step exits non-zero
- **THEN** the entrypoint reports the failure and holds in the foreground with the SSH daemon alive
- **AND** the inference server is not started, and nothing on the volume is removed

#### Scenario: preparing the namespace is held open the same way fetching is
- **Key:** `model-provisioning:reachability:namespace-setup-is-held-open-too`
- **Layers:** unit
- **WHEN** preparing the models namespace fails before any artifact is fetched
- **THEN** the entrypoint reports the failure and holds the pod open exactly as a fetch failure does
- **AND** no step of preparing the namespace can terminate the entrypoint

#### Scenario: the hold is bounded and leaves a marker outside the log
- **Key:** `model-provisioning:reachability:the-hold-is-bounded-and-marked`
- **Layers:** unit
- **WHEN** the entrypoint holds the pod open after a provisioning failure
- **THEN** the hold ends by stopping the pod, within a stated window shorter than the session's spending ceiling
  allows
- **AND** a marker recording the failure is written where the failure cannot have made it unwritable
- **AND** the marker is not written onto the volume

#### Scenario: the pod refuses to provision onto anything but its network volume
- **Key:** `model-provisioning:reachability:provisioning-requires-the-network-volume`
- **Layers:** unit
- **WHEN** the pod is created without the network volume it expects, or the models namespace would be prepared
  somewhere that is not that volume
- **THEN** the pod is refused before it is created if the volume it expects is not named
- **AND** the entrypoint refuses before preparing the namespace if what it finds is not that volume
- **AND** the entrypoint is told which volume to expect rather than inferring it

### Requirement: Model artifacts resolve inside the project's own namespace

Every artifact this project provisions SHALL resolve within a directory tree belonging to this
project, including artifacts a custom node downloads for itself. A node that fetches its own models SHALL be
bound to the manifest by name rather than by a naming convention.

Files written outside that tree land on storage that does not survive the pod, so they are re-fetched during
metered renders and never verified against the manifest. A rule matching how a class is spelled binds the nodes
spelled that way and silently passes the rest.

#### Scenario: annotator checkpoints resolve onto the project's models tree
- **Key:** `model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree`
- **Layers:** unit
- **WHEN** the pod's configuration is examined
- **THEN** the preprocessor pack's checkpoint directory is set to a path inside the project's models
  tree
- **AND** a configuration that leaves it at the pack's own default fails the check

#### Scenario: every self-fetching node in the graph is bound to the manifest by name
- **Key:** `model-provisioning:namespace:self-fetching-nodes-are-bound-by-name`
- **Layers:** unit
- **WHEN** the shipped graph is examined against the set of node classes known to fetch their own
  models
- **THEN** every such class present in the graph has its artifacts declared in the manifest, and a
  class in the graph that is absent from that set fails the check
- **AND** membership is by name, not by how a class is spelled

### Requirement: Manifest derivation is shared and each manifest stays byte-identical

The system SHALL derive every manifest through one shared module carrying the entry types and both
digest strategies — reading a published digest where the artifact is stored as a large file, and
hashing the bytes where it is small enough to fetch — and each deriver SHALL continue to produce output
that is byte-identical on a re-run. A deriver that hashes fetched bytes SHALL digest the artifact
itself and nothing else: it SHALL refuse a response whose body is shorter than the length that response
declares, and SHALL require the identity content coding.

One module means no two entry shapes share a name. The byte-identical rule makes any change to a deriver
checkable: re-run it, and any difference is the change's. A digest of whatever arrived is a real SHA-256, written
to a tracked file, that later refuses the correct artifact. A dropped connection returns a truncated body without
complaint, which the length check catches; a request naming no coding may be answered compressed, which only the
identity coding prevents, because a coded response declares its coded length.

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

#### Scenario: a truncated response is refused rather than digested
- **Key:** `model-provisioning:derivation:a-truncated-fetch-is-refused`
- **Layers:** unit
- **WHEN** a deriver fetches an artifact and the body it receives is shorter than the declared length
- **THEN** the derivation fails naming the shortfall
- **AND** no digest is computed over the partial body

#### Scenario: a fetched digest is of the artifact and not of a transfer encoding
- **Key:** `model-provisioning:derivation:fetched-digest-demands-identity-encoding`
- **Layers:** unit
- **WHEN** a deriver digests an artifact by fetching and hashing its bytes
- **THEN** the request declares that only the identity coding is acceptable
- **AND** a compressed response is never hashed in place of the artifact

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

### Requirement: The reader's files are provisioned from their own manifest, keyed by the model they build

The system SHALL declare the reader's model and projector files as pinned, digested entries in a manifest
of their own, derived like every other manifest, and SHALL name, for each model a flow may declare, which
entry is its model file and which its projector. The provisioning driver SHALL fetch and verify that
manifest's entries exactly as it does every other's.

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
- **WHEN** the provisioning driver is pointed at the reader's manifest
- **THEN** it plans and lands every entry that manifest declares, verified by digest
