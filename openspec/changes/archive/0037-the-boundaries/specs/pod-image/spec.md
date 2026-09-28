## ADDED Requirements

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
