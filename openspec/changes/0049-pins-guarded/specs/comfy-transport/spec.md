## MODIFIED Requirements

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

#### Scenario: a report in a shape this build does not read is permanent
- **Key:** `comfy-transport:runtime:an-unread-report-is-permanent`
- **Layers:** unit
- **WHEN** the system report does not carry the versions where they are read
- **THEN** the failure is permanent
- **AND** it is worded as any answer in a shape this build does not read

#### Scenario: a report the transport cannot fetch keeps the transport's kind
- **Key:** `comfy-transport:runtime:an-unfetched-report-keeps-its-kind`
- **Layers:** unit
- **WHEN** the request for the system report fails in the transport
- **THEN** the failure is classified as the same failure of any other call
