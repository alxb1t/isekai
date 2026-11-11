## ADDED Requirements

### Requirement: A zip entry's members are unpacked and each verified

The system SHALL let a manifest entry declare `unpack`, a list of members, each with its name in the archive, its
destination, its digest and its size. It SHALL verify the archive against its digest before it reads a member, and SHALL
write each member to its declared destination alone, never to a name the archive supplies, through a `.partial` that
is renamed only once the member's digest verifies. It SHALL read no more bytes of a member than its declared size.
It SHALL keep the archive, so that a member gone from the models directory is unpacked again with no transfer, and
SHALL refuse a member the archive lacks and a destination that does not resolve inside the models directory. It SHALL
resolve a member's destination only against the member's own digest.

The archive's names are the publisher's, and a name such as `../x` must never decide where a byte lands. A digest of
the archive says the members are the pinned ones, and a digest of each member says the unpacked file is still the one.

#### Scenario: a verified archive lands its members
- **Key:** `model-provisioning:unpack:a-verified-archive-lands-its-members`
- **Layers:** unit
- **WHEN** an entry for a zip with two declared members is fetched through a fake source
- **THEN** the archive and each member are at their destinations, each hashing to its declared digest

#### Scenario: the archive names no destination
- **Key:** `model-provisioning:unpack:the-archive-names-no-destination`
- **Layers:** unit
- **WHEN** a zip holds a member named `../escape.onnx` beside the declared one
- **THEN** only the declared destinations are written, and no file lies outside the models directory

#### Scenario: a member that does not verify is removed and refused
- **Key:** `model-provisioning:unpack:a-member-that-does-not-verify-is-removed-and-refused`
- **Layers:** unit
- **WHEN** a member's bytes differ from its declared digest
- **THEN** the unpack is refused naming the member and both digests
- **AND** neither the `.partial` nor the destination remains

#### Scenario: a member past its size is refused
- **Key:** `model-provisioning:unpack:a-member-past-its-size-is-refused`
- **Layers:** unit
- **WHEN** a member holds more bytes than its declared size
- **THEN** the unpack is refused, and no more than the declared size plus one byte was read

#### Scenario: a gone member is unpacked with no transfer
- **Key:** `model-provisioning:unpack:a-gone-member-is-unpacked-with-no-transfer`
- **Layers:** unit
- **WHEN** the archive is present and verified and one member's file is gone
- **THEN** a fetch writes that member from the archive and makes no transfer

#### Scenario: a member the archive lacks is refused
- **Key:** `model-provisioning:unpack:a-member-the-archive-lacks-is-refused`
- **Layers:** unit
- **WHEN** an entry declares a member the zip does not hold
- **THEN** the fetch is refused naming that member

#### Scenario: a present member with other bytes stops the fetch before a transfer
- **Key:** `model-provisioning:unpack:a-present-member-with-other-bytes-stops-the-fetch`
- **Layers:** unit
- **WHEN** a member's destination holds a file that does not hash to its digest
- **THEN** the fetch stops before any transfer, naming the file, and leaves it where it is

#### Scenario: a member resolves only when its digest verifies
- **Key:** `model-provisioning:unpack:a-member-resolves-only-when-its-digest-verifies`
- **Layers:** unit
- **WHEN** a member's destination is resolved, and then its file is changed
- **THEN** the first resolves to its path, and the second is refused by the digest check

### Requirement: The placement models are one manifest, fetched by setup

The repository SHALL keep the models that propose a placement's pairs in `config/placement.json`: the pose detector,
the pose estimator and the segmenter's archive, each at an immutable revision with its digest and size, and the
archive's encoder and decoder as its members. `make setup` SHALL fetch it and `make drift` SHALL re-derive it. The
pose detector SHALL be the file `config/models.json` already pins for the pod, byte for byte. CI SHALL declare these
models absent by `ISEKAI_PLACEMENT=absent`, a check that reads them SHALL skip under that declaration alone, and
anywhere else SHALL fail naming the fetch.

The tagger's vocabulary is the precedent: one manifest for one question, fetched by setup, and the gate never fetches.

#### Scenario: every source is pinned and every entry digested
- **Key:** `model-provisioning:placement:every-source-is-pinned-and-every-entry-digested`
- **Layers:** unit
- **WHEN** the placement manifest is read
- **THEN** each source addresses a 40-hex revision, each entry has a 64-hex digest and a size, and each member has both

#### Scenario: the detector is the pod's pin
- **Key:** `model-provisioning:placement:the-detector-is-the-pods-pin`
- **Layers:** unit
- **WHEN** the placement manifest's detector and the render manifest's `yolox_l.onnx` are compared
- **THEN** their digests, sizes and primary sources are equal

#### Scenario: the archive declares its encoder and decoder
- **Key:** `model-provisioning:placement:the-archive-declares-its-encoder-and-decoder`
- **Layers:** unit
- **WHEN** the segmenter's entry is read
- **THEN** its members land at `sam2/encoder.onnx` and `sam2/decoder.onnx`, inside the models directory

#### Scenario: a check that reads the models skips only under the declaration
- **Key:** `model-provisioning:placement:a-check-that-reads-the-models-skips-only-under-the-declaration`
- **Layers:** unit
- **WHEN** a model file is absent, with `ISEKAI_PLACEMENT=absent` and then without it
- **THEN** the first skips and the second fails naming the fetch

#### Scenario: setup and drift carry the manifest
- **Key:** `model-provisioning:placement:setup-and-drift-carry-the-manifest`
- **Layers:** unit
- **WHEN** the Makefile is read
- **THEN** `setup` fetches `config/placement.json`, `drift` runs its deriver, and `gate` names neither
