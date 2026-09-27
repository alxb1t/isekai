## ADDED Requirements

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
