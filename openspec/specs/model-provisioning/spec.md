# Capability: `model-provisioning`

Which model artifacts the shipped graph requires, where each one comes from, how its bytes are
proven to be the intended ones before anything loads them, and the binding that keeps the manifest
and the graph describing the same set of files.

**Source:** `scripts/models.json`, `isekai/provision.py`, `scripts/download_models.sh`,
`scripts/derive_manifest.py`, `start.sh` ·
**Tests:** `tests/test_provision.py`, `tests/test_manifest.py`, `tests/test_manifest_binding.py`,
`tests/test_infra.py`

The manifest is the source of truth for what the stack *is*: every source pinned to an immutable
revision, every artifact carrying a digest, and nothing trusted by name. `provision.py` is **not**
in `convert.py`'s import graph, so this capability leaves the stdlib-only runtime rule untouched.
Every scenario here is proven offline against a fake fetcher — no test reaches a network or a pod.

## Requirements

### Requirement: The manifest declares every artifact the shipped graph requires

The manifest SHALL declare an entry for every model file a render of `workflows/pipeline.json`
loads, including files that no field of the graph names — the annotator checkpoints a preprocessor
node fetches for itself. A graph that requires a file the manifest does not declare MUST fail the
suite offline, because the alternative is discovering it on a metered pod.

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

#### Scenario: a provisioning abort holds the pod open instead of stopping it
- **Key:** `model-provisioning:reachability:a-provisioning-abort-holds-the-pod-open`
- **Layers:** unit
- **WHEN** the pod entrypoint's provisioning step exits non-zero
- **THEN** the entrypoint reports the failure and holds in the foreground with the SSH daemon alive
- **AND** the inference server is not started, and nothing on the volume is removed

### Requirement: Model artifacts resolve inside the project's own namespace

Every artifact this project provisions SHALL resolve within a directory tree belonging to this
project, including artifacts a custom node downloads for itself. Files written outside that tree
land on storage that does not survive the pod, so they are re-fetched during metered renders and
cannot be verified against the manifest at all.

#### Scenario: annotator checkpoints resolve onto the project's models tree
- **Key:** `model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree`
- **Layers:** unit
- **WHEN** the pod's configuration is examined
- **THEN** the preprocessor pack's checkpoint directory is set to a path inside the project's models
  tree
- **AND** a configuration that leaves it at the pack's own default fails the check
