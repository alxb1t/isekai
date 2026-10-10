## MODIFIED Requirements

### Requirement: A pod boots only the image the repository pins by digest

The system SHALL boot a pod only from the image `gpunit.toml` names by digest, SHALL offer no way to boot another
from the environment, and `config/image.json` SHALL name the same digest. A render SHALL record the image its
session booted.

A moving tag names a new image with every build, so no record can say which one a render ran on
([D28](../../../docs/decisions.md#d28--the-image-carries-code-the-volume-carries-weights)). A digest names one
image forever, `gpunit.toml` is the one place a session reads it from, and the build record says what it was built
from.

#### Scenario: the pod is created from the pinned digest
- **Key:** `pod-image:boot:the-pinned-digest-is-booted`
- **Layers:** unit
- **WHEN** `gpunit.toml` is read
- **THEN** its `image` is a reference with a digest, equal to the reference and digest `config/image.json` records
- **AND** no moving tag appears in it

#### Scenario: nothing in the environment overrides the image
- **Key:** `pod-image:boot:no-override`
- **Layers:** unit
- **WHEN** `isekai render` opens a session
- **THEN** it names `gpunit.toml`, and no environment variable or argument changes the image it boots

#### Scenario: the booted reference is recorded and removed with the pod
- **Key:** `pod-image:boot:the-booted-image-is-recorded`
- **Layers:** unit
- **WHEN** `isekai render` renders inside a session
- **THEN** each render records the image the session names

### Requirement: The image is built only on request, from inputs pinned by digest and a locked environment

The system SHALL build the image only on a manual request naming a tag other than the released one, and
SHALL report the digest the build produced and the SHA-256 of every file the build copies. The image's base and
its build tool SHALL be named by digest, a file it adds from a URL SHALL carry a checksum, and its Python
environment SHALL be installed from a lock that carries every package's hash, with no resolution at build time.
The tools that build its source-only packages SHALL be checked by hash. `config/image.json` SHALL record the
SHA-256 of the build file and of every file it copies, and SHALL agree with the tree.

A build on request means every image that exists was asked for, and its digest is known
([D28](../../../docs/decisions.md#d28--the-image-carries-code-the-volume-carries-weights)). The lock makes two
builds of one commit install the same packages; a build tool fetched by version alone runs code the lock never
checked. A record of the copied files is what says an image is no longer built from this tree.

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
- **AND** every file it adds from a URL carries a checksum

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

#### Scenario: the build record agrees with the tree
- **Key:** `pod-image:build:the-record-matches-the-tree`
- **Layers:** unit
- **WHEN** `config/image.json` is read beside the build file
- **THEN** it holds a SHA-256 for the build file and for every file the build file copies, each equal to the tree's

#### Scenario: the workflow prints the record
- **Key:** `pod-image:build:the-workflow-prints-the-record`
- **Layers:** unit
- **WHEN** the image workflow is read
- **THEN** it writes the SHA-256 of the build file and of every file it copies to its summary, from its own checkout

### Requirement: A boot prints when each step begins

The system SHALL print the UTC time at which each step of the pod's start-up begins.

Nobody knows what a boot's minutes are spent on, so every cut to it would be a guess. A timestamp per step,
read from the pod log, turns the guess into a measurement at no cost. The session's own lines carry their time too.

#### Scenario: each start-up step is timestamped
- **Key:** `pod-image:boot:each-step-is-timestamped`
- **Layers:** unit
- **WHEN** the pod's start-up script is read
- **THEN** each of its steps prints a UTC time before it begins

### Requirement: A render session always tears its pod down

The system SHALL offer one verb, `isekai render`, that runs a whole render session: it assembles every prompt
before anything is rented, opens a session through gpunit, waits a bounded time for the endpoint to answer,
renders each named flow, and closes the session. The session SHALL be closed on every way out, including an
error and an interrupt.

```
assemble ──▶ gpunit.session() ──▶ await endpoint ──▶ render each flow ──▶ block ends
                     ▲                                                        │
                     └──── any exit, error or signal: the session closes ◀────┘
```

A pod left running is money and a personal photograph on someone else's machine. A session can stop at any step,
and the block that holds it closes on every one
([D36](../../../docs/decisions.md#d36--a-render-session-is-isekai-render)).

#### Scenario: every exit tears the pod down
- **Key:** `pod-image:session:every-exit-tears-down`
- **Layers:** unit
- **WHEN** a flow raises, the endpoint never answers, or `SIGTERM` arrives inside the session
- **THEN** the session's block is left, and the session closes
- **AND** nothing is rented before every prompt is assembled

#### Scenario: rendering waits for the endpoint, within a bound
- **Key:** `pod-image:session:the-endpoint-is-awaited`
- **Layers:** unit
- **WHEN** the session is open
- **THEN** the endpoint's report is asked for through the forwarded port before any render
- **AND** after a stated bound with no answer, `isekai render` refuses and the session closes

### Requirement: A render session reaches its tunnel without a proxy

`isekai render` SHALL reach the endpoint through its tunnel directly, ignoring any proxy the environment names.

The verb's own checks call the loopback address the tunnel listens on. A proxy exported for some other tool would
receive them, the endpoint would never seem to answer, and the session would bill its wait and refuse.

#### Scenario: the script's checks ignore an exported proxy
- **Key:** `pod-image:session:the-tunnel-is-reached-directly`
- **Layers:** unit
- **WHEN** `isekai render` asks the endpoint for its report with `http_proxy` exported
- **THEN** the request goes to the loopback address, through no proxy

### Requirement: A pod makes its own host key and prints its fingerprint

The image SHALL carry no SSH host key, and SHALL boot through gpunit's boot script, added at a pinned tag with its
checksum, which makes each pod's host key and prints its fingerprint for the session to check.

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
- **WHEN** the image's build file is read
- **THEN** its entrypoint is gpunit's boot script followed by `--`, added from the tag `pyproject.toml` pins gpunit at,
  with a checksum

### Requirement: A pod sends no usage report its libraries can be told not to send

The image SHALL carry the telemetry and update-check switches of the libraries it runs, turned off, so every pod
runs with them off. The session's spec SHALL NOT set them a second time.

The pod renders a person's likeness; nothing on it needs to report anything to anyone. A switch declared in the image
holds for every pod made from it.

#### Scenario: the pod is created with telemetry off
- **Key:** `pod-image:telemetry:the-switches-are-off`
- **Layers:** unit
- **WHEN** the image's build file is read
- **THEN** its environment turns off onnxruntime's and the Hugging Face hub's telemetry and albumentations' update
  check, and sets `DO_NOT_TRACK`
- **AND** `gpunit.toml`'s `[env]` sets none of them

## ADDED Requirements

### Requirement: A render session's watchdog ends with it

The system SHALL bound a render session with a ceiling watchdog that starts before the session opens, ends the
session by `SIGTERM` at its ceiling, and stops within seconds of the session's end, however it ends.

A watchdog that outlives a killed session later signals whatever process holds the session's id. One started after
the pod exists would count from too late, and the pod's own stop would come first.

#### Scenario: the watchdog ends with its session
- **Key:** `pod-image:session:the-watchdog-ends-with-its-session`
- **Layers:** unit
- **WHEN** a render session ends, however it ends
- **THEN** its watchdog is cancelled and signals nothing

#### Scenario: the watchdog ends a session at its ceiling
- **Key:** `pod-image:session:the-watchdog-ends-the-session`
- **Layers:** unit
- **WHEN** the ceiling passes with the session still open
- **THEN** `isekai render` writes a refusal naming the ceiling to the batch's log
- **AND** the session closes, and it exits `143`

### Requirement: The session's spec asks for a host that can render

The session's spec SHALL ask for a card with at least the stated memory, a host with at least the stated memory, and
a CUDA version the image's PyTorch build can run.

A host the render cannot use still boots, pulls and bills before anything fails.

#### Scenario: the create asks for host memory and a CUDA version
- **Key:** `pod-image:placement:the-create-carries-the-floors`
- **Layers:** unit
- **WHEN** `gpunit.toml` is read
- **THEN** it names `vram_gb` and `ram_gb` of at least 24 and `cuda` of `12.8`

### Requirement: The pod stops itself through gpunit's boot at its ceiling

The pod SHALL stop itself through gpunit's boot script at the ceiling `gpunit.toml` names, no longer than the
session's 45 minutes, whatever happens to the machine that opened it. The start-up script SHALL end every boot that
does not serve by exiting, so the boot script stops the pod, and SHALL hand its process to ComfyUI, so ComfyUI's exit
is the end of the boot.

A watchdog on the laptop dies with the laptop, and a pod left running bills with a photograph in its memory. A boot
that held forever, or a ComfyUI left running after its script was told to stop, would bill with nothing watching.

#### Scenario: the pod arms its stop first
- **Key:** `pod-image:stop:armed-at-boot`
- **Layers:** unit
- **WHEN** `gpunit.toml` and the image's build file are read
- **THEN** the ceiling is no longer than 45 minutes, and the image's entrypoint is gpunit's boot script

#### Scenario: every hold ends in the stop
- **Key:** `pod-image:stop:a-hold-ends-in-the-stop`
- **Layers:** unit
- **WHEN** the start-up script holds the pod, for any reason
- **THEN** once its window has passed it exits non-zero, so the boot script stops the pod

#### Scenario: a boot that ends stops the pod
- **Key:** `pod-image:stop:a-boot-that-ends-stops-the-pod`
- **Layers:** unit
- **WHEN** the start-up script reaches ComfyUI, or a step before it fails
- **THEN** ComfyUI replaces the script's process, or the script exits non-zero

## REMOVED Requirements

### Requirement: A render session's guards end with it

**Reason**: gpunit keeps the session's checked host key in a file of its own and removes it at teardown (gpunit's
`session:down:success-clears`); the watchdog is all that is left of this requirement.
**Migration**: the requirement *A render session's watchdog ends with it*.

### Requirement: A pod is placed only on a host that can render

**Reason**: gpunit skips a card short of memory and refuses one the catalogue does not know (gpunit's `session:place:*`); the
floors themselves stay isekai's, as values in `gpunit.toml`.
**Migration**: the requirement *The session's spec asks for a host that can render*.

### Requirement: A pod stops itself at its ceiling

**Reason**: gpunit's boot script stops the pod at its ceiling and retries a failed stop (gpunit's `boot:stop:*`), and runs its
command without the provider's key (gpunit's `boot:child:no-key`); the start-up script no longer holds either.
**Migration**: the requirement *The pod stops itself through gpunit's boot at its ceiling* keeps what isekai still does.

### Requirement: A pod's host key is checked before anything is sent

**Reason**: gpunit checks the pod's host key against its printed fingerprint before anything connects, and keeps it
for that session alone (gpunit's `session:hostkey:*`).
**Migration**: `isekai render` opens its session through `gpunit.session()`, which refuses and tears down on a
mismatch, a missing fingerprint or an unanswered scan.

### Requirement: A pod runs beside its models volume

**Reason**: gpunit creates the pod in its volume's data centre, read from the volume (gpunit's
`session:volume:pins-datacenter`); the laptop-side size check is dropped, and the start-up script's capacity floor
holds a wrong disk on the pod (`model-provisioning:reachability:provisioning-requires-the-network-volume`).
**Migration**: `gpunit.toml` names the volume; `RUNPOD_DATACENTER` leaves `.env`.

### Requirement: No `isekai` pod goes unseen

**Reason**: gpunit refuses a session beside a recorded, pending or listed pod of the project, sweeps every listed one
at teardown, and reports a lost create (gpunit's `session:one:*`, `session:down:*`, `session:lost:*` and `library:*`).
**Migration**: pods are named `gpunit-isekai`; `uv run --env-file .env gpunit down` tears down what a session left.
