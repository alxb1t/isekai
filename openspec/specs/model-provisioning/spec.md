# Capability: `model-provisioning`

## Purpose

Which model artifacts the shipped graph requires, where each one comes from, how its bytes are
proven to be the intended ones before anything loads them, and the binding that keeps the manifest
and the graph describing the same set of files.

**Source:** `scripts/models.json`, `isekai/boundary/provision.py`, `scripts/download_models.sh`,
`scripts/derive_manifest.py`, `start.sh` ·
**Tests:** `tests/test_provision.py`, `tests/test_manifest.py`, `tests/test_manifest_binding.py`,
`tests/test_infra.py`, `tests/test_derivation.py`, `tests/test_vocabulary_manifest.py`

The manifest is the source of truth for what the stack *is*: every source pinned to an immutable
revision, every artifact carrying a digest, and nothing trusted by name. `provision.py` is **not**
in `python -m isekai`'s import graph, so this capability leaves the stdlib-only runtime rule
untouched.
Every scenario here is proven offline against a fake fetcher — no test reaches a network or a pod.

## Requirements

### Requirement: The manifest declares every artifact the shipped graph requires

The manifest SHALL declare an entry for every model file a render of a tracked flow's graph loads,
including files that no field of the graph names — the annotator checkpoints a preprocessor node
fetches for itself. A graph that requires a file the manifest does not declare MUST fail the suite
offline, because the alternative is discovering it on a metered pod.

The graph the rule is stated over is the one the repository ships under `flows/<id>/graph.json`, not a
single path fixed here. A flow is the unit that owns a graph, so a rule naming one file by hand would
go stale the moment a second flow is added — and it would go stale silently, because a manifest check
against a graph that is no longer rendered still passes. Stating it over the tracked flows keeps the
check binding on whatever is actually rendered; while `summon-v1` is the only flow, that is its graph.

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
- **AND** adding such a node without extending the mapping fails the check rather than passing
  silently

### Requirement: Every source is pinned to an immutable revision and a digest

Every entry SHALL name its bytes by a revision that cannot move and by a SHA-256 digest. A source
that resolves a branch is not a pin: the same URL returns different bytes on different days, and no
record in this repository would show that it had.

Where an artifact has no first-party source at all — every host serving it is a mirror — the digest
is not merely a check on the transfer but the whole trust root, and it SHALL be the digest the
artifact's publisher states rather than one computed from whichever copy was fetched first. A digest
taken from a mirror attests only that the mirrors agree with each other.

These rules SHALL be enforced where the manifest is read on the pod, not only where it is asserted
against in the suite. A check that runs at commit time constrains the manifest this repository
tracks; it does not constrain a manifest the module is handed, and it is the module that joins a
destination onto the filesystem, hands a URL to a transfer, and decides what to fetch. Accordingly
the system SHALL refuse — before any transfer begins and with a message naming the entry — a
destination that does not resolve inside the models root, a source that is not a pinned URL free of
whitespace, and an entry declaring no sources at all.

The system SHALL also carry the resolved destination through to whatever performs the transfer,
rather than having that component join paths of its own, so the containment rule is enforced in one
place instead of being restated wherever a path is assembled.

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
- **AND** the digest is what makes any of those sources acceptable, so the alternates add
  availability without adding trust

#### Scenario: an artifact its publisher does not host is pinned to the publisher's stated digest
- **Key:** `model-provisioning:immutable-pins:mirrored-artifact-pins-the-published-digest`
- **Layers:** unit
- **WHEN** an entry is served only by mirrors, none of them the publisher
- **THEN** its declared digest equals the one the publisher states for that artifact, and the check
  runs offline as part of the ordinary suite rather than only when a human re-derives the manifest
- **AND** the tie between the shipped bytes and the publisher's own digest is therefore held by the
  gate, so changing it is a deliberate test edit rather than a silent retrust of the mirrors
- **AND** that published digest is read from the publisher's own machine-readable record when the
  manifest is derived, rather than transcribed by hand into the files that compare against each
  other, because three copies of one transcription cross-check the copying and not the value

#### Scenario: a destination that escapes the models root is refused
- **Key:** `model-provisioning:immutable-pins:an-escaping-destination-is-refused`
- **Layers:** unit
- **WHEN** an entry names a destination that is absolute, or that resolves outside the models root
- **THEN** provisioning refuses before any transfer, naming the entry and the destination
- **AND** the destination handed to the transfer is the already-resolved path, so no component
  downstream joins a path of its own and the rule is enforced in exactly one place
- **AND** the digest offers no protection here, because whoever supplies the destination supplies the
  digest beside it — and a second project shares the volume this tree lives on

#### Scenario: a source that is not a pinned URL is refused at the point of use
- **Key:** `model-provisioning:immutable-pins:a-malformed-source-is-refused-at-runtime`
- **Layers:** unit
- **WHEN** an entry declares a source that is not a pinned URL, or that contains whitespace
- **THEN** provisioning refuses before any transfer, naming the entry and the source
- **AND** the transfer receives the sources as a list rather than as a string it must split, so a
  source's shape can never change how many arguments the transfer is given

