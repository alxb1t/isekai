## MODIFIED Requirements

### Requirement: A provisioning failure leaves the pod reachable

When provisioning aborts, the pod SHALL stay up with its SSH daemon running rather than terminating.
The abort policy leaves a mismatched file on disk for a human to inspect, and that is only true if
the human can get in: a container whose entrypoint exits takes its daemon with it and dies again on
every subsequent boot, within seconds of start.

That hold SHALL cover preparing the models namespace as well as fetching into it. Preparing the
volume is provisioning by any reading a human would give the word, and a failure there — an
unwritable volume, a link onto a path that could not be cleared — terminates the entrypoint exactly
as a fetch failure used to.

The hold SHALL be bounded rather than indefinite, SHALL end in the pod stopping itself, and the failure SHALL be
legible from outside the container's log. A pod holding open reports as running and healthy while it bills, so an
unattended failure that looks like success is the one that outlasts the session's spending ceiling; the bound
SHALL be shorter than that ceiling allows. A hold that ended in its process exiting would boot again if the
container restarted, and hold again, so it would never end.

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
- **THEN** the hold ends within a stated window shorter than the session's spending ceiling allows, by
  stopping the pod, and a marker recording the failure is written where the failure itself cannot have
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
