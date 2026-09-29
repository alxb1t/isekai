## MODIFIED Requirements

### Requirement: A pod's host key is checked before anything is sent

The pod-creation script SHALL read the host-key fingerprint the pod printed to its log, SHALL scan the pod's host key
and compare them, and SHALL keep the key, for that pod alone, only when they match. On a mismatch, when no
fingerprint line appears within a fixed time, or when the pod's SSH answers no scan within a fixed time, it SHALL
refuse and tear the pod down. The render session SHALL tunnel to the pod only with the kept key.

A tunnel that trusts the first key it sees trusts whatever machine answers. The fingerprint the pod printed reaches
the client through the provider's authenticated API, not through the connection it vouches for.

#### Scenario: a matching key is kept for that pod alone
- **Key:** `pod-image:host-key:a-matching-key-is-kept`
- **Layers:** unit
- **WHEN** the scanned key's fingerprint matches the one the pod printed
- **THEN** the key is written to a known-hosts file of the pod's own
- **AND** the printed connection lines and the render session's tunnel name that file with strict checking

#### Scenario: a mismatch is refused
- **Key:** `pod-image:host-key:a-mismatch-is-refused`
- **Layers:** unit
- **WHEN** the scanned key's fingerprint differs from the one the pod printed
- **THEN** the pod-creation script refuses, naming the mismatch
- **AND** tears the pod down

#### Scenario: no fingerprint line is refused
- **Key:** `pod-image:host-key:no-fingerprint-is-refused`
- **Layers:** unit
- **WHEN** no fingerprint line appears in the pod's log within the fixed time
- **THEN** the pod-creation script refuses, naming where to read the log
- **AND** tears the pod down

#### Scenario: a scan no one answers is refused
- **Key:** `pod-image:host-key:a-scan-no-one-answers-is-refused`
- **Layers:** unit
- **WHEN** the pod printed its fingerprint, but its SSH answers no scan within the fixed time
- **THEN** the pod-creation script refuses, naming the unanswered scan
- **AND** tears the pod down
