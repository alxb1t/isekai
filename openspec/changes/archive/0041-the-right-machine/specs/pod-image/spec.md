## ADDED Requirements

### Requirement: A pod's host key is checked before anything is sent

The pod-creation script SHALL read the host-key fingerprint the pod printed to its log, SHALL scan the pod's host key
and compare them, and SHALL keep the key, for that pod alone, only when they match. On a mismatch, or when no
fingerprint line appears within a fixed time, it SHALL refuse and tear the pod down. The render session SHALL tunnel
to the pod only with the kept key.

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

The pod-creation script SHALL create every pod with the telemetry switches of the libraries it runs turned off.

The pod renders a person's likeness; nothing on it needs to report anything to anyone.

#### Scenario: the pod is created with telemetry off
- **Key:** `pod-image:telemetry:the-switches-are-off`
- **Layers:** unit
- **WHEN** the pod-creation script builds its request
- **THEN** the pod's environment turns off onnxruntime's and the Hugging Face hub's telemetry, and sets `DO_NOT_TRACK`

## MODIFIED Requirements

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
