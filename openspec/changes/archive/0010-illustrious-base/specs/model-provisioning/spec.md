## MODIFIED Requirements

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
