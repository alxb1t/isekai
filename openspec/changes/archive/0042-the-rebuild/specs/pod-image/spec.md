## MODIFIED Requirements

### Requirement: The image is built only on request, from inputs pinned by digest and a locked environment

The system SHALL build the image only on a manual request naming a tag other than the released one, and
SHALL report the digest the build produced. The image's base and its build tool SHALL be named by digest,
and its Python environment SHALL be installed from a lock that carries every package's hash, with no
resolution at build time. The tools that build its source-only packages SHALL be checked by hash.

A build on every merge made a new image under the same name each time, and the build was not reproducible,
so the name meant nothing fixed. Building on request means every image that exists was asked for, and its
digest is known. The lock is what makes two builds of one commit install the same packages, and a build tool
fetched by version alone runs code the lock never checked.

#### Scenario: a merge builds nothing
- **Key:** `pod-image:build:only-a-request-builds`
- **Layers:** unit
- **WHEN** the image workflow's triggers are read
- **THEN** a manual request is the only one
- **AND** the build reports its digest

#### Scenario: the base and the build tool are named by digest
- **Key:** `pod-image:build:inputs-are-named-by-digest`
- **Layers:** unit
- **WHEN** the image's build file is read
- **THEN** every image it builds from or copies from carries a digest

#### Scenario: the environment is installed from the lock
- **Key:** `pod-image:build:the-environment-is-locked`
- **Layers:** unit
- **WHEN** the image's build file is read
- **THEN** its Python environment is installed from the committed lock, refusing a lock that is out of date
- **AND** no requirements file is resolved at build time

#### Scenario: the build tools are checked by hash
- **Key:** `pod-image:build:the-build-tools-are-hashed`
- **Layers:** unit
- **WHEN** the image project's build constraints are read
- **THEN** every build tool is named with its version and at least one hash

### Requirement: Everything ComfyUI writes lives in the pod's memory

The pod SHALL start ComfyUI with its input, output, temp and user directories, and the directory its temporary
files go to, in the pod's memory-backed filesystem. It SHALL hold instead of starting ComfyUI when that filesystem is
not a tmpfs, when its free space cannot be read, or when it has less than 1 GB free.

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

### Requirement: A pod sends no usage report its libraries can be told not to send

The image SHALL carry the telemetry and update-check switches of the libraries it runs, turned off, so every pod
runs with them off. The pod-creation script SHALL NOT set them a second time.

The pod renders a person's likeness; nothing on it needs to report anything to anyone. A switch declared in the image
holds for every pod made from it.

#### Scenario: the pod is created with telemetry off
- **Key:** `pod-image:telemetry:the-switches-are-off`
- **Layers:** unit
- **WHEN** the image's build file is read
- **THEN** its environment turns off onnxruntime's and the Hugging Face hub's telemetry and albumentations' update
  check, and sets `DO_NOT_TRACK`
- **AND** the pod-creation script sets none of them
