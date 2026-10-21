## MODIFIED Requirements

### Requirement: The pod stops itself through gpunit's boot at its ceiling

The pod SHALL stop itself through gpunit's boot script at the session's own ceiling, its limit, whatever happens to
the machine that opened it; no session's ceiling SHALL exceed the hard maximum `gpunit.toml` names, and that maximum
with gpunit's timeout SHALL end before a fresh volume window does. The start-up script SHALL end every boot that does
not serve by exiting, so the boot script stops the pod, and SHALL hand its process to ComfyUI, so ComfyUI's exit is
the end of the boot.

A watchdog on the laptop dies with the laptop, and a pod left running bills with a photograph in its memory. A boot
that held forever, or a ComfyUI left running after its script was told to stop, would bill with nothing watching. A
window that ends before the longest session can is a session gpunit refuses to open.

#### Scenario: the pod arms its stop first
- **Key:** `pod-image:stop:armed-at-boot`
- **Layers:** unit
- **WHEN** `gpunit.toml` and the image's build file are read
- **THEN** the ceiling is no longer than three hours, and the image's entrypoint is gpunit's boot script

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

#### Scenario: a session's ceiling is its limit
- **Key:** `pod-image:stop:a-sessions-ceiling-is-its-limit`
- **Layers:** unit
- **WHEN** a render session opens with a limit
- **THEN** the spec gpunit receives carries that limit as its ceiling
- **AND** a limit over the hard maximum is refused before anything is rented

#### Scenario: the window outlasts the longest session
- **Key:** `pod-image:stop:the-window-outlasts-the-longest-session`
- **Layers:** unit
- **WHEN** `gpunit.toml` is read
- **THEN** its ceiling plus its timeout is shorter than its volume ceiling
