## MODIFIED Requirements

### Requirement: A render records the image and the runtime it ran on

The system SHALL record in every render the image reference a pod was booted from, and declare the render
pinned, when the pod-boot record names one; otherwise it SHALL record no image and declare the render
unpinned. It SHALL also record the ComfyUI, Python and PyTorch versions the endpoint reports about itself,
read once per session and only when a render will run.

The declared image says what should have run; the endpoint's own report says what did. Recording both is
what catches a pod that is not what the pin says, and an endpoint that is not a pod at all declares itself
unpinned rather than borrowing a pin it never had. Reading the report only when a render will run keeps a
completed batch inert.

#### Scenario: a render on a pinned pod records its image and runtime
- **Key:** `image-generation:runtime:a-pinned-pod-is-recorded`
- **Layers:** unit
- **WHEN** a render is written while the pod-boot record names an image
- **THEN** the render records that image and declares itself pinned
- **AND** it records the ComfyUI, Python and PyTorch versions the endpoint reported

#### Scenario: a render on an endpoint no pod-boot record names is unpinned
- **Key:** `image-generation:runtime:an-unrecorded-endpoint-is-unpinned`
- **Layers:** unit
- **WHEN** a render is written with no pod-boot record
- **THEN** the render records no image and declares itself unpinned

#### Scenario: a complete batch asks the endpoint nothing
- **Key:** `image-generation:runtime:a-complete-batch-reads-no-report`
- **Layers:** unit
- **WHEN** every requested seed is already rendered
- **THEN** the endpoint's report is not read

#### Scenario: a refused report is asked once and submits nothing
- **Key:** `image-generation:runtime:a-refused-report-is-asked-once`
- **Layers:** unit
- **WHEN** the endpoint's report is refused during a session
- **THEN** no graph is submitted in that session
- **AND** the endpoint is asked for its report once
