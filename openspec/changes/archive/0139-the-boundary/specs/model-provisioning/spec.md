## MODIFIED Requirements

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

#### Scenario: the published digest is read from the source's answer
- **Key:** `model-provisioning:preflight:the-published-digest-is-read-from-the-sources-answer`
- **Layers:** unit
- **WHEN** a source answers the check with a redirect that carries the digest of the file it would serve
- **THEN** that digest is the one compared with the manifest's
- **AND** a source that publishes none, or one that is not a digest, is verified after the transfer instead
