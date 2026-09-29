# Capability: `pod-image`

## Purpose

The image a rented pod runs: what it is built from, how a build is asked for, and how a pod boots it — by
digest, never by a moving tag.

## Requirements

### Requirement: A pod boots only the image the repository pins by digest

The system SHALL boot a pod only from the image named by the digest the repository's image file declares,
and SHALL offer no way to boot another from the environment. It SHALL record the reference it booted beside
the pod's identifier, and SHALL remove that record when the pod is torn down.

A moving tag names a new image with every build, so no record can say which one a render ran on
([D28](../../../docs/decisions.md#d28--the-image-carries-code-the-volume-carries-weights)). A digest names one
image forever, the image file is the one place it is declared, and the boot record says which image a render ran on.

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
resolution at build time. The tools that build its source-only packages SHALL be checked by hash.

A build on request means every image that exists was asked for, and its digest is known
([D28](../../../docs/decisions.md#d28--the-image-carries-code-the-volume-carries-weights)). The lock makes two
builds of one commit install the same packages; a build tool fetched by version alone runs code the lock never
checked.

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

```
up.sh ──▶ tunnel ──▶ await endpoint ──▶ render each flow ──▶ exit
  ▲                                                            │
  └─ trap set first: any exit, error or interrupt ─▶ down.sh ◀─┘
```

A pod left running is money and a personal photograph on someone else's machine. A session can stop at any step,
and a trap on exit holds whichever step fails
([D36](../../../docs/decisions.md#d36--a-render-session-is-infrarendersh)).

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
SHALL tunnel only with the host key checked against the pod's printed fingerprint, kept in a file of the pod's own
and removed at teardown.

A watchdog that outlives a killed session later signals whatever process holds the session's id. A key kept in the
operator's own known-hosts file refuses a later pod on the same address, and an unchecked key trusts whatever
answers.

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
- **THEN** it names the pod's checked known-hosts file, with strict host-key checking
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

### Requirement: No render carries metadata

The pod SHALL start ComfyUI so that no image it saves carries the prompt or any other text metadata.

The saved image travels to the operator's machine and may be shared. The prompt holds the approved sheet's tags.

#### Scenario: ComfyUI writes no metadata
- **Key:** `pod-image:render-metadata:none-is-written`
- **Layers:** unit
- **WHEN** the pod's start-up script is read
- **THEN** ComfyUI starts with its metadata turned off

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

### Requirement: A pod runs beside its models volume

The pod-creation script SHALL read the models volume before creating a pod, and SHALL refuse a data centre other
than the volume's, or a volume smaller than the render models' manifest.

A volume cannot move between data centres, and a pod elsewhere boots without its models. A volume too small for the
manifest fails its download after the pod is already billing.

#### Scenario: another data centre is refused
- **Key:** `pod-image:volume:another-data-centre-is-refused`
- **Layers:** unit
- **WHEN** the configured data centre differs from the volume's
- **THEN** the pod-creation script refuses before any pod is created, naming both

#### Scenario: a volume too small is refused
- **Key:** `pod-image:volume:a-volume-too-small-is-refused`
- **Layers:** unit
- **WHEN** the volume is smaller than the sum of the manifest's file sizes
- **THEN** the pod-creation script refuses before any pod is created, naming both sizes

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

### Requirement: A pod is placed only on a host that can render

The pod-creation script SHALL ask the provider to place the pod only on a host with at least the stated host memory
and a CUDA version the image's PyTorch build can run. It SHALL skip a listed card whose memory is below the stated
floor, naming it, and SHALL refuse a listed card the provider does not know.

A host the render cannot use still boots, pulls and bills before anything fails. A misspelt first choice that is
skipped in silence places the pod on a different card than the operator chose.

#### Scenario: the create asks for host memory and a CUDA version
- **Key:** `pod-image:placement:the-create-carries-the-floors`
- **Layers:** unit
- **WHEN** the pod-creation script builds its request
- **THEN** the request names a floor for the host's memory and a floor for the host's CUDA version

#### Scenario: a card short of memory is skipped
- **Key:** `pod-image:placement:a-card-short-of-memory-is-skipped`
- **Layers:** unit
- **WHEN** the provider's catalogue gives a listed card less memory than the floor
- **THEN** the pod-creation script names the card, skips it, and tries the next

#### Scenario: an unknown card is refused
- **Key:** `pod-image:placement:an-unknown-card-is-refused`
- **Layers:** unit
- **WHEN** the provider's catalogue does not know a listed card
- **THEN** the pod-creation script refuses before creating anything, naming the card

### Requirement: No `isekai` pod goes unseen

The pod-creation script SHALL refuse while a pod is recorded, or while the provider lists any pod this project
made. The teardown script SHALL leave no pod this project made: the recorded one, then every other listed. A create
whose outcome is unknown SHALL name the teardown script. The listing SHALL name only pods from this project's image,
and SHALL fail, never end in silence or loop, when a page repeats its cursor or a live pod this project named
carries no image. A render session SHALL sweep without a record only after its own create was lost.

A pod no file records bills with nothing watching it. A second creation would overwrite the record and orphan the
first pod, and a lost create leaves one only the provider's console can find. A listing that misses a pod, or never
ends, leaves it billing; one that over-matches deletes a pod that is not this project's
([D36](../../../docs/decisions.md#d36--a-render-session-is-infrarendersh)).

#### Scenario: a recorded pod refuses a creation
- **Key:** `pod-image:reconcile:a-recorded-pod-refuses`
- **Layers:** unit
- **WHEN** a pod is recorded and the pod-creation script runs
- **THEN** it refuses before any request to the provider, naming the record and the teardown script

#### Scenario: a listed pod refuses a creation
- **Key:** `pod-image:reconcile:a-listed-pod-refuses`
- **Layers:** unit
- **WHEN** the provider lists a pod this project made, on any page
- **THEN** the pod-creation script refuses before creating anything, naming the pod and the teardown script

#### Scenario: the teardown leaves no pod
- **Key:** `pod-image:reconcile:the-teardown-leaves-none`
- **Layers:** unit
- **WHEN** the teardown script runs, with a recorded pod or without one
- **THEN** it removes the recorded pod and every other listed pod this project made
- **AND** it exits non-zero when any removal, or the listing, fails

#### Scenario: a lost create names the teardown
- **Key:** `pod-image:reconcile:a-lost-create-names-the-teardown`
- **Layers:** unit
- **WHEN** a create's outcome is unknown
- **THEN** the pod-creation script says a pod may exist and names the teardown script

#### Scenario: a render session refuses a recorded pod
- **Key:** `pod-image:reconcile:a-session-refuses-a-recorded-pod`
- **Layers:** unit
- **WHEN** a pod is recorded and the render-session script runs
- **THEN** it refuses before its trap is set
- **AND** its teardown does not remove that pod

#### Scenario: a repeated cursor fails the listing
- **Key:** `pod-image:reconcile:a-repeated-cursor-fails`
- **Layers:** unit
- **WHEN** the provider answers a page with the cursor it was asked for, and more to come
- **THEN** the listing fails rather than asking again

#### Scenario: a cycle of cursors fails the listing
- **Key:** `pod-image:reconcile:a-cursor-cycle-fails`
- **Layers:** unit
- **WHEN** the provider answers pages whose cursors cycle, each with more to come
- **THEN** the listing fails at its page cap, naming it, rather than asking without end

#### Scenario: only this project's image is listed
- **Key:** `pod-image:reconcile:only-this-image-is-listed`
- **Layers:** unit
- **WHEN** a pod named for this project runs an image whose name only begins with this project's
- **THEN** the listing leaves it out

#### Scenario: a pod with no image fails the listing
- **Key:** `pod-image:reconcile:a-pod-with-no-image-fails`
- **Layers:** unit
- **WHEN** a pod named for this project, and not terminated, carries no image
- **THEN** the listing fails rather than leaving it out

#### Scenario: a terminated pod is not listed
- **Key:** `pod-image:reconcile:a-terminated-pod-is-not-listed`
- **Layers:** unit
- **WHEN** a pod named for this project is terminated, with an image or with none
- **THEN** the listing leaves it out and does not fail

#### Scenario: a refused session leaves a listed pod
- **Key:** `pod-image:reconcile:a-refused-session-leaves-a-listed-pod`
- **Layers:** unit
- **WHEN** a render session holds no record and its pod-creation script refuses, beside a listed pod
- **THEN** the session's teardown does not run the teardown script
- **AND** after a create whose outcome is unknown, it does

#### Scenario: an interrupt sweeps only once a create began
- **Key:** `pod-image:reconcile:an-interrupt-sweeps-only-once-a-create-began`
- **Layers:** unit
- **WHEN** a render session holding no record is interrupted while its pod-creation script runs, beside a listed pod
- **THEN** the session's teardown does not run the teardown script if no create had begun
- **AND** it does once a create had begun and no record was written

#### Scenario: an unrecorded create is swept
- **Key:** `pod-image:reconcile:an-unrecorded-create-is-swept`
- **Layers:** unit
- **WHEN** a render session's pod-creation script began a create and ended before its record, by a failed write
  or a kill
- **THEN** the session's teardown runs the teardown script

### Requirement: A pod stops itself at its ceiling

The pod SHALL stop itself through the provider's API, with the key the provider gives it, a stated time after it
starts, whatever happens to the machine that created it. A boot that ends, however it ends, SHALL end in the stop. A
stop that fails SHALL be retried, at an interval that grows to a stated bound, until it succeeds. ComfyUI SHALL start
without that key in its environment.

A watchdog on the laptop dies with the laptop, and a pod left running bills with a photograph in its memory. A
start-up script whose process exits restarts the container, and the restart arms a fresh ceiling, so a boot that
fails before its ceiling would never be stopped; so would a pod whose stop gave up. ComfyUI needs no key, and code it
runs can print its environment into a log.

#### Scenario: the pod arms its stop first
- **Key:** `pod-image:stop:armed-at-boot`
- **Layers:** unit
- **WHEN** the pod's start-up script is read
- **THEN** its first step starts, in the background, a timer that runs the stop at the pod's ceiling
- **AND** that ceiling is no longer than the session's

#### Scenario: every hold ends in the stop
- **Key:** `pod-image:stop:a-hold-ends-in-the-stop`
- **Layers:** unit
- **WHEN** the start-up script holds the pod, for any reason
- **THEN** once its window has passed it runs the stop, rather than letting its process exit

#### Scenario: a boot that ends stops the pod
- **Key:** `pod-image:stop:a-boot-that-ends-stops-the-pod`
- **Layers:** unit
- **WHEN** ComfyUI exits, with success or not, or a step of the start-up script fails before it starts
- **THEN** the start-up script runs the stop, with the provider's key, rather than letting its process exit

#### Scenario: a failed stop is retried until it succeeds
- **Key:** `pod-image:stop:a-failed-stop-is-retried`
- **Layers:** unit
- **WHEN** the provider does not answer the stop with success
- **THEN** the stop script tries again, at an interval that grows to a stated bound, until the provider does

#### Scenario: ComfyUI starts without the key
- **Key:** `pod-image:stop:comfyui-holds-no-key`
- **Layers:** unit
- **WHEN** the pod's start-up script starts ComfyUI
- **THEN** the provider's key is no longer in the start-up script's environment
