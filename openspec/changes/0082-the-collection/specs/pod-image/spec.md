## MODIFIED Requirements

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
- **THEN** `isekai render` writes a refusal naming the ceiling to the collection's log
- **AND** the session closes, and it exits `143`
