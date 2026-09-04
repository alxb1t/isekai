## Purpose

Which model artifacts the shipped graph requires, where each one comes from, how its bytes are
proven to be the intended ones before anything loads them, and the binding that keeps the manifest
and the graph describing the same set of files.

## ADDED Requirements

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
