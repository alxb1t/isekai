## ADDED Requirements

### Requirement: The server's runtime is read from its own report

The system SHALL read the ComfyUI, Python and PyTorch versions from the endpoint's own system report through
the same transport seam every other call uses, and SHALL classify a failure of that call exactly as it
classifies the others.

The render records what ran it, and only the server knows. Reading the report through the seam keeps the
offline stand-in able to answer it, so the suite stays offline.

#### Scenario: the transport reads the server's versions
- **Key:** `comfy-transport:runtime:the-report-is-read-through-the-seam`
- **Layers:** unit
- **WHEN** the system report is requested
- **THEN** the transport returns the ComfyUI, Python and PyTorch versions the server reports
- **AND** the offline stand-in answers the same request without a network
