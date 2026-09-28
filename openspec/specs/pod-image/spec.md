# Capability: `pod-image`

## Purpose

The image a rented pod runs: what it is built from, how a build is asked for, and how a pod boots it — by
digest, never by a moving tag.

## Requirements

### Requirement: A pod boots only the image the repository pins by digest

The system SHALL boot a pod only from the image named by the digest the repository's image file declares,
and SHALL offer no way to boot another from the environment. It SHALL record the reference it booted beside
the pod's identifier, and SHALL remove that record when the pod is torn down.

A moving tag is not a pin: every build under the same name was a different image, and nothing recorded which
one a render ran on. A digest names one image forever, and the file holding it is the one place it is
declared. The boot record is what lets a render say which image it ran on.

#### Scenario: the pod is created from the pinned digest
- **Key:** `pod-image:boot:the-pinned-digest-is-booted`
- **Layers:** unit
- **WHEN** the pod-creation script builds its request
- **THEN** the image it names is the image file's reference with its digest
- **AND** no moving tag appears in the request

#### Scenario: nothing in the environment overrides the image
- **Key:** `pod-image:boot:no-override`
- **Layers:** unit
- **WHEN** the pod-creation script is read
- **THEN** no environment variable changes the image it boots

#### Scenario: the booted reference is recorded and removed with the pod
- **Key:** `pod-image:boot:the-booted-image-is-recorded`
- **Layers:** unit
- **WHEN** a pod is created and later torn down
- **THEN** the reference it booted is written beside the pod's identifier on creation
- **AND** it is removed when the teardown succeeds

### Requirement: The image is built only on request, from inputs pinned by digest and a locked environment

The system SHALL build the image only on a manual request naming a tag other than the released one, and
SHALL report the digest the build produced. The image's base and its build tool SHALL be named by digest,
and its Python environment SHALL be installed from a lock that carries every package's hash, with no
resolution at build time.

A build on every merge made a new image under the same name each time, and the build was not reproducible,
so the name meant nothing fixed. Building on request means every image that exists was asked for, and its
digest is known. The lock is what makes two builds of one commit install the same packages.

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

### Requirement: A boot prints when each step begins

The system SHALL print the UTC time at which each step of the pod's start-up begins, and the pod-creation
script SHALL print when the pod was created and when its SSH port was mapped.

Nobody knows what a boot's minutes are spent on, so every cut to it would be a guess. A timestamp per step,
read from the pod log, turns the guess into a measurement at no cost.

#### Scenario: each start-up step is timestamped
- **Key:** `pod-image:boot:each-step-is-timestamped`
- **Layers:** unit
- **WHEN** the pod's start-up script is read
- **THEN** each of its steps prints a UTC time before it begins

### Requirement: A render session always tears its pod down

The system SHALL offer one script that runs a whole render session — creates the pod, opens the tunnel, waits a
bounded time for the endpoint to answer, renders each named flow, and tears the pod down — and that script SHALL
tear the pod down and close the tunnel on every way out, including an error and an interrupt.

A pod left running is money and a personal photograph on someone else's machine. The steps were run by hand, and a
session that stopped between `up.sh` and `down.sh` left the pod billing; an agent running them can stop at any step.
A trap on exit is the one mechanism that holds whichever step fails.

#### Scenario: every exit tears the pod down
- **Key:** `pod-image:session:every-exit-tears-down`
- **Layers:** unit
- **WHEN** the render-session script is read
- **THEN** a trap on exit runs the teardown script and closes the tunnel
- **AND** the trap is set before the pod is created

#### Scenario: rendering waits for the endpoint, within a bound
- **Key:** `pod-image:session:the-endpoint-is-awaited`
- **Layers:** unit
- **WHEN** the render-session script is read
- **THEN** it asks the endpoint for its report through the tunnel before any render
- **AND** it gives up after a stated bound, which exits through the trap

### Requirement: A render session's guards end with it

The system SHALL stop a render session's ceiling watchdog within seconds of the session's end, however it ends, and
SHALL keep the host keys the session's tunnel accepts in a file of the session's own, removed at teardown.

A watchdog that outlives a killed session later signals whatever process holds the session's id. A key kept in the
operator's own known-hosts file refuses a later pod on the same address, and the session bills its wait for nothing.

#### Scenario: the watchdog ends with its session
- **Key:** `pod-image:session:the-watchdog-ends-with-its-session`
- **Layers:** unit
- **WHEN** the render script is read
- **THEN** its watchdog checks at short intervals that the session still runs, and exits once it does not
- **AND** it signals the session only after that check

#### Scenario: a session's host keys are its own
- **Key:** `pod-image:session:host-keys-are-the-sessions-own`
- **Layers:** unit
- **WHEN** the render script opens the tunnel
- **THEN** it names a known-hosts file the session created
- **AND** the teardown removes that file

### Requirement: A render session reaches its tunnel without a proxy

The render script SHALL reach the endpoint through its tunnel directly, ignoring any proxy the environment names.

The script's own checks call the loopback address the tunnel listens on. A proxy exported for some other tool would
receive them, the endpoint would never seem to answer, and the session would bill its wait and refuse.

#### Scenario: the script's checks ignore an exported proxy
- **Key:** `pod-image:session:the-tunnel-is-reached-directly`
- **Layers:** unit
- **WHEN** the render script is read
- **THEN** every request it makes to the endpoint's address is told to use no proxy

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
