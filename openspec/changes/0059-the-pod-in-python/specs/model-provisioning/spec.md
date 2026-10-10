## MODIFIED Requirements

### Requirement: A transfer that fails advances to the next declared source

Provisioning SHALL try an entry's sources in the manifest's order and abort only when every one of them has
failed. A transfer that breaks off SHALL be tried again from the same source, three attempts in all, before that
source has failed; bytes that fail verification SHALL fail their source at once.

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
- **WHEN** a source's transfer breaks off a third time, or the bytes it served fail verification
- **THEN** provisioning moves on to the next source for that entry
- **AND** the run aborts only once every source for the entry has failed

#### Scenario: a broken transfer is tried again from the same source
- **Key:** `model-provisioning:source-fallback:a-broken-transfer-is-tried-again`
- **Layers:** unit
- **WHEN** a transfer breaks off before its source's third attempt
- **THEN** provisioning waits and transfers from the same source again
- **AND** the entry lands when a later attempt serves bytes that verify
