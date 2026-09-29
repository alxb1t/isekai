## MODIFIED Requirements

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