#### Scenario: an entry declaring no sources is refused
- **Key:** `model-provisioning:immutable-pins:an-entry-with-no-sources-is-refused`
- **Layers:** unit
- **WHEN** an entry declares an empty list of sources
- **THEN** provisioning refuses with a message saying that no source was declared for that
  destination
- **AND** it does not report that every source was rejected, because an entry that offered nothing
  and an entry whose every offer was refused are different failures with different fixes

### Requirement: Bytes are verified before they are trusted

Provisioning SHALL compute each file's digest and compare it to the manifest before that file is
usable, whether it was just downloaded or was already on the volume. Verification that runs only on
the download path leaves a warm volume permanently unchecked — which is the case the digest exists
for.

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
- **AND** a subsequent run therefore sees the file as absent rather than as present-and-trusted

#### Scenario: an existing file that fails verification is left on disk
- **Key:** `model-provisioning:byte-verification:a-present-file-that-fails-is-not-deleted`
- **Layers:** unit
- **WHEN** a file that was already present fails verification
- **THEN** provisioning stops without removing it
- **AND** the file survives for inspection, because the volume may hold artifacts this project did
  not put there

### Requirement: A source is checked before a large transfer begins

Where a source publishes the digest of what it will serve, provisioning SHALL compare that published
digest against the manifest before transferring the file. A multi-gigabyte download that ends in a
mismatch costs the same as one that ends in success.

#### Scenario: a published digest that disagrees with the manifest aborts before transfer
- **Key:** `model-provisioning:preflight:published-digest-mismatch-aborts-before-transfer`
- **Layers:** unit
- **WHEN** a source advertises a digest for the file it would serve, and that digest differs from
  the manifest's
- **THEN** provisioning rejects the source without transferring the file
- **AND** the next declared source for that entry is tried

### Requirement: A transfer that fails advances to the next declared source

Where an entry declares more than one source, provisioning SHALL try them in the manifest's order
and abort only when every one of them has failed. An alternate that is never reached buys no
availability: the failure it exists for — a mirror that has gone away — is exactly the one that
stops the run.

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

When provisioning aborts, the pod SHALL stay up with its SSH daemon running rather than terminating.
The abort policy leaves a mismatched file on disk for a human to inspect, and that is only true if
the human can get in: a container whose entrypoint exits takes its daemon with it and dies again on
every subsequent boot, within seconds of start.

That hold SHALL cover preparing the models namespace as well as fetching into it. Preparing the
volume is provisioning by any reading a human would give the word, and a failure there — an
unwritable volume, a link onto a path that could not be cleared — terminates the entrypoint exactly
as a fetch failure used to.

The hold SHALL be bounded rather than indefinite, and the failure SHALL be legible from outside the
container's log. A pod holding open reports as running and healthy while it bills, so an unattended
failure that looks like success is the one that outlasts the session's spending ceiling; the bound
SHALL be shorter than that ceiling allows.

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
- **AND** no step of preparing the namespace can terminate the entrypoint, because the guarantee is
  about provisioning and not about one of its steps

#### Scenario: the hold is bounded and leaves a marker outside the log
- **Key:** `model-provisioning:reachability:the-hold-is-bounded-and-marked`
- **Layers:** unit
- **WHEN** the entrypoint holds the pod open after a provisioning failure
- **THEN** the hold ends on its own within a stated window shorter than the session's spending
  ceiling allows, and a marker recording the failure is written where the failure itself cannot have
  made it unwritable
- **AND** the marker is therefore not written onto the volume, because the volume is exactly the
  thing that may have failed

#### Scenario: the pod refuses to provision onto anything but its network volume
- **Key:** `model-provisioning:reachability:provisioning-requires-the-network-volume`
- **Layers:** unit
- **WHEN** the pod is created without the network volume it expects, or the models namespace would
  otherwise be prepared somewhere that is not that volume
- **THEN** the pod is refused before it is created if the volume it expects is not named, and the
  entrypoint refuses before preparing the namespace if what it finds is not that volume
- **AND** the entrypoint is told which volume to expect rather than inferring it, because the failure
  this prevents — a full model stack downloaded onto storage that does not survive the pod — renders
  correctly, bills fully and is discovered only on the next metered session

### Requirement: Model artifacts resolve inside the project's own namespace

Every artifact this project provisions SHALL resolve within a directory tree belonging to this
project, including artifacts a custom node downloads for itself. Files written outside that tree
land on storage that does not survive the pod, so they are re-fetched during metered renders and
cannot be verified against the manifest at all.

A node that fetches its own models SHALL be bound to the manifest by name rather than by a naming
convention. A rule that recognises such nodes by how their class is spelled binds the ones that
happen to be spelled that way and silently passes the ones that are not, so the artifacts of an
unrecognised node are load-bearing while nothing checks that they are still declared.

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
- **AND** membership is by name rather than by how a class is spelled, so a node that fetches for
  itself cannot pass by not matching a pattern
</content>

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
