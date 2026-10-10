## MODIFIED Requirements

### Requirement: Everything ComfyUI writes lives in the pod's memory

The pod SHALL start ComfyUI with its input, output, temp and user directories, and the directory its temporary
files go to, in the pod's memory-backed filesystem. It SHALL hold instead of starting ComfyUI when that filesystem is
not a tmpfs, when its type or its free space cannot be read, or when it has less than 1 GB free. It SHALL print
whether the container can swap, and SHALL not hold for it.

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

#### Scenario: an upload is spooled to memory
- **Key:** `pod-image:memory:uploads-spool-to-memory`
- **Layers:** unit
- **WHEN** the pod's start-up script is read
- **THEN** ComfyUI starts with its temporary-file directory under `/dev/shm`
- **AND** that directory exists before it starts

#### Scenario: a /dev/shm that is not memory holds the pod
- **Key:** `pod-image:memory:a-disk-backed-shm-holds`
- **Layers:** unit
- **WHEN** `/dev/shm` is not a tmpfs
- **THEN** the start-up script prints what it is and holds instead of starting ComfyUI

#### Scenario: an unreadable free figure holds the pod
- **Key:** `pod-image:memory:an-unread-figure-holds`
- **Layers:** unit
- **WHEN** `/dev/shm`'s free space cannot be read
- **THEN** the start-up script prints that it could not read it and holds instead of starting ComfyUI

#### Scenario: an unreadable filesystem type holds the pod
- **Key:** `pod-image:memory:an-unread-type-holds`
- **Layers:** unit
- **WHEN** `/dev/shm`'s filesystem type cannot be read
- **THEN** the start-up script prints that it could not read the type and holds instead of starting ComfyUI

#### Scenario: swap is reported, never held for
- **Key:** `pod-image:memory:swap-is-reported`
- **Layers:** unit
- **WHEN** the container can swap, and when it cannot
- **THEN** the start-up script prints which, and starts ComfyUI either way
