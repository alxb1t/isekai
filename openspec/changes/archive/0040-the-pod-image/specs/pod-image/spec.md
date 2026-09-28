## ADDED Requirements

### Requirement: A pod makes its own host key and prints its fingerprint

The image SHALL carry no SSH host key. Each pod SHALL make an Ed25519 host key at boot, SHALL serve SSH with that key
alone, and SHALL print its fingerprint as one line of the form `isekai host key: SHA256:<fingerprint>`.

A key baked into a public image is held by anyone who pulls it, so every pod presents the same identity and no check
against it proves anything. A key made at boot is the pod's own, and the printed line is what a client reads to
check it.

#### Scenario: the image carries no host key
- **Key:** `pod-image:host-key:the-image-carries-none`
- **Layers:** unit
- **WHEN** the image's build file is read
- **THEN** the step that installs the SSH server deletes the host keys it made, in the same step

#### Scenario: each boot makes and prints its own key
- **Key:** `pod-image:host-key:each-boot-makes-and-prints-one`
- **Layers:** unit
- **WHEN** the pod's start-up script is read
- **THEN** it makes an Ed25519 host key, starts the SSH server with that key alone, and prints its fingerprint
  line

### Requirement: Everything ComfyUI writes lives in the pod's memory

The pod SHALL start ComfyUI with its input, output, temp and user directories in the pod's memory-backed filesystem,
and SHALL hold instead of starting ComfyUI when that filesystem has less than 1 GB free.

The container disk outlives a render on a disk nobody can wipe. Memory dies with the pod.

#### Scenario: ComfyUI writes to memory
- **Key:** `pod-image:memory:comfyui-writes-to-memory`
- **Layers:** unit
- **WHEN** the pod's start-up script is read
- **THEN** ComfyUI starts with its input, output, temp and user directories under `/dev/shm`
- **AND** those directories exist before it starts

#### Scenario: too little memory holds the pod
- **Key:** `pod-image:memory:too-little-memory-holds`
- **Layers:** unit
- **WHEN** the pod's memory-backed filesystem has less than 1 GB free
- **THEN** the start-up script prints why and holds instead of starting ComfyUI

### Requirement: No render carries metadata

The pod SHALL start ComfyUI so that no image it saves carries the prompt or any other text metadata.

The saved image travels to the operator's machine and may be shared. The prompt holds the approved sheet's tags.

#### Scenario: ComfyUI writes no metadata
- **Key:** `pod-image:render-metadata:none-is-written`
- **Layers:** unit
- **WHEN** the pod's start-up script is read
- **THEN** ComfyUI starts with its metadata turned off
