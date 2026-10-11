## MODIFIED Requirements

### Requirement: Everything ComfyUI writes lives in the pod's memory

The pod SHALL start ComfyUI with its input, output, temp and user directories, and the directory its temporary
files go to, in the pod's memory-backed filesystem. It SHALL hold instead of starting ComfyUI when that filesystem is
not a tmpfs, when its type or its free space cannot be read, or when it has less than 1 GB free. It SHALL print
whether the container can swap, and SHALL not hold for it.

The container disk outlives a render on a disk nobody can wipe. Memory dies with the pod. Memory the host swaps out
reaches its disk, and the host is the operator's boundary, so the pod reports swap rather than holding for what it
cannot change ([D35](../../../docs/decisions.md#d35--the-pods-operator-is-a-trust-boundary-accepted-knowingly)).

#### Scenario: ComfyUI writes to memory
- **Key:** `pod-image:memory:comfyui-writes-to-memory`
- **Layers:** unit
- **WHEN** the pod starts
- **THEN** ComfyUI starts with its input, output, temp and user directories under `/dev/shm`
- **AND** those directories exist before it starts

#### Scenario: too little memory holds the pod
- **Key:** `pod-image:memory:too-little-memory-holds`
- **Layers:** unit
- **WHEN** the pod's memory-backed filesystem has less than 1 GB free
- **THEN** the pod prints why and holds instead of starting ComfyUI

#### Scenario: an upload is spooled to memory
- **Key:** `pod-image:memory:uploads-spool-to-memory`
- **Layers:** unit
- **WHEN** the pod starts
- **THEN** ComfyUI starts with its temporary-file directory under `/dev/shm`
- **AND** that directory exists before it starts

#### Scenario: a /dev/shm that is not memory holds the pod
- **Key:** `pod-image:memory:a-disk-backed-shm-holds`
- **Layers:** unit
- **WHEN** `/dev/shm` is not a tmpfs
- **THEN** the pod prints what it is and holds instead of starting ComfyUI

#### Scenario: an unreadable free figure holds the pod
- **Key:** `pod-image:memory:an-unread-figure-holds`
- **Layers:** unit
- **WHEN** `/dev/shm`'s free space cannot be read
- **THEN** the pod prints that it could not read it and holds instead of starting ComfyUI

#### Scenario: an unreadable filesystem type holds the pod
- **Key:** `pod-image:memory:an-unread-type-holds`
- **Layers:** unit
- **WHEN** `/dev/shm`'s filesystem type cannot be read
- **THEN** the pod prints that it could not read the type and holds instead of starting ComfyUI

#### Scenario: swap is reported, never held for
- **Key:** `pod-image:memory:swap-is-reported`
- **Layers:** unit
- **WHEN** the pod starts
- **THEN** it prints whether the container can swap
- **AND** it starts ComfyUI either way

### Requirement: A boot prints when each step begins

The system SHALL print the UTC time at which each step of the pod's start-up begins.

Nobody knows what a boot's minutes are spent on, so every cut to it would be a guess. A timestamp per step,
read from the pod log, turns the guess into a measurement at no cost. The session's own lines carry their time too.

#### Scenario: each start-up step is timestamped
- **Key:** `pod-image:boot:each-step-is-timestamped`
- **Layers:** unit
- **WHEN** the pod starts
- **THEN** each of its steps prints a UTC time before it begins

### Requirement: No render carries metadata

The pod SHALL start ComfyUI so that no image it saves carries the prompt or any other text metadata.

The saved image travels to the operator's machine and may be shared. The prompt holds the approved sheet's tags.

#### Scenario: ComfyUI writes no metadata
- **Key:** `pod-image:render-metadata:none-is-written`
- **Layers:** unit
- **WHEN** the pod starts
- **THEN** ComfyUI starts with its metadata turned off
