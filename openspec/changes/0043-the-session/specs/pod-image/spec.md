## ADDED Requirements

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
whose outcome is unknown SHALL name the teardown script.

A pod no file records bills with nothing watching it. A second creation overwrote the record and orphaned the first
pod, and a lost create left one only the provider's console could find.

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
- **THEN** it refuses before its trap is set, so its teardown cannot remove that pod

### Requirement: A pod stops itself at its ceiling

The pod SHALL stop itself through the provider's API, with the key the provider gives it, a stated time after it
starts, whatever happens to the machine that created it. A stop that fails SHALL be retried for a stated window and
then give up. ComfyUI SHALL start without that key in its environment.

A watchdog on the laptop dies with the laptop, and a pod left running bills with a photograph in its memory. ComfyUI
needs no key, and code it runs can print its environment into a log.

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

#### Scenario: a failed stop is retried, then given up
- **Key:** `pod-image:stop:a-failed-stop-is-retried`
- **Layers:** unit
- **WHEN** the provider does not answer the stop with success
- **THEN** the stop script tries again at a stated interval, and exits non-zero once a stated window has passed

#### Scenario: ComfyUI starts without the key
- **Key:** `pod-image:stop:comfyui-holds-no-key`
- **Layers:** unit
- **WHEN** the pod's start-up script starts ComfyUI
- **THEN** the provider's key is no longer in the start-up script's environment
