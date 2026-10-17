## MODIFIED Requirements

### Requirement: A transfer that fails advances to the next declared source

Provisioning SHALL try an entry's sources in the manifest's order and abort only when every one of them has
failed. It SHALL try a transfer that breaks off again from the same source, three attempts in all. A source has
failed when its third attempt breaks off, at once when it answers with a client error, or at once when the bytes it
served fail verification.

An alternate that is never reached buys no availability: a mirror that has gone away is the failure it exists for.
A dropped connection is transient, and an entry with one source has no alternate to fall to. A client error — a
file gone, a request refused — and bytes that do not verify would fail the same way again
([D21](../../../docs/decisions.md#d21--retries-follow-what-can-fail)).

```
source ──▶ transfer ── breaks off, attempts left ──▶ wait ──▶ transfer again
              │
              ├── breaks off a third time ─┐
              ├── answers a client error ──┤
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
- **WHEN** a source has failed
- **THEN** provisioning moves on to the next source for that entry
- **AND** the run aborts only once every source for the entry has failed

#### Scenario: a broken transfer is tried again from the same source
- **Key:** `model-provisioning:source-fallback:a-broken-transfer-is-tried-again`
- **Layers:** unit
- **WHEN** a transfer breaks off before its source's third attempt
- **THEN** provisioning waits and transfers from the same source again
- **AND** the entry lands when a later attempt serves bytes that verify

#### Scenario: a source that answers a client error is not tried again
- **Key:** `model-provisioning:source-fallback:a-refusing-source-is-not-tried-again`
- **Layers:** unit
- **WHEN** a source answers a transfer with a client error, as a 404
- **THEN** provisioning moves on to the next source without waiting
- **AND** that source is asked once

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
and healthy while it bills, so an unbounded hold outlasts the spending ceiling; a hold whose end did not stop the
pod would restart with the container and hold again. Its exit is what stops it: gpunit's boot stops the pod when its
command ends.

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
- **THEN** the hold ends by the entrypoint exiting, which stops the pod, within a stated window shorter than the
  session's spending ceiling allows
- **AND** a marker recording the failure is written where the failure cannot have made it unwritable
- **AND** the marker is not written onto the volume

#### Scenario: the pod refuses to provision onto anything but its network volume
- **Key:** `model-provisioning:reachability:provisioning-requires-the-network-volume`
- **Layers:** unit
- **WHEN** the pod is created without the network volume it expects, or the models namespace would be prepared
  somewhere that is not that volume
- **THEN** no session is opened unless the session's spec declares a window volume, by its size and its ceiling
- **AND** the entrypoint refuses before preparing the namespace if what it finds is not that volume
- **AND** the entrypoint is told which volume to expect, as `GPUNIT_VOLUME_ID`, rather than inferring it

#### Scenario: the window volume clears the capacity floor
- **Key:** `model-provisioning:reachability:the-window-volume-clears-the-floor`
- **Layers:** unit
- **WHEN** the session's spec is read
- **THEN** its window volume's size, in decimal bytes, is at least the entrypoint's capacity floor
