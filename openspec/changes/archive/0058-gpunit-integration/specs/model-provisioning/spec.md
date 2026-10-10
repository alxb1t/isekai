## MODIFIED Requirements

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
- **THEN** no session is opened unless the session's spec names the volume
- **AND** the entrypoint refuses before preparing the namespace if what it finds is not that volume
- **AND** the entrypoint is told which volume to expect, as `GPUNIT_VOLUME_ID`, rather than inferring it
