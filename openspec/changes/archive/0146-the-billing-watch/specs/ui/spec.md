## MODIFIED Requirements

### Requirement: Billing state is read from gpunit's own records

The system SHALL show a pod as possibly billing when gpunit holds a pod record or a pending create while no session
runs, SHALL ask gpunit for its status only on start, every half minute while a session runs or an alert is open, and
on Check again, and SHALL clear an alert only when gpunit confirms the pod or volume gone. It SHALL offer the alert's
way out on its own page, `/billing`, which the alert band opens. It SHALL show an open volume as a quiet item until
the end gpunit recorded for its window, and as the alert band after it. The page SHALL show unknown billing while
its first snapshot is pending and an open volume while one is recorded; it SHALL say nothing is billing only when
both pod and volume are known absent.

gpunit already records what it created; reading those records adds no state to disagree with them. Idle, the surface
reaches nothing.

#### Scenario: a pod record without a session is an alert
- **Key:** `ui:billing:a-pod-record-is-an-alert`
- **Layers:** unit
- **WHEN** gpunit holds a pod record and no session runs
- **THEN** the pod alert is shown
- **AND** Render is disabled

#### Scenario: an alert clears only on gpunit's word
- **Key:** `ui:billing:an-alert-clears-on-evidence`
- **Layers:** unit
- **WHEN** Check again is asked for and gpunit still reports the pod
- **THEN** the alert stays

#### Scenario: gpunit is asked while a session runs or an alert is open
- **Key:** `ui:billing:gpunit-is-asked-while-a-session-or-an-alert-is-open`
- **Layers:** unit
- **WHEN** the surface starts, and then a session runs, and then an alert is open, and then neither
- **THEN** gpunit is asked once on start, and again at each interval while a session runs or an alert is open
- **AND** it is asked no more once neither holds, or once the surface stops

#### Scenario: an ask that raises does not stop the asking
- **Key:** `ui:billing:an-ask-that-raises-does-not-stop-the-asking`
- **Layers:** unit
- **WHEN** an ask of gpunit raises, on start or at an interval while a session runs or an alert is open
- **THEN** gpunit is asked again at the next interval while a session runs or an alert is open
- **AND** Check again, asked for, still raises to its caller

#### Scenario: a volume past its window takes the band
- **Key:** `ui:billing:a-volume-past-its-window-takes-the-band`
- **Layers:** unit
- **WHEN** gpunit's window record ends in the past and the volume is still recorded
- **THEN** the alert band is shown in place of the quiet item

#### Scenario: billing clearance requires known absence
- **Key:** `ui:billing:clearance-requires-known-absence`
- **Layers:** unit
- **WHEN** billing is unknown, a volume is open, or both resources are known absent
- **THEN** the page respectively shows pending state, the open volume, or nothing billing
