## MODIFIED Requirements

### Requirement: A pod makes its own host key and prints its fingerprint

The image SHALL carry no SSH host key, and SHALL boot through gpunit's boot script, added at a pinned tag with its
checksum, which makes each pod's host key and prints its fingerprint for the session to check.

A key baked into a public image is held by anyone who pulls it, so every pod presents the same identity and no check
against it proves anything. A key made at boot is the pod's own, and the printed line is what a client reads to
check it. The boot script's tag is pinned on its own, so the laptop's gpunit moves without a rebuild.

#### Scenario: the image carries no host key
- **Key:** `pod-image:host-key:the-image-carries-none`
- **Layers:** unit
- **WHEN** the image's build file is read
- **THEN** the step that installs the SSH server deletes the host keys it made, in the same step

#### Scenario: each boot makes and prints its own key
- **Key:** `pod-image:host-key:each-boot-makes-and-prints-one`
- **Layers:** unit
- **WHEN** the image's build file is read
- **THEN** its entrypoint is gpunit's boot script followed by `--`, added from a pinned gpunit tag, with a checksum
